import io
import uuid
import warnings

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.views import validated
from apps.core.storage import get_storage
from apps.notifications.models import Notification

from . import services
from .models import Event
from .serializers import (
    BannerInput,
    DraftInput,
    EventSerializer,
    PublicEventSerializer,
    ReviewInput,
)


class Pagination(PageNumberPagination):
    page_size = 20


class PrivateView:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class EventList(PrivateView, generics.ListCreateAPIView):
    serializer_class = EventSerializer
    pagination_class = Pagination

    def get_queryset(self):
        services.require_organizer(self.request.user)
        return Event.objects.filter(owner=self.request.user).prefetch_related(
            "categories", "form_fields"
        )

    @extend_schema(request=DraftInput, responses={201: EventSerializer})
    def post(self, request):
        event = services.save_draft(request.user, validated(DraftInput, request))
        return Response(EventSerializer(event).data, status=201)


class EventDetail(PrivateView, generics.RetrieveAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        return services.editable_events(self.request.user).prefetch_related(
            "categories", "form_fields"
        )

    @extend_schema(request=DraftInput, responses=EventSerializer)
    def patch(self, request, pk):
        serializer = DraftInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        event = services.save_draft(request.user, serializer.validated_data, pk)
        return Response(EventSerializer(event).data)


class SubmitView(PrivateView, APIView):
    @extend_schema(request=None, responses=EventSerializer)
    def post(self, request, pk):
        return Response(EventSerializer(services.submit(request.user, pk)).data)


class ReviewQueue(PrivateView, generics.ListAPIView):
    serializer_class = EventSerializer
    pagination_class = Pagination

    def get_queryset(self):
        services.require_admin(self.request.user)
        return Event.objects.filter(status=Event.Status.PENDING).prefetch_related(
            "categories", "form_fields"
        )


class ApproveView(PrivateView, APIView):
    @extend_schema(request=None, responses=EventSerializer)
    def post(self, request, pk):
        return Response(EventSerializer(services.review(request.user, pk, True)).data)


class RejectView(PrivateView, APIView):
    @extend_schema(request=ReviewInput, responses=EventSerializer)
    def post(self, request, pk):
        services.require_admin(request.user)
        data = validated(ReviewInput, request)
        return Response(
            EventSerializer(services.review(request.user, pk, False, data["reason"])).data
        )


class PublicList(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = PublicEventSerializer
    pagination_class = Pagination

    def get_queryset(self):
        queryset = Event.objects.filter(status=Event.Status.APPROVED).prefetch_related(
            "categories", "form_fields"
        )
        search = self.request.query_params.get("search", "")[:180]
        return queryset.filter(title__icontains=search)


class PublicDetail(generics.RetrieveAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = PublicEventSerializer
    lookup_field = "slug"
    queryset = Event.objects.filter(status=Event.Status.APPROVED).prefetch_related(
        "categories", "form_fields"
    )


class BannerView(PrivateView, APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(responses={(200, "image/jpeg"): bytes})
    def get(self, request, pk):
        queryset = (
            Event.objects.all()
            if request.user.role == "admin"
            else services.editable_events(request.user)
        )
        event = get_object_or_404(queryset, pk=pk)
        if not event.banner_key:
            from django.http import Http404

            raise Http404
        return HttpResponse(get_storage().read(event.banner_key), content_type="image/jpeg")

    @extend_schema(request=BannerInput, responses=EventSerializer)
    def post(self, request, pk):
        event = get_object_or_404(services.editable_events(request.user), pk=pk)
        services.editable(event)
        upload = validated(BannerInput, request)["banner"]
        if upload.size > 5 * 1024 * 1024:
            raise serializers.ValidationError({"banner": "Use an image smaller than 5 MB."})
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(upload) as source:
                    if (
                        source.format not in ("JPEG", "PNG", "WEBP")
                        or source.width * source.height > 16000000
                    ):
                        raise ValueError()
                    picture = ImageOps.exif_transpose(source).convert("RGB")
                    picture.thumbnail((2000, 2000))
                    output = io.BytesIO()
                    picture.save(output, format="JPEG", quality=85)
        except (
            ValueError,
            OSError,
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise serializers.ValidationError(
                {"banner": "Use a valid JPEG, PNG or WebP image up to 16 megapixels."}
            ) from None
        # Upload outside the transaction, then recheck state under the event lock.
        key = f"banners/{event.pk}/{uuid.uuid4().hex}.jpg"
        get_storage().put(key, output.getvalue(), "image/jpeg")
        with transaction.atomic():
            event = get_object_or_404(
                services.editable_events(request.user).select_for_update(), pk=pk
            )
            services.recheck_editor(request.user, event)
            services.editable(event)
            event.banner_key = key
            event.save(update_fields=["banner_key", "updated_at"])
        return Response(EventSerializer(event).data)


class PublicBanner(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={(200, "image/jpeg"): bytes})
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug, status=Event.Status.APPROVED)
        if not event.banner_key:
            from django.http import Http404

            raise Http404
        response = HttpResponse(get_storage().read(event.banner_key), content_type="image/jpeg")
        response["X-Content-Type-Options"] = "nosniff"
        return response


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "event", "type", "message", "is_read", "created_at"]


class NotificationList(PrivateView, generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = Pagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationRead(PrivateView, APIView):
    @extend_schema(request=None, responses=NotificationSerializer)
    def post(self, request, pk):
        item = get_object_or_404(Notification, pk=pk, recipient=request.user)
        item.is_read = True
        item.save(update_fields=["is_read"])
        return Response(NotificationSerializer(item).data)
