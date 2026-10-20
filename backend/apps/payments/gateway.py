import secrets
from typing import Any, Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class PaymentGateway(Protocol):
    """Provider boundary; dummy implementation and typed domain results arrive in Phase 2."""

    def initiate(self, order: Any) -> Any: ...
    def verify_otp(self, payment: Any, otp: str) -> Any: ...
    def status(self, payment: Any) -> Any: ...


class DummyGateway:
    """A visibly simulated gateway. No SMS, money movement or external calls."""

    def initiate(self, order):
        return order.total

    def verify_otp(self, payment, otp):
        return secrets.compare_digest(otp, "123456")

    def status(self, payment):
        return payment.status


def gateway():
    if settings.PAYMENT_GATEWAY != "dummy":
        raise ImproperlyConfigured("Only the explicitly simulated payment gateway is implemented.")
    return DummyGateway()
