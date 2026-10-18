import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events"
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=230, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=300, blank=True)
    banner_key = models.CharField(max_length=300, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    sales_start = models.DateTimeField(null=True, blank=True)
    sales_end = models.DateTimeField(null=True, blank=True)
    max_per_order = models.PositiveIntegerField(default=10)
    collect_attendee_names = models.BooleanField(default=False)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    rejection_reason = models.TextField(blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviewed_events",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(max_per_order__gt=0), name="event_positive_order_cap"
            ),
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="event_time_order"
            ),
            models.CheckConstraint(
                condition=Q(sales_end__gt=F("sales_start")), name="event_sales_order"
            ),
            models.CheckConstraint(
                condition=Q(sales_end__lte=F("ends_at")), name="event_sales_before_end"
            ),
        ]


class TicketCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat_limit = models.PositiveIntegerField(null=True, blank=True)
    sold_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="category_nonnegative_price"),
            models.CheckConstraint(
                condition=Q(seat_limit__isnull=True) | Q(seat_limit__gt=0),
                name="category_positive_capacity",
            ),
            models.CheckConstraint(
                condition=Q(seat_limit__isnull=True) | Q(sold_count__lte=F("seat_limit")),
                name="category_sold_within_capacity",
            ),
        ]


class EventFormField(models.Model):
    class Type(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DROPDOWN = "dropdown", "Dropdown"
        CHECKBOX = "checkbox", "Checkbox"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="form_fields")
    label = models.CharField(max_length=150)
    type = models.CharField(max_length=10, choices=Type.choices)
    required = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
