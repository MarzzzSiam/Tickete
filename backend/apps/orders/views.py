from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.authentication import enforce_csrf
from apps.accounts.throttles import AuthIPThrottle
from apps.core.storage import get_storage
from apps.tickets.models import TicketDelivery

from . import services
from .serializers import (
    CheckoutInput,
    CheckoutResult,
    PaymentInput,
    QuoteInput,
    QuoteOutput,
    VerifyInput,
)


class CheckoutThrottle(AuthIPThrottle):
    scope = "checkout"


class CheckoutView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CheckoutThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            enforce_csrf(request)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response

    def output(self, order):
        return Response(CheckoutResult(services.result(order)).data)


def validated(serializer, request):
    value = serializer(data=request.data)
    value.is_valid(raise_exception=True)
    return value.validated_data


class CreateOrder(CheckoutView):
    @extend_schema(request=CheckoutInput, responses=CheckoutResult)
    def post(self, request):
        return self.output(services.create_order(validated(CheckoutInput, request), request.user))


class OrderStatus(CheckoutView):
    @extend_schema(responses=CheckoutResult)
    def get(self, request, pk):
        return self.output(services.read_order(pk, request.headers.get("X-Checkout-Token", "")))


class StartPayment(CheckoutView):
    @extend_schema(request=PaymentInput, responses=CheckoutResult)
    def post(self, request, pk):
        return self.output(
            services.initiate_payment(
                pk, request.headers.get("X-Checkout-Token", ""), validated(PaymentInput, request)
            )
        )


class VerifyPayment(CheckoutView):
    @extend_schema(request=VerifyInput, responses=CheckoutResult)
    def post(self, request, pk):
        return self.output(
            services.verify_payment(
                pk,
                request.headers.get("X-Checkout-Token", ""),
                validated(VerifyInput, request)["otp"],
            )
        )


class CancelOrder(CheckoutView):
    @extend_schema(request=None, responses=CheckoutResult)
    def post(self, request, pk):
        return self.output(services.cancel_order(pk, request.headers.get("X-Checkout-Token", "")))


class DownloadTickets(CheckoutView):
    @extend_schema(responses={(200, "application/pdf"): bytes})
    def get(self, request, pk):
        order = services.read_order(pk, request.headers.get("X-Checkout-Token", ""))
        job = TicketDelivery.objects.filter(order=order).exclude(pdf_key="").first()
        if order.status != "paid" or not job:
            return Response({"detail": "Tickets are not ready yet."}, status=409)
        response = HttpResponse(get_storage().read(job.pdf_key), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{order.number}.pdf"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


class CouponQuote(CheckoutView):
    @extend_schema(request=QuoteInput, responses=QuoteOutput)
    def post(self, request):
        return Response(QuoteOutput(services.quote_coupon(validated(QuoteInput, request))).data)
