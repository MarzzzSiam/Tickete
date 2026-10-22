from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from django.db import close_old_connections
from rest_framework.exceptions import ValidationError

from apps.events.coupons import CouponInput, create_coupon, toggle_coupon
from apps.events.models import Event
from apps.events.serializers import DraftInput, PublicEventSerializer
from apps.events.services import save_draft
from apps.orders.services import create_order, initiate_payment, quote_coupon, verify_payment
from apps.payments.models import Payment
from tests import test_orders
from tests.test_operations import actor, client

event = test_orders.event
category = test_orders.category
pytestmark = pytest.mark.django_db


def coupon_data(code="Tickete10", percentage=10):
    serializer = CouponInput(data={"code": code, "percentage": percentage})
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def test_creation_limits_duplicate_normalization_and_draft_atomicity(event):
    coupon = create_coupon(event.owner, event.pk, coupon_data())
    assert coupon.code == "TICKETE10"
    with pytest.raises(ValidationError):
        create_coupon(event.owner, event.pk, coupon_data("tickete10"))
    create_coupon(event.owner, event.pk, coupon_data("SECOND"))
    third = create_coupon(event.owner, event.pk, coupon_data("THIRD"))
    toggle_coupon(event.owner, event.pk, third.pk, False)
    with pytest.raises(ValidationError):
        create_coupon(event.owner, event.pk, coupon_data("FOURTH"))
    draft = DraftInput(
        data={"title": "Coupons at creation", "coupons": [{"code": "New10", "percentage": 10}]}
    )
    draft.is_valid(raise_exception=True)
    new = save_draft(event.owner, draft.validated_data)
    assert new.coupons.get().code == "NEW10"
    before = Event.objects.count()
    with pytest.raises(ValidationError):
        save_draft(event.owner, {"title": "Rollback", "coupons": [coupon_data(), coupon_data()]})
    assert Event.objects.count() == before
    assert "coupons" not in PublicEventSerializer(event).data


@pytest.mark.parametrize("percentage", [0, -1, 100, 101, 10.5])
def test_percentage_validation(percentage):
    with pytest.raises(ValidationError):
        coupon_data(percentage=percentage)


@pytest.mark.parametrize("role", ["manager", "viewer", "scanner", "admin", "outsider"])
def test_only_owner_can_read_create_or_pause(event, role):
    coupon = create_coupon(event.owner, event.pk, coupon_data())
    api = client(actor(event, role))
    url = f"/api/v1/events/{event.pk}/coupons/"
    assert api.get(url).status_code == 404
    assert api.post(url, coupon_data("OTHER"), format="json").status_code == 404
    assert api.patch(f"{url}{coupon.pk}/", {"is_active": False}, format="json").status_code == 404
    owner = client(event.owner)
    assert owner.get(url).status_code == 200
    assert owner.get(url)["Cache-Control"] == "no-store"


def test_server_price_quote_rounding_payment_and_replay(event, category):
    create_coupon(event.owner, event.pk, coupon_data())
    category.price = Decimal("10.05")
    category.save()
    payload = test_orders.data(event, category, coupon_code="tickete10")
    quote = quote_coupon(payload)
    assert quote["subtotal"] == "10.05" and quote["discount"] == "1.01" and quote["total"] == "9.04"
    order = create_order(payload)
    assert order.total == Decimal("9.04")
    assert order.snapshot["coupon"]["code"] == "TICKETE10"
    assert create_order(payload).pk == order.pk
    paid = test_orders.pay(order, payload["access_token"])
    assert paid.status == "paid" and paid.tickets.count() == 1
    assert Payment.objects.get(order=order).amount == Decimal("9.04")


