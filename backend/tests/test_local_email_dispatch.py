from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.accounts.throttles import AuthUnavailable
from apps.accounts.views import enqueue_link


@override_settings(DEBUG=True, LOCAL_ACCOUNT_EMAIL_SYNC=True)
def test_local_dispatch_does_not_queue():
    with (
        patch("apps.accounts.views.deliver_account_link") as task,
        patch("apps.accounts.views.send_account_link") as send,
    ):
        enqueue_link("fictional@example.com", "verify")
        send.assert_called_once_with("fictional@example.com", "verify")
        task.apply_async.assert_not_called()


@override_settings(DEBUG=False, LOCAL_ACCOUNT_EMAIL_SYNC=True)
def test_hosted_dispatch_never_uses_local_mode():
    with (
        patch("apps.accounts.views.deliver_account_link") as task,
        patch("apps.accounts.views.send_account_link") as send,
    ):
        enqueue_link("fictional@example.com", "verify")
        task.apply_async.assert_called_once_with(
            args=["fictional@example.com", "verify"], retry=False
        )
        send.assert_not_called()


@override_settings(DEBUG=True, LOCAL_ACCOUNT_EMAIL_SYNC=True)
def test_local_failure_does_not_claim_delivery():
    with (
        patch("apps.accounts.views.deliver_account_link") as task,
        patch("apps.accounts.views.send_account_link", side_effect=RuntimeError("private")),
    ):
        with pytest.raises(AuthUnavailable):
            enqueue_link("fictional@example.com", "verify")
        task.apply_async.assert_not_called()
