import re
import secrets
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.test import APIClient

from apps.orders.services import cleanup_expired_holds, create_order
from apps.tickets import recovery
from apps.tickets.delivery import process_next
from apps.tickets.models import Ticket, TicketDelivery, TicketRecovery
from tests import test_orders
from tests.test_orders import data, pay

event = test_orders.event
category = test_orders.category
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def local_mail():
    with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
        yield


def session(email="buyer@example.com"):
    token = secrets.token_urlsafe(32)
    item = recovery.start(email, token)
    assert recovery.process_recovery() == "recovery_code_sent"
    code = re.search(r"code is (\d{6})", mail.outbox[-1].body)[1]
    return item, token, code


def test_code_is_private_single_use_and_email_bound(event, category):
    payload = data(event, category)
    order = pay(create_order(payload), payload["access_token"])
    item, token, code = session("BUYER@example.com")
    item.refresh_from_db()
    assert item.code_digest != code and item.access_digest != token
    with pytest.raises(NotFound):
        recovery.authorized(item.pk, token)
    with pytest.raises(NotFound):
        recovery.verify(item.pk, "wrong-token", code)
    item = recovery.verify(item.pk, token, code)
    assert list(recovery.orders_for(item)) == [order]
    assert not item.code_digest
    with pytest.raises(ValidationError):
        recovery.verify(item.pk, token, code)
    item.session_expires_at = timezone.now() - timedelta(seconds=1)
    item.save()
    with pytest.raises(NotFound):
        recovery.authorized(item.pk, token)


def test_five_wrong_codes_lock_session_and_expired_codes_fail():
    item, token, code = session()
    bad = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(ValidationError):
            recovery.verify(item.pk, token, bad)
    item.refresh_from_db()
    assert item.attempts == 5
    with pytest.raises(ValidationError):
        recovery.verify(item.pk, token, code)
    other, token, code = session("other@example.com")
    other.expires_at = timezone.now() - timedelta(seconds=1)
    other.save()
    with pytest.raises(ValidationError):
        recovery.verify(other.pk, token, code)


def test_unknown_email_gets_same_response_and_no_purchase_data():
    item, token, code = session("unknown@example.com")
    item = recovery.verify(item.pk, token, code)
    assert recovery.orders_for(item).count() == 0
    assert mail.outbox[-1].to == ["unknown@example.com"]


def test_mail_retries_are_bounded_without_storing_code_or_provider_error():
    item = recovery.start("nobody@example.com", secrets.token_urlsafe(32))
    with patch("apps.tickets.recovery.send_mail", side_effect=RuntimeError("private password")):
        for _ in range(5):
            TicketRecovery.objects.filter(pk=item.pk).update(next_attempt_at=timezone.now())
            assert recovery.process_recovery() == "recovery_email_failed"
        assert recovery.process_recovery() is None
    item.refresh_from_db()
    assert not item.code_digest and not item.sent_at
    stale = recovery.start("stale@example.com", secrets.token_urlsafe(32))
    stale.created_at = timezone.now() - timedelta(minutes=31)
    stale.save()
    assert recovery.process_recovery() is None


