from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AuthSession, EmailChallenge, User
from apps.accounts.services import create_challenge

pytestmark = pytest.mark.django_db
PASSWORD = "Fictional-Account-Password-749!"
NEW_PASSWORD = "Another-Fictional-Password-472!"


@pytest.fixture(autouse=True)
def isolated_cache():
    with override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    ):
        cache.clear()
        yield
        cache.clear()


@pytest.fixture
def client():
    return APIClient(enforce_csrf_checks=True)


def post(client, route, data=None):
    csrf = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
    return client.post(f"/api/v1/auth/{route}/", data or {}, format="json", HTTP_X_CSRFTOKEN=csrf)


def create_user():
    return User.objects.create_user("organizer@example.com", PASSWORD, role="organizer")


def login(client):
    return post(client, "login", {"email": "ORGANIZER@example.com", "password": PASSWORD})


def test_registration_normalizes_email_and_rejects_privilege_assignment(client):
    data = {
        "email": " Organizer@Example.com ",
        "password": PASSWORD,
        "full_name": "Demo Host",
        "role": "organizer",
    }
    response = post(client, "register", {**data, "is_staff": True})
    assert response.status_code == 400
    assert not User.objects.exists()
    assert post(client, "register", {**data, "role": "admin"}).status_code == 400
    response = post(client, "register", data)
    assert response.status_code == 201
    user = User.objects.get()
    assert user.email == "organizer@example.com"
    assert user.check_password(PASSWORD)
    assert not user.is_staff and not user.email_verified
    assert "password" not in response.json()
    assert post(client, "register", data).status_code == 400


def test_weak_password_rejected(client):
    response = post(
        client,
        "register",
        {"email": "demo@example.com", "password": "password", "full_name": "Demo"},
    )
    assert response.status_code == 400
    assert not User.objects.exists()


def test_login_profile_and_cookie_properties(client):
    user = create_user()
    with override_settings(AUTH_COOKIE_SECURE=True):
        response = login(client)
    assert response.status_code == 200
    assert response.cookies[settings.AUTH_ACCESS_COOKIE]["httponly"]
    assert response.cookies[settings.AUTH_ACCESS_COOKIE]["secure"]
    assert response.cookies[settings.AUTH_REFRESH_COOKIE]["path"] == "/api/v1/auth/"
    assert "access" not in response.json() and "refresh" not in response.json()
    assert response["Cache-Control"] == "no-store"
    me = client.get("/api/v1/auth/me/")
    assert me.status_code == 200 and me.json()["id"] == str(user.id)
    csrf = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
    assert (
        client.patch(
            "/api/v1/auth/me/", {"email_verified": True}, format="json", HTTP_X_CSRFTOKEN=csrf
        ).status_code
        == 400
    )
    response = client.patch(
        "/api/v1/auth/me/", {"full_name": "Updated"}, format="json", HTTP_X_CSRFTOKEN=csrf
    )
    assert response.status_code == 200 and response.json()["full_name"] == "Updated"


def test_login_requires_csrf_and_rejects_wrong_password(client):
    create_user()
    assert (
        client.post(
            "/api/v1/auth/login/", {"email": "organizer@example.com", "password": PASSWORD}
        ).status_code
        == 403
    )
    assert (
        post(client, "login", {"email": "organizer@example.com", "password": "wrong"}).status_code
        == 401
    )
    assert not AuthSession.objects.exists()


def test_refresh_rotates_and_replay_fails(client):
    create_user()
    assert login(client).status_code == 200
    old_refresh = client.cookies[settings.AUTH_REFRESH_COOKIE].value
    assert post(client, "refresh").status_code == 200
    new_refresh = client.cookies[settings.AUTH_REFRESH_COOKIE].value
    assert old_refresh != new_refresh
    client.cookies[settings.AUTH_REFRESH_COOKIE] = old_refresh
    assert post(client, "refresh").status_code == 401
    client.cookies[settings.AUTH_REFRESH_COOKIE] = new_refresh
    assert post(client, "refresh").status_code == 200


