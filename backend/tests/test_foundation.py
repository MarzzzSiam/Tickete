from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.core.exceptions import api_exception_handler
from apps.core.storage import LocalStorage, validate_key


def test_liveness_does_not_claim_database_readiness():
    response = APIClient().get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "tickete-api", "version": "0.1.0"}


@pytest.mark.parametrize(
    "key", ["../secret", "/secret", "a/../../secret", "C:/secret", "a\\secret", ""]
)
def test_storage_rejects_paths_outside_private_root(key):
    with pytest.raises(ValueError):
        validate_key(key)


def test_local_storage_roundtrip(tmp_path):
    storage = LocalStorage(tmp_path)
    key = storage.put("orders/demo/ticket.pdf", b"private-content", "application/pdf")
    assert storage.read(key) == b"private-content"


def test_validation_error_contract_preserves_fields():
    response = api_exception_handler(ValidationError({"email": ["Enter a valid email."]}), {})
    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"
    assert "email" in response.data["error"]["fields"]


def test_permission_error_contract():
    response = api_exception_handler(PermissionDenied("Access denied."), {})
    assert response.status_code == 403
    assert response.data["error"]["message"] == "Access denied."


def test_readiness_fails_without_leaking_connection_details():
    output = StringIO()
    with (
        patch("apps.core.management.commands.check_services.connection") as connection,
        patch("apps.core.management.commands.check_services.Redis.from_url") as redis,
    ):
        connection.cursor.side_effect = RuntimeError("secret-password")
        redis.side_effect = RuntimeError("secret-password")
        with pytest.raises(CommandError):
            call_command("check_services", stdout=output, stderr=output)
    assert "unavailable" in output.getvalue()
    assert "secret-password" not in output.getvalue()
