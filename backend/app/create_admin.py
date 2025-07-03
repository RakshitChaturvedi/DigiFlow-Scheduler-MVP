from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import User
from backend.app.utils import hash_password
from backend.app.config import DATABASE_URL

# --- configuration ---
ADMIN_USERNAME = "rakshitchaturvedi"
ADMIN_PASSWORD = "supersecretpassword"
ADMIN_EMAIL = "rakshitchaturvedi@example.com"
# ----------------------

def create_admin_user():
    # Connects to the database and creates the initial admin user.
    print("Connecting to the database...")

    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    db = SessionLocal()

    try:
        print(f"Checking if user '{ADMIN_USERNAME}' already exists...")

        # Optionally check if user already exists
        existing_user = db.query(User).filter_by(username=ADMIN_USERNAME).first()
        if existing_user:
            print("Admin user already exists.")
            return

        hashed_password = hash_password(ADMIN_PASSWORD)

        admin_user = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            is_superuser=True,
            role="admin"
        )

        print("Creating new admin user...")
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
