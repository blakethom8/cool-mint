#!/usr/bin/env python
"""
Simple test to verify the application runs without import errors.
Run this to quickly check if the recent fixes work.
"""

def test_imports():
    """Test that all critical imports work."""
    try:
        # Test database models can be imported
        from app.database.data_models.salesforce_data import SfUser
        from app.database.data_models.relationship_management import Relationships, Campaigns
        from app.database.data_models.crm_lookups import EntityTypes, RelationshipStatusTypes
        print("✓ Database models imported successfully")
        
        # Test SQLAlchemy mapper configuration
        from sqlalchemy.orm import configure_mappers
        configure_mappers()
        print("✓ SQLAlchemy mappers configured successfully")
        
        # Test API can be imported
        from app.main import app
        print("✓ FastAPI app imported successfully")
        
        print("\n🎉 All imports successful! The relationship configuration issues are fixed.")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = test_imports()
    sys.exit(0 if success else 1)