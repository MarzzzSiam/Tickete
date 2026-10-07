from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class UnconfiguredProductionEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise ImproperlyConfigured("Transactional email provider is not configured yet.")
