# run_migrations.py
from db import engine
from models import Base
import models  # This ensures all models are imported and registered

def run_migrations():
    """
    Run database migrations to create new tables and columns.
    This will add:
    - role column to users table
    - status and rejection_reason columns to books table
    """
    print("Starting database migrations...")
    
    try:
        # This will create any new tables or columns that don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Migrations completed successfully!")
        print("✅ Added 'role' column to users table")
        print("✅ Added 'status' and 'rejection_reason' columns to books table")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migrations()