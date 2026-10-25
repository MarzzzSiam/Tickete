from unittest.mock import patch

import httpx
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.test import override_settings

from apps.core.email import BrevoEmailBackend, MailDeliveryError


@override_settings(BREVO_API_KEY="fictional-test-key")
def test_email_payload_and_safe_errors():
    message = EmailMessage(
        "Verify", "Private link", "TICKETÉ <sender@example.com>", ["recipient@example.com"]
    )
    with patch("httpx.post") as post:
        assert BrevoEmailBackend().send_messages([message]) == 1
        assert post.call_args.kwargs["json"]["textContent"] == "Private link"
        assert post.call_args.kwargs["headers"]["api-key"] == "fictional-test-key"
        post.side_effect = httpx.ConnectError("sensitive provider detail")
        with pytest.raises(MailDeliveryError) as error:
            BrevoEmailBackend().send_messages([message])
        assert "sensitive" not in str(error.value)
        assert BrevoEmailBackend(fail_silently=True).send_messages([message]) == 0


@override_settings(BREVO_API_KEY="")
def test_email_fails_closed_without_credentials():
    with pytest.raises(ImproperlyConfigured):
        BrevoEmailBackend().send_messages([])


@override_settings(BREVO_API_KEY="fictional-test-key")
def test_pdf_attachment_is_encoded_without_public_file_url():
    from base64 import b64decode

    message = EmailMessage("Tickets", "Your tickets", "sender@example.com", ["buyer@example.com"])
    pdf = b"%PDF-1.7\nprivate ticket bytes\x00\xff"
    message.attach("tickets.pdf", pdf, "application/pdf")
    with patch("httpx.post") as post:
        assert BrevoEmailBackend().send_messages([message]) == 1
        attachment = post.call_args.kwargs["json"]["attachment"][0]
        assert attachment["name"] == "tickets.pdf"
        assert b64decode(attachment["content"]) == pdf
        assert "url" not in attachment
