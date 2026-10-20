import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.events.models import Event, TicketCategory


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
        now = timezone.now()
        event, created = Event.objects.get_or_create(
            slug="fictional-checkout-demo",
            defaults={
                "owner": User.objects.get(email="demo-organizer@example.com"),
                "title": "Fictional Afterglow Sessions",
                "description": "Disposable test event. No real money is charged.",
                "venue": "Sample Hall, Dhaka",
                "status": "approved",
                "starts_at": now + timedelta(days=7),
                "ends_at": now + timedelta(days=8),
                "sales_start": now - timedelta(days=1),
                "sales_end": now + timedelta(days=6),
                "max_per_order": 5,
                "collect_attendee_names": True,
            },
        )
        if created:
            for name, price in [
                ("General", "500.00"),
                ("Premium", "900.00"),
                ("Balcony", "700.00"),
            ]:
                TicketCategory.objects.create(event=event, name=name, price=price, seat_limit=100)
        self.stdout.write("Demo accounts and fictional event ready; passwords are not printed.")
