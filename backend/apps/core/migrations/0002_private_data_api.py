from django.db import migrations

TABLES = [
    "accounts_user",
    "accounts_user_groups",
    "accounts_user_user_permissions",
    "accounts_authsession",
    "accounts_emailchallenge",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "django_content_type",
    "django_admin_log",
    "django_session",
    "django_migrations",
    "core_auditlog",
    "events_event",
    "events_ticketcategory",
    "events_eventformfield",
    "notifications_notification",
]

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
        ("core", "0001_initial"),
        ("accounts", "0002_authsession_emailchallenge"),
        ("events", "0001_initial"),
        ("notifications", "0001_initial"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("sessions", "0001_initial"),
    ]
    # Django connects as the table owner; browser access goes only through Django.
    # Rollback deliberately does not reopen direct Data API privileges.
    operations = [migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop)]
