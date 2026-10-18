import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=60)
    target_type = models.CharField(max_length=30)
    target_id = models.UUIDField()
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
