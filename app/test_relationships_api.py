#!/usr/bin/env python3
"""
Test script to debug relationships API issues
"""

import sys
sys.path.append('/Users/blakethomson/Documents/Repo/cool-mint/app')

try:
    print("Testing imports...")
    
    # Test schema imports
    from schemas.relationship_schema import (
        RelationshipListResponse,
        RelationshipDetail,
        RelationshipFilters,
        FilterOptionsResponse
    )
    print("✓ Schema imports successful")
    
    # Test service import
    from services.relationship_service import RelationshipService
    print("✓ Service import successful")
    
    # Test model imports
    from database.data_models.relationship_management import Relationships
    from database.data_models.crm_lookups import RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes
    print("✓ Model imports successful")
    
    # Test database session
    from database.session import db_session
    print("✓ Database session import successful")
    
    # Test API endpoint import
    from api.relationships import router
    print("✓ API router import successful")
    
    # Test a simple query
    print("\nTesting database connection...")
    with next(db_session()) as session:
        # Count relationships
        count = session.query(Relationships).count()
        print(f"✓ Found {count} relationships in database")
        
        # Get filter options
        service = RelationshipService(session)
        options = service.get_filter_options()
        print(f"✓ Filter options retrieved: {len(options['users'])} users, {len(options['entity_types'])} entity types")
        
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()