import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.teams.services import process_invitation
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
                invitation_result = process_invitation()
                if invitation_result:
                    self.stdout.write(invitation_result)
                if result:
                    self.stdout.write(result)
                elif options["once"] and not invitation_result:
                    break
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            self.stdout.write("Ticket processor stopped; queued jobs are retained.")
