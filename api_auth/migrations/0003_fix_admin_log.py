from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('api_auth', '0002_user_groups_user_user_permissions'), 
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE django_admin_log
            DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_auth_user_id;
            """,
            """
            ALTER TABLE django_admin_log
            ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id
            FOREIGN KEY (user_id) REFERENCES auth_user(id);
            """
        ),
        migrations.RunSQL(
            """
            ALTER TABLE django_admin_log
            ADD CONSTRAINT django_admin_log_user_id_fk
            FOREIGN KEY (user_id) REFERENCES api_auth_user(id);
            """,
            """
            ALTER TABLE django_admin_log
            DROP CONSTRAINT IF EXISTS django_admin_log_user_id_fk;
            """
        ),
    ]