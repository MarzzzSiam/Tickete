from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections
from rest_framework.exceptions import ValidationError

from apps.checkin.services import cancel, scan
from apps.events.models import TicketCategory
from apps.events.reporting import close_event
from apps.orders.services import create_order, initiate_payment, verify_payment
from tests import test_operations, test_orders
from tests.test_operations import actor, client

event = test_orders.event
category = test_orders.category
prepared = test_operations.prepared
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "role,allowed",
    [
        ("owner", True),
        ("manager", True),
        ("viewer", True),
        ("admin", True),
        ("scanner", False),
        ("outsider", False),
    ],
)
def test_report_roles(prepared, role, allowed):
    owner, event, _ = prepared
    user = owner if role == "owner" else actor(event, role)
    api = client(user)
    base = f"/api/v1/events/{event.pk}"
    assert api.get(f"{base}/dashboard/").status_code == (200 if allowed else 403)
    assert api.get(f"{base}/report/").status_code == (409 if allowed else 403)
    if role != "owner":
        assert api.post(f"{base}/close/", {}, format="json").status_code == 403


def test_close_snapshot_counts_and_blocks_mutations(prepared, category):
    owner, event, tickets = prepared
    TicketCategory.objects.create(
        event=event, name="Unlimited", price=100, seat_limit=None, is_active=False
    )
    scan(owner, event.pk, tickets[0].code, "manual")
    cancel(owner, event.pk, tickets[1].pk)
    pending = create_order(test_orders.data(event, category, email="pending@example.com"))
    report = close_event(owner, event.pk)
    assert (
        report["sold"] == 2
        and report["checked_in"] == 1
        and report["cancelled"] == 1
        and report["not_checked_in"] == 0
    )
    assert report["revenue"] == "1000.00"
    assert next(c for c in report["categories"] if c["name"] == "General")["unsold"] == 3
    assert next(c for c in report["categories"] if c["name"] == "Unlimited")["unsold"] is None
    assert report == close_event(owner, event.pk)
    pending.refresh_from_db()
    assert pending.status == "expired" and pending.holds.get().status == "released"
    assert scan(owner, event.pk, tickets[0].code, "manual")["result"] == "event_unavailable"
    with pytest.raises(ValidationError):
        cancel(owner, event.pk, tickets[1].pk)
    with pytest.raises(Exception) as failure:
        create_order(test_orders.data(event, category, email="late@example.com"))
    assert getattr(failure.value, "status_code", None) == 409
    response = client(owner).get(f"/api/v1/events/{event.pk}/report/")
    assert response.status_code == 200 and response.data == report
    assert "buyer_email" not in str(report) and "qr_token" not in str(report)
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db(transaction=True)
def test_close_races_payment_without_partial_sale(event, category):
    owner = event.owner
    owner.email_verified = True
    owner.save()
    payload = test_orders.data(event, category)
    order = create_order(payload)
    initiate_payment(
        order.pk, payload["access_token"], {"provider": "dummy_bkash", "phone": "01700000000"}
    )
    barrier = Barrier(2)

    def pay():
        close_old_connections()
        try:
            barrier.wait()
            return verify_payment(order.pk, payload["access_token"], "123456").status
        finally:
            close_old_connections()

    def close():
        close_old_connections()
        try:
            barrier.wait()
            return close_event(owner, event.pk)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(2) as pool:
        payment = pool.submit(pay)
        closure = pool.submit(close)
        status, report = payment.result(), closure.result()
    order.refresh_from_db()
    category.refresh_from_db()
    assert status in ("paid", "expired")
    assert (
        report["sold"]
        == category.sold_count
        == order.tickets.count()
        == (1 if status == "paid" else 0)
    )
    assert order.holds.get().status == ("converted" if status == "paid" else "released")
