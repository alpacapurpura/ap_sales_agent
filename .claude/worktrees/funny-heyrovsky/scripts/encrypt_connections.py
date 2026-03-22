import sys
import os
from sqlalchemy import create_engine, select, Column
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from src.core.config import settings
from src.shared.infrastructure.database.types import EncryptedJSON

# Define a local Base to avoid importing complex models with circular dependencies
Base = declarative_base()

class ChannelConnectionModel(Base):
    __tablename__ = "channel_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Define tenant_id as simple column to avoid FK resolution issues in migration script
    tenant_id = Column(UUID(as_uuid=True)) 
    
    # This is the column we want to migrate
    credentials = Column(EncryptedJSON, default={})
    
    # We can ignore other columns for this operation

def migrate_credentials():
    """
    Migrates all plaintext credentials in ChannelConnectionModel to encrypted format.
    """
    print("Starting credentials migration...")
    
    # Ensure we connect to the right host (localhost if running from host machine)
    db_url = settings.DATABASE_URL
    if os.environ.get("POSTGRES_HOST"):
        # Replace host in URL if env var is set (rudimentary replacement)
        # settings.DATABASE_URL is a property, so we construct it manually or replace string
        # Assuming format postgresql://user:pass@host:port/db
        pass

    print(f"Connecting to DB...")
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all connections
        stmt = select(ChannelConnectionModel)
        connections = db.execute(stmt).scalars().all()
        
        count = 0
        migrated = 0
        
        for conn in connections:
            count += 1
            # Accessing conn.credentials triggers the TypeDecorator.process_result_value
            # If it was plaintext, it returns the dict.
            # If it was encrypted, it decrypts and returns the dict.
            
            creds = conn.credentials
            
            # To force re-encryption (or initial encryption), we need to mark it as modified.
            # The EncryptedJSON type handles the logic:
            # - On save (process_bind_param), it encrypts.
            
            # If we just re-assign, SQLAlchemy detects change?
            # Since creds is a dict (mutable), simply accessing it might not trigger update if identity is same.
            # We explicitly flag it as modified.
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(conn, "credentials")
            migrated += 1
            
        db.commit()
        print(f"Processed {count} connections. Migrated/Verified {migrated}.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_credentials()
