# Generated migration to add ON DELETE CASCADE to account_emailconfirmation foreign key

from django.db import migrations


class Migration(migrations.Migration):
    """
    Add ON DELETE CASCADE to account_emailconfirmation foreign key constraint
    that references account_emailaddress.

    This ensures that when an email address is deleted (cascading from user deletion),
    all related email confirmations are automatically deleted as well.
    """

    dependencies = [
        ("authentication", "0003_add_cascade_to_authtoken_foreign_key"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop existing constraint
                DO $$ 
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'account_emailconfirmation'::regclass
                    AND confrelid = 'account_emailaddress'::regclass
                    AND contype = 'f'
                    LIMIT 1;
                    
                    IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE account_emailconfirmation DROP CONSTRAINT %I', constraint_name);
                    END IF;
                END $$;
                
                -- Recreate with ON DELETE CASCADE
                ALTER TABLE account_emailconfirmation 
                ADD CONSTRAINT account_emailconfirmation_email_address_id_cascade_fk 
                FOREIGN KEY (email_address_id) 
                REFERENCES account_emailaddress(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Drop CASCADE constraint
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'account_emailconfirmation_email_address_id_cascade_fk'
                    ) THEN
                        ALTER TABLE account_emailconfirmation 
                        DROP CONSTRAINT account_emailconfirmation_email_address_id_cascade_fk;
                    END IF;
                END $$;
                
                -- Recreate without CASCADE (original behavior)
                DO $$ 
                DECLARE
                    constraint_name TEXT;
                BEGIN
                    SELECT conname INTO constraint_name
                    FROM pg_constraint
                    WHERE conrelid = 'account_emailconfirmation'::regclass
                    AND confrelid = 'account_emailaddress'::regclass
                    AND contype = 'f'
                    LIMIT 1;
                    
                    IF constraint_name IS NULL THEN
                        ALTER TABLE account_emailconfirmation 
                        ADD CONSTRAINT account_emailconfirmation_email_address_id_fk 
                        FOREIGN KEY (email_address_id) 
                        REFERENCES account_emailaddress(id) 
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
            """,
        ),
    ]
