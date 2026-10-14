from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.parametrize("failure", ["publish", "timeout", "wrong_result"])
def test_worker_check_does_not_claim_success_or_leak_errors(failure):
    output = StringIO()
    with patch("apps.core.management.commands.check_worker.worker_ping") as task:
        if failure == "publish":
            task.apply_async.side_effect = RuntimeError("secret-password")
        elif failure == "timeout":
            task.apply_async.return_value.get.side_effect = TimeoutError("secret-password")
        else:
            task.apply_async.return_value.get.return_value = {"status": "wrong"}
        with pytest.raises(CommandError, match="Worker check failed") as error:
            call_command("check_worker", stdout=output)
    assert "secret-password" not in str(error.value)
    assert "completed" not in output.getvalue()


def test_worker_check_waits_for_valid_result():
    output = StringIO()
    with patch("apps.core.management.commands.check_worker.worker_ping") as task:
        task.apply_async.return_value.get.return_value = {
            "status": "ok",
            "service": "tickete-worker",
        }
        call_command("check_worker", timeout=10, stdout=output)
        task.apply_async.return_value.get.assert_called_once_with(timeout=10)
    assert "result verified" in output.getvalue()
