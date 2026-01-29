# Generated migration to add ON DELETE CASCADE to authtoken foreign key

from django.db import migrations


class Migration(migrations.Migration):
    """
    Add ON DELETE CASCADE to authtoken_token foreign key constraint
    that references authentication_user.

    This ensures that when a user is deleted, their auth tokens
    are automatically deleted as well.
    """

    dependencies = [
        ("authentication", "0002_add_cascade_to_allauth_foreign_keys"),
    ]

    operations = [
        # Drop and recreate foreign key constraint for authtoken_token.user_id
        migrations.RunSQL(
            sql="""
                -- Drop existing constraint (using dynamic lookup for safety)
                DO $$ 
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'authtoken_token'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;
                    
                    IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE authtoken_token DROP CONSTRAINT %I', constraint_name);
                    END IF;
                END $$;
                
                -- Recreate with ON DELETE CASCADE
                ALTER TABLE authtoken_token 
                ADD CONSTRAINT authtoken_token_user_id_cascade_fk 
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
                        WHERE conname = 'authtoken_token_user_id_cascade_fk'
                    ) THEN
                        ALTER TABLE authtoken_token 
                        DROP CONSTRAINT authtoken_token_user_id_cascade_fk;
                    END IF;
                END $$;
                
                -- Recreate without CASCADE (original behavior)
                DO $$ 
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'authtoken_token'::regclass
                    AND confrelid = 'authentication_user'::regclass
                    AND contype = 'f'
                    LIMIT 1;
                    
                    IF constraint_name IS NULL THEN
                        ALTER TABLE authtoken_token 
                        ADD CONSTRAINT authtoken_token_user_id_fk 
                        FOREIGN KEY (user_id) 
                        REFERENCES authentication_user(id) 
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
        ),
    ]
