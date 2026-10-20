from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.core.email import MailDeliveryError


class Command(BaseCommand):
    help = "Send one plain test email to an explicitly supplied recipient (no account tokens)."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True)

    def handle(self, *args, **options):
        recipient = options["to"]
        try:
            validate_email(recipient)
        except ValidationError:
            raise CommandError("Provide a valid recipient email.") from None
        if settings.EMAIL_PROVIDER not in ("smtp", "brevo"):
            raise CommandError("Configure EMAIL_PROVIDER=smtp or brevo before testing delivery.")
        try:
            sent = send_mail(
                "TICKETÉ email delivery test",
                "This is a TICKETÉ configuration test. No account action is required.",
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
        except (ImproperlyConfigured, MailDeliveryError) as exc:
            raise CommandError(str(exc)) from None
        if sent != 1:
            raise CommandError("Email provider did not confirm acceptance.")
        self.stdout.write(
            self.style.SUCCESS("Provider accepted one test email. Check the recipient inbox/spam.")
        )
