from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.notifications.models import Notification

from .models import Event, EventFormField, TicketCategory


class StateConflict(APIException):
    status_code = 409
    default_detail = "This event has changed state. Reload before continuing."
    default_code = "event_state_conflict"


def require_organizer(user):
    if user.role != User.Role.ORGANIZER:
        raise PermissionDenied("An organizer account is required.")


def editable_events(user):
    from apps.teams.models import TeamMember

    if user.role == User.Role.ADMIN:
        raise PermissionDenied("Admins review events but do not edit them.")
    query = Q(owner=user)
    if user.email_verified:
        query |= Q(
            pk__in=TeamMember.objects.filter(user=user, role="manager", active=True).values(
                "event_id"
            )
        )
    return Event.objects.filter(query)


def require_admin(user):
    if user.role != User.Role.ADMIN:
        raise PermissionDenied("Administrator access is required.")


def editable(event):
    if event.status not in (Event.Status.DRAFT, Event.Status.REJECTED):
        raise StateConflict("Only draft or rejected events can be edited.")


def validate_schedule(event, complete=False):
    errors = {}
    if complete:
        for field in ("description", "venue", "starts_at", "ends_at", "sales_start", "sales_end"):
            if not getattr(event, field):
                errors[field] = "Required before submission."
        if event.ends_at and event.ends_at <= timezone.now():
            errors["ends_at"] = "The event must not have ended."
    for start, end in (("starts_at", "ends_at"), ("sales_start", "sales_end")):
        if (
            getattr(event, start)
            and getattr(event, end)
            and getattr(event, start) >= getattr(event, end)
        ):
            errors[end] = "Must be after the start time."
    if event.sales_end and event.ends_at and event.sales_end > event.ends_at:
        errors["sales_end"] = "Sales must end no later than the event."
    if errors:
        raise ValidationError(errors)


def replace_children(event, relation, model, rows):
    existing = {item.pk: item for item in getattr(event, relation).all()}
    seen = set()
    for values in rows:
        values = dict(values)
        pk = values.pop("id", None)
        if pk and (pk not in existing or pk in seen):
            raise ValidationError({relation: "IDs must be unique and belong to this event."})
        item = existing[pk] if pk else model(event=event)
        for key, value in values.items():
            setattr(item, key, value)
        item.save()
        seen.add(item.pk)
    getattr(event, relation).exclude(pk__in=seen).delete()


@transaction.atomic
def save_draft(user, data, event_id=None):
    if not event_id:
        require_organizer(user)
    event = (
        get_object_or_404(editable_events(user).select_for_update(), pk=event_id)
        if event_id
        else Event(owner=user)
    )
    editable(event)
    data = dict(data)
    categories = data.pop("categories", None)
    fields = data.pop("form_fields", None)
    for key, value in data.items():
        setattr(event, key, value)
    validate_schedule(event)
    event.status = Event.Status.DRAFT
    event.save()
    if categories is not None:
        replace_children(event, "categories", TicketCategory, categories)
    if fields is not None:
        replace_children(event, "form_fields", EventFormField, fields)
    return event


@transaction.atomic
def submit(user, event_id):
    # Always read current verification state, not JWT claims or browser state.
    if not User.objects.get(pk=user.pk).email_verified:
        raise PermissionDenied("Verify your email before submitting an event.")
    event = get_object_or_404(editable_events(user).select_for_update(), pk=event_id)
    if event.status != Event.Status.DRAFT:
        raise StateConflict("Save a draft before submitting it.")
    validate_schedule(event, complete=True)
    if not event.categories.filter(is_active=True).exists():
        raise ValidationError({"categories": "Add at least one active ticket category."})
    event.status = Event.Status.PENDING
    event.rejection_reason = ""
    event.reviewer = None
    event.reviewed_at = None
    event.save()
    Notification.objects.bulk_create(
        [
            Notification(
                recipient=admin,
                event=event,
                type="event_submitted",
                message=f"Review requested: {event.title}",
            )
            for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True)
        ]
    )
    return event


@transaction.atomic
def review(user, event_id, approved, reason=""):
    require_admin(user)
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    if event.status != Event.Status.PENDING:
        raise StateConflict("Only pending events can be reviewed.")
    if approved:
        validate_schedule(event, complete=True)
        event.status = Event.Status.APPROVED
        event.slug = f"{slugify(event.title)[:150] or 'event'}-{event.pk.hex}"
    else:
        if not reason.strip():
            raise ValidationError({"reason": "Explain why the event was rejected."})
        event.status = Event.Status.REJECTED
        event.rejection_reason = reason.strip()
    event.reviewer = user
    event.reviewed_at = timezone.now()
    event.save()
    AuditLog.objects.create(
        actor=user,
        action=f"event_{event.status}",
        target_type="event",
        target_id=event.pk,
        details={"reason": event.rejection_reason},
    )
    Notification.objects.create(
        recipient=event.owner,
        event=event,
        type=f"event_{event.status}",
        message=f"{event.title}: {event.get_status_display()}.",
    )
    return event
