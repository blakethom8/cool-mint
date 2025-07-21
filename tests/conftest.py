"""
Shared pytest fixtures for testing Market Explorer and Relationship Management applications.

This configuration focuses on rapid prototyping with minimal overhead.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Generator
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database.session import Base, db_session
from app.database.data_models.salesforce_data import SfUser, SfContact
from app.database.data_models.relationship_management import (
    Relationships, Campaigns
)
from app.database.data_models.crm_lookups import (
    RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes
)
from app.database.data_models.claims_data import ClaimsProvider, SiteOfService


# Test database URL - uses SQLite for speed in testing
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back after each test for isolation.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Begin a transaction
    session.begin()
    
    yield session
    
    # Rollback the transaction to keep tests isolated
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """Create a test client with database session override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[db_session] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Lookup Data Fixtures ---

@pytest.fixture(scope="function")
def entity_types(db_session) -> list[EntityTypes]:
    """Create standard entity types."""
    types = [
        EntityTypes(
            id=1,
            code="SfContact",
            common_name="Contacts",
            description="Salesforce contacts",
            table_name="sf_contacts"
        ),
        EntityTypes(
            id=2,
            code="ClaimsProvider",
            common_name="Providers",
            description="Healthcare providers from claims data",
            table_name="claims_providers"
        ),
        EntityTypes(
            id=3,
            code="SiteOfService",
            common_name="Sites",
            description="Healthcare facility sites",
            table_name="site_of_service"
        )
    ]
    db_session.add_all(types)
    db_session.commit()
    return types


@pytest.fixture(scope="function")
def relationship_statuses(db_session) -> list[RelationshipStatusTypes]:
    """Create standard relationship statuses."""
    statuses = [
        RelationshipStatusTypes(
            id=1,
            code="ESTABLISHED",
            display_name="Established",
            description="Strong, established relationship"
        ),
        RelationshipStatusTypes(
            id=2,
            code="BUILDING",
            display_name="Building",
            description="Actively building relationship"
        ),
        RelationshipStatusTypes(
            id=3,
            code="PROSPECTING",
            display_name="Prospecting",
            description="Initial outreach phase"
        )
    ]
    db_session.add_all(statuses)
    db_session.commit()
    return statuses


@pytest.fixture(scope="function")
def loyalty_statuses(db_session) -> list[LoyaltyStatusTypes]:
    """Create standard loyalty statuses."""
    statuses = [
        LoyaltyStatusTypes(
            id=1,
            code="LOYAL",
            display_name="Loyal",
            description="Highly loyal to organization",
            color_hex="#00AA00"
        ),
        LoyaltyStatusTypes(
            id=2,
            code="NEUTRAL",
            display_name="Neutral",
            description="No strong loyalty either way",
            color_hex="#FFA500"
        ),
        LoyaltyStatusTypes(
            id=3,
            code="AT_RISK",
            display_name="At Risk",
            description="At risk of leaving",
            color_hex="#FF0000"
        )
    ]
    db_session.add_all(statuses)
    db_session.commit()
    return statuses


# --- User and Entity Fixtures ---

