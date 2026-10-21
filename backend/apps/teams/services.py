import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core.models import AuditLog
from apps.events.models import Event

from .models import Invitation, TeamMember


def role_for(user, event):
    if not user.is_active or not user.email_verified:
        raise PermissionDenied("A verified account is required for event operations.")
    if event.owner_id == user.pk:
        return "owner"
    if user.role == "admin":
        return "admin"
    return (
        TeamMember.objects.filter(event=event, user=user, active=True)
        .values_list("role", flat=True)
        .first()
    )


def require_role(user, event, roles):
    role = role_for(user, event)
    if role not in roles:
        raise PermissionDenied("You do not have access to this event operation.")
    return role


def audit(user, event, action, **details):
    AuditLog.objects.create(
        actor=user, action=action, target_type="event", target_id=event.pk, details=details
    )


@transaction.atomic
def invite(user, event_id, email, role):
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    require_role(user, event, ["owner"])
    email = email.strip().lower()
    if email == user.email:
        raise ValidationError("The owner already has full access.")
    if Invitation.objects.filter(
        event=event,
        email=email,
        revoked_at__isnull=True,
        accepted_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).exists():
        raise ValidationError("An invitation is already pending. Revoke it before replacing it.")
    invitation = Invitation.objects.create(
        event=event, email=email, role=role, expires_at=timezone.now() + timedelta(days=7)
    )
    audit(user, event, "team.invited", invitation_id=str(invitation.pk), role=role)
    return invitation


@transaction.atomic
def accept(user, invitation_id, token):
    reference = get_object_or_404(Invitation, pk=invitation_id)
    event = Event.objects.select_for_update().get(pk=reference.event_id)
    invitation = Invitation.objects.select_for_update().get(pk=invitation_id)
    if (
        not user.email_verified
        or user.email.lower() != invitation.email
        or not invitation.token_digest
        or not secrets.compare_digest(
            invitation.token_digest, hashlib.sha256(token.encode()).hexdigest()
        )
        or invitation.revoked_at
        or invitation.expires_at <= timezone.now()
    ):
        raise PermissionDenied(
            "Use an unexpired invitation with the matching verified email account."
        )
    if invitation.accepted_at:
        # A previously accepted link can never reinstate revoked membership.
        raise ValidationError("This invitation has already been accepted.")
    TeamMember.objects.update_or_create(
        event=event, user=user, defaults={"role": invitation.role, "active": True}
    )
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at"])
    audit(user, event, "team.accepted", invitation_id=str(invitation.pk))
    return event


@transaction.atomic
def change_member(user, event_id, member_id, role=None, active=None):
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    require_role(user, event, ["owner"])
    member = get_object_or_404(TeamMember, pk=member_id, event=event)
    if role is not None:
        member.role = role
    if active is not None:
        member.active = active
    member.save()
    audit(
        user,
        event,
        "team.updated",
        member_id=str(member.pk),
        role=member.role,
        active=member.active,
    )
    return member


@transaction.atomic
def revoke_invitation(user, event_id, invitation_id):
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    require_role(user, event, ["owner"])
    invitation = get_object_or_404(Invitation, pk=invitation_id, event=event)
    invitation.revoked_at = timezone.now()
    invitation.save(update_fields=["revoked_at"])
    audit(user, event, "team.invitation_revoked", invitation_id=str(invitation.pk))


@transaction.atomic
def process_invitation():
    now = timezone.now()
    item = (
        Invitation.objects.select_for_update(skip_locked=True)
        .filter(
            sent_at__isnull=True,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=now,
            attempts__lt=5,
            next_attempt_at__lte=now,
        )
        .order_by("created_at")
        .first()
    )
    if not item:
        return None
    raw = secrets.token_urlsafe(32)
    item.token_digest = hashlib.sha256(raw.encode()).hexdigest()
    item.attempts += 1
    link = f"{settings.FRONTEND_ORIGIN}/team/accept#" + urlencode(
        {"invitation": str(item.pk), "token": raw}
    )
    try:
        accepted = send_mail(
            "TICKETÉ event team invitation",
            f"You are invited as {item.role} for {item.event.title}.\nSign in with this email address, verify it and accept within seven days:\n{link}",
            settings.DEFAULT_FROM_EMAIL,
            [item.email],
        )
        if accepted != 1:
            raise RuntimeError("Delivery not accepted")
        item.sent_at = timezone.now()
    except Exception:
        item.next_attempt_at = now + timedelta(seconds=min(60 * 2**item.attempts, 3600))
    item.save()
    return "invitation_sent" if item.sent_at else "invitation_email_failed"
