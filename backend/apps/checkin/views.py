from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import StrictSerializer
from apps.accounts.throttles import AuthIPThrottle
from apps.accounts.views import validated
from apps.events.models import Event
from apps.events.views import PrivateView
from apps.orders.models import Order
from apps.teams import services as teams
from apps.teams.models import ROLES, Invitation, TeamMember
from apps.tickets.models import Ticket

from .services import cancel, scan


class OperationsThrottle(AuthIPThrottle):
    scope = "operations"


class ScanThrottle(AuthIPThrottle):
    scope = "scan"


class InviteThrottle(AuthIPThrottle):
    scope = "team_invite"


class OperationsView(PrivateView, APIView):
    throttle_classes = [OperationsThrottle]


class ScanInput(StrictSerializer):
    value = serializers.CharField(max_length=128, trim_whitespace=True)
    method = serializers.ChoiceField(choices=["qr", "manual"])


class InviteInput(StrictSerializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ROLES)


class MemberInput(StrictSerializer):
    role = serializers.ChoiceField(choices=ROLES, required=False)
    active = serializers.BooleanField(required=False)


class AcceptInput(StrictSerializer):
    invitation = serializers.UUIDField()
    token = serializers.CharField(max_length=128)


class TeamEvents(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not request.user.email_verified:
            return Response({"results": []})
        queryset = (
            Event.objects.filter(
                Q(owner=request.user)
                | Q(team_members__user=request.user, team_members__active=True)
            )
            .distinct()
            .order_by("-created_at")
        )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            [{"id": e.pk, "title": e.title, "role": teams.role_for(request.user, e)} for e in page]
        )


class Summary(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        role = teams.require_role(
            request.user, event, ["owner", "admin", "manager", "viewer", "scanner"]
        )
        tickets = Ticket.objects.filter(order__event=event, order__status="paid")
        result = {
            "id": event.pk,
            "title": event.title,
            "role": role,
            "checked_in": tickets.filter(status="used").count(),
            "tickets_sold": tickets.count(),
        }
        if role != "scanner":
            stats = Order.objects.filter(event=event, status="paid").aggregate(
                orders=Count("id"), revenue=Sum("total")
            )
            result.update(
                orders=stats["orders"],
                revenue=str(stats["revenue"] or "0.00"),
                categories=list(
                    tickets.values("category__name").annotate(
                        sold=Count("id"), checked_in=Count("id", filter=Q(status="used"))
                    )
                ),
            )
        return Response(result)


class Attendees(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        teams.require_role(request.user, event, ["owner", "admin", "manager"])
        tickets = (
            Ticket.objects.filter(order__event=event, order__status="paid")
            .select_related("order", "category")
            .order_by("-order__paid_at", "position", "id")
        )
        search = request.query_params.get("search", "")[:254].strip()
        if search:
            tickets = tickets.filter(
                Q(order__buyer_email__icontains=search)
                | Q(recipient_email__icontains=search)
                | Q(code__icontains=search)
                | Q(attendee_name__icontains=search)
            )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(tickets, request)
        return paginator.get_paginated_response(
            [
                {
                    "id": t.pk,
                    "code": t.code,
                    "buyer_email": t.order.buyer_email,
                    "recipient_email": t.recipient_email,
                    "attendee_name": t.attendee_name,
                    "category": t.category.name,
                    "status": t.status,
                    "order_number": t.order.number,
                    "order_quantity": t.order.quantity,
                    "paid_at": t.order.paid_at,
                }
                for t in page
            ]
        )


class Team(OperationsView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        teams.require_role(request.user, event, ["owner"])
        return Response(
            {
                "server_time": timezone.now(),
                "members": list(
                    TeamMember.objects.filter(event=event).values(
                        "id", "user__email", "role", "active"
                    )
                ),
                "invitations": list(
                    Invitation.objects.filter(event=event)
                    .order_by("-created_at")[:100]
                    .values(
                        "id",
                        "email",
                        "role",
                        "sent_at",
                        "accepted_at",
                        "revoked_at",
                        "expires_at",
                        "attempts",
                    )
                ),
            }
        )

    @extend_schema(request=InviteInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        limiter = InviteThrottle()
        if not limiter.allow_request(request, self):
            self.throttled(request, limiter.wait())
        item = teams.invite(request.user, pk, **validated(InviteInput, request))
        return Response({"id": item.pk, "status": "queued"}, status=201)


class Member(OperationsView):
    @extend_schema(request=MemberInput, responses=OpenApiTypes.OBJECT)
    def patch(self, request, pk, member_id):
        member = teams.change_member(request.user, pk, member_id, **validated(MemberInput, request))
        return Response({"id": member.pk, "role": member.role, "active": member.active})


class RevokeInvitation(OperationsView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, pk, invitation_id):
        teams.revoke_invitation(request.user, pk, invitation_id)
        return Response(status=204)


class AcceptInvitation(OperationsView):
    @extend_schema(request=AcceptInput, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        data = validated(AcceptInput, request)
        event = teams.accept(request.user, data["invitation"], data["token"])
        return Response({"event_id": event.pk})


class Scan(OperationsView):
    throttle_classes = [ScanThrottle]

    @extend_schema(request=ScanInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        return Response(scan(request.user, pk, **validated(ScanInput, request)))


class CancelTicket(OperationsView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, pk, ticket_id):
        cancel(request.user, pk, ticket_id)
        return Response(status=204)
