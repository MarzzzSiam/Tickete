from uuid import UUID

from django.conf import settings
from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AuthSession


def enforce_csrf(request):
    """Use for cookie-authenticated writes and anonymous login/refresh endpoints."""
    check = CSRFCheck(lambda request: None)
    check.process_request(request)
    if check.process_view(request, None, (), {}):
        raise PermissionDenied("CSRF validation failed.", code="csrf_failed")


class CookieJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        try:
            session_id = UUID(validated_token["sid"])
        except (KeyError, ValueError, TypeError, AttributeError):
            raise AuthenticationFailed("Invalid session.") from None
        if not AuthSession.objects.filter(
            pk=session_id, user=user, revoked_at__isnull=True, expires_at__gt=timezone.now()
        ).exists():
            raise AuthenticationFailed("Session has ended.")
        return user

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if not raw_token:
            return None
        token = self.get_validated_token(raw_token)
        enforce_csrf(request)
        return self.get_user(token), token


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.CookieJWTAuthentication"
    name = "cookieJWT"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "cookie", "name": settings.AUTH_ACCESS_COOKIE}
