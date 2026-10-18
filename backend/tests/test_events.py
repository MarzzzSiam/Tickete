from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.events.models import Event, TicketCategory
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_application_tables_have_row_security_enabled():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname IN ('events_event', 'accounts_user', 'accounts_authsession', 'core_auditlog', 'notifications_notification')"
        )
        flags = cursor.fetchall()
    assert len(flags) == 5
    assert all(enabled for _, enabled in flags)


@pytest.fixture
def owner():
    return User.objects.create_user("owner@example.com", role="organizer", email_verified=True)


@pytest.fixture
def admin():
    return User.objects.create_user("admin@example.com", role="admin")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def draft_data():
    now = timezone.now()
    return {
        "title": "Demo festival",
        "description": "A fictional event.",
        "venue": "Dhaka",
        "starts_at": (now + timedelta(days=3)).isoformat(),
        "ends_at": (now + timedelta(days=4)).isoformat(),
        "sales_start": now.isoformat(),
        "sales_end": (now + timedelta(days=2)).isoformat(),
        "max_per_order": 5,
        "categories": [{"name": "General", "price": "500.00", "seat_limit": 20}],
        "form_fields": [
            {"label": "Meal", "type": "dropdown", "options": ["Standard", "Vegetarian"]}
        ],
    }


def draft(owner):
    response = client_for(owner).post("/api/v1/events/", draft_data(), format="json")
    assert response.status_code == 201, response.data
    return response.data["id"]


def test_publish_flow_is_private_until_approved_and_records_audit(owner, admin):
    pk = draft(owner)
    user = client_for(owner)
    assert APIClient().get("/api/v1/public/events/").data["count"] == 0
    assert user.post(f"/api/v1/events/{pk}/submit/").status_code == 200
    assert Notification.objects.filter(recipient=admin, type="event_submitted").count() == 1
    assert (
        user.patch(f"/api/v1/events/{pk}/", {"title": "Changed"}, format="json").status_code == 409
    )
    result = client_for(admin).post(f"/api/v1/admin/events/{pk}/approve/")
    assert result.status_code == 200
    assert result.data["slug"]
    public = APIClient().get(f"/api/v1/public/events/{result.data['slug']}/")
    assert public.status_code == 200
    assert not ({"owner", "reviewer", "rejection_reason", "banner_key"} & set(public.data))
    assert AuditLog.objects.filter(target_id=pk, action="event_approved").count() == 1
    assert Notification.objects.filter(recipient=owner).count() == 1
    assert client_for(admin).post(f"/api/v1/admin/events/{pk}/approve/").status_code == 409
    assert (
        user.patch(f"/api/v1/events/{pk}/", {"title": "Changed"}, format="json").status_code == 409
    )


def test_rejection_requires_reason_then_edit_and_resubmit(owner, admin):
    pk = draft(owner)
    client_for(owner).post(f"/api/v1/events/{pk}/submit/")
    api = client_for(admin)
    assert (
        api.post(f"/api/v1/admin/events/{pk}/reject/", {"reason": " "}, format="json").status_code
        == 400
    )
    assert (
        api.post(
            f"/api/v1/admin/events/{pk}/reject/", {"reason": "Clarify venue"}, format="json"
        ).status_code
        == 200
    )
    assert client_for(owner).post(f"/api/v1/events/{pk}/submit/").status_code == 409
    assert (
        client_for(owner)
        .patch(f"/api/v1/events/{pk}/", {"venue": "Dhaka Hall"}, format="json")
        .status_code
        == 200
    )
    assert client_for(owner).post(f"/api/v1/events/{pk}/submit/").status_code == 200
    event = Event.objects.get(pk=pk)
    assert event.rejection_reason == "" and event.slug is None


@pytest.mark.parametrize("role", ["buyer", "admin"])
def test_only_organizers_create_drafts(role):
    user = User.objects.create_user(f"{role}@example.com", role=role)
    assert client_for(user).post("/api/v1/events/", draft_data(), format="json").status_code == 403


