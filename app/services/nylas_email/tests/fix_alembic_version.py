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

print("Fixing Alembic migration state...")
print("-" * 50)

with engine.connect() as conn:
    # Clear the table
    conn.execute(text("DELETE FROM alembic_version"))
    conn.commit()
    print("✓ Cleared alembic_version table")
    
    # Stamp with the correct head (before our email migration)
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('c8f5d4a3b21e')"))
    conn.commit()
    print("✓ Stamped database with migration c8f5d4a3b21e")
    
print("\nNow you can generate a new migration for email tables")