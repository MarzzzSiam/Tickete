from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from redis import Redis


class Command(BaseCommand):
    help = "Check PostgreSQL and Redis without printing connection strings or credentials."

    def add_arguments(self, parser):
        parser.add_argument("--service", choices=["all", "database", "redis"], default="all")

    def handle(self, *args, **options):
        failed = []
        if options["service"] in ("all", "database"):
            self.check_database(failed)
        if options["service"] in ("all", "redis"):
            self.check_redis(failed)
        if failed:
            raise CommandError("Readiness failed: " + ", ".join(failed))

    def check_database(self, failed):
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

    def check_redis(self, failed):
        try:
            with Redis.from_url(
                settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3
            ) as client:
                client.ping()
            self.stdout.write(self.style.SUCCESS("Redis: ready"))
        except Exception:
            failed.append("Redis")
            self.stderr.write("Redis: unavailable; check REDIS_URL and service status.")
