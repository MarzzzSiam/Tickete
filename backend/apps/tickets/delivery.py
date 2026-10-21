from datetime import timedelta

from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from apps.core.storage import get_storage

from .models import TicketDelivery
from .pdf import render_order_pdf


def delivery_status(order):
    delivery = TicketDelivery.objects.filter(order=order).first()
    if not delivery:
        return "not_queued"
    if delivery.completed_at:
        return "sent"
    if delivery.attempts >= 5:
        return "failed"
    return "retrying" if delivery.attempts else "queued"


@transaction.atomic
def process_next():
    # Keep this lock through processing: another worker skips the in-flight job.
    # A crashed process releases its lock and the durable row can be retried.
    job = (
        TicketDelivery.objects.select_for_update(skip_locked=True)
        .filter(completed_at__isnull=True, attempts__lt=5, next_attempt_at__lte=timezone.now())
        .order_by("next_attempt_at")
        .first()
    )
    if not job:
        return None
    job.attempts += 1
    stage = "pdf"
    try:
        order = job.order
        if order.status != "paid":
            raise ValueError("Only paid orders may be delivered.")
        storage = get_storage()
        if not job.pdf_key:
            content = render_order_pdf(order, list(order.tickets.all()))
            job.pdf_key = storage.put(f"tickets/{order.id}/order.pdf", content, "application/pdf")
        else:
            content = storage.read(job.pdf_key)
        stage = "email"
        if not job.recipient_sent:
            message = EmailMessage(
                f"Your TICKETÉ tickets - {order.number}",
                f"Your tickets for {order.snapshot['title']} are attached. "
                "Each page admits one person. Keep your QR codes private.\n\n"
                "This order used a simulated payment; no money was charged.",
                to=[order.recipient_email],
            )
            message.attach(f"{order.number}.pdf", content, "application/pdf")
            if message.send() != 1:
                raise RuntimeError("Email backend did not accept delivery.")
            job.recipient_sent = True
        if not job.receipt_sent:
            if order.is_gift and order.buyer_email != order.recipient_email:
                message = EmailMessage(
                    f"TICKETÉ gift receipt - {order.number}",
                    f"Your gift order for {order.snapshot['title']} contains {order.quantity} "
                    f"ticket(s). Ticket delivery was accepted for {order.recipient_email}.\n"
                    f"Order total: BDT {order.total}. Simulated payment only; no money was charged.",
                    to=[order.buyer_email],
                )
                if message.send() != 1:
                    raise RuntimeError("Email backend did not accept receipt.")
            job.receipt_sent = True
        job.completed_at = timezone.now()
        job.last_error = ""
    except Exception:
        # Never store provider errors that may contain passwords, addresses or QR data.
        job.last_error = f"{stage}_failed"
        job.next_attempt_at = timezone.now() + timedelta(seconds=min(60 * 2**job.attempts, 3600))
    job.save()
    return "sent" if job.completed_at else job.last_error
