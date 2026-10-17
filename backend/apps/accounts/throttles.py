from django.utils.crypto import salted_hmac
from rest_framework.exceptions import APIException
from rest_framework.throttling import SimpleRateThrottle


class AuthUnavailable(APIException):
    status_code = 503
    default_detail = "Account service is temporarily unavailable. Please try again later."
    default_code = "account_service_unavailable"


class AuthIPThrottle(SimpleRateThrottle):
    scope = "auth_ip"

    def get_cache_key(self, request, view):
        # Do not trust forwarded IP headers from arbitrary clients.
        identity = request.META.get("REMOTE_ADDR", "unknown")
        key = salted_hmac("auth-throttle", identity).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": key}

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception:
            raise AuthUnavailable() from None


class AuthEmailThrottle(AuthIPThrottle):
    scope = "auth_email"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "") if isinstance(request.data, dict) else ""
        if not isinstance(email, str) or not email:
            return None
        identity = salted_hmac("auth-throttle-email", email.strip().lower()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": identity}
