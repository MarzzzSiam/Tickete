from django.conf import settings
from django.middleware.csrf import get_token, rotate_token
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings

from . import services
from .authentication import enforce_csrf
from .models import EmailChallenge
from .serializers import (
    ChangePasswordSerializer,
    ConfirmSerializer,
    EmailSerializer,
    LoginSerializer,
    MessageSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResetConfirmSerializer,
)
from .tasks import deliver_account_link, send_account_link
from .throttles import AuthEmailThrottle, AuthIPThrottle, AuthUnavailable


class CsrfSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=CsrfSerializer, auth=[])
    def get(self, request):
        response = Response({"csrf_token": get_token(request)})
        response["Cache-Control"] = "no-store"
        return response


class AccountView(APIView):
    throttle_classes = [AuthIPThrottle]

    def initial(self, request, *args, **kwargs):
        # Applies even when no access cookie exists, including login/refresh/logout.
        enforce_csrf(request)
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class PublicAccountView(AccountView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthIPThrottle, AuthEmailThrottle]

    def get_authenticate_header(self, request):
        return 'Cookie realm="api"'


def validated(serializer_class, request):
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def session_response(request, user, tokens):
    response = Response(ProfileSerializer(user).data)
    access, refresh = tokens
    for name, value, lifetime, path in [
        (settings.AUTH_ACCESS_COOKIE, access, api_settings.ACCESS_TOKEN_LIFETIME, "/api/v1/"),
        (
            settings.AUTH_REFRESH_COOKIE,
            refresh,
            api_settings.REFRESH_TOKEN_LIFETIME,
            "/api/v1/auth/",
        ),
    ]:
        response.set_cookie(
            name,
            value,
            max_age=int(lifetime.total_seconds()),
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite="Lax",
            path=path,
        )
    rotate_token(request)
    return response


def clear_session_cookies(response):
    response.delete_cookie(settings.AUTH_ACCESS_COOKIE, path="/api/v1/", samesite="Lax")
    response.delete_cookie(settings.AUTH_REFRESH_COOKIE, path="/api/v1/auth/", samesite="Lax")
    return response


def enqueue_link(email, purpose):
    try:
        if settings.DEBUG and getattr(settings, "LOCAL_ACCOUNT_EMAIL_SYNC", False):
            # Bypass Celery retry scheduling in local mode. A failed SMTP request
            # fails once; the developer can retry after fixing configuration.
            send_account_link(email, purpose)
        else:
            deliver_account_link.apply_async(args=[email, purpose], retry=False)
    except Exception:
        raise AuthUnavailable() from None


class RegisterView(PublicAccountView):
    @extend_schema(request=RegisterSerializer, responses={201: ProfileSerializer})
    def post(self, request):
        user = services.register(validated(RegisterSerializer, request))
        # Verification is explicitly requested separately; registration cannot be
        # reported failed after a committed account creation due to a queue outage.
        return Response(ProfileSerializer(user).data, status=201)


class LoginView(PublicAccountView):
    @extend_schema(request=LoginSerializer, responses=ProfileSerializer)
    def post(self, request):
        user, tokens = services.login(**validated(LoginSerializer, request))
        return session_response(request, user, tokens)


class RefreshView(PublicAccountView):
    @extend_schema(request=None, responses=ProfileSerializer)
    def post(self, request):
        user, tokens = services.refresh_session(
            request.COOKIES.get(settings.AUTH_REFRESH_COOKIE, "")
        )
        return session_response(request, user, tokens)


class LogoutView(PublicAccountView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.logout(request.COOKIES.get(settings.AUTH_REFRESH_COOKIE, ""))
        return clear_session_cookies(Response(status=204))


class MeView(AccountView):
    @extend_schema(responses=ProfileSerializer)
    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=ProfileSerializer)
    def patch(self, request):
        data = validated(ProfileUpdateSerializer, request)
        for key, value in data.items():
            setattr(request.user, key, value)
        if data:
            request.user.save(update_fields=list(data))
        return Response(ProfileSerializer(request.user).data)


class ChangePasswordView(AccountView):
    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        services.change_password(request.user.pk, **validated(ChangePasswordSerializer, request))
        return clear_session_cookies(Response(status=204))


class VerifyRequestView(AccountView):
    @extend_schema(request=None, responses={202: MessageSerializer})
    def post(self, request):
        enqueue_link(request.user.email, EmailChallenge.Purpose.VERIFY)
        return Response({"detail": "Verification requested. Delivery may be delayed."}, status=202)


class VerifyConfirmView(PublicAccountView):
    @extend_schema(request=ConfirmSerializer, responses={204: None})
    def post(self, request):
        data = validated(ConfirmSerializer, request)
        services.consume_challenge(
            data["challenge_id"], data["token"], EmailChallenge.Purpose.VERIFY
        )
        return Response(status=204)


class ResetRequestView(PublicAccountView):
    @extend_schema(request=EmailSerializer, responses={202: MessageSerializer})
    def post(self, request):
        data = validated(EmailSerializer, request)
        # Dispatch for both known and unknown emails: no account lookup in this response.
        enqueue_link(data["email"], EmailChallenge.Purpose.RESET)
        return Response(
            {"detail": "If an eligible account exists, a reset link will be sent."}, status=202
        )


class ResetConfirmView(PublicAccountView):
    @extend_schema(request=ResetConfirmSerializer, responses={204: None})
    def post(self, request):
        data = validated(ResetConfirmSerializer, request)
        services.consume_challenge(
            data["challenge_id"], data["token"], EmailChallenge.Purpose.RESET, data["password"]
        )
        return clear_session_cookies(Response(status=204))
