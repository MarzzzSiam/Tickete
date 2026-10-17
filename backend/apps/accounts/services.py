import hashlib
import secrets
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from uuid import UUID

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuthSession, EmailChallenge, User


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check_password_policy(password, user):
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise ValidationError({"password": exc.messages}) from None


def register(data):
    user = User(**{k: data[k] for k in ("email", "full_name", "role")})
    check_password_policy(data["password"], user)
    user.set_password(data["password"])
    try:
        with transaction.atomic():
            user.save()
    except IntegrityError:
        raise ValidationError({"email": ["An account with this email already exists."]}) from None
    return user


def token_pair(user, session):
    refresh = RefreshToken.for_user(user)
    refresh["sid"] = str(session.id)
    raw_refresh = str(refresh)
    session.refresh_digest = digest(raw_refresh)
    session.expires_at = datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc)
    session.save()
    return str(refresh.access_token), raw_refresh


def login(email, password):
    user = authenticate(email=email, password=password)
    if user is None:
        raise AuthenticationFailed("Invalid email or password.")
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        # A password reset or deactivation may have raced the password check.
        if not locked.is_active or locked.password != user.password:
            raise AuthenticationFailed("Invalid email or password.")
        return locked, token_pair(locked, AuthSession(user=locked))


def parse_refresh(raw):
    try:
        token = RefreshToken(raw)
        return UUID(token["user_id"]), UUID(token["sid"])
    except (TokenError, ValueError, TypeError, KeyError, AttributeError):
        raise AuthenticationFailed("Invalid or expired session.") from None


def refresh_session(raw):
    user_id, session_id = parse_refresh(raw)
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id, is_active=True).first()
        session = (
            AuthSession.objects.select_for_update()
            .filter(
                pk=session_id,
                user_id=user_id,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if (
            not user
            or not session
            or not secrets.compare_digest(session.refresh_digest, digest(raw))
        ):
            raise AuthenticationFailed("Invalid or expired session.")
        return user, token_pair(user, session)


def logout(raw):
    if not raw:
        return
    try:
        user_id, session_id = parse_refresh(raw)
    except AuthenticationFailed:
        return
    # Even an older signed refresh token can revoke its own session after rotation.
    AuthSession.objects.filter(pk=session_id, user_id=user_id, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


def create_challenge(user_id, purpose):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        now = timezone.now()
        EmailChallenge.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True).update(
            consumed_at=now
        )
        raw = secrets.token_urlsafe(32)
        challenge = EmailChallenge.objects.create(
            user=user,
            purpose=purpose,
            token_digest=digest(raw),
            expires_at=now + timedelta(minutes=30),
        )
        return challenge, raw


def consume_challenge(challenge_id, raw, purpose, password=None):
    invalid = ValidationError({"token": ["Invalid or expired link."]})
    owner = (
        EmailChallenge.objects.filter(pk=challenge_id, purpose=purpose)
        .values_list("user_id", flat=True)
        .first()
    )
    if owner is None:
        raise invalid
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=owner)
        challenge = EmailChallenge.objects.select_for_update().get(pk=challenge_id)
        if (
            not user.is_active
            or challenge.consumed_at
            or challenge.expires_at <= timezone.now()
            or not secrets.compare_digest(challenge.token_digest, digest(raw))
        ):
            raise invalid
        if purpose == EmailChallenge.Purpose.RESET:
            check_password_policy(password, user)
            user.set_password(password)
            user.save(update_fields=["password"])
            AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
                revoked_at=timezone.now()
            )
        else:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        challenge.consumed_at = timezone.now()
        challenge.save(update_fields=["consumed_at"])


def change_password(user_id, current_password, password):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        if not user.check_password(current_password):
            raise ValidationError({"current_password": ["Incorrect password."]})
        check_password_policy(password, user)
        user.set_password(password)
        user.save(update_fields=["password"])
        AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        EmailChallenge.objects.filter(user=user, consumed_at__isnull=True).update(
            consumed_at=timezone.now()
        )
