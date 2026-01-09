"""
Configuration for property-based tests
"""

import pytest
from hypothesis import settings, Verbosity


# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)

# Load the appropriate profile
settings.load_profile("default")


@pytest.fixture(scope="session")
def property_test_config():
    """Configuration for property-based tests"""
    return {
        "max_examples": 100,
        "deadline": 60000,  # 60 seconds
        "stateful_step_count": 50,
        "suppress_health_check": []
    }


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    return {}


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger for testing"""
    class MockAuditLogger:
        def __init__(self):
            self.logs = []
        
        def log_event(self, event_type, entity_id, details):
            self.logs.append({
                'event_type': event_type,
                'entity_id': entity_id,
                'details': details,
                'timestamp': pytest.approx(pytest.now(), abs=1)
            })
    
    return MockAuditLogger()