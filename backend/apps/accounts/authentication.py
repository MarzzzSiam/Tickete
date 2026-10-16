from django.conf import settings
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication


def enforce_csrf(request):
    """Use for cookie-authenticated writes and anonymous login/refresh endpoints."""
    check = CSRFCheck(lambda request: None)
    check.process_request(request)
    if check.process_view(request, None, (), {}):
        raise PermissionDenied("CSRF validation failed.", code="csrf_failed")


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if not raw_token:
            return None
        token = self.get_validated_token(raw_token)
        enforce_csrf(request)
        return self.get_user(token), token
