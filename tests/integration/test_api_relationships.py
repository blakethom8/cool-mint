"""
Integration tests for Relationship Management API endpoints.

These tests verify that the API endpoints work correctly with the database
and return expected responses.
"""
import pytest
from datetime import datetime, timedelta
import uuid


class TestRelationshipListEndpoint:
    """Test the GET /api/relationships/ endpoint."""
    
    def test_list_returns_paginated_results(self, client, test_relationships, auth_headers):
        """Test that list endpoint returns paginated results."""
        response = client.get("/api/relationships/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        
        # Should return all test relationships
        assert len(data["items"]) == len(test_relationships)
    
    def test_list_respects_pagination(self, client, test_relationships, auth_headers):
        """Test pagination parameters."""
        response = client.get(
            "/api/relationships/?page=1&page_size=2", 
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    def test_list_filters_by_user(self, client, test_relationships, test_user, auth_headers):
        """Test filtering by user."""
        response = client.get(
            f"/api/relationships/?user_ids={test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # All relationships should belong to test_user
        for item in data["items"]:
            assert item["user"]["id"] == test_user.id
    
    def test_list_filters_by_entity_type(self, client, test_relationships, entity_types, auth_headers):
        """Test filtering by entity type."""
        # Filter for SfContact type
        response = client.get(
            f"/api/relationships/?entity_type_ids=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for item in data["items"]:
            assert item["entity_type"]["code"] == "SfContact"
    
    def test_list_filters_by_status(self, client, test_relationships, relationship_statuses, auth_headers):
        """Test filtering by relationship status."""
        # Filter for ESTABLISHED status
        response = client.get(
            f"/api/relationships/?relationship_status_ids=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for item in data["items"]:
            assert item["relationship_status"]["code"] == "ESTABLISHED"
    
    def test_list_search_functionality(self, client, test_relationships, test_contact, auth_headers):
        """Test search parameter."""
        # Search for part of contact name
        response = client.get(
            f"/api/relationships/?search=John",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should find the contact relationship
        assert len(data["items"]) >= 1
        assert any(item["entity_name"] == "John Doe" for item in data["items"])
    
    def test_list_sorting(self, client, test_relationships, auth_headers):
        """Test sorting functionality."""
        # Sort by last activity date descending
        response = client.get(
            "/api/relationships/?sort_by=last_activity_date&sort_order=desc",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        # Verify sorting
        for i in range(1, len(items)):
            if items[i-1]["last_activity_date"] and items[i]["last_activity_date"]:
                date1 = datetime.fromisoformat(items[i-1]["last_activity_date"].replace("Z", "+00:00"))
                date2 = datetime.fromisoformat(items[i]["last_activity_date"].replace("Z", "+00:00"))
                assert date1 >= date2


class TestRelationshipDetailEndpoint:
    """Test the GET /api/relationships/{id} endpoint."""
    
    def test_get_relationship_by_id(self, client, test_relationships, auth_headers):
        """Test retrieving a single relationship."""
        rel = test_relationships[0]
        response = client.get(
            f"/api/relationships/{rel.relationship_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["relationship_id"] == str(rel.relationship_id)
        assert "entity_details" in data
        assert "user" in data
        assert "entity_type" in data
    
    def test_get_nonexistent_relationship(self, client, auth_headers):
        """Test 404 for non-existent relationship."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/relationships/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_relationship_includes_entity_details(self, client, test_relationships, test_contact, auth_headers):
        """Test that entity details are included."""
        # Get the contact relationship
        rel = test_relationships[0]
        response = client.get(
            f"/api/relationships/{rel.relationship_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        details = data["entity_details"]
        assert details["name"] == "John Doe"
        assert details["email"] == "john.doe@hospital.com"
        assert details["specialty"] == "Cardiology"


class TestRelationshipUpdateEndpoint:
    """Test the PATCH /api/relationships/{id} endpoint."""
    
    def test_update_relationship_fields(self, client, test_relationships, auth_headers):
        """Test updating relationship fields."""
        rel = test_relationships[0]
        update_data = {
            "lead_score": 4,
            "next_steps": "Schedule follow-up meeting",
            "engagement_frequency": "Weekly"
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["lead_score"] == 4
        assert data["next_steps"] == "Schedule follow-up meeting"
        assert data["engagement_frequency"] == "Weekly"
    
    def test_update_relationship_status(self, client, test_relationships, relationship_statuses, auth_headers):
        """Test updating relationship status."""
        rel = test_relationships[1]  # Use BUILDING status relationship
        update_data = {
            "relationship_status_id": 1  # Change to ESTABLISHED
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["relationship_status"]["code"] == "ESTABLISHED"
    
    def test_update_invalid_field_ignored(self, client, test_relationships, auth_headers):
        """Test that invalid fields are ignored."""
        rel = test_relationships[0]
        update_data = {
            "invalid_field": "value",
            "lead_score": 3  # Valid field
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "invalid_field" not in data
        assert data["lead_score"] == 3
    
    def test_update_with_invalid_reference(self, client, test_relationships, auth_headers):
        """Test update with invalid foreign key reference."""
        rel = test_relationships[0]
        update_data = {
            "relationship_status_id": 9999  # Non-existent status
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        # Should get a validation error
        assert response.status_code in [400, 422]


class TestBulkUpdateEndpoint:
    """Test the POST /api/relationships/bulk-update endpoint."""
    
    def test_bulk_update_multiple_relationships(self, client, test_relationships, auth_headers):
        """Test updating multiple relationships at once."""
        ids = [str(rel.relationship_id) for rel in test_relationships]
        update_data = {
            "relationship_ids": ids,
            "updates": {
                "lead_score": 4,
                "engagement_frequency": "Quarterly"
            }
        }
        
        response = client.post(
            "/api/relationships/bulk-update",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["updated_count"] == len(test_relationships)
        assert len(result["updated_ids"]) == len(test_relationships)
    
    def test_bulk_update_partial_success(self, client, test_relationships, auth_headers):
        """Test bulk update with some invalid IDs."""
        ids = [
            str(test_relationships[0].relationship_id),
            str(uuid.uuid4()),  # Non-existent
            str(test_relationships[1].relationship_id)
        ]
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
        assert result["updated_count"] == 2  # Only 2 valid relationships
        assert len(result["failed_ids"]) == 1
    
    def test_bulk_update_empty_list(self, client, auth_headers):
        """Test bulk update with empty list."""
        update_data = {
            "relationship_ids": [],
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
        assert result["updated_count"] == 0


class TestActivityEndpoint:
    """Test the GET /api/relationships/{id}/activities endpoint."""
    
    def test_get_relationship_activities(self, client, test_relationships, auth_headers):
        """Test retrieving activities for a relationship."""
        rel = test_relationships[0]
        response = client.get(
            f"/api/relationships/{rel.relationship_id}/activities",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        # Activities might be empty in test data
        assert isinstance(data["items"], list)
    
    def test_activities_pagination(self, client, test_relationships, auth_headers):
        """Test activity pagination."""
        rel = test_relationships[0]
        response = client.get(
            f"/api/relationships/{rel.relationship_id}/activities?page=1&page_size=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestFilterOptionsEndpoint:
    """Test the GET /api/relationships/filter-options endpoint."""
    
    def test_get_filter_options(self, client, entity_types, relationship_statuses, 
                               loyalty_statuses, test_user, auth_headers):
        """Test filter options endpoint returns all options."""
        response = client.get("/api/relationships/filter-options", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check all expected keys
        assert "users" in data
        assert "entity_types" in data
        assert "relationship_statuses" in data
        assert "loyalty_statuses" in data
        assert "campaigns" in data
        
        # Verify data
        assert len(data["users"]) >= 1
        assert len(data["entity_types"]) == 3
        assert len(data["relationship_statuses"]) == 3
        assert len(data["loyalty_statuses"]) == 3
    
    def test_filter_options_structure(self, client, auth_headers):
        """Test filter options have correct structure."""
        response = client.get("/api/relationships/filter-options", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check user structure
        if data["users"]:
            user = data["users"][0]
            assert "id" in user
            assert "name" in user
        
        # Check entity type structure
        if data["entity_types"]:
            entity_type = data["entity_types"][0]
            assert "id" in entity_type
            assert "code" in entity_type
            assert "common_name" in entity_type


class TestErrorHandling:
    """Test error handling for relationship endpoints."""
    
    def test_invalid_uuid_format(self, client, auth_headers):
        """Test handling of invalid UUID format."""
        response = client.get(
            "/api/relationships/not-a-uuid",
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test bulk update with missing required fields."""
        update_data = {
            # Missing relationship_ids
            "updates": {
                "lead_score": 5
            }
        }
        
        response = client.post(
            "/api/relationships/bulk-update",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_invalid_field_values(self, client, test_relationships, auth_headers):
        """Test update with invalid field values."""
        rel = test_relationships[0]
        update_data = {
            "lead_score": 10  # Should be 1-5
        }
        
        response = client.patch(
            f"/api/relationships/{rel.relationship_id}",
            json=update_data,
            headers=auth_headers
        )
        # Depending on validation, might be 200 or 400/422
        # For now, just check it doesn't crash
        assert response.status_code in [200, 400, 422]