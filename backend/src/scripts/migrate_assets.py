import os
import sys

from sqlalchemy import text

# Adjust PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(backend_dir)

from src.core.database import engine  # noqa: E402


def migrate():
    print("Starting Assets Module Migration...")
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # 1. Rename Table
            print("Renaming table 'offer_gallery_images' to 'assets'...")
            try:
                connection.execute(
                    text("ALTER TABLE offer_gallery_images RENAME TO assets;")
                )
                print("✅ Table renamed.")
            except Exception as e:
                if "does not exist" in str(e):
                    print(
                        "⚠️ Table 'offer_gallery_images' not found. Checking if 'assets' exists..."
                    )
                elif "already exists" in str(e):
                    print("ℹ️ Table 'assets' already exists.")
                else:
                    print(f"⚠️ Error renaming table: {e}")

            # 2. Alter offer_id to NULLABLE
            print("Altering 'offer_id' to be NULLABLE...")
            connection.execute(
                text("ALTER TABLE assets ALTER COLUMN offer_id DROP NOT NULL;")
            )
            print("✅ offer_id is now nullable.")

            # 3. Add New Columns
            print("Adding new columns...")
            columns = [
                ("type", "VARCHAR", "'IMAGE'"),
                ("storage_provider", "VARCHAR", "'LOCAL'"),
                ("storage_path", "VARCHAR", "NULL"),
                ("mime_type", "VARCHAR", "NULL"),
                ("ai_metadata", "JSONB", "'{}'"),
            ]

            for col_name, col_type, default in columns:
                try:
                    connection.execute(
                        text(
                            f"ALTER TABLE assets ADD COLUMN {col_name} {col_type} DEFAULT {default};"
                        )
                    )
                    print(f"✅ Column '{col_name}' added.")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"ℹ️ Column '{col_name}' already exists.")
                    else:
                        print(f"❌ Error adding column '{col_name}': {e}")
                        raise e

            # 4. Data Migration (Backfill)
            print("Backfilling data...")
            # Copy file_path to storage_path if empty
            connection.execute(
                text(
                    "UPDATE assets SET storage_path = file_path WHERE storage_path IS NULL;"
                )
            )
            # Set mime_type default for existing images (assuming they are images)
            connection.execute(
                text(
                    "UPDATE assets SET mime_type = 'image/jpeg' WHERE mime_type IS NULL;"
                )
            )  # Approximation
            print("✅ Data backfilled.")

            trans.commit()
            print("🎉 Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    migrate()
