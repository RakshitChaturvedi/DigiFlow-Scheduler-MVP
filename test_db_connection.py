from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


DATABASE_URL = "postgresql://digiflow_user:Password2005@localhost:5432/digiflow_db"


try:
    engine = create_engine(DATABASE_URL, echo=True)

    connection = engine.connect()
    print("Successfully connected to PostgreSQL database!")

    connection.close()

except OperationalError as e:
    print(f"ERROR: Could not connect to the database. Details: {e}")
    print("\nPlease check the following: ")
    print("  - Is the PostgreSQL server running?:")
    print("  - Is the 'DATABASE_URL' string correct (username, password, host, port, database name)?")
    print("  - Did you use the correct password for 'digiflow_user'?")
    print("  - Is the database 'digiflow_db' created?")
except Exception as e:
    print(f"An unexpected error occured: {e}")