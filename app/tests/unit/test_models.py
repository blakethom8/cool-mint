"""
Test SQLAlchemy model relationships and configurations.

These tests would have caught the relationship configuration issues we just fixed!
Focus on preventing runtime errors rather than comprehensive validation.
"""
import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers
from sqlalchemy.exc import InvalidRequestError

from database.session import Base
from database.data_models.salesforce_data import SfUser, SfContact, SfActivity
from database.data_models.relationship_management import (
    Relationships, Campaigns, CampaignRelationships,
    RelationshipHistory, RelationshipMetrics, Reminders,
    ContentLibrary, NextBestActions, LLMProcessingQueue,
    SalesforceSync, CampaignTargetSpecialties, CampaignContent
)
from database.data_models.crm_lookups import (
    RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes
)


class TestModelRelationships:
    """Test that all SQLAlchemy relationships are properly configured."""
    
    def test_all_mappers_can_initialize(self):
        """
        Test that SQLAlchemy can initialize all mappers without errors.
        This is the most important test - it catches configuration issues.
        """
        try:
            # This will raise an error if any relationships are misconfigured
            configure_mappers()
        except InvalidRequestError as e:
            pytest.fail(f"Failed to configure mappers: {str(e)}")
    
    def test_all_models_can_be_instantiated(self):
        """Test that all models can be created without errors."""
        # Just instantiate each model to ensure no __init__ issues
        models = [
            SfUser(salesforce_id="test", username="test", email="test@test.com", 
                   last_name="Test", name="Test"),
            EntityTypes(code="TEST", common_name="Test"),
            RelationshipStatusTypes(code="TEST", display_name="Test"),
            LoyaltyStatusTypes(code="TEST", display_name="Test"),
            Campaigns(campaign_name="Test", owner_user_id=1),
            Relationships(user_id=1, entity_type_id=1, linked_entity_id="test",
                         relationship_status_id=1),
            Reminders(user_id=1, entity_type_id=1, linked_entity_id="test",
                     description="Test", due_date="2024-01-01"),
            LLMProcessingQueue(entity_type_id=1, entity_id="test", 
                              processing_type="test")
        ]
        
        # If we get here without exceptions, models are properly defined
        assert len(models) > 0
    
    def test_relationship_back_populates_are_symmetric(self):
        """
        Test that all relationships have matching back_populates.
        This catches the exact issue we just fixed.
        """
        models_to_check = [
            (Campaigns, "owner", SfUser, "owned_campaigns"),
            (Relationships, "user", SfUser, "managed_relationships"),
            (Relationships, "entity_type", EntityTypes, "relationships"),
            (Relationships, "relationship_status_type", RelationshipStatusTypes, "relationships"),
            (Relationships, "loyalty_status_type", LoyaltyStatusTypes, "relationships"),
            (CampaignRelationships, "campaign", Campaigns, "campaign_relationships"),
            (CampaignRelationships, "relationship", Relationships, "campaign_relationships"),
            (RelationshipHistory, "related_relationship", Relationships, "history"),
            (RelationshipMetrics, "related_relationship", Relationships, "metrics"),
            (NextBestActions, "related_relationship", Relationships, "next_best_actions"),
            (ContentLibrary, "uploaded_by", SfUser, "uploaded_content"),
            (Reminders, "user", SfUser, "reminders"),
        ]
        
        for model_a, rel_name_a, model_b, rel_name_b in models_to_check:
            # Check that model_a has the relationship
            mapper_a = inspect(model_a)
            assert rel_name_a in mapper_a.relationships, \
                f"{model_a.__name__} missing relationship '{rel_name_a}'"
            
            # Check that model_b has the corresponding relationship
            mapper_b = inspect(model_b)
            assert rel_name_b in mapper_b.relationships, \
                f"{model_b.__name__} missing relationship '{rel_name_b}'"
            
            # Check that they reference each other
            rel_a = mapper_a.relationships[rel_name_a]
            rel_b = mapper_b.relationships[rel_name_b]
            
            # Verify back_populates is set correctly
            assert rel_a.back_populates == rel_name_b, \
                f"{model_a.__name__}.{rel_name_a} back_populates mismatch"
            assert rel_b.back_populates == rel_name_a, \
                f"{model_b.__name__}.{rel_name_b} back_populates mismatch"
    
    def test_foreign_keys_have_relationships(self):
        """Test that foreign key columns have corresponding relationships."""
        # Check key models that should have relationships for their FKs
        checks = [
            (Campaigns, "owner_user_id", "owner"),
            (Relationships, "user_id", "user"),
            (Relationships, "entity_type_id", "entity_type"),
            (Relationships, "relationship_status_id", "relationship_status_type"),
            (Relationships, "loyalty_status_id", "loyalty_status_type"),
            (Reminders, "user_id", "user"),
            (Reminders, "entity_type_id", "entity_type"),
        ]
        
        for model, fk_column, expected_relationship in checks:
            mapper = inspect(model)
            
            # Check that the FK column exists
            assert fk_column in [c.name for c in mapper.columns], \
                f"{model.__name__} missing column '{fk_column}'"
            
            # Check that there's a corresponding relationship
            assert expected_relationship in mapper.relationships, \
                f"{model.__name__} missing relationship '{expected_relationship}' for FK '{fk_column}'"
    
    def test_generic_entity_relationships_work(self):
        """
        Test that our generic entity pattern (entity_type_id + entity_id) works.
        This is used in Reminders and LLMProcessingQueue.
        """
        # These models use the generic pattern
        generic_models = [
            (Reminders, "entity_type_id", "linked_entity_id"),
            (LLMProcessingQueue, "entity_type_id", "entity_id")
        ]
        
        for model, type_column, id_column in generic_models:
            mapper = inspect(model)
            columns = [c.name for c in mapper.columns]
            
            # Ensure both columns exist
            assert type_column in columns, \
                f"{model.__name__} missing '{type_column}' column"
            assert id_column in columns, \
                f"{model.__name__} missing '{id_column}' column"
            
            # Ensure entity_type relationship exists
            assert "entity_type" in mapper.relationships, \
                f"{model.__name__} missing 'entity_type' relationship"
    
    def test_no_circular_imports(self):
        """
        Test that we can import all models without circular import errors.
        This is a simple smoke test.
        """
        # If we got this far in the test file, imports worked
        # But let's be explicit
        from database.data_models import (
            salesforce_data, relationship_management, 
            crm_lookups, provider_crm, sites
        )
        
        # Just check that modules loaded
        assert salesforce_data is not None
        assert relationship_management is not None
        assert crm_lookups is not None
    
    def test_required_columns_are_not_nullable(self):
        """Test that critical columns are marked as required (nullable=False)."""
        critical_columns = [
            (Campaigns, ["campaign_name", "owner_user_id", "start_date"]),
            (Relationships, ["user_id", "entity_type_id", "linked_entity_id", 
                           "relationship_status_id"]),
            (EntityTypes, ["code", "common_name"]),
            (Reminders, ["user_id", "entity_type_id", "linked_entity_id", 
                        "description", "due_date"]),
        ]
        
        for model, required_cols in critical_columns:
            mapper = inspect(model)
            for col_name in required_cols:
                col = mapper.columns.get(col_name)
                assert col is not None, f"{model.__name__} missing column '{col_name}'"
                assert not col.nullable, \
                    f"{model.__name__}.{col_name} should not be nullable"


