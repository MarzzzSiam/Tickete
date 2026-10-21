import hashlib
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from rest_framework.exceptions import NotFound, ValidationError

from apps.orders.models import Order

from .models import TicketDelivery, TicketRecovery


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def code_digest(item, code):
    return salted_hmac("ticket-recovery-code", f"{item.pk}:{code}", algorithm="sha256").hexdigest()


def start(email, token):
    # Queue the same email for all valid addresses, regardless of purchase history.
    return TicketRecovery.objects.create(email=email.strip().lower(), access_digest=digest(token))


@transaction.atomic
def process_recovery():
    now = timezone.now()
    item = (
        TicketRecovery.objects.select_for_update(skip_locked=True)
        .filter(
            sent_at__isnull=True,
            send_attempts__lt=5,
            next_attempt_at__lte=now,
            created_at__gt=now - timedelta(minutes=30),
        )
        .order_by("created_at")
        .first()
    )
    if not item:
        return None
    code = f"{secrets.randbelow(1000000):06d}"
    item.send_attempts += 1
    try:
        sent = send_mail(
            "Your TICKETÉ recovery code",
            f"Your ticket recovery code is {code}. It expires in 10 minutes.\n\n"
            "Enter it only in the TICKETÉ recovery page you opened. Never share this code. "
            "If you did not request it, ignore this email.",
            None,
            [item.email],
        )
        if sent != 1:
            raise RuntimeError("Email not accepted")
        item.code_digest = code_digest(item, code)
        item.sent_at = timezone.now()
        item.expires_at = item.sent_at + timedelta(minutes=10)
    except Exception:
        item.next_attempt_at = now + timedelta(seconds=min(60 * 2**item.send_attempts, 3600))
    item.save()
    return "recovery_code_sent" if item.sent_at else "recovery_email_failed"


def authorized(pk, token, lock=False, verified=True):
    queryset = TicketRecovery.objects.select_for_update() if lock else TicketRecovery.objects.all()
    item = get_object_or_404(queryset, pk=pk)
    if not token or not constant_time_compare(item.access_digest, digest(token)):
        raise NotFound("Recovery session not found.")
    if verified and (not item.verified_at or item.session_expires_at <= timezone.now()):
        raise NotFound("Recovery session expired. Request a new code.")
    return item


def verify(pk, token, code):
    # Commit failed attempts before raising the validation error.
    with transaction.atomic():
        item = authorized(pk, token, lock=True, verified=False)
        valid = False
        if (
            not item.verified_at
            and item.sent_at
            and item.expires_at > timezone.now()
            and item.attempts < 5
        ):
            item.attempts += 1
            valid = constant_time_compare(item.code_digest, code_digest(item, code))
            if valid:
                item.verified_at = timezone.now()
                item.session_expires_at = item.verified_at + timedelta(minutes=30)
                item.code_digest = ""
            item.save()
    if not valid:
        raise ValidationError(
            {"detail": "Code invalid, expired or already used. Request a new code if needed."}
        )
    return item


def orders_for(item):
    return Order.objects.filter(
        Q(buyer_email=item.email) | Q(recipient_email=item.email), status="paid"
    ).order_by("-paid_at", "-id")


@transaction.atomic
def resend(item, order_id):
    order = get_object_or_404(orders_for(item), pk=order_id)
    # Only fixed addresses on the paid order are used; no destination input accepted.
    job, _ = TicketDelivery.objects.get_or_create(order=order)
    job = TicketDelivery.objects.select_for_update().get(order=order)
    now = timezone.now()
    if job.last_requested_at and job.last_requested_at > now - timedelta(minutes=1):
        raise ValidationError(
            {"detail": "Please wait one minute before requesting another resend."}
        )
    if job.completed_at or job.attempts >= 5:
        job.recipient_sent = False
        job.receipt_sent = False
        job.completed_at = None
        job.attempts = 0
        job.last_error = ""
        job.next_attempt_at = now
    job.last_requested_at = now
    job.save()
    return job
