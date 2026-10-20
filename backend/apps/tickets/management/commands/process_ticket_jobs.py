import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.tickets.delivery import process_next


class Command(BaseCommand):
    help = "Generate and email queued tickets locally; no paid worker or Celery required."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Process currently due jobs and exit."
        )

    def handle(self, *args, **options):
        self.stdout.write("Ticket processor started. Press Ctrl+C to stop.")
        try:
            while True:
                close_old_connections()
                result = process_next()
                if result:
                    self.stdout.write(result)
                elif options["once"]:
                    break
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            self.stdout.write("Ticket processor stopped; queued jobs are retained.")
