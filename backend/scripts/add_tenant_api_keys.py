import os
import sys

from sqlalchemy import text

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.database import engine


def migrate():
    with engine.connect() as connection:
        print("Starting migration...")

        # Add openai_api_key
        try:
            connection.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS openai_api_key VARCHAR;"))
            print("Added openai_api_key column.")
        except Exception as e:
            print(f"Error adding openai_api_key: {e}")

        # Add gemini_api_key
        try:
            connection.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS gemini_api_key VARCHAR;"))
            print("Added gemini_api_key column.")
        except Exception as e:
            print(f"Error adding gemini_api_key: {e}")

        # Add can_use_platform_keys
        try:
            connection.execute(
                text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS can_use_platform_keys BOOLEAN DEFAULT FALSE;")
            )
            print("Added can_use_platform_keys column.")
        except Exception as e:
            print(f"Error adding can_use_platform_keys: {e}")

        connection.commit()
        print("Migration completed successfully.")


if __name__ == "__main__":
    migrate()
