import os
import sys

from sqlalchemy import text

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.database import engine


def migrate():
    try:
        with engine.begin() as connection:
            print("Starting webhook migration...")

            # Add webhook_secret
            try:
                connection.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS webhook_secret VARCHAR;"))
                print("Added webhook_secret column.")
            except Exception as e:
                print(f"Error adding webhook_secret: {e}")

            print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate()
