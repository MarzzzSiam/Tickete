from django.db import migrations

TABLES = ["orders_order", "orders_seathold", "payments_payment", "tickets_ticket"]
SQL = "\n".join(f"""ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
  REVOKE ALL ON TABLE public."{table}" FROM anon;
 END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
  REVOKE ALL ON TABLE public."{table}" FROM authenticated;
 END IF;
END $$;""" for table in TABLES)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_private_data_api"),
        ("orders", "0001_initial"),
        ("payments", "0001_initial"),
        ("tickets", "0001_initial"),
    ]
    operations = [migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop)]
