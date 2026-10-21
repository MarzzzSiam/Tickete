import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.orders.services import cleanup_expired_holds
from apps.teams.services import process_invitation
from apps.tickets.delivery import process_next
from apps.tickets.recovery import process_recovery


class Command(BaseCommand):
    help = "Process ticket, invitation and recovery emails, and expire abandoned holds locally."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Process currently due jobs and exit."
        )

    def handle(self, *args, **options):
        self.stdout.write("Ticket processor started. Press Ctrl+C to stop.")
        last_cleanup = 0
        try:
            while True:
                close_old_connections()
                if time.monotonic() - last_cleanup >= 60:
                    cleanup_expired_holds()
                    last_cleanup = time.monotonic()
                recovery_result = process_recovery()
                if recovery_result:
                    self.stdout.write(recovery_result)
                result = process_next()
                invitation_result = process_invitation()
                if invitation_result:
                    self.stdout.write(invitation_result)
                if result:
                    self.stdout.write(result)
                elif options["once"] and not invitation_result and not recovery_result:
                    break
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            self.stdout.write("Ticket processor stopped; queued jobs are retained.")
