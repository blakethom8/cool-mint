import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

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
inspector = inspect(engine)

# Check if tables exist
tables = inspector.get_table_names()

print("Checking email-related tables...")
print("-" * 50)

email_tables = ['emails', 'email_attachments', 'email_activities']

for table in email_tables:
    if table in tables:
        print(f"✓ Table '{table}' exists")
        # Get column info
        columns = inspector.get_columns(table)
        print(f"  Columns: {', '.join([col['name'] for col in columns[:5]])}...")
    else:
        print(f"✗ Table '{table}' does NOT exist")

print("\nAll tables in database:")
print("-" * 50)
for table in sorted(tables):
    print(f"  - {table}")

print(f"\nTotal tables: {len(tables)}")