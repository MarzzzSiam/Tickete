from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.authentication import CookieJWTAuthentication, enforce_csrf


def request_with_cookie(method="get", token=None, csrf=False, origin=None):
    request = getattr(APIRequestFactory(enforce_csrf_checks=True), method)("/api/v1/test/")
    request.COOKIES[settings.AUTH_ACCESS_COOKIE] = str(token or AccessToken())
    if csrf:
        request.META["HTTP_X_CSRFTOKEN"] = get_token(request)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
    if origin:
        request.META["HTTP_ORIGIN"] = origin
    return request


def test_csrf_bootstrap_sets_cookie_and_is_not_cacheable():
    response = APIClient(enforce_csrf_checks=True).get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    assert response.json()["csrf_token"]
    assert settings.CSRF_COOKIE_NAME in response.cookies
    assert response["Cache-Control"] == "no-store"


def test_no_cookie_is_anonymous_even_with_bearer_header():
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {AccessToken()}")
    assert CookieJWTAuthentication().authenticate(request) is None


@pytest.mark.parametrize("method", ["post", "patch", "put", "delete"])
def test_cookie_writes_require_csrf_before_user_lookup(method):
    with patch.object(CookieJWTAuthentication, "get_user") as lookup:
        with pytest.raises(PermissionDenied):
            CookieJWTAuthentication().authenticate(request_with_cookie(method))
        lookup.assert_not_called()


def test_matching_csrf_allows_cookie_write():
    with patch.object(CookieJWTAuthentication, "get_user", return_value="test-user"):
        user, _ = CookieJWTAuthentication().authenticate(
            request_with_cookie("post", csrf=True, origin=settings.FRONTEND_ORIGIN)
        )
    assert user == "test-user"


def test_untrusted_origin_is_rejected_even_with_matching_csrf():
    with pytest.raises(PermissionDenied):
        CookieJWTAuthentication().authenticate(
            request_with_cookie("post", csrf=True, origin="https://untrusted.invalid")
        )


def test_anonymous_login_can_require_csrf():
    request = APIRequestFactory(enforce_csrf_checks=True).post("/api/v1/auth/login/")
    with pytest.raises(PermissionDenied):
        enforce_csrf(request)


@pytest.mark.parametrize("kind", ["expired", "refresh", "malformed"])
def test_invalid_access_cookie_is_rejected(kind):
    token = AccessToken()
    if kind == "expired":
        token.set_exp(lifetime=timedelta(seconds=-1))
    elif kind == "refresh":
        token = RefreshToken()
    else:
        token = "not-a-token"
    with pytest.raises(InvalidToken):
        CookieJWTAuthentication().authenticate(request_with_cookie(token=token))
