import hashlib
import json
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.events.models import Event, TicketCategory
from apps.payments.gateway import gateway
from apps.payments.models import Payment
from apps.tickets.models import Ticket, TicketDelivery

from .models import Order, SeatHold


class CheckoutConflict(APIException):
    status_code = 409
    default_code = "checkout_conflict"
    default_detail = "Checkout changed. Please choose your tickets again."


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def authorize(order, token):
    if not token or not secrets.compare_digest(order.access_digest, digest(token)):
        raise NotFound("Order not found.")


def sales_open(event, now):
    return bool(
        event.status == Event.Status.APPROVED
        and event.sales_start
        and event.sales_end
        and event.ends_at
        and event.sales_start <= now < event.sales_end
        and now < event.ends_at
    )


def validate_answers(event, answers):
    fields = list(event.form_fields.all())
    if set(answers) - {str(field.id) for field in fields}:
        raise ValidationError("An answer refers to an unknown event question.")
    snapshot = []
    for field in fields:
        value = answers.get(str(field.id))
        missing = value is None or value == "" or (field.type == "checkbox" and value is False)
        if field.required and missing:
            raise ValidationError(f"Answer required: {field.label}")
        if not missing:
            valid = True
            if field.type == "text":
                valid = isinstance(value, str) and len(value) <= 2000
            elif field.type == "dropdown":
                valid = isinstance(value, str) and value in field.options
            elif field.type == "checkbox":
                valid = isinstance(value, bool)
            elif field.type == "number":
                try:
                    valid = (
                        not isinstance(value, bool)
                        and len(str(value)) <= 50
                        and Decimal(str(value)).is_finite()
                    )
                except (InvalidOperation, ValueError):
                    valid = False
            if not valid:
                raise ValidationError(f"Invalid answer: {field.label}")
        snapshot.append({"id": str(field.id), "label": field.label, "value": value})
    return snapshot


def create_order(data, user=None):
    try:
        return _create_order(data, user)
    except IntegrityError:
        # Concurrent reuse across different event locks is also rejected safely.
        raise CheckoutConflict(
            "Checkout reference is already in use. Retry your original request."
        ) from None


@transaction.atomic
def _create_order(data, user):
    event = get_object_or_404(
        Event.objects.select_for_update(), pk=data["event_id"], status="approved"
    )
    fingerprint = digest(json.dumps(data, sort_keys=True, default=str))
    existing = Order.objects.filter(idempotency_key=data["idempotency_key"]).first()
    if existing:
        authorize(existing, data["access_token"])
        if existing.request_digest != fingerprint:
            raise CheckoutConflict("This checkout reference belongs to different details.")
        return existing
    now = timezone.now()
    if not sales_open(event, now):
        raise CheckoutConflict("Ticket sales are not open for this event.")
    buyer_email = data["buyer_email"].strip().lower()
    recipient = data.get("recipient_email", "").strip().lower() if data["is_gift"] else buyer_email
    if not recipient:
        raise ValidationError("Enter a recipient email for your gift.")
    quantity = sum(item["quantity"] for item in data["selections"])
    paid = (
        Order.objects.filter(event=event, buyer_email=buyer_email, status="paid").aggregate(
            n=Sum("quantity")
        )["n"]
        or 0
    )
    reserved = (
        Order.objects.filter(
            event=event, buyer_email=buyer_email, status="pending", expires_at__gt=now
        ).aggregate(n=Sum("quantity"))["n"]
        or 0
    )
    if quantity > event.max_per_order or quantity + paid + reserved > event.max_per_order:
        raise CheckoutConflict(
            "The ticket limit per order or buyer email for this event would be exceeded."
        )
    ids = [item["category_id"] for item in data["selections"]]
    categories = {
        c.id: c
        for c in TicketCategory.objects.select_for_update()
        .filter(event=event, id__in=ids)
        .order_by("id")
    }
    items = []
    total = Decimal("0.00")
    for selection in data["selections"]:
        category = categories.get(selection["category_id"])
        if not category or not category.is_active or category.price <= 0:
            raise ValidationError(
                "Choose active, paid ticket categories from this event. Free tickets are not available yet."
            )
        held = (
            SeatHold.objects.filter(
                category=category, status="active", expires_at__gt=now
            ).aggregate(n=Sum("quantity"))["n"]
            or 0
        )
        if (
            category.seat_limit is not None
            and category.sold_count + held + selection["quantity"] > category.seat_limit
        ):
            raise CheckoutConflict(f"Not enough tickets remain in {category.name}.")
        names = selection["attendee_names"]
        if len(names) > selection["quantity"] or (names and not event.collect_attendee_names):
            raise ValidationError("Attendee names do not match this event's ticket selection.")
        items.append(
            {
                "category_id": str(category.id),
                "name": category.name,
                "price": str(category.price),
                "quantity": selection["quantity"],
                "attendee_names": names + [""] * (selection["quantity"] - len(names)),
            }
        )
        total += category.price * selection["quantity"]
    snapshot = {
        "banner_key": event.banner_key,
        "organizer_contact": event.owner.email,
        "title": event.title,
        "venue": event.venue,
        "starts_at": event.starts_at.isoformat(),
        "ends_at": event.ends_at.isoformat(),
        "items": items,
        "answers": validate_answers(event, data["answers"]),
    }
    buyer = (
        user
        if user and user.is_authenticated and user.email_verified and user.email == buyer_email
        else None
    )
    order = Order.objects.create(
        event=event,
        buyer=buyer,
        buyer_email=buyer_email,
        recipient_email=recipient,
        is_gift=data["is_gift"],
        total=total,
        quantity=quantity,
        access_digest=digest(data["access_token"]),
        idempotency_key=data["idempotency_key"],
        request_digest=fingerprint,
        snapshot=snapshot,
        expires_at=min(now + timedelta(minutes=10), event.sales_end, event.ends_at),
    )
    SeatHold.objects.bulk_create(
        [
            SeatHold(
                order=order,
                category=categories[item["category_id"]],
                quantity=item["quantity"],
                expires_at=order.expires_at,
            )
            for item in data["selections"]
        ]
    )
    return order


