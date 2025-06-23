from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.models import Base

from app.config import DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    print("Attempting to create/update database tables... ")
    Base.metadata.create_all(engine)
    print("Database tables created/updated successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
