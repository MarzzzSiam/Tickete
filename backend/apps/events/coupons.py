from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import StrictSerializer
from apps.accounts.views import validated
from apps.core.models import AuditLog

from .models import Coupon, Event


class CouponInput(StrictSerializer):
    code = serializers.RegexField(r"^[A-Za-z0-9_-]{1,32}$", max_length=32)
    percentage = serializers.IntegerField(min_value=1, max_value=99)

    def validate_code(self, value):
        return value.upper()


class CouponToggle(StrictSerializer):
    is_active = serializers.BooleanField()


class CouponOutput(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id", "code", "percentage", "is_active"]


def add_coupon(user, event, data):
    # Caller holds the event lock (or has just inserted the event).
    if event.owner_id != user.pk:
        raise PermissionDenied("Only the event owner can manage coupons.")
    if event.closed_at:
        raise ValidationError("This event is closed.")
    if event.coupons.count() >= 3:
        raise ValidationError("An event can have at most three coupons, including paused coupons.")
    if event.coupons.filter(code=data["code"]).exists():
        raise ValidationError("This coupon code already exists for this event.")
    coupon = Coupon.objects.create(event=event, **data)
    AuditLog.objects.create(
        actor=user,
        action="coupon_created",
        target_type="event",
        target_id=event.pk,
        details={"code": coupon.code, "percentage": coupon.percentage},
    )
    return coupon


@transaction.atomic
def create_coupon(user, event_id, data):
    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id, owner=user)
    return add_coupon(user, event, data)


@transaction.atomic
def toggle_coupon(user, event_id, coupon_id, active):
    from apps.orders.models import Order
    from apps.orders.services import release

    event = get_object_or_404(Event.objects.select_for_update(), pk=event_id, owner=user)
    if event.closed_at:
        raise ValidationError("This event is closed.")
    coupon = get_object_or_404(Coupon, pk=coupon_id, event=event)
    coupon.is_active = active
    coupon.save(update_fields=["is_active"])
    if not active:
        # Serializes against checkout/payment on the same event lock. Paid tickets survive.
        for order in Order.objects.filter(
            event=event, status="pending", snapshot__coupon__id=str(coupon.pk)
        ):
            release(order, "expired")
    AuditLog.objects.create(
        actor=user,
        action="coupon_resumed" if active else "coupon_paused",
        target_type="event",
        target_id=event.pk,
        details={"code": coupon.code},
    )
    return coupon


def discounted_total(event, subtotal, code):
    coupon = None
    discount = Decimal("0.00")
    if code:
        coupon = event.coupons.filter(code=code.strip().upper(), is_active=True).first()
        if not coupon:
            raise ValidationError(
                {"coupon_code": "This coupon is invalid or paused for this event."}
            )
        discount = (subtotal * coupon.percentage / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    total = subtotal - discount
    if total <= 0:
        raise ValidationError("The discounted total must be at least BDT 0.01.")
    return {
        "subtotal": str(subtotal),
        "discount": str(discount),
        "total": str(total),
        "coupon": (
            {"id": str(coupon.pk), "code": coupon.code, "percentage": coupon.percentage}
            if coupon
            else None
        ),
    }


class CouponList(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response

    @extend_schema(responses=CouponOutput(many=True))
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, owner=request.user)
        return Response(CouponOutput(event.coupons.all(), many=True).data)

    @extend_schema(request=CouponInput, responses={201: CouponOutput})
    def post(self, request, pk):
        return Response(
            CouponOutput(create_coupon(request.user, pk, validated(CouponInput, request))).data,
            status=201,
        )


class CouponDetail(CouponList):
    http_method_names = ["patch", "options"]

    @extend_schema(request=CouponToggle, responses=CouponOutput)
    def patch(self, request, pk, coupon_id):
        data = validated(CouponToggle, request)
        return Response(
            CouponOutput(toggle_coupon(request.user, pk, coupon_id, data["is_active"])).data
        )
