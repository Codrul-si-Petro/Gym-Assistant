# Generated migration to add ON DELETE CASCADE to django-allauth foreign keys

from django.db import migrations


class Migration(migrations.Migration):
    """
    Add ON DELETE CASCADE to django-allauth foreign key constraints
    that reference authentication_user.

    This ensures that when a user is deleted, all related records in
    django-allauth tables (account_emailaddress, socialaccount_socialaccount, etc.)
    are automatically deleted as well.
    """

    dependencies = [
        ("authentication", "0001_initial"),
        ("account", "0001_initial"),  # Ensure account migrations are applied
        ("socialaccount", "0001_initial"),  # Ensure socialaccount migrations are applied
    ]

    operations = [
        # Drop and recreate foreign key constraint for account_emailaddress.user_id
        migrations.RunSQL(
            sql="""
                -- Drop existing constraint (using dynamic lookup for safety)
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
                
                -- Recreate with ON DELETE CASCADE
                ALTER TABLE account_emailaddress 
                ADD CONSTRAINT account_emailaddress_user_id_cascade_fk 
                FOREIGN KEY (user_id) 
                REFERENCES authentication_user(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Drop CASCADE constraint
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
                
                -- Recreate without CASCADE (original behavior)
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
        # Drop and recreate foreign key constraint for socialaccount_socialaccount.user_id
        migrations.RunSQL(
            sql="""
                -- Drop existing constraint
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
                
                -- Recreate with ON DELETE CASCADE
                ALTER TABLE socialaccount_socialaccount 
                ADD CONSTRAINT socialaccount_socialaccount_user_id_cascade_fk 
                FOREIGN KEY (user_id) 
                REFERENCES authentication_user(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Drop CASCADE constraint
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
                
                -- Recreate without CASCADE (original behavior)
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
        # Drop and recreate foreign key constraint for socialaccount_socialtoken.account_id
        # This references socialaccount_socialaccount, which will cascade from user deletion
        migrations.RunSQL(
            sql="""
                -- Drop existing constraint
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
                
                -- Recreate with ON DELETE CASCADE
                ALTER TABLE socialaccount_socialtoken 
                ADD CONSTRAINT socialaccount_socialtoken_account_id_cascade_fk 
                FOREIGN KEY (account_id) 
                REFERENCES socialaccount_socialaccount(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Drop CASCADE constraint
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
                
                -- Recreate without CASCADE (original behavior)
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
