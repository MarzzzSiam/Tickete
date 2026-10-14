from django.core.management.base import BaseCommand, CommandError

from apps.core.tasks import worker_ping


class Command(BaseCommand):
    help = "Submit a harmless task and verify its result without printing credentials."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=30)

    def handle(self, *args, **options):
        if not 1 <= options["timeout"] <= 120:
            raise CommandError("Timeout must be between 1 and 120 seconds.")
        try:
            result = worker_ping.apply_async(retry=False, expires=options["timeout"])
            payload = result.get(timeout=options["timeout"])
            if payload != {"status": "ok", "service": "tickete-worker"}:
                raise ValueError("Unexpected worker result")
        except Exception:
            raise CommandError(
                "Worker check failed: verify Redis, worker logs and matching environments."
            ) from None
        self.stdout.write(self.style.SUCCESS("Celery: task completed and result verified"))
