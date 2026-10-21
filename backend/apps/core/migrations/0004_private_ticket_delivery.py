from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0003_checkout_privacy"), ("tickets", "0002_ticketdelivery")]
    operations = [
        migrations.RunSQL(
            """
ALTER TABLE public.tickets_ticketdelivery ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
  REVOKE ALL ON TABLE public.tickets_ticketdelivery FROM anon;
 END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
  REVOKE ALL ON TABLE public.tickets_ticketdelivery FROM authenticated;
 END IF;
END $$;
""",
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
