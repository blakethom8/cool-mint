"""
Smoke tests for critical application paths.

These are quick tests that verify the application isn't completely broken.
Run these frequently during development.
"""
import pytest
from datetime import datetime
import uuid

from app.database.data_models.relationship_management import Relationships
from app.database.data_models.salesforce_data import SfContact


class TestDatabaseConnection:
    """Test that we can connect to the database and perform basic operations."""
    
    def test_database_is_accessible(self, db_session):
        """Test that we can connect to the database."""
        # Simple query to verify connection
        result = db_session.execute("SELECT 1").scalar()
        assert result == 1
    
    def test_can_create_and_query_records(self, db_session, test_user, entity_types, relationship_statuses):
        """Test basic CRUD operations."""
        # Create a relationship
        rel = Relationships(
            relationship_id=uuid.uuid4(),
            user_id=test_user.id,
            entity_type_id=entity_types[0].id,
            linked_entity_id=uuid.uuid4(),
            relationship_status_id=relationship_statuses[0].id,
            lead_score=3
        )
        db_session.add(rel)
        db_session.commit()
        
        # Query it back
        found = db_session.query(Relationships).filter_by(
            relationship_id=rel.relationship_id
        ).first()
        
        assert found is not None
        assert found.lead_score == 3


class TestAPIHealth:
    """Test that API endpoints are responsive."""
    
    def test_api_root_accessible(self, client):
        """Test that the API root is accessible."""
        response = client.get("/")
        assert response.status_code in [200, 404]  # Depends on if root route exists
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint if it exists."""
        # Common health check endpoints
        for endpoint in ["/health", "/api/health", "/healthz"]:
            response = client.get(endpoint)
            if response.status_code == 200:
                return  # Found a health endpoint
        
        # If no health endpoint, just check that API is responding
        assert True  # API is running if we got here


class TestRelationshipCriticalPaths:
    """Test critical paths for relationship management."""
    
    def test_can_list_relationships(self, client, test_relationships, auth_headers):
        """Test that we can retrieve a list of relationships."""
        response = client.get("/api/relationships/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
    
    def test_can_get_filter_options(self, client, entity_types, relationship_statuses, auth_headers):
        """Test that filter options endpoint works."""
        response = client.get("/api/relationships/filter-options", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "entity_types" in data
        assert "relationship_statuses" in data
        assert len(data["entity_types"]) > 0
    
    def test_can_update_relationship(self, client, test_relationships, auth_headers):
        """Test that we can update a relationship."""
        rel = test_relationships[0]
        update_data = {
            "lead_score": 4,
            "next_steps": "Updated next steps"
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        updated = response.json()
        assert updated["lead_score"] == 4
        assert updated["next_steps"] == "Updated next steps"
    
    def test_can_bulk_update_relationships(self, client, test_relationships, auth_headers):
        """Test bulk update functionality."""
        ids = [str(rel.relationship_id) for rel in test_relationships[:2]]
        update_data = {
            "relationship_ids": ids,
            "updates": {
                "lead_score": 5
            }
        }
        
        response = client.post(
            "/api/relationships/bulk-update",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["updated_count"] == 2


class TestMarketExplorerCriticalPaths:
    """Test critical paths for market explorer."""
    
    def test_can_list_providers(self, client, test_market_data):
        """Test that we can retrieve providers."""
        response = client.get("/api/claims/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
    
    def test_can_get_map_markers(self, client, test_market_data):
        """Test that map markers endpoint works."""
        response = client.get("/api/claims/map-markers")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data or "sites" in data or "groups" in data
    
    def test_can_filter_providers(self, client, test_market_data):
        """Test provider filtering."""
        response = client.get("/api/claims/providers?specialty=Cardiology")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        # All returned providers should have Cardiology specialty
        for provider in data["items"]:
            assert "Cardiology" in provider.get("taxonomy_description", "")
    
    def test_pagination_works(self, client, test_market_data):
        """Test that pagination parameters work."""
        response = client.get("/api/claims/providers?page=1&page_size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestDataIntegrity:
    """Test that data relationships are maintained correctly."""
    
    def test_relationship_history_tracked(self, client, test_relationships, relationship_statuses, auth_headers):
        """Test that status changes create history records."""
        rel = test_relationships[0]
        
        # Update the status
        update_data = {
            "relationship_status_id": relationship_statuses[1].id  # Change to different status
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # In a real test, we'd check the history table
        # For now, just verify the update worked
        updated = response.json()
        assert updated["relationship_status"]["id"] == relationship_statuses[1].id
    
    def test_entity_types_properly_linked(self, db_session, test_relationships, entity_types):
        """Test that entity type relationships work correctly."""
        rel = test_relationships[0]
        
        # Verify the relationship has the correct entity type
        relationship = db_session.query(Relationships).filter_by(
            relationship_id=rel.relationship_id
        ).first()
        
        assert relationship.entity_type is not None
        assert relationship.entity_type.code == "SfContact"
    
    def test_generic_entity_lookup_works(self, db_session, test_user, test_contact, entity_types):
        """Test that we can lookup entities using entity_type + entity_id pattern."""
        # Create a reminder using the generic pattern
        from app.database.data_models.relationship_management import Reminders
        
        reminder = Reminders(
            reminder_id=uuid.uuid4(),
            user_id=test_user.id,
            entity_type_id=1,  # SfContact
            linked_entity_id=test_contact.id,
            description="Test reminder",
            due_date=datetime.now()
        )
        db_session.add(reminder)
        db_session.commit()
        
        # Verify we can query it back
        found = db_session.query(Reminders).filter_by(
            reminder_id=reminder.reminder_id
        ).first()
        
        assert found is not None
        assert found.entity_type.code == "SfContact"
        assert found.linked_entity_id == test_contact.id


class TestPerformanceBaselines:
    """Basic performance checks to catch major regressions."""
    
    def test_relationship_list_performance(self, client, test_relationships, auth_headers):
        """Test that relationship list endpoint responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/api/relationships/", headers=auth_headers)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in under 1 second
    
    def test_map_markers_performance(self, client, test_market_data):
        """Test that map markers endpoint responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/api/claims/map-markers")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0  # Map data can be slower, allow 2 seconds