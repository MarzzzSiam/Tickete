from base64 import b64encode
from smtplib import SMTPAuthenticationError, SMTPException, SMTPServerDisconnected

from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend


class MailDeliveryError(Exception):
    """Safe, credential-free provider failure that background jobs may retry."""


class SafeSMTPEmailBackend(DjangoSMTPBackend):
    """Django SMTP delivery with sanitized failures for Celery retries."""

    def send_messages(self, email_messages):
        if not self.username or not self.password:
            raise ImproperlyConfigured(
                "Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD privately before enabling SMTP."
            )
        if not (self.use_tls or self.use_ssl):
            raise ImproperlyConfigured("SMTP delivery requires TLS or SSL.")
        # Django's fail_silently handling would hide partial delivery failures.
        # Use a separate connection so every error reaches this safe boundary.
        try:
            with DjangoSMTPBackend(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                use_ssl=self.use_ssl,
                timeout=self.timeout,
                fail_silently=False,
            ) as connection:
                return connection.send_messages(email_messages)
        except (SMTPException, OSError) as exc:
            if self.fail_silently:
                return 0
            if isinstance(exc, SMTPAuthenticationError):
                raise MailDeliveryError(
                    "SMTP authentication rejected. Check the sender account and Google app password."
                ) from None
            if isinstance(exc, SMTPServerDisconnected):
                raise MailDeliveryError(
                    "SMTP connection closed unexpectedly. This does not confirm a bad password. "
                    "Check Google account alerts and retry on another network."
                ) from None
            raise MailDeliveryError(
                "SMTP delivery failed. Check credentials, provider limits and network access."
            ) from None


class BrevoEmailBackend(BaseEmailBackend):
    """Transactional HTTPS delivery; never uses a personal mailbox password."""

    def send_messages(self, email_messages):
        from email.utils import parseaddr

        import httpx
        from django.conf import settings

        if not settings.BREVO_API_KEY:
            raise ImproperlyConfigured("Set BREVO_API_KEY privately before enabling Brevo.")
        sent = 0
        for message in email_messages:
            name, sender = parseaddr(message.from_email)
            if not sender or sender.endswith(".invalid"):
                raise ImproperlyConfigured("Set DEFAULT_FROM_EMAIL to your verified sender.")
            if message.cc or message.bcc:
                raise ImproperlyConfigured("This email adapter does not support CC or BCC.")
            payload = {
                "sender": {"email": sender, "name": name or "TICKETÉ"},
                "to": [{"email": address} for address in message.to],
                "subject": message.subject,
                "textContent": message.body,
            }
            if message.attachments:
                attachments = []
                for attachment in message.attachments:
                    if not isinstance(attachment, tuple) or len(attachment) != 3:
                        raise ImproperlyConfigured("Only named file attachments are supported.")
                    filename, content, _ = attachment
                    if not filename:
                        raise ImproperlyConfigured("Email attachments require a filename.")
                    if isinstance(content, str):
                        content = content.encode(message.encoding or "utf-8")
                    attachments.append(
                        {"name": filename, "content": b64encode(content).decode("ascii")}
                    )
                payload["attachment"] = attachments
            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    payload["htmlContent"] = content
                    payload.pop("textContent", None)
            if message.reply_to:
                payload["replyTo"] = {"email": parseaddr(message.reply_to[0])[1]}
            try:
                response = httpx.post(
                    "https://api.brevo.com/v3/smtp/email",
                    json=payload,
                    headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
                    timeout=15,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                # Provider bodies and request headers can contain private content.
                if not self.fail_silently:
                    raise MailDeliveryError("Email provider did not confirm acceptance.") from None
            else:
                sent += 1
        return sent


class UnconfiguredProductionEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise ImproperlyConfigured("Transactional email provider is not configured yet.")
