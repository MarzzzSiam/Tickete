from smtplib import SMTPAuthenticationError
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.core.email import MailDeliveryError, SafeSMTPEmailBackend


def backend(**kwargs):
    return SafeSMTPEmailBackend(
        username="sender@example.com", password="fictional-app-password", use_tls=True, **kwargs
    )


def test_smtp_uses_authenticated_encrypted_connection():
    message = EmailMessage("Test", "Body", "sender@example.com", ["recipient@example.com"])
    with patch("apps.core.email.DjangoSMTPBackend") as smtp:
        smtp.return_value.__enter__.return_value.send_messages.return_value = 1
        assert backend().send_messages([message]) == 1
        assert smtp.call_args.kwargs["use_tls"] is True
        assert smtp.call_args.kwargs["fail_silently"] is False
        smtp.return_value.__enter__.return_value.send_messages.assert_called_once_with([message])


@pytest.mark.parametrize(
    "error", [SMTPAuthenticationError(535, b"private details"), OSError("secret")]
)
def test_smtp_failure_is_safe_and_retryable(error):
    with patch("apps.core.email.DjangoSMTPBackend", side_effect=error):
        with pytest.raises(MailDeliveryError) as exc:
            backend().send_messages([MagicMock()])
        assert "private" not in str(exc.value)
        assert "secret" not in str(exc.value)
        assert backend(fail_silently=True).send_messages([MagicMock()]) == 0


def test_smtp_rejects_missing_credentials_and_plaintext():
    with pytest.raises(ImproperlyConfigured):
        SafeSMTPEmailBackend(username="", password="", use_tls=True).send_messages([])
    with pytest.raises(ImproperlyConfigured):
        SafeSMTPEmailBackend(
            username="sender", password="test", use_tls=False, use_ssl=False
        ).send_messages([])


@override_settings(EMAIL_PROVIDER="smtp")
def test_test_email_command_reports_acceptance_without_tokens():
    with patch("apps.core.management.commands.test_email.send_mail", return_value=1) as send:
        call_command("test_email", to="sender@example.com")
        assert send.call_args.args[3] == ["sender@example.com"]
        assert "token" not in send.call_args.args[1]


@override_settings(EMAIL_PROVIDER="console")
def test_test_email_command_rejects_console_backend():
    with pytest.raises(CommandError):
        call_command("test_email", to="sender@example.com")
