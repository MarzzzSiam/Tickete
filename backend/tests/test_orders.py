import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.http import Http404
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.events.models import Event, EventFormField, TicketCategory
from apps.orders.models import Order, SeatHold
from apps.orders.serializers import CheckoutInput
from apps.orders.services import (
    CheckoutConflict,
    cancel_order,
    create_order,
    initiate_payment,
    read_order,
    verify_payment,
)
from apps.payments.models import Payment
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


@pytest.fixture
def event():
    now = timezone.now()
    owner = User.objects.create_user("organizer@example.com", role="organizer")
    return Event.objects.create(
        owner=owner,
        title="Checkout test",
        slug="checkout-test",
        status="approved",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=2),
        sales_start=now - timedelta(days=1),
        sales_end=now + timedelta(hours=2),
        max_per_order=5,
        collect_attendee_names=True,
    )


@pytest.fixture
def category(event):
    return TicketCategory.objects.create(event=event, name="General", price="500.00", seat_limit=5)


def data(event, category, quantity=1, email="buyer@example.com", **extra):
    payload = {
        "event_id": str(event.id),
        "buyer_email": email,
        "selections": [{"category_id": str(category.id), "quantity": quantity}],
        "idempotency_key": str(uuid.uuid4()),
        "access_token": secrets.token_urlsafe(32),
        **extra,
    }
    serializer = CheckoutInput(data=payload)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def pay(order, token, otp="123456"):
    initiate_payment(order.id, token, {"provider": "dummy_bkash", "phone": "01700000000"})
    return verify_payment(order.id, token, otp)


def test_hold_payment_replay_and_private_access(event, category):
    payload = data(event, category, 2)
    order = create_order(payload)
    assert order.total == 1000
    assert create_order(payload).id == order.id
    assert Order.objects.count() == 1
    assert Ticket.objects.count() == 0
    with pytest.raises(NotFound):
        read_order(order.id, "wrong")
    paid = pay(order, payload["access_token"])
    assert paid.status == "paid"
    assert pay(order, payload["access_token"]).status == "paid"
    category.refresh_from_db()
    assert category.sold_count == 2
    assert Ticket.objects.count() == 2
    assert len(set(Ticket.objects.values_list("qr_token", flat=True))) == 2
    assert order.holds.get().status == "converted"


def test_cap_counts_paid_and_pending_across_categories_normalized_email(event, category):
    second = TicketCategory.objects.create(event=event, name="VIP", price="1000", seat_limit=None)
    first = data(event, category, 2, "Buyer@Example.com")
    pay(create_order(first), first["access_token"])
    create_order(data(event, second, 3))
    with pytest.raises(CheckoutConflict):
        create_order(data(event, second))


def test_expiry_releases_allowance_and_blocks_payment(event, category):
    payload = data(event, category, 5)
    order = create_order(payload)
    deadline = timezone.now() - timedelta(seconds=1)
    Order.objects.filter(pk=order.pk).update(expires_at=deadline)
    SeatHold.objects.filter(order=order).update(expires_at=deadline)
    assert pay(order, payload["access_token"]).status == "expired"
    assert order.holds.get().status == "released"
    create_order(data(event, category, 5))
    assert Ticket.objects.count() == 0


def test_wrong_otp_exhausts_attempts_and_releases_hold(event, category):
    payload = data(event, category)
    order = create_order(payload)
    for _ in range(5):
        order = pay(order, payload["access_token"], "000000")
    assert order.status == "failed"
    assert pay(order, payload["access_token"]).status == "failed"
    assert Ticket.objects.count() == 0
    assert Payment.objects.get().attempts == 5
    assert order.holds.get().status == "released"


