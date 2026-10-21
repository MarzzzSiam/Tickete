from pathlib import Path
from types import SimpleNamespace

from django.core.management.base import BaseCommand

from apps.tickets.pdf import render_order_pdf


class Command(BaseCommand):
    help = "Render a fictional two-ticket PDF without database access or email."

    def add_arguments(self, parser):
        parser.add_argument("output")

    def handle(self, *args, **options):
        order = SimpleNamespace(
            number="TE-SAMPLE-ORDER",
            quantity=2,
            snapshot={
                "title": "Afterglow Sessions.",
                "venue": "Sample Hall, Dhaka, Bangladesh",
                "starts_at": "2026-11-21T12:00:00+00:00",
                "ends_at": "2026-11-21T16:00:00+00:00",
                "organizer_contact": "organizer@example.com",
                "items": [{"category_id": "sample", "name": "GENERAL ADMISSION"}],
            },
        )
        tickets = [
            SimpleNamespace(
                category_id="sample",
                position=i,
                code=f"TE-SAMPLE-TICKET-{i}",
                attendee_name="Samira Rahman" if i == 1 else "",
                qr_token=f"TICKETE-SAMPLE-NOT-VALID-{i}",
            )
            for i in (1, 2)
        ]
        path = Path(options["output"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(render_order_pdf(order, tickets, sample=True))
        self.stdout.write("Fictional PDF generated; no tickets or emails were created.")
