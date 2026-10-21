from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.serializers import EmailSerializer, StrictSerializer
from apps.accounts.throttles import AuthEmailThrottle, AuthIPThrottle
from apps.core.storage import get_storage
from apps.orders.views import CheckoutView, validated

from . import recovery
from .delivery import delivery_status
from .models import TicketDelivery


class RecoveryThrottle(AuthIPThrottle):
    scope = "recovery"


class RecoveryEmailThrottle(AuthEmailThrottle):
    scope = "recovery_email"


class StartInput(EmailSerializer):
    access_token = serializers.RegexField(r"^[A-Za-z0-9_-]{43,128}$", write_only=True)


class CodeInput(StrictSerializer):
    code = serializers.RegexField(r"^\d{6}$", write_only=True)


class RecoveryView(CheckoutView):
    authentication_classes = []
    throttle_classes = [RecoveryThrottle]

    def session(self, request, pk):
        return recovery.authorized(pk, request.headers.get("X-Recovery-Token", ""))


class StartRecovery(RecoveryView):
    throttle_classes = [RecoveryThrottle, RecoveryEmailThrottle]

    @extend_schema(request=StartInput, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        data = validated(StartInput, request)
        item = recovery.start(data["email"], data["access_token"])
        return Response(
            {
                "id": item.pk,
                "detail": "A recovery code has been queued. Check your inbox and spam folder.",
            },
            status=202,
        )


class VerifyRecovery(RecoveryView):
    @extend_schema(request=CodeInput, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        item = recovery.verify(
            pk, request.headers.get("X-Recovery-Token", ""), validated(CodeInput, request)["code"]
        )
        return Response({"expires_at": item.session_expires_at})


class RecoveryOrders(RecoveryView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        item = self.session(request, pk)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(recovery.orders_for(item), request)
        return paginator.get_paginated_response(
            [
                {
                    "id": order.pk,
                    "number": order.number,
                    "title": order.snapshot["title"],
                    "quantity": order.quantity,
                    "paid_at": order.paid_at,
                    "can_download": order.recipient_email == item.email,
                    "delivery_status": delivery_status(order),
                }
                for order in page
            ]
        )


class RecoveryResend(RecoveryView):
    @extend_schema(request=StrictSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk, order_id):
        validated(StrictSerializer, request)
        recovery.resend(self.session(request, pk), order_id)
        return Response(
            {
                "detail": "Tickets queued for the original recipient. Any gift receipt goes to the buyer."
            },
            status=202,
        )


class RecoveryDownload(RecoveryView):
    @extend_schema(responses={(200, "application/pdf"): bytes})
    def get(self, request, pk, order_id):
        item = self.session(request, pk)
        order = get_object_or_404(
            recovery.orders_for(item), pk=order_id, recipient_email=item.email
        )
        job = TicketDelivery.objects.filter(order=order).exclude(pdf_key="").first()
        if not job:
            return Response(
                {"detail": "PDF not ready. Request a resend and try again shortly."}, status=409
            )
        response = HttpResponse(get_storage().read(job.pdf_key), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{order.number}.pdf"'
        response["X-Content-Type-Options"] = "nosniff"
        return response
