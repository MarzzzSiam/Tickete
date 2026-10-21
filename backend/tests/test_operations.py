import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail
from django.db import close_old_connections, connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.checkin.models import CheckInLog
from apps.checkin.services import cancel, scan
from apps.events.models import Event
from apps.events.services import save_draft
from apps.orders.services import create_order
from apps.teams.models import Invitation, TeamMember
from apps.teams.services import accept, change_member, invite, process_invitation, revoke_invitation
from tests import test_orders

event = test_orders.event
category = test_orders.category
pytestmark = pytest.mark.django_db


@pytest.fixture
def prepared(event, category):
    owner = event.owner
    owner.email_verified = True
    owner.save()
    payload = test_orders.data(event, category, 2)
    order = test_orders.pay(create_order(payload), payload["access_token"])
    return owner, event, list(order.tickets.all())


def actor(event, role):
    user = User.objects.create_user(
        f"{role}@example.com",
        full_name=f"Test {role}",
        email_verified=True,
        role="admin" if role == "admin" else "buyer",
    )
    if role in ("scanner", "manager", "viewer"):
        TeamMember.objects.create(event=event, user=user, role=role)
    return user


def client(user):
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.mark.parametrize(
    "role,can_read,can_scan",
    [
        ("owner", True, True),
        ("manager", True, True),
        ("scanner", False, True),
        ("viewer", False, False),
        ("admin", True, False),
        ("outsider", False, False),
    ],
)
def test_role_matrix(prepared, role, can_read, can_scan):
    owner, event, tickets = prepared
    user = owner if role == "owner" else actor(event, role)
    api = client(user)
    prefix = f"/api/v1/events/{event.pk}"
    response = api.get(f"{prefix}/attendees/")
    assert response.status_code == (200 if can_read else 403)
    if can_read:
        assert response.data["count"] == 2
        assert "qr_token" not in str(response.data)
        assert tickets[0].qr_token not in str(response.data)
    assert api.post(
        f"{prefix}/scan/", {"value": tickets[0].code, "method": "manual"}, format="json"
    ).status_code == (200 if can_scan else 403)
    assert api.get(f"{prefix}/team/").status_code == (200 if role == "owner" else 403)
    summary = api.get(f"{prefix}/operations/")
    if role == "scanner":
        assert "revenue" not in summary.data and "buyer_email" not in str(summary.data)
    if role == "outsider":
        assert summary.status_code == 403


def test_scan_outcomes_and_no_cross_event_disclosure(prepared):
    owner, event, tickets = prepared
    scanner = actor(event, "scanner")
    assert scan(scanner, event.pk, tickets[0].qr_token, "qr")["result"] == "admitted"
    again = scan(owner, event.pk, tickets[0].code, "manual")
    assert again["result"] == "already_used"
    assert again["ticket"]["used_by"] == "Test scanner" and again["ticket"]["used_at"]
    cancel(owner, event.pk, tickets[1].pk)
    assert scan(scanner, event.pk, tickets[1].code, "manual")["result"] == "cancelled"
    assert scan(scanner, event.pk, "missing", "qr")["result"] == "invalid"
    other = Event.objects.create(owner=owner, title="Other", status="approved")
    result = scan(owner, other.pk, tickets[0].qr_token, "qr")
    assert result["result"] == "wrong_event" and result["ticket"] is None
    assert CheckInLog.objects.count() == 5
    assert not CheckInLog.objects.filter(input_digest=tickets[0].qr_token).exists()
    with pytest.raises(ValidationError):
        cancel(owner, event.pk, tickets[0].pk)


@pytest.mark.django_db(transaction=True)
def test_simultaneous_qr_and_manual_admit_once(prepared):
    owner, event, tickets = prepared
    barrier = Barrier(2)

    def attempt(method):
        close_old_connections()
        try:
            user = User.objects.get(pk=owner.pk)
            barrier.wait()
            return scan(
                user,
                event.pk,
                tickets[0].code if method == "manual" else tickets[0].qr_token,
                method,
            )["result"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["manual", "qr"]))
    assert sorted(results) == ["admitted", "already_used"]
    assert CheckInLog.objects.filter(result="admitted").count() == 1


