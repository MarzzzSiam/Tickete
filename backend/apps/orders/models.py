import secrets
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


def order_number():
    return "TE-" + secrets.token_hex(8).upper()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid (simulated)"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=20, unique=True, default=order_number)
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    buyer_email = models.EmailField()
    recipient_email = models.EmailField()
    is_gift = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    access_digest = models.CharField(max_length=64)
    idempotency_key = models.UUIDField(unique=True)
    request_digest = models.CharField(max_length=64)
    snapshot = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["event", "buyer_email", "status"])]
        constraints = [
            models.CheckConstraint(condition=Q(total__gte=0), name="order_nonnegative_total"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="order_positive_quantity"),
        ]


class SeatHold(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="holds")
    category = models.ForeignKey("events.TicketCategory", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        default="active",
        choices=[("active", "Active"), ("converted", "Converted"), ("released", "Released")],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "category"], name="one_hold_per_category"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="hold_positive_quantity"),
        ]
        indexes = [models.Index(fields=["category", "status", "expires_at"])]