def test_cross_event_permissions_and_unverified_submission(owner, admin):
    pk = draft(owner)
    other = User.objects.create_user("other@example.com", role="organizer")
    client = client_for(other)
    for suffix in ("", "preview/"):
        assert client.get(f"/api/v1/events/{pk}/{suffix}").status_code == 404
    assert (
        client.patch(f"/api/v1/events/{pk}/", {"title": "Stolen"}, format="json").status_code == 404
    )
    assert client.post(f"/api/v1/admin/events/{pk}/approve/").status_code == 403
    assert client_for(admin).get(f"/api/v1/events/{pk}/").status_code == 403
    owner.email_verified = False
    owner.save()
    assert client_for(owner).post(f"/api/v1/events/{pk}/submit/").status_code == 403


@pytest.mark.parametrize(
    "change",
    [
        {"status": "approved"},
        {"owner": "anything"},
        {"max_per_order": 0},
        {"categories": [{"name": "Bad", "price": "-1", "seat_limit": 1}]},
        {"categories": [{"name": "Bad", "price": "1", "seat_limit": 0}]},
        {"form_fields": [{"label": "Bad", "type": "dropdown", "options": []}]},
    ],
)
def test_invalid_or_privileged_fields_rejected(owner, change):
    assert (
        client_for(owner)
        .post("/api/v1/events/", {**draft_data(), **change}, format="json")
        .status_code
        == 400
    )
    assert not Event.objects.exists()


def test_schedule_and_required_submission_fields(owner):
    api = client_for(owner)
    data = draft_data()
    data["sales_end"] = data["starts_at"] = data["ends_at"]
    assert api.post("/api/v1/events/", data, format="json").status_code == 400
    response = api.post("/api/v1/events/", {"title": "Incomplete"}, format="json")
    assert response.status_code == 201
    assert api.post(f"/api/v1/events/{response.data['id']}/submit/").status_code == 400


def test_nested_edits_preserve_ids_and_reject_cross_event_ids_atomically(owner):
    first, second = draft(owner), draft(owner)
    category = TicketCategory.objects.get(event_id=first)
    api = client_for(owner)
    data = {
        "categories": [
            {"id": str(category.pk), "name": "Updated", "price": "600.50", "seat_limit": None}
        ]
    }
    assert api.patch(f"/api/v1/events/{first}/", data, format="json").status_code == 200
    category.refresh_from_db()
    assert category.price == Decimal("600.50") and category.seat_limit is None
    data["title"] = "Must roll back"
    assert api.patch(f"/api/v1/events/{second}/", data, format="json").status_code == 400
    assert Event.objects.get(pk=second).title == "Demo festival"


def test_notifications_are_recipient_scoped(owner, admin):
    pk = draft(owner)
    client_for(owner).post(f"/api/v1/events/{pk}/submit/")
    item = Notification.objects.get(recipient=admin)
    assert client_for(owner).get("/api/v1/notifications/").data["count"] == 0
    assert client_for(owner).post(f"/api/v1/notifications/{item.pk}/read/").status_code == 404
    assert client_for(admin).post(f"/api/v1/notifications/{item.pk}/read/").data["is_read"] is True


def test_banner_validation_reencoding_and_public_privacy(owner):
    pk = draft(owner)
    api = client_for(owner)
    assert (
        api.post(
            f"/api/v1/events/{pk}/banner/", {"banner": SimpleUploadedFile("bad.svg", b"<svg/>")}
        ).status_code
        == 400
    )
    source = BytesIO()
    Image.new("RGB", (32, 32), "blue").save(source, format="PNG")
    with patch("apps.events.views.get_storage") as storage:
        response = api.post(
            f"/api/v1/events/{pk}/banner/",
            {
                "banner": SimpleUploadedFile(
                    "banner.png", source.getvalue(), content_type="image/png"
                )
            },
        )
    assert response.status_code == 200 and response.data["has_banner"]
    assert storage.return_value.put.call_args.args[1].startswith(b"\xff\xd8")
    assert APIClient().get(f"/api/v1/public/events/{pk}/banner/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_reviews_have_only_one_winner(owner, admin):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    from apps.events.services import StateConflict, review

    pk = draft(owner)
    client_for(owner).post(f"/api/v1/events/{pk}/submit/")
    barrier = Barrier(2)

    def compete(approved):
        close_old_connections()
        try:
            reviewer = User.objects.get(pk=admin.pk)
            barrier.wait(timeout=10)
            try:
                review(reviewer, pk, approved, "Needs details")
                return "won"
            except StateConflict:
                return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, [True, False]))
    assert sorted(results) == ["conflict", "won"]
    assert AuditLog.objects.filter(target_id=pk).count() == 1
