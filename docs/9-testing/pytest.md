# Running Tests with pytest

## Introduction

This guide explains how to effectively use pytest for testing in the GenAI Project Launchpad. Pytest is a powerful and flexible testing framework for Python that simplifies the process of writing and running tests. By leveraging pytest, you can ensure the reliability and correctness of your AI applications.

## Table of Contents

- [Running Tests with pytest](#running-tests-with-pytest)
  - [Introduction](#introduction)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Understanding pytest](#understanding-pytest)
  - [Running Tests](#running-tests)
  - [Test Discovery](#test-discovery)
  - [Writing Tests](#writing-tests)
  - [Fixtures](#fixtures)
  - [Markers](#markers)
  - [Best Practices](#best-practices)

## Project Structure

The testing structure in the GenAI Project Launchpad is organized as follows:

```text
app/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_events.py
│   └── features/
│       ├── __init__.py
│       └── test_customer_pipeline.py
```

- `tests/`: Main directory for all test files.
- `conftest.py`: Contains shared fixtures for tests.
- `test_*.py`: Individual test files.
- `features/`: Subdirectory for feature-specific tests.

## Understanding pytest

Pytest uses conventions to automatically discover and run tests:

1. Test files should be named `test_*.py` or `*_test.py`.
2. Test functions should be prefixed with `test_`.
3. Test classes should be prefixed with `Test`.

## Running Tests

To run tests in the GenAI Project Launchpad:

1. Ensure Docker containers are running:
   ```
   cd docker
   ./start.sh
   ```

2. Execute pytest:
   ```
   cd app
   pytest
   ```

This command will discover and run all tests in the project.

## Test Discovery

Pytest automatically discovers tests based on naming conventions:

- It searches recursively from the current directory.
- Files matching `test_*.py` or `*_test.py` are considered test files.
- Functions prefixed with `test_` in these files are executed as tests.

For example, in `test_events.py`:

```python
def test_event():
    # Test logic here
    assert True
```

## Writing Tests

Here's a basic example of a test function:

```python
def test_customer_pipeline():
    # Setup
    pipeline = CustomerPipeline()
    
    # Exercise
    result = pipeline.process(customer_data)
    
    # Verify
    assert result.status == 'success'
    assert result.output is not None
```

## Fixtures

Fixtures in `conftest.py` provide reusable setup for tests:

```python
import pytest
from database.session import SessionLocal

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    yield session
    session.close()
```

Use fixtures in tests like this:

```python
def test_database_operation(db_session):
    # Use db_session for database operations
    result = db_session.query(SomeModel).filter_by(id=1).first()
    assert result is not None
```

## Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_long_running_process():
    # Test logic for a slow process
```

Run specific markers:

```bash
pytest -m slow
```

## Best Practices

1. Keep tests isolated and independent.
2. Use meaningful names for test functions.
3. Utilize fixtures for common setup and teardown.
4. Group related tests in classes.
5. Use markers to categorize tests.
6. Write tests for both success and failure scenarios.
7. Regularly run the full test suite before committing changes.

By following these guidelines and leveraging the power of pytest, you can create a robust testing framework for your GenAI Project Launchpad, ensuring the reliability and quality of your AI applications.