def locked_order(order_id, token):
    initial = get_object_or_404(Order, pk=order_id)
    authorize(initial, token)
    event = Event.objects.select_for_update().get(pk=initial.event_id)
    categories = list(
        TicketCategory.objects.select_for_update()
        .filter(seathold__order_id=order_id)
        .order_by("id")
    )
    order = Order.objects.select_for_update().get(pk=order_id)
    authorize(order, token)
    return event, categories, order


def release(order, status):
    order.status = status
    order.save(update_fields=["status"])
    order.holds.filter(status="active").update(status="released")
    Payment.objects.filter(order=order, status="initiated").update(status="failed")


def expire_if_needed(event, order):
    if order.status == "pending" and (
        order.expires_at <= timezone.now() or not sales_open(event, timezone.now())
    ):
        release(order, "expired")


@transaction.atomic
def read_order(order_id, token):
    event, _, order = locked_order(order_id, token)
    expire_if_needed(event, order)
    return order


@transaction.atomic
def initiate_payment(order_id, token, data):
    event, _, order = locked_order(order_id, token)
    expire_if_needed(event, order)
    if order.status != "pending":
        return order
    payment = Payment.objects.filter(order=order).first()
    if payment:
        if payment.provider != data["provider"] or payment.phone != data["phone"]:
            raise CheckoutConflict("A payment attempt already exists for this order.")
    else:
        Payment.objects.create(order=order, amount=gateway().initiate(order), **data)
    return order


@transaction.atomic
def verify_payment(order_id, token, otp):
    event, categories, order = locked_order(order_id, token)
    expire_if_needed(event, order)
    if order.status != "pending":
        return order
    payment = get_object_or_404(Payment.objects.select_for_update(), order=order)
    if payment.status != "initiated" or payment.amount != order.total:
        raise CheckoutConflict("Payment is not available for this order.")
    payment.attempts += 1
    if not gateway().verify_otp(payment, otp):
        payment.save(update_fields=["attempts"])
        if payment.attempts >= 5:
            release(order, "failed")
        return order
    holds = list(order.holds.all())
    if any(hold.status != "active" or hold.expires_at <= timezone.now() for hold in holds):
        release(order, "expired")
        return order
    by_id = {c.id: c for c in categories}
    for hold in holds:
        category = by_id[hold.category_id]
        if (
            category.seat_limit is not None
            and category.sold_count + hold.quantity > category.seat_limit
        ):
            raise CheckoutConflict("Inventory changed; contact support.")
        category.sold_count += hold.quantity
        category.save(update_fields=["sold_count"])
    tickets = []
    for item in order.snapshot["items"]:
        for name in item["attendee_names"]:
            tickets.append(
                Ticket(
                    order=order,
                    category_id=item["category_id"],
                    attendee_name=name,
                    recipient_email=order.recipient_email,
                    position=len(tickets) + 1,
                )
            )
    Ticket.objects.bulk_create(tickets)
    order.holds.update(status="converted")
    order.status = "paid"
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at"])
    payment.status = "success"
    payment.verified_at = order.paid_at
    payment.save(update_fields=["status", "verified_at", "attempts"])
    TicketDelivery.objects.get_or_create(order=order)
    return order


@transaction.atomic
def cancel_order(order_id, token):
    event, _, order = locked_order(order_id, token)
    expire_if_needed(event, order)
    if order.status == "pending":
        release(order, "failed")
    return order


def result(order):
    from apps.tickets.delivery import delivery_status

    payment = Payment.objects.filter(order=order).first()
    return {
        "id": order.id,
        "number": order.number,
        "status": order.status,
        "total": order.total,
        "quantity": order.quantity,
        "expires_at": order.expires_at,
        "server_time": timezone.now(),
        "recipient_email": order.recipient_email,
        "is_gift": order.is_gift,
        "snapshot": order.snapshot,
        "payment": (
            {
                "provider": payment.provider,
                "status": payment.status,
                "attempts_remaining": max(0, 5 - payment.attempts),
            }
            if payment
            else None
        ),
        "tickets": list(
            order.tickets.values("id", "code", "category_id", "attendee_name", "position", "status")
        ),
        "delivery_status": delivery_status(order),
        "pdf_ready": TicketDelivery.objects.filter(order=order).exclude(pdf_key="").exists(),
    }


def cleanup_expired_holds(limit=100):
    """Use the same event-before-order locking order as checkout/payment."""
    ids = list(
        Order.objects.filter(status="pending", expires_at__lte=timezone.now())
        .order_by("expires_at")
        .values_list("pk", "event_id")[:limit]
    )
    count = 0
    for order_id, event_id in ids:
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=event_id)
            order = Order.objects.select_for_update().get(pk=order_id)
            if order.status == "pending" and order.expires_at <= timezone.now():
                expire_if_needed(event, order)
                count += 1
    return count
