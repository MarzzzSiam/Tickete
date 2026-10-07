from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from redis import Redis


class Command(BaseCommand):
    help = "Check PostgreSQL and Redis without printing connection strings or credentials."

    def handle(self, *args, **options):
        failed = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS("PostgreSQL: ready"))
        except Exception:
            failed.append("PostgreSQL")
            self.stderr.write("PostgreSQL: unavailable; check DATABASE_URL and service status.")
        finally:
            connection.close()
        try:
            with Redis.from_url(
                settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3
            ) as client:
                client.ping()
            self.stdout.write(self.style.SUCCESS("Redis: ready"))
        except Exception:
            failed.append("Redis")
            self.stderr.write("Redis: unavailable; check REDIS_URL and service status.")
        if failed:
            raise CommandError("Readiness failed: " + ", ".join(failed))
