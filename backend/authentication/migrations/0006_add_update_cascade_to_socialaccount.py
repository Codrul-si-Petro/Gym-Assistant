# Add ON UPDATE CASCADE to socialaccount FKs that reference authentication_user

from django.db import migrations


class Migration(migrations.Migration):
    """
    Add ON UPDATE CASCADE to socialaccount_socialaccount.user_id and
    socialaccount_socialtoken.account_id so updates to authentication_user.id
    (or socialaccount_socialaccount.id) cascade instead of violating the FK.
    """

    dependencies = [
        ("authentication", "0005_add_update_cascade_to_auth"),
    ]

    operations = [
        # socialaccount_socialaccount.user_id -> authentication_user(id)
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'socialaccount_socialaccount'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE socialaccount_socialaccount DROP CONSTRAINT %I', constraint_name);
                    END IF;
                END $$;

                ALTER TABLE socialaccount_socialaccount
                ADD CONSTRAINT socialaccount_socialaccount_user_id_cascade_fk
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
                        WHERE conname = 'socialaccount_socialaccount_user_id_cascade_fk'
                    ) THEN
                        ALTER TABLE socialaccount_socialaccount
                        DROP CONSTRAINT socialaccount_socialaccount_user_id_cascade_fk;
                    END IF;
                END $$;

                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'socialaccount_socialaccount'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NULL THEN
                        ALTER TABLE socialaccount_socialaccount
                        ADD CONSTRAINT socialaccount_socialaccount_user_id_fk
                        FOREIGN KEY (user_id)
                        REFERENCES authentication_user(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
        ),
        # socialaccount_socialtoken.account_id -> socialaccount_socialaccount(id)
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'socialaccount_socialtoken'::regclass
                    AND confrelid = 'socialaccount_socialaccount'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE socialaccount_socialtoken DROP CONSTRAINT %I', constraint_name);
                    END IF;
                END $$;

                ALTER TABLE socialaccount_socialtoken
                ADD CONSTRAINT socialaccount_socialtoken_account_id_cascade_fk
                FOREIGN KEY (account_id)
                REFERENCES socialaccount_socialaccount(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'socialaccount_socialtoken_account_id_cascade_fk'
                    ) THEN
                        ALTER TABLE socialaccount_socialtoken
                        DROP CONSTRAINT socialaccount_socialtoken_account_id_cascade_fk;
                    END IF;
                END $$;

                DO $$
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'socialaccount_socialtoken'::regclass
                    AND confrelid = 'socialaccount_socialaccount'::regclass
                    AND contype = 'f'
                    LIMIT 1;

                    IF constraint_name IS NULL THEN
                        ALTER TABLE socialaccount_socialtoken
                        ADD CONSTRAINT socialaccount_socialtoken_account_id_fk
                        FOREIGN KEY (account_id)
                        REFERENCES socialaccount_socialaccount(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
        ),
    ]
