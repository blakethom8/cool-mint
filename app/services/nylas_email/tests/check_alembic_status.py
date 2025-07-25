import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Create database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Construct from individual components
    host = os.environ.get("DATABASE_HOST", "localhost")
    port = os.environ.get("DATABASE_PORT", "5432")
    db = os.environ.get("DATABASE_NAME", "postgres")
    user = os.environ.get("DATABASE_USER", "postgres")
    password = os.environ.get("DATABASE_PASSWORD")
    
    if password:
        DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    else:
        print("ERROR: Could not construct DATABASE_URL")
        sys.exit(1)

engine = create_engine(DATABASE_URL)

print("Checking Alembic migration status...")
print("-" * 50)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    versions = result.fetchall()
    
    if versions:
        print("Current migration versions in database:")
        for version in versions:
            print(f"  - {version[0]}")
    else:
        print("No migration versions found in database")
        
print("\nLet's clear the alembic_version table and re-stamp it correctly...")

# Clear the table
with engine.connect() as conn:
    conn.execute(text("DELETE FROM alembic_version"))
    conn.commit()
    print("✓ Cleared alembic_version table")
    
    # Stamp with the correct head
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('ea810a3d13c0')"))
    conn.commit()
    print("✓ Stamped database with migration ea810a3d13c0")