from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("tickets", "0004_recovery_sessions"), ("core", "0005_operations_privacy")]
    operations = [
        migrations.RunSQL(
            """
        ALTER TABLE public.tickets_ticketrecovery ENABLE ROW LEVEL SECURITY;
        DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
            REVOKE ALL ON TABLE public.tickets_ticketrecovery FROM anon;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
            REVOKE ALL ON TABLE public.tickets_ticketrecovery FROM authenticated;
        END IF;
        END $$;
    """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