def test_gift_optional_names_and_question_snapshot(event, category):
    field = EventFormField.objects.create(
        event=event, label="Meal", type="dropdown", required=True, options=["Vegetarian"]
    )
    payload = data(
        event,
        category,
        is_gift=True,
        recipient_email="Friend@Example.com",
        answers={str(field.id): "Vegetarian"},
    )
    order = pay(create_order(payload), payload["access_token"])
    assert order.buyer_email == "buyer@example.com"
    assert order.recipient_email == "friend@example.com"
    assert order.snapshot["answers"][0]["label"] == "Meal"
    assert order.tickets.get().attendee_name == ""
    with pytest.raises(ValidationError):
        create_order(data(event, category))


@pytest.mark.parametrize("change", ["free", "inactive", "closed", "not_approved", "capacity"])
def test_invalid_sales_cannot_reserve(event, category, change):
    if change == "free":
        category.price = 0
    if change == "inactive":
        category.is_active = False
    if change == "capacity":
        category.sold_count = category.seat_limit
    category.save()
    if change == "closed":
        event.sales_end = timezone.now() - timedelta(minutes=1)
    if change == "not_approved":
        event.status = "draft"
    event.save()
    with pytest.raises((ValidationError, CheckoutConflict, NotFound, Http404)):
        create_order(data(event, category))
    assert Order.objects.count() == 0


def test_idempotency_rejects_changed_body_and_cancel_is_terminal(event, category):
    payload = data(event, category)
    order = create_order(payload)
    changed = {**payload, "buyer_email": "other@example.com"}
    with pytest.raises(CheckoutConflict):
        create_order(changed)
    assert cancel_order(order.id, payload["access_token"]).status == "failed"
    assert pay(order, payload["access_token"]).status == "failed"
    assert category.sold_count == 0


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_api_requires_csrf_and_capability(event, category):
    client = APIClient(enforce_csrf_checks=True)
    payload = data(event, category)
    assert client.post("/api/v1/orders/", payload, format="json").status_code == 403
    csrf = client.get("/api/v1/auth/csrf/").data["csrf_token"]
    response = client.post("/api/v1/orders/", payload, format="json", HTTP_X_CSRFTOKEN=csrf)
    assert response.status_code == 200, response.data
    pk = response.data["id"]
    assert client.get(f"/api/v1/orders/{pk}/status/").status_code == 404
    result = client.get(
        f"/api/v1/orders/{pk}/status/", HTTP_X_CHECKOUT_TOKEN=payload["access_token"]
    )
    assert result.status_code == 200
    assert result["Cache-Control"] == "no-store"
    assert "access_digest" not in result.data
    assert result.data["delivery_status"] == "not_implemented"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("same_email", [False, True])
def test_competing_checkouts_do_not_oversell_or_exceed_email_cap(event, category, same_email):
    category.seat_limit = 1 if not same_email else 5
    category.save()
    event.max_per_order = 1
    event.save()
    other = (
        TicketCategory.objects.create(event=event, name="Other", price="100", seat_limit=5)
        if same_email
        else category
    )
    barrier = Barrier(2)
    payloads = [
        data(event, category),
        data(event, other, email="BUYER@example.com" if same_email else "other@example.com"),
    ]

    def attempt(payload):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            create_order(payload)
            return "held"
        except CheckoutConflict:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, payloads)) == ["conflict", "held"]
    assert Order.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_simultaneous_verification_issues_once(event, category):
    payload = data(event, category, 2)
    order = create_order(payload)
    initiate_payment(
        order.id, payload["access_token"], {"provider": "dummy_bkash", "phone": "01700000000"}
    )
    barrier = Barrier(2)

    def verify(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return verify_payment(order.id, payload["access_token"], "123456").status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(verify, [1, 2])) == ["paid", "paid"]
    category.refresh_from_db()
    assert category.sold_count == Ticket.objects.count() == 2


def test_checkout_tables_are_private():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname IN ('orders_order','orders_seathold','payments_payment','tickets_ticket')"
        )
        rows = cursor.fetchall()
    assert len(rows) == 4 and all(row[0] for row in rows)
