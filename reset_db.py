#!/usr/bin/env python3
"""
Script to reset the database by dropping and recreating all tables.
WARNING: This will delete all existing data!
"""

import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel

# Load environment variables
load_dotenv()

def reset_database():
    """Drop all tables and recreate them with the new schema"""
    
    # Import models to ensure they're registered with SQLModel
    from models import User, Book
    
    # Get database URL
    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not database_url:
        raise ValueError("SQLALCHEMY_DATABASE_URL not found in environment variables")
    
    # Create engine
    engine = create_engine(database_url, pool_pre_ping=True)
    
    print("🚨 WARNING: This will DELETE ALL DATA in the database!")
    print("📋 Current tables will be dropped and recreated with new schema.")
    
    # Ask for confirmation
    confirm = input("Are you sure you want to continue? Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("❌ Operation cancelled.")
        return
    
    try:
        print("🗑️  Dropping all existing tables...")
        # Drop all tables
        SQLModel.metadata.drop_all(engine)
        
        print("🏗️  Creating new tables with updated schema...")
        # Create all tables with new schema
        SQLModel.metadata.create_all(engine)
        
        print("✅ Database reset completed successfully!")
        print("📝 New tables created with the following models:")
        print("   - User")
        print("   - Book (with new fields: subtitle, co_author, synopsis, copyright_info, category, subcategory)")
        
    except Exception as e:
        print(f"❌ Error during database reset: {e}")
        raise

if __name__ == "__main__":
    reset_database()
