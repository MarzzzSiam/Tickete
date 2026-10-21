from django.db import migrations

TABLES = ["teams_teammember", "teams_invitation", "checkin_checkinlog"]
SQL = "\n".join(f"""ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN REVOKE ALL ON TABLE public."{table}" FROM anon; END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN REVOKE ALL ON TABLE public."{table}" FROM authenticated; END IF;
END $$;""" for table in TABLES)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_private_ticket_delivery"),
        ("teams", "0001_initial"),
        ("checkin", "0001_initial"),
        ("tickets", "0003_ticket_used_at_ticket_used_by"),
    ]
    operations = [migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop)]
