import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def ticket_code():
    return "TE-" + secrets.token_hex(8).upper()


def qr_token():
    return secrets.token_urlsafe(32)


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, default=ticket_code, unique=True)
    qr_token = models.CharField(max_length=64, default=qr_token, unique=True)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="tickets")
    category = models.ForeignKey("events.TicketCategory", on_delete=models.PROTECT)
    attendee_name = models.CharField(max_length=150, blank=True)
    recipient_email = models.EmailField()
    status = models.CharField(
        max_length=12,
        default="valid",
        choices=[("valid", "Valid"), ("used", "Used"), ("cancelled", "Cancelled")],
    )
    position = models.PositiveIntegerField()
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["order", "position"], name="one_ticket_per_position")
        ]


class TicketDelivery(models.Model):
    """Durable local-worker queue; a row lock prevents concurrent processing."""

    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, primary_key=True)
    pdf_key = models.CharField(max_length=300, blank=True)
    recipient_sent = models.BooleanField(default=False)
    receipt_sent = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=40, blank=True)
    last_requested_at = models.DateTimeField(null=True, blank=True)


class TicketRecovery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    access_digest = models.CharField(max_length=64)
    code_digest = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)
    verified_at = models.DateTimeField(null=True)
    session_expires_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
    send_attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