class TestModelIndexes:
    """Test that important indexes are defined for performance."""
    
    def test_relationship_indexes(self):
        """Test that the Relationships table has proper indexes."""
        mapper = inspect(Relationships)
        table = mapper.persist_selectable
        
        # Get all index names
        index_names = [idx.name for idx in table.indexes]
        
        # Check for critical indexes
        expected_indexes = [
            "idx_relationships_user_entity",
            "idx_relationships_status_loyalty",
            "idx_relationships_lead_score"
        ]
        
        for expected in expected_indexes:
            assert expected in index_names, \
                f"Relationships table missing index '{expected}'"
    
    def test_lookup_table_indexes(self):
        """Test that lookup tables have proper indexes."""
        lookup_models = [
            (EntityTypes, "idx_entity_types_active"),
            (RelationshipStatusTypes, "idx_relationship_status_types_active"),
            (LoyaltyStatusTypes, "idx_loyalty_status_types_active")
        ]
        
        for model, expected_index in lookup_models:
            mapper = inspect(model)
            table = mapper.persist_selectable
            index_names = [idx.name for idx in table.indexes]
            
            assert expected_index in index_names, \
                f"{model.__name__} missing index '{expected_index}'"


class TestModelConstraints:
    """Test that important constraints are defined."""
    
    def test_unique_constraints(self):
        """Test that unique constraints are properly defined."""
        unique_checks = [
            (EntityTypes, "code"),
            (RelationshipStatusTypes, "code"),
            (LoyaltyStatusTypes, "code"),
            (SfUser, "salesforce_id"),
            (SfContact, "salesforce_id"),
        ]
        
        for model, column_name in unique_checks:
            mapper = inspect(model)
            col = mapper.columns.get(column_name)
            assert col is not None, f"{model.__name__} missing column '{column_name}'"
            assert col.unique, f"{model.__name__}.{column_name} should be unique"
    
    def test_check_constraints(self):
        """Test that check constraints are defined where expected."""
        # Note: SQLite doesn't enforce check constraints by default,
        # but we can still verify they're defined
        
        mapper = inspect(Relationships)
        table = mapper.persist_selectable
        
        # Look for the lead_score constraint
        constraint_names = [c.name for c in table.constraints if hasattr(c, 'name')]
        assert "check_lead_score" in constraint_names, \
            "Relationships table missing lead_score check constraint"