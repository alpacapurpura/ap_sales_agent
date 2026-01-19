from sqlalchemy.orm import Session
from src.services.database import SessionLocal

class BaseRepository:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def close(self):
        self.db.close()
