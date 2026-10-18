from urllib.parse import urlencode

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.core.email import MailDeliveryError

from .models import EmailChallenge, User
from .services import create_challenge


@shared_task(
    ignore_result=True,
    autoretry_for=(MailDeliveryError,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def deliver_account_link(email, purpose):
    if purpose not in EmailChallenge.Purpose.values:
        return
    user = User.objects.filter(email=email, is_active=True).first()
    if not user or (purpose == EmailChallenge.Purpose.VERIFY and user.email_verified):
        return
    challenge, raw = create_challenge(user.pk, purpose)
    # Fragments are not sent in HTTP requests or referrers; the form reads them.
    route = "verify-email" if purpose == EmailChallenge.Purpose.VERIFY else "reset-password"
    link = f"{settings.FRONTEND_ORIGIN}/{route}#" + urlencode(
        {
            "challenge_id": str(challenge.pk),
            "token": raw,
        }
    )
    send_mail(
        "TICKETÉ: verify your email" if purpose == "verify" else "TICKETÉ: reset your password",
        f"Use this link within 30 minutes:\n{link}\n\nIf you did not request this, ignore this email.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
