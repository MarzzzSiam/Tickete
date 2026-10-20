import uuid

from django.db import models


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=12)
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=10,
        default="initiated",
        choices=[("initiated", "Initiated"), ("success", "Success"), ("failed", "Failed")],
    )
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True)
