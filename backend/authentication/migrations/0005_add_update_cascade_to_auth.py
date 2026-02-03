# Generated migration to fix account_emailaddress FK to use ON DELETE CASCADE

from django.db import migrations


class Migration(migrations.Migration):
    """
    Re-apply ON DELETE CASCADE (and ON UPDATE CASCADE) to account_emailaddress.user_id
    -> authentication_user.id.

    Use this if the constraint was recreated without CASCADE (e.g. by a later
    django-allauth migration) and deletes/updates on authentication_user fail.
    """

    dependencies = [
        ("authentication", "0004_add_cascade_to_emailconfirmation"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop existing FK from account_emailaddress to authentication_user (any name)
                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'account_emailaddress'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE account_emailaddress DROP CONSTRAINT %I', constraint_name);
                    END IF;
                END $$;

                -- Recreate with ON DELETE CASCADE and ON UPDATE CASCADE
                ALTER TABLE account_emailaddress
                ADD CONSTRAINT account_emailaddress_user_id_cascade_fk
                FOREIGN KEY (user_id)
                REFERENCES authentication_user(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'account_emailaddress_user_id_cascade_fk'
                    ) THEN
                        ALTER TABLE account_emailaddress
                        DROP CONSTRAINT account_emailaddress_user_id_cascade_fk;
                    END IF;
                END $$;

                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'account_emailaddress'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NULL THEN
                        ALTER TABLE account_emailaddress
                        ADD CONSTRAINT account_emailaddress_user_id_fk
                        FOREIGN KEY (user_id)
                        REFERENCES authentication_user(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
        ),
    ]
