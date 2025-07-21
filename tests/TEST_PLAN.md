# Test Plan for Market Explorer and Relationship Management Applications

## Overview

This test plan outlines our testing strategy for the Market Explorer and Relationship Management applications, with a focus on **rapid prototyping and development velocity**. The plan is designed to catch critical issues early while supporting fast iteration cycles.

## Testing Philosophy

### Current Phase: Rapid Prototyping
- **Goal**: Prevent breaking changes and ensure core functionality works
- **Focus**: Critical path testing, not comprehensive coverage
- **Speed**: Tests should run quickly (< 30 seconds for full suite)
- **Maintenance**: Minimal test maintenance overhead

### Future Phase: Production-Ready
- Comprehensive test coverage (80%+)
- Performance benchmarking
- Security testing
- Load testing

## Test Categories

### 1. Smoke Tests (Priority: HIGH)
**Purpose**: Quick validation that nothing is on fire

#### What We Test:
- Database models can be instantiated
- API endpoints return 200/201 status codes
- Frontend builds without errors
- Critical user paths work end-to-end

#### Implementation:
```python
# tests/smoke/test_critical_paths.py
- test_database_connection()
- test_api_health_check()
- test_create_relationship()
- test_fetch_market_data()
```

### 2. Model Relationship Tests (Priority: HIGH)
**Purpose**: Prevent SQLAlchemy relationship errors (like we just fixed)

#### What We Test:
- All relationships have valid back_populates
- Foreign keys are properly defined
- No circular import issues
- Generic entity relationships work correctly

#### Implementation:
```python
# tests/unit/test_models.py
- test_all_models_instantiate()
- test_relationship_back_populates()
- test_foreign_key_constraints()
- test_entity_type_relationships()
```

### 3. API Contract Tests (Priority: MEDIUM)
**Purpose**: Ensure API endpoints behave consistently

#### Market Explorer Tests:
```python
# tests/integration/test_api_market_explorer.py
- test_filter_providers_by_specialty()
- test_map_markers_performance()
- test_pagination_works()
- test_invalid_filters_handled()
```

#### Relationship Management Tests:
```python
# tests/integration/test_api_relationships.py
- test_list_relationships_with_filters()
- test_update_relationship_status()
- test_bulk_update_relationships()
- test_activity_timeline_retrieval()
```

### 4. Service Layer Tests (Priority: LOW - for now)
**Purpose**: Test business logic in isolation

- Deferred until services stabilize
- Will add when core features are locked

## Test Data Strategy

### Approach: Minimal Fixtures
```python
# tests/conftest.py
@pytest.fixture
def test_user():
    """Single test user for all tests"""
    
@pytest.fixture
def test_relationships(test_user):
    """5-10 relationships with varied data"""
    
@pytest.fixture
def test_market_data():
    """Small dataset of providers/sites"""
```

### Key Principles:
- Use transaction rollback for test isolation
- Minimal data creation (fast tests)
- Reusable fixtures across tests
- No external dependencies

## Implementation Phases

### Phase 1: Foundation (Current Sprint)
- [x] Create test directory structure
- [x] Write test plan
- [ ] Setup pytest configuration
- [ ] Create model validation tests
- [ ] Add smoke tests for critical paths

### Phase 2: API Coverage (Next Sprint)
- [ ] Market Explorer API tests
- [ ] Relationship Management API tests
- [ ] Error handling tests
- [ ] Basic performance checks

### Phase 3: Frontend Testing (Future)
- [ ] Component unit tests with Jest
- [ ] Critical user flow tests
- [ ] Visual regression tests (optional)

### Phase 4: Production Hardening (Future)
- [ ] Load testing
- [ ] Security testing
- [ ] Data integrity tests
- [ ] Performance benchmarks

## Running Tests

### Quick Check (Developers):
```bash
# Run smoke tests only (< 5 seconds)
pytest tests/smoke -v

# Run before committing
pytest tests/unit tests/smoke -v
```

### Full Suite:
```bash
# Run all tests
pytest tests -v

# With coverage
pytest tests --cov=app --cov-report=html
```

### CI/CD Integration:
```yaml
# .github/workflows/test.yml
- Run smoke tests on every push
- Run full suite on PR
- Block merge if tests fail
```

## Success Metrics

### Current Phase:
- ✅ No runtime errors in production
- ✅ Core features work as expected
- ✅ Tests run in < 30 seconds
- ✅ Low maintenance overhead

### Future Phase:
- 80%+ code coverage
- < 1% test flakiness
- Performance benchmarks met
- Security vulnerabilities identified

## Anti-Patterns to Avoid

1. **Over-testing during prototyping**
   - Don't test every edge case yet
   - Don't mock everything
   - Don't write brittle UI tests

2. **Test complexity**
   - Keep tests simple and readable
   - Avoid complex test setup
   - Don't test framework code

3. **Slow tests**
   - Avoid hitting external APIs
   - Minimize database operations
   - Use transactions for cleanup

## Specific Test Scenarios

### Market Explorer Critical Paths:
1. User can filter providers by specialty
2. Map displays markers for filtered results
3. Quick View shows provider details
4. View mode switching works
5. Pagination handles large datasets

### Relationship Management Critical Paths:
1. User can view their relationships
2. Filters reduce the displayed list
3. Status updates are saved
4. Bulk updates work correctly
5. Activity timeline displays data

## Tools and Libraries

### Required:
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **factory-boy**: Test data generation
- **freezegun**: Time mocking

### Optional (Future):
- **pytest-benchmark**: Performance testing
- **hypothesis**: Property-based testing
- **playwright**: E2E testing

## Maintenance Guidelines

### When to Add Tests:
- Bug fixes (regression prevention)
- New features (happy path only)
- Breaking changes to APIs
- Complex business logic

### When to Skip Tests (for now):
- UI styling changes
- Prototype features
- Third-party integrations
- Admin-only features

## Conclusion

This test plan prioritizes **development velocity** while establishing a foundation for comprehensive testing later. The focus is on preventing critical failures and ensuring core functionality works reliably.

Remember: **Perfect test coverage is the enemy of shipping features quickly**. We'll increase coverage as the application stabilizes.