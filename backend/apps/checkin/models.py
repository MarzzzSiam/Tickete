import uuid

from django.conf import settings
from django.db import models


class CheckInLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ticket = models.ForeignKey("tickets.Ticket", null=True, on_delete=models.PROTECT)
    result = models.CharField(max_length=20)
    method = models.CharField(max_length=10)
    input_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
