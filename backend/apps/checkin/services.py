import hashlib

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.events.models import Event
from apps.teams.services import audit, require_role
from apps.tickets.models import Ticket

from .models import CheckInLog


@transaction.atomic
def scan(user, event_id, value, method):
    # All access changes and scans lock the event first: revocation is immediate
    # for subsequent scans, and a scanner cannot pass a stale membership check.
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    require_role(user, event, ["owner", "manager", "scanner"])
    lookup = {"code": value.upper()} if method == "manual" else {"qr_token": value}
    ticket = (
        Ticket.objects.select_related("category", "used_by")
        .filter(order__event=event, **lookup)
        .first()
    )
    result = "invalid"
    if event.status != "approved":
        result = "event_unavailable"
    elif not ticket:
        if Ticket.objects.filter(**lookup).exists():
            result = "wrong_event"
    elif ticket.status == "cancelled":
        result = "cancelled"
    elif ticket.status == "used":
        result = "already_used"
    elif Ticket.objects.filter(pk=ticket.pk, status="valid", order__status="paid").update(
        status="used", used_at=timezone.now(), used_by=user
    ):
        result = "admitted"
        ticket.refresh_from_db()
    CheckInLog.objects.create(
        event=event,
        actor=user,
        ticket=ticket,
        result=result,
        method=method,
        input_digest=hashlib.sha256(value.encode()).hexdigest(),
    )
    return {
        "result": result,
        "ticket": (
            {
                "code": ticket.code,
                "attendee_name": ticket.attendee_name,
                "category": ticket.category.name,
                "used_at": ticket.used_at,
                "used_by": (
                    (ticket.used_by.full_name or "Event team") if ticket.used_by_id else None
                ),
            }
            if ticket
            else None
        ),
        "checked_in": Ticket.objects.filter(order__event=event, status="used").count(),
    }


@transaction.atomic
def cancel(user, event_id, ticket_id):
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
    require_role(user, event, ["owner"])
    ticket = get_object_or_404(Ticket, pk=ticket_id, order__event=event)
    if ticket.status == "used":
        raise ValidationError("A checked-in ticket cannot be cancelled.")
    Ticket.objects.filter(pk=ticket.pk, status="valid").update(status="cancelled")
    audit(user, event, "ticket.cancelled", ticket_id=str(ticket.pk))