def test_pause_expires_pending_not_paid_and_resume_requires_new_order(event, category):
    coupon = create_coupon(event.owner, event.pk, coupon_data())
    paid_data = test_orders.data(event, category, coupon_code=coupon.code)
    paid = test_orders.pay(create_order(paid_data), paid_data["access_token"])
    pending_data = test_orders.data(
        event, category, coupon_code=coupon.code, email="pending@example.com"
    )
    pending = create_order(pending_data)
    initiate_payment(
        pending.pk,
        pending_data["access_token"],
        {"provider": "dummy_bkash", "phone": "01700000000"},
    )
    toggle_coupon(event.owner, event.pk, coupon.pk, False)
    pending.refresh_from_db()
    paid.refresh_from_db()
    assert pending.status == "expired" and pending.holds.get().status == "released"
    assert Payment.objects.get(order=pending).status == "failed"
    assert paid.status == "paid" and paid.tickets.get().status == "valid"
    assert verify_payment(pending.pk, pending_data["access_token"], "123456").status == "expired"
    with pytest.raises(ValidationError):
        quote_coupon(pending_data)
    with pytest.raises(ValidationError):
        create_order(test_orders.data(event, category, coupon_code=coupon.code))
    toggle_coupon(event.owner, event.pk, coupon.pk, True)
    assert create_order(pending_data).status == "expired"
    assert create_order(test_orders.data(event, category, coupon_code=coupon.code)).total == 450


def test_event_scoping_zero_total_and_closed_event(event, category):
    create_coupon(event.owner, event.pk, coupon_data())
    other = Event.objects.create(owner=event.owner, title="Other")
    create_coupon(event.owner, other.pk, coupon_data("OTHER"))
    with pytest.raises(ValidationError):
        create_order(test_orders.data(event, category, coupon_code="OTHER"))
    coupon = create_coupon(event.owner, event.pk, coupon_data("NINETYNINE", 99))
    category.price = Decimal("0.01")
    category.save()
    with pytest.raises(ValidationError):
        create_order(test_orders.data(event, category, coupon_code=coupon.code))
    from django.utils import timezone

    event.closed_at = timezone.now()
    event.save()
    with pytest.raises(ValidationError):
        toggle_coupon(event.owner, event.pk, coupon.pk, False)
    with pytest.raises(ValidationError):
        create_coupon(event.owner, event.pk, coupon_data("CLOSED"))


@pytest.mark.django_db(transaction=True)
def test_pause_and_payment_are_serialized(event, category):
    coupon = create_coupon(event.owner, event.pk, coupon_data())
    payload = test_orders.data(event, category, coupon_code=coupon.code)
    order = create_order(payload)
    initiate_payment(
        order.pk, payload["access_token"], {"provider": "dummy_bkash", "phone": "01700000000"}
    )
    barrier = Barrier(2)

    def run(pay):
        close_old_connections()
        try:
            barrier.wait()
            if pay:
                return verify_payment(order.pk, payload["access_token"], "123456").status
            return toggle_coupon(event.owner, event.pk, coupon.pk, False)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(2) as pool:
        payment, pause = pool.submit(run, True), pool.submit(run, False)
        status = payment.result()
        pause.result()
    order.refresh_from_db()
    assert order.status == status and status in ("paid", "expired")
    assert order.tickets.count() == (1 if status == "paid" else 0)
    assert order.holds.get().status == ("converted" if status == "paid" else "released")


@pytest.mark.django_db(transaction=True)
def test_concurrent_creation_cannot_exceed_three(event):
    create_coupon(event.owner, event.pk, coupon_data("FIRST"))
    create_coupon(event.owner, event.pk, coupon_data("SECOND"))
    barrier = Barrier(2)

    def run(code):
        close_old_connections()
        try:
            barrier.wait()
            try:
                create_coupon(event.owner, event.pk, coupon_data(code))
                return "created"
            except ValidationError:
                return "limited"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(2) as pool:
        one, two = pool.submit(run, "THIRD"), pool.submit(run, "FOURTH")
        assert sorted([one.result(), two.result()]) == ["created", "limited"]
    assert event.coupons.count() == 3


def test_checkout_rejects_client_prices_and_quote_duplicate_categories(event, category):
    from apps.orders.serializers import CheckoutInput, QuoteInput

    payload = test_orders.data(event, category)
    for field in ("total", "discount", "percentage"):
        serializer = CheckoutInput(data={**payload, field: "1.00"})
        assert not serializer.is_valid()
    quote = QuoteInput(
        data={
            "event_id": str(event.pk),
            "coupon_code": "CODE",
            "selections": [{"category_id": str(category.pk), "quantity": 1}] * 2,
        }
    )
    assert not quote.is_valid()
