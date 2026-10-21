from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.serializers import StrictSerializer
from apps.checkin.views import OperationsView
from apps.events.models import Event
from apps.orders.models import Order
from apps.orders.services import release
from apps.teams.services import audit, require_role
from apps.tickets.models import Ticket

ROLES = ["owner", "manager", "viewer", "admin"]


def snapshot(event):
    orders = Order.objects.filter(event=event, status="paid")
    tickets = Ticket.objects.filter(order__event=event, order__status="paid")
    totals = orders.aggregate(orders=Count("id"), sold=Sum("quantity"), revenue=Sum("total"))
    attendance = tickets.aggregate(
        checked_in=Count("id", filter=Q(status="used")),
        cancelled=Count("id", filter=Q(status="cancelled")),
        not_checked_in=Count("id", filter=Q(status="valid")),
    )
    categories = []
    for category in event.categories.annotate(
        purchased=Count("ticket", filter=Q(ticket__order__status="paid")),
        admitted=Count("ticket", filter=Q(ticket__status="used", ticket__order__status="paid")),
    ):
        categories.append(
            {
                "id": str(category.pk),
                "name": category.name,
                "active": category.is_active,
                "capacity": category.seat_limit,
                "sold": category.purchased,
                "unsold": (
                    None
                    if category.seat_limit is None
                    else max(category.seat_limit - category.purchased, 0)
                ),
                "checked_in": category.admitted,
            }
        )
    daily = (
        orders.annotate(day=TruncDate("paid_at", tzinfo=ZoneInfo("Asia/Dhaka")))
        .values("day")
        .annotate(sold=Sum("quantity"), revenue=Sum("total"))
        .order_by("day")
    )
    return {
        "id": str(event.pk),
        "title": event.title,
        "generated_at": timezone.now().isoformat(),
        "closed_at": event.closed_at.isoformat() if event.closed_at else None,
        "orders": totals["orders"],
        "sold": totals["sold"] or 0,
        "revenue": str(totals["revenue"] or "0.00"),
        **attendance,
        "categories": categories,
        "daily": [
            {"day": row["day"].isoformat(), "sold": row["sold"], "revenue": str(row["revenue"])}
            for row in daily
        ],
    }


@transaction.atomic
def close_event(user, pk):
    event = get_object_or_404(Event.objects.select_for_update(), pk=pk)
    require_role(user, event, ["owner"])
    if event.closed_at:
        return event.final_report
    if event.status != "approved":
        raise ValidationError({"detail": "Only an approved event can be closed."})
    # The same event lock serializes close, payment, admission and cancellation.
    for order in Order.objects.select_for_update().filter(event=event, status="pending"):
        release(order, "expired")
    event.closed_at = timezone.now()
    event.final_report = snapshot(event)
    event.save(update_fields=["closed_at", "final_report", "updated_at"])
    audit(user, event, "event.closed")
    return event.final_report


class Dashboard(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        # One event lock keeps all aggregates consistent with concurrent sales.
        with transaction.atomic():
            event = get_object_or_404(Event.objects.select_for_update(), pk=pk)
            role = require_role(request.user, event, ROLES)
            return Response(
                {"role": role, **(event.final_report if event.closed_at else snapshot(event))}
            )


class FinalReport(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        require_role(request.user, event, ROLES)
        if not event.closed_at:
            return Response({"detail": "Close the event to create its final report."}, status=409)
        return Response(event.final_report)


class CloseEvent(OperationsView):
    @extend_schema(request=StrictSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        value = StrictSerializer(data=request.data)
        value.is_valid(raise_exception=True)
        return Response(close_event(request.user, pk))
