from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class CsrfSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=CsrfSerializer, auth=[])
    def get(self, request):
        response = Response({"csrf_token": get_token(request)})
        response["Cache-Control"] = "no-store"
        return response
