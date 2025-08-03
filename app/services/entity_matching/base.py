"""Base classes and interfaces for entity matching"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from .models.match_results import MatchResult, MatchContext

load_dotenv()


class BaseEntityMatcher(ABC):
    """Abstract base class for all entity matchers"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the matcher with optional database session
        
        Args:
            session: Optional SQLAlchemy session. If not provided,
                    creates its own session.
        """
        self._external_session = session is not None
        
        if session:
            self.session = session
        else:
            # Create own session
            self.session = self._create_session()
    
    def _create_session(self) -> Session:
        """Create a database session"""
        DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
        DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
        DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
        DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
        DATABASE_PORT = os.getenv("DATABASE_PORT", "5433")
        
        DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
    
    @abstractmethod
    def match(self, query: str, context: Optional[MatchContext] = None) -> List[MatchResult]:
        """
        Main matching method that must be implemented by subclasses
        
        Args:
            query: The search query (name, email, etc.)
            context: Optional context to help with matching
            
        Returns:
            List of MatchResult objects sorted by confidence
        """
        pass
    
    def close(self):
        """Close the database session if we created it"""
        if not self._external_session and self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


class MatcherRegistry:
    """Registry for all available entity matchers"""
    
    _matchers = {}
    
    @classmethod
    def register(cls, entity_type: str, matcher_class: type):
        """Register a matcher for an entity type"""
        cls._matchers[entity_type] = matcher_class
    
    @classmethod
    def get_matcher(cls, entity_type: str, session: Optional[Session] = None) -> BaseEntityMatcher:
        """Get a matcher instance for the specified entity type"""
        matcher_class = cls._matchers.get(entity_type)
        if not matcher_class:
            raise ValueError(f"No matcher registered for entity type: {entity_type}")
        return matcher_class(session)
    
    @classmethod
    def list_matchers(cls) -> List[str]:
        """List all registered entity types"""
        return list(cls._matchers.keys())


class MatchingConfig:
    """Configuration for matching behavior"""
    
    # Default confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.5
    MAX_RESULTS = 10
    
    # Weights for different match types
    MATCH_TYPE_WEIGHTS = {
        "email": 1.0,
        "npi": 1.0,
        "external_id": 1.0,
        "exact_name": 0.95,
        "first_last_name": 0.9,
        "last_name": 0.7,
        "fuzzy_name": 0.8,
        "phone": 0.85,
        "address": 0.8,
        "alias": 0.75
    }
    
    # Context boost values
    CONTEXT_BOOSTS = {
        "organization_match": 0.15,
        "specialty_match": 0.1,
        "location_match": 0.1
    }
    
    # Penalties
    INACTIVE_PENALTY = 0.2