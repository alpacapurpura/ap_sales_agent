
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Use database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/visionarias_logs")

def check_data():
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("\n--- Checking Users ---")
        users = session.execute(text("SELECT id, email, clerk_id FROM users")).fetchall()
        if not users:
            print("No users found in database.")
        else:
            for u in users:
                print(f"User: {u.email} (ID: {u.id}, Clerk: {u.clerk_id})")

        print("\n--- Checking Tenants ---")
        tenants = session.execute(text("SELECT id, name, is_active FROM tenants")).fetchall()
        if not tenants:
            print("No tenants found in database.")
        else:
            for t in tenants:
                print(f"Tenant: {t.name} (ID: {t.id}, Active: {t.is_active})")

        print("\n--- Checking User-Tenant Links ---")
        links = session.execute(text("SELECT user_id, tenant_id, role FROM user_tenants")).fetchall()
        if not links:
            print("No user-tenant links found.")
        else:
            for l in links:
                print(f"Link: User {l.user_id} -> Tenant {l.tenant_id} (Role: {l.role})")
                
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure the database container is running and exposed.")

if __name__ == "__main__":
    check_data()
