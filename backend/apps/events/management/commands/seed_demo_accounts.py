import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create fictional, verified review accounts in an explicitly enabled development environment."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_ACCOUNT_PASSWORD", "")
        if (
            not settings.DEBUG
            or os.environ.get("TICKETE_ALLOW_DEMO_SEED") != "1"
            or len(password) < 16
        ):
            raise CommandError(
                "Requires local settings, TICKETE_ALLOW_DEMO_SEED=1 and a private DEMO_ACCOUNT_PASSWORD of at least 16 characters."
            )
        for role in ("organizer", "admin"):
            email = f"demo-{role}@example.com"
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"Existing demo {role} left unchanged.")
                continue
            User.objects.create_user(
                email, password, role=role, full_name=f"Demo {role}", email_verified=True
            )
        self.stdout.write("Demo accounts ready; passwords are not printed.")
