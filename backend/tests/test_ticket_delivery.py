from unittest.mock import patch

import pytest
from django.core import mail
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.services import create_order
from apps.tickets.delivery import process_next
from apps.tickets.models import TicketDelivery
from apps.tickets.pdf import render_order_pdf
from tests import test_orders
from tests.test_orders import data, pay

event = test_orders.event
category = test_orders.category

pytestmark = pytest.mark.django_db


def paid_order(event, category, **extra):
    payload = data(event, category, quantity=2, **extra)
    order = pay(create_order(payload), payload["access_token"])
    return order, payload["access_token"]


def test_real_pdf_and_gift_delivery_are_private_and_replay_safe(event, category, tmp_path):
    order, token = paid_order(event, category, is_gift=True, recipient_email="gift@example.com")
    assert TicketDelivery.objects.filter(order=order).count() == 1
    with override_settings(
        MEDIA_ROOT=tmp_path,
        STORAGE_BACKEND="local",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ):
        assert process_next() == "sent"
        assert process_next() is None
        assert len(mail.outbox) == 2
        assert mail.outbox[0].to == ["gift@example.com"]
        assert mail.outbox[1].to == ["buyer@example.com"]
        assert len(mail.outbox[0].attachments) == 1
        assert not mail.outbox[1].attachments
        pdf = mail.outbox[0].attachments[0].content
        assert pdf.startswith(b"%PDF-")
        client = APIClient()
        route = f"/api/v1/orders/{order.id}/tickets.pdf"
        assert client.get(route).status_code == 404
        response = client.get(route, HTTP_X_CHECKOUT_TOKEN=token)
        assert response.status_code == 200
        assert response.content == pdf
        assert response["Cache-Control"] == "no-store"


def test_smtp_retry_reuses_pdf_and_does_not_resend_successful_gift(event, category, tmp_path):
    order, _ = paid_order(event, category, is_gift=True, recipient_email="gift@example.com")
    with override_settings(MEDIA_ROOT=tmp_path, STORAGE_BACKEND="local"):
        with patch("apps.tickets.delivery.render_order_pdf", return_value=b"%PDF-test") as renderer:
            with patch(
                "apps.tickets.delivery.EmailMessage.send", side_effect=[1, RuntimeError("secret")]
            ):
                assert process_next() == "email_failed"
            job = TicketDelivery.objects.get(order=order)
            assert job.recipient_sent and not job.receipt_sent
            assert job.last_error == "email_failed"
            assert process_next() is None
            job.next_attempt_at = timezone.now()
            job.save()
            with patch("apps.tickets.delivery.EmailMessage.send", return_value=1) as sender:
                assert process_next() == "sent"
                assert sender.call_count == 1
            assert renderer.call_count == 1


def test_pdf_failure_does_not_send_and_stops_after_five_attempts(event, category):
    order, _ = paid_order(event, category)
    with (
        patch("apps.tickets.delivery.render_order_pdf", side_effect=ValueError("secret")),
        patch("apps.tickets.delivery.EmailMessage.send") as sender,
    ):
        for _ in range(5):
            TicketDelivery.objects.filter(order=order).update(next_attempt_at=timezone.now())
            assert process_next() == "pdf_failed"
        assert process_next() is None
        sender.assert_not_called()


def test_pdf_escapes_user_text_and_refuses_network_fetch(event, category):
    order, _ = paid_order(event, category)
    order.snapshot["title"] = '<img src="https://example.invalid/private"> & Evening'
    with patch("httpx.get", side_effect=AssertionError("No remote assets")):
        assert render_order_pdf(order, list(order.tickets.all())).startswith(b"%PDF-")


def test_delivery_table_is_private():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname = 'tickets_ticketdelivery'"
        )
        assert cursor.fetchone() == (True,)