def test_logout_revokes_copied_access_and_refresh(client):
    create_user()
    login(client)
    access = client.cookies[settings.AUTH_ACCESS_COOKIE].value
    refresh = client.cookies[settings.AUTH_REFRESH_COOKIE].value
    assert post(client, "logout").status_code == 204
    client.cookies[settings.AUTH_ACCESS_COOKIE] = access
    client.cookies[settings.AUTH_REFRESH_COOKIE] = refresh
    assert client.get("/api/v1/auth/me/").status_code == 401
    assert post(client, "refresh").status_code == 401


def test_deactivated_user_cannot_use_existing_session(client):
    user = create_user()
    login(client)
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert client.get("/api/v1/auth/me/").status_code == 401
    assert post(client, "refresh").status_code == 401


def test_expired_server_session_denied(client):
    create_user()
    login(client)
    AuthSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert client.get("/api/v1/auth/me/").status_code == 401


def test_verification_is_single_use_and_purpose_bound(client):
    user = create_user()
    challenge, token = create_challenge(user.id, "verify")
    assert challenge.token_digest != token
    payload = {"challenge_id": str(challenge.pk), "token": token}
    assert (
        post(client, "password-reset/confirm", {**payload, "password": NEW_PASSWORD}).status_code
        == 400
    )
    assert post(client, "verify-email/confirm", payload).status_code == 204
    user.refresh_from_db()
    assert user.email_verified
    assert post(client, "verify-email/confirm", payload).status_code == 400


def test_resend_invalidates_old_link_and_expiry_is_enforced(client):
    user = create_user()
    old, old_token = create_challenge(user.id, "verify")
    new, new_token = create_challenge(user.id, "verify")
    assert (
        post(
            client, "verify-email/confirm", {"challenge_id": str(old.id), "token": old_token}
        ).status_code
        == 400
    )
    EmailChallenge.objects.filter(pk=new.pk).update(expires_at=timezone.now())
    assert (
        post(
            client, "verify-email/confirm", {"challenge_id": str(new.id), "token": new_token}
        ).status_code
        == 400
    )


def test_password_reset_revokes_sessions_and_is_single_use(client):
    user = create_user()
    login(client)
    access = client.cookies[settings.AUTH_ACCESS_COOKIE].value
    challenge, token = create_challenge(user.id, "reset")
    payload = {"challenge_id": str(challenge.id), "token": token, "password": NEW_PASSWORD}
    assert post(client, "password-reset/confirm", payload).status_code == 204
    client.cookies[settings.AUTH_ACCESS_COOKIE] = access
    assert client.get("/api/v1/auth/me/").status_code == 401
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert post(client, "password-reset/confirm", payload).status_code == 400


def test_change_password_requires_current_password_and_revokes_sessions(client):
    user = create_user()
    login(client)
    assert (
        post(
            client, "change-password", {"current_password": "wrong", "password": NEW_PASSWORD}
        ).status_code
        == 400
    )
    assert (
        post(
            client, "change-password", {"current_password": PASSWORD, "password": NEW_PASSWORD}
        ).status_code
        == 204
    )
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert not AuthSession.objects.filter(revoked_at__isnull=True).exists()


def test_recovery_is_generic_and_dispatches_without_account_lookup(client):
    create_user()
    with patch("apps.accounts.views.deliver_account_link.apply_async") as dispatch:
        known = post(client, "password-reset/request", {"email": "organizer@example.com"})
        unknown = post(client, "password-reset/request", {"email": "missing@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert dispatch.call_count == 2


def test_queue_failure_is_explicit_without_secret_disclosure(client):
    with patch(
        "apps.accounts.views.deliver_account_link.apply_async",
        side_effect=RuntimeError("secret-url"),
    ):
        response = post(client, "password-reset/request", {"email": "missing@example.com"})
    assert response.status_code == 503
    assert "secret-url" not in str(response.json())


def test_email_rate_limit_applies_to_unknown_accounts(client):
    with patch("apps.accounts.views.deliver_account_link.apply_async"):
        results = [
            post(client, "password-reset/request", {"email": "missing@example.com"}).status_code
            for _ in range(11)
        ]
    assert results[:10] == [202] * 10
    assert results[-1] == 429


def test_throttle_storage_failure_fails_closed(client):
    with patch(
        "apps.accounts.throttles.AuthIPThrottle.cache.get", side_effect=RuntimeError("secret")
    ):
        response = post(client, "login", {"email": "missing@example.com", "password": PASSWORD})
    assert response.status_code == 503
    assert "secret" not in str(response.json())
