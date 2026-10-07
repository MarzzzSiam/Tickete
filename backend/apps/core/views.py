from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses=HealthSerializer,
        auth=[],
        description="Process liveness only; not database readiness.",
    )
    def get(self, request):
        return Response({"status": "ok", "service": "tickete-api", "version": "0.1.0"})
