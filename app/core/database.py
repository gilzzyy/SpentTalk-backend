import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

class DatabaseManager:
    """
    DatabaseManager encapsulates database connection setup and session creation.
    Provides session management for repository operations.
    Supports secure SSL connection when using Aiven MySQL.
    """
    def __init__(self, db_url: str):
        ca_path = os.path.join(os.path.dirname(__file__), "ca.pem")
        connect_args = {}
        
        # Configure SSL context for Aiven cloud connection
        if os.path.exists(ca_path) and "aivencloud.com" in db_url:
            connect_args = {
                "ssl": {
                    "ca": ca_path
                }
            }
        
        self.engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_db(self):
        """
        Dependency generator to obtain database session.
        Closes session after usage.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db_manager = DatabaseManager(settings.database_url)
get_db = db_manager.get_db