def test_revocation_and_role_change_apply_immediately(prepared):
    owner, event, tickets = prepared
    scanner = actor(event, "scanner")
    member = TeamMember.objects.get(user=scanner)
    change_member(owner, event.pk, member.pk, role="viewer")
    with pytest.raises(PermissionDenied):
        scan(scanner, event.pk, tickets[0].code, "manual")
    change_member(owner, event.pk, member.pk, role="scanner", active=False)
    with pytest.raises(PermissionDenied):
        scan(scanner, event.pk, tickets[0].code, "manual")
    assert not CheckInLog.objects.exists()


def test_invitation_delivery_acceptance_and_no_reinstatement(prepared):
    owner, event, _ = prepared
    user = User.objects.create_user("volunteer@example.com", email_verified=True)
    invitation = invite(owner, event.pk, " Volunteer@Example.com ", "scanner")
    with pytest.raises(ValidationError):
        invite(owner, event.pk, user.email, "viewer")
    with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
        assert process_invitation() == "invitation_sent"
        assert process_invitation() is None
    link = mail.outbox[0].body.splitlines()[-1]
    token = parse_qs(urlparse(link).fragment)["token"][0]
    invitation.refresh_from_db()
    assert invitation.token_digest == hashlib.sha256(token.encode()).hexdigest()
    with pytest.raises(PermissionDenied):
        accept(owner, invitation.pk, token)
    user.email_verified = False
    with pytest.raises(PermissionDenied):
        accept(user, invitation.pk, token)
    user.email_verified = True
    assert accept(user, invitation.pk, token).pk == event.pk
    member = TeamMember.objects.get(event=event, user=user)
    change_member(owner, event.pk, member.pk, active=False)
    with pytest.raises(ValidationError):
        accept(user, invitation.pk, token)
    member.refresh_from_db()
    assert not member.active


@pytest.mark.parametrize("condition", ["expired", "revoked", "bad_token"])
def test_bad_invitation_cannot_grant_access(prepared, condition):
    owner, event, _ = prepared
    user = User.objects.create_user("invitee@example.com", email_verified=True)
    item = invite(owner, event.pk, user.email, "scanner")
    item.token_digest = hashlib.sha256(b"secret").hexdigest()
    if condition == "expired":
        item.expires_at = timezone.now() - timedelta(seconds=1)
    if condition == "revoked":
        item.revoked_at = timezone.now()
    item.save()
    with pytest.raises(PermissionDenied):
        accept(user, item.pk, "bad" if condition == "bad_token" else "secret")
    assert not TeamMember.objects.exists()


def test_invite_failures_retry_and_revocation_stops_delivery(prepared):
    owner, event, _ = prepared
    item = invite(owner, event.pk, "volunteer@example.com", "scanner")
    with patch("apps.teams.services.send_mail", side_effect=RuntimeError("secret")):
        for _ in range(5):
            Invitation.objects.filter(pk=item.pk).update(next_attempt_at=timezone.now())
            assert process_invitation() == "invitation_email_failed"
        assert process_invitation() is None
    revoke_invitation(owner, event.pk, item.pk)
    assert process_invitation() is None


def test_manager_can_edit_draft_but_cannot_manage_team(prepared):
    _, event, _ = prepared
    manager = actor(event, "manager")
    event.status = "draft"
    event.save()
    assert save_draft(manager, {"title": "Updated draft"}, event.pk).title == "Updated draft"
    with pytest.raises(PermissionDenied):
        invite(manager, event.pk, "other@example.com", "scanner")
    viewer = actor(event, "viewer")
    assert (
        client(viewer)
        .patch(f"/api/v1/events/{event.pk}/", {"title": "No"}, format="json")
        .status_code
        == 404
    )


def test_operations_tables_are_private():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname IN ('teams_teammember','teams_invitation','checkin_checkinlog')"
        )
        assert cursor.fetchall() == [(True,), (True,), (True,)]