def test_recovery_routes_gifts_resend_and_original_ticket_identity(event, category, tmp_path):
    payload = data(event, category, is_gift=True, recipient_email="friend@example.com")
    order = pay(create_order(payload), payload["access_token"])
    original = list(Ticket.objects.values_list("id", "qr_token"))
    with (
        override_settings(MEDIA_ROOT=tmp_path, STORAGE_BACKEND="local"),
        patch("apps.tickets.delivery.render_order_pdf", return_value=b"%PDF-test"),
    ):
        assert process_next() == "sent"
        item, token, code = session()
        recovery.verify(item.pk, token, code)
        client = APIClient()
        headers = {"HTTP_X_RECOVERY_TOKEN": token}
        base = f"/api/v1/tickets/recovery/{item.pk}/orders/"
        assert client.get(base).status_code == 404
        response = client.get(base, **headers)
        assert response.status_code == 200 and response["Cache-Control"] == "no-store"
        assert response.data["results"][0]["can_download"] is False
        assert "qr_token" not in str(response.data)
        assert client.get(f"{base}{order.pk}/pdf/", **headers).status_code == 404
        assert (
            client.post(
                f"{base}{order.pk}/resend/",
                {"recipient_email": "thief@example.com"},
                format="json",
                **headers,
            ).status_code
            == 400
        )
        assert (
            client.post(f"{base}{order.pk}/resend/", {}, format="json", **headers).status_code
            == 202
        )
        assert (
            client.post(f"{base}{order.pk}/resend/", {}, format="json", **headers).status_code
            == 400
        )
        assert process_next() == "sent"
        assert mail.outbox[-2].to == ["friend@example.com"]
        assert mail.outbox[-1].to == ["buyer@example.com"]
        assert original == list(Ticket.objects.values_list("id", "qr_token"))
        friend, friend_token, friend_code = session("friend@example.com")
        recovery.verify(friend.pk, friend_token, friend_code)
        url = f"/api/v1/tickets/recovery/{friend.pk}/orders/{order.pk}/pdf/"
        response = client.get(url, HTTP_X_RECOVERY_TOKEN=friend_token)
        assert response.content == b"%PDF-test"
        stranger, stranger_token, stranger_code = session("stranger@example.com")
        recovery.verify(stranger.pk, stranger_token, stranger_code)
        assert (
            client.get(
                f"/api/v1/tickets/recovery/{stranger.pk}/orders/{order.pk}/pdf/",
                HTTP_X_RECOVERY_TOKEN=stranger_token,
            ).status_code
            == 404
        )
        Ticket.objects.filter(order=order).update(status="used")
        TicketDelivery.objects.filter(order=order).update(last_requested_at=None)
        recovery.resend(recovery.authorized(friend.pk, friend_token), order.pk)
        assert process_next() == "sent"
        assert Ticket.objects.get(order=order).status == "used"


def test_csrf_required_and_recovery_header_allowed():
    client = APIClient(enforce_csrf_checks=True)
    assert (
        client.post(
            "/api/v1/tickets/recovery/",
            {"email": "any@example.com", "access_token": secrets.token_urlsafe(32)},
        ).status_code
        == 403
    )
    response = client.options(
        "/api/v1/tickets/recovery/",
        HTTP_ORIGIN="http://127.0.0.1:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-recovery-token",
    )
    assert "x-recovery-token" in response["Access-Control-Allow-Headers"]


def test_cleanup_releases_only_expired_pending_holds(event, category):
    payload = data(event, category)
    order = create_order(payload)
    paid_payload = data(event, category, email="paid@example.com")
    paid = pay(create_order(paid_payload), paid_payload["access_token"])
    order.expires_at = timezone.now() - timedelta(seconds=1)
    order.save()
    assert cleanup_expired_holds() == 1
    assert cleanup_expired_holds() == 0
    order.refresh_from_db()
    paid.refresh_from_db()
    category.refresh_from_db()
    assert order.status == "expired" and order.holds.get().status == "released"
    assert paid.status == "paid" and category.sold_count == 1


def test_recovery_table_has_rls():
    with connection.cursor() as cursor:
        cursor.execute("SELECT relrowsecurity FROM pg_class WHERE relname='tickets_ticketrecovery'")
        assert cursor.fetchone() == (True,)


def test_request_verify_api_and_throttle_fail_closed():
    client = APIClient()
    token = secrets.token_urlsafe(32)
    response = client.post(
        "/api/v1/tickets/recovery/",
        {"email": "api@example.com", "access_token": token},
        format="json",
    )
    assert response.status_code == 202
    pk = response.data["id"]
    assert recovery.process_recovery() == "recovery_code_sent"
    code = re.search(r"code is (\d{6})", mail.outbox[-1].body)[1]
    response = client.post(
        f"/api/v1/tickets/recovery/{pk}/verify/",
        {"code": code},
        format="json",
        HTTP_X_RECOVERY_TOKEN=token,
    )
    assert response.status_code == 200
    assert (
        client.get(f"/api/v1/tickets/recovery/{pk}/orders/", HTTP_X_RECOVERY_TOKEN=token).data[
            "count"
        ]
        == 0
    )
    with patch(
        "apps.accounts.throttles.AuthIPThrottle.cache.get", side_effect=RuntimeError("private")
    ):
        response = client.post(
            "/api/v1/tickets/recovery/",
            {"email": "api@example.com", "access_token": token},
            format="json",
        )
    assert response.status_code == 503 and "private" not in str(response.data)


def test_recovery_email_budget_rejects_repeated_requests():
    from django.core.cache import cache

    cache.clear()
    client = APIClient()
    payload = {"email": "budget@example.com", "access_token": secrets.token_urlsafe(32)}
    for _ in range(5):
        assert client.post("/api/v1/tickets/recovery/", payload, format="json").status_code == 202
    assert client.post("/api/v1/tickets/recovery/", payload, format="json").status_code == 429
    cache.clear()
