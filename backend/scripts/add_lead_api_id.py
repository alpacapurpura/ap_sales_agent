import os
import sys

from sqlalchemy import text

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.database import engine


def migrate():
    try:
        with engine.begin() as connection:
            print("Starting lead migration...")

            # Add api_id for generic webhook integration
            try:
                connection.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS api_id VARCHAR;"))
                # Add index for performance
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_leads_api_id ON leads (api_id);"))
                print("Added api_id column and index.")
            except Exception as e:
                print(f"Error adding api_id: {e}")

            print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate()