@pytest.fixture(scope="function")
def test_user(db_session) -> SfUser:
    """Create a test user."""
    user = SfUser(
        id=1,
        salesforce_id="005000000000001",
        username="test.user@example.com",
        email="test.user@example.com",
        first_name="Test",
        last_name="User",
        name="Test User",
        is_profile_photo_active=True,
        sf_created_date=datetime.now(),
        sf_last_modified_date=datetime.now(),
        sf_system_modstamp=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def test_contact(db_session) -> SfContact:
    """Create a test Salesforce contact."""
    contact = SfContact(
        id=uuid.uuid4(),
        salesforce_id="003000000000001",
        first_name="John",
        last_name="Doe",
        name="John Doe",
        email="john.doe@hospital.com",
        phone="555-1234",
        title="Chief of Cardiology",
        specialty="Cardiology",
        is_physician=True,
        active=True,
        mailing_city="Boston",
        mailing_state="MA",
        sf_created_date=datetime.now(),
        sf_last_modified_date=datetime.now(),
        sf_system_modstamp=datetime.now()
    )
    db_session.add(contact)
    db_session.commit()
    return contact


@pytest.fixture(scope="function")
def test_provider(db_session) -> ClaimsProvider:
    """Create a test claims provider."""
    provider = ClaimsProvider(
        provider_key=uuid.uuid4(),
        npi="1234567890",
        name="Dr. Jane Smith",
        first_name="Jane",
        last_name="Smith",
        taxonomy_description="Internal Medicine",
        primary_taxonomy_classification="Physician",
        phone_number="555-5678",
        entity_type_code="1",
        mailing_address_1="123 Medical Way",
        mailing_city="Cambridge",
        mailing_state="MA",
        mailing_postal_code="02139"
    )
    db_session.add(provider)
    db_session.commit()
    return provider


@pytest.fixture(scope="function")
def test_site(db_session) -> SiteOfService:
    """Create a test site of service."""
    site = SiteOfService(
        site_id=uuid.uuid4(),
        customer_name="Boston General Hospital",
        site_name="Main Campus",
        site_type="Hospital",
        site_specialty="General",
        phone="555-9999",
        site_address="456 Hospital Blvd",
        city="Boston",
        state="MA",
        zip_code="02115",
        latitude=42.3601,
        longitude=-71.0589
    )
    db_session.add(site)
    db_session.commit()
    return site


# --- Campaign and Relationship Fixtures ---

@pytest.fixture(scope="function")
def test_campaign(db_session, test_user) -> Campaigns:
    """Create a test campaign."""
    campaign = Campaigns(
        campaign_id=uuid.uuid4(),
        campaign_name="Q1 Cardiology Outreach",
        description="Focus on cardiology referrals",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        owner_user_id=test_user.id,
        status="Active",
        target_metrics={"referrals": 50, "meetings": 20}
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture(scope="function")
def test_relationships(
    db_session, 
    test_user, 
    test_contact, 
    test_provider,
    test_site,
    entity_types,
    relationship_statuses,
    loyalty_statuses
) -> list[Relationships]:
    """Create a set of test relationships with varied data."""
    relationships = []
    
    # Contact relationship
    contact_rel = Relationships(
        relationship_id=uuid.uuid4(),
        user_id=test_user.id,
        entity_type_id=1,  # SfContact
        linked_entity_id=test_contact.id,
        relationship_status_id=1,  # ESTABLISHED
        loyalty_status_id=1,  # LOYAL
        lead_score=5,
        last_activity_date=datetime.now() - timedelta(days=2),
        next_steps="Schedule quarterly review",
        engagement_frequency="Monthly"
    )
    relationships.append(contact_rel)
    
    # Provider relationship
    provider_rel = Relationships(
        relationship_id=uuid.uuid4(),
        user_id=test_user.id,
        entity_type_id=2,  # ClaimsProvider
        linked_entity_id=test_provider.provider_key,
        relationship_status_id=2,  # BUILDING
        loyalty_status_id=2,  # NEUTRAL
        lead_score=3,
        last_activity_date=datetime.now() - timedelta(days=10),
        next_steps="Follow up on referral patterns",
        engagement_frequency="Bi-weekly"
    )
    relationships.append(provider_rel)
    
    # Site relationship
    site_rel = Relationships(
        relationship_id=uuid.uuid4(),
        user_id=test_user.id,
        entity_type_id=3,  # SiteOfService
        linked_entity_id=test_site.site_id,
        relationship_status_id=3,  # PROSPECTING
        loyalty_status_id=3,  # AT_RISK
        lead_score=2,
        last_activity_date=datetime.now() - timedelta(days=30),
        next_steps="Initial meeting with administrator",
        engagement_frequency="Monthly"
    )
    relationships.append(site_rel)
    
    db_session.add_all(relationships)
    db_session.commit()
    return relationships


# --- Market Explorer Test Data ---

@pytest.fixture(scope="function")
def test_market_data(db_session) -> dict:
    """Create test data for market explorer."""
    # Create multiple providers
    providers = []
    for i in range(5):
        provider = ClaimsProvider(
            provider_key=uuid.uuid4(),
            npi=f"123456789{i}",
            name=f"Dr. Provider {i}",
            first_name=f"Provider{i}",
            last_name="Test",
            taxonomy_description=["Cardiology", "Internal Medicine", "Pediatrics"][i % 3],
            primary_taxonomy_classification="Physician",
            phone_number=f"555-100{i}",
            entity_type_code="1",
            mailing_address_1=f"{i+1} Medical Way",
            mailing_city=["Boston", "Cambridge", "Brookline"][i % 3],
            mailing_state="MA",
            mailing_postal_code=f"0210{i}",
            latitude=42.3601 + (i * 0.01),
            longitude=-71.0589 - (i * 0.01)
        )
        providers.append(provider)
    
    # Create multiple sites
    sites = []
    for i in range(3):
        site = SiteOfService(
            site_id=uuid.uuid4(),
            customer_name=f"Hospital {i}",
            site_name=f"Campus {i}",
            site_type=["Hospital", "Clinic", "Urgent Care"][i],
            site_specialty="General",
            phone=f"555-200{i}",
            site_address=f"{i+1} Hospital St",
            city=["Boston", "Cambridge", "Quincy"][i],
            state="MA",
            zip_code=f"0211{i}",
            latitude=42.3601 + (i * 0.02),
            longitude=-71.0589 - (i * 0.02)
        )
        sites.append(site)
    
    db_session.add_all(providers + sites)
    db_session.commit()
    
    return {
        "providers": providers,
        "sites": sites
    }


# --- Utility Functions ---

@pytest.fixture
def auth_headers(test_user) -> dict:
    """Mock authentication headers."""
    # In a real app, this would generate a JWT token
    return {"Authorization": f"Bearer test-token-{test_user.id}"}


@pytest.fixture
def make_relationship(db_session, test_user, entity_types, relationship_statuses, loyalty_statuses):
    """Factory fixture for creating relationships."""
    def _make_relationship(
        entity_type_id: int,
        linked_entity_id: uuid.UUID,
        **kwargs
    ) -> Relationships:
        defaults = {
            "relationship_id": uuid.uuid4(),
            "user_id": test_user.id,
            "entity_type_id": entity_type_id,
            "linked_entity_id": linked_entity_id,
            "relationship_status_id": 1,
            "loyalty_status_id": 2,
            "lead_score": 3,
            "engagement_frequency": "Monthly"
        }
        defaults.update(kwargs)
        
        relationship = Relationships(**defaults)
        db_session.add(relationship)
        db_session.commit()
        return relationship
    
    return _make_relationship