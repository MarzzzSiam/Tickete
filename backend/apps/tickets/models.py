import secrets
import uuid

from django.db import models


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

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["order", "position"], name="one_ticket_per_position")
        ]
