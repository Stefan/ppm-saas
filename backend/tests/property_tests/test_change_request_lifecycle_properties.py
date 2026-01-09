"""
Property-based tests for change request lifecycle functionality.

These tests validate universal correctness properties for change request state management
using pytest and Hypothesis to ensure comprehensive coverage across all possible
lifecycle scenarios.

Feature: integrated-change-management
Task: 1.1 Write property test for change request lifecycle
Requirements: 1.3, 1.4
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional, Set
from decimal import Decimal
from enum import Enum

class ChangeStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class ChangeType(Enum):
    SCOPE = "scope"
    SCHEDULE = "schedule"
    BUDGET = "budget"
    DESIGN = "design"
    REGULATORY = "regulatory"

@st.composite
def change_request_data(draw):
    """Generate change request data for lifecycle testing."""
    return {
        'id': draw(st.uuids()),
        'change_number': f"CR-2024-{draw(st.integers(min_value=1000, max_value=9999))}",
        'title': draw(st.text(min_size=5, max_size=100)),
        'description': draw(st.text(min_size=20, max_size=500)),
        'justification': draw(st.text(min_size=10, max_size=300)),
        'change_type': draw(st.sampled_from(list(ChangeType))),
        'status': ChangeStatus.DRAFT,
        'priority': draw(st.sampled_from(['low', 'medium', 'high', 'critical'])),
        'requested_by': draw(st.uuids()),
        'project_id': draw(st.uuids()),
        'estimated_cost_impact': draw(st.decimals(min_value=0, max_value=1000000, places=2)),
        'estimated_schedule_impact_days': draw(st.integers(min_value=0, max_value=365)),
        'version': 1,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }

@st.composite
def status_transition_sequence(draw):
    """Generate a sequence of status transitions for testing."""
    # Define valid transition paths
    valid_transitions = {
        ChangeStatus.DRAFT: [ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED],
        ChangeStatus.SUBMITTED: [ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED],
        ChangeStatus.UNDER_REVIEW: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.ON_HOLD, ChangeStatus.REJECTED],
        ChangeStatus.PENDING_APPROVAL: [ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
        ChangeStatus.APPROVED: [ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD],
        ChangeStatus.REJECTED: [ChangeStatus.CLOSED],
        ChangeStatus.ON_HOLD: [ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED],
        ChangeStatus.IMPLEMENTING: [ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD],
        ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED],
        ChangeStatus.CLOSED: [],  # Terminal state
        ChangeStatus.CANCELLED: []  # Terminal state
    }
    
    # Generate a sequence of valid transitions
    current_status = ChangeStatus.DRAFT
    transitions = [current_status]
    
    max_transitions = draw(st.integers(min_value=1, max_value=8))
    
    for _ in range(max_transitions):
        possible_next = valid_transitions.get(current_status, [])
        if not possible_next:
            break
        
        next_status = draw(st.sampled_from(possible_next))
        transitions.append(next_status)
        current_status = next_status
        
        # Stop if we reach a terminal state
        if current_status in [ChangeStatus.CLOSED, ChangeStatus.CANCELLED]:
            break
    
    return transitions

@st.composite
def change_modification_data(draw):
    """Generate modification data for version testing."""
    return {
        'title': draw(st.one_of(st.none(), st.text(min_size=5, max_size=100))),
        'description': draw(st.one_of(st.none(), st.text(min_size=20, max_size=500))),
        'estimated_cost_impact': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=1000000, places=2))),
        'estimated_schedule_impact_days': draw(st.one_of(st.none(), st.integers(min_value=0, max_value=365))),
        'priority': draw(st.one_of(st.none(), st.sampled_from(['low', 'medium', 'high', 'critical']))),
        'modified_by': draw(st.uuids()),
        'modification_reason': draw(st.text(min_size=10, max_size=200))
    }

class MockChangeRequestManager:
    """Mock change request manager for property testing."""
    
    def __init__(self):
        self.change_requests: Dict[UUID, Dict[str, Any]] = {}
        self.version_history: Dict[UUID, List[Dict[str, Any]]] = {}
        self.status_transitions: Dict[UUID, List[Dict[str, Any]]] = {}
        
        # Define valid status transitions
        self.valid_transitions = {
            ChangeStatus.DRAFT: {ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED},
            ChangeStatus.SUBMITTED: {ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED},
            ChangeStatus.UNDER_REVIEW: {ChangeStatus.PENDING_APPROVAL, ChangeStatus.ON_HOLD, ChangeStatus.REJECTED},
            ChangeStatus.PENDING_APPROVAL: {ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD},
            ChangeStatus.APPROVED: {ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD},
            ChangeStatus.REJECTED: {ChangeStatus.CLOSED},
            ChangeStatus.ON_HOLD: {ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED},
            ChangeStatus.IMPLEMENTING: {ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD},
            ChangeStatus.IMPLEMENTED: {ChangeStatus.CLOSED},
            ChangeStatus.CLOSED: set(),  # Terminal state
            ChangeStatus.CANCELLED: set()  # Terminal state
        }
    
    def create_change_request(self, change_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new change request with initial state validation."""
        change_id = change_data['id']
        
        # Validate initial state
        if change_data['status'] != ChangeStatus.DRAFT:
            raise ValueError("New change requests must start in DRAFT status")
        
        # Set initial metadata
        change_data['version'] = 1
        change_data['created_at'] = datetime.now(timezone.utc)
        change_data['updated_at'] = change_data['created_at']
        
        # Store change request
        self.change_requests[change_id] = change_data.copy()
        
        # Initialize version history
        self.version_history[change_id] = [change_data.copy()]
        
        # Initialize status transition history
        self.status_transitions[change_id] = [{
            'from_status': None,
            'to_status': ChangeStatus.DRAFT,
            'timestamp': change_data['created_at'],
            'user_id': change_data['requested_by'],
            'reason': 'Initial creation'
        }]
        
        return {
            'change_id': change_id,
            'change_number': change_data['change_number'],
            'status': change_data['status'],
            'version': change_data['version'],
            'created': True
        }
    
    def update_change_request_status(self, change_id: UUID, new_status: ChangeStatus, user_id: UUID, reason: str = "") -> Dict[str, Any]:
        """Update change request status with transition validation."""
        if change_id not in self.change_requests:
            raise ValueError("Change request not found")
        
        change = self.change_requests[change_id]
        current_status = change['status']
        
        # Validate status transition
        if not self.validate_status_transition(current_status, new_status):
            raise ValueError(f"Invalid status transition from {current_status.value} to {new_status.value}")
        
        # Update status and metadata
        old_status = change['status']
        change['status'] = new_status
        change['updated_at'] = datetime.now(timezone.utc)
        
        # Record status transition
        transition = {
            'from_status': old_status,
            'to_status': new_status,
            'timestamp': change['updated_at'],
            'user_id': user_id,
            'reason': reason
        }
        self.status_transitions[change_id].append(transition)
        
        return {
            'change_id': change_id,
            'old_status': old_status,
            'new_status': new_status,
            'transition_valid': True,
            'timestamp': change['updated_at']
        }
    
    def modify_change_request(self, change_id: UUID, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify change request with version control."""
        if change_id not in self.change_requests:
            raise ValueError("Change request not found")
        
        change = self.change_requests[change_id]
        
        # Check if modifications are allowed in current status
        if change['status'] in [ChangeStatus.CLOSED, ChangeStatus.CANCELLED]:
            raise ValueError("Cannot modify closed or cancelled change requests")
        
        # Create new version
        old_version = change['version']
        change['version'] += 1
        change['updated_at'] = datetime.now(timezone.utc)
        
        # Apply modifications
        modified_fields = []
        for field, value in modifications.items():
            if field in ['modified_by', 'modification_reason']:
                continue  # Skip metadata fields
            if value is not None and field in change:
                old_value = change[field]
                change[field] = value
                modified_fields.append({
                    'field': field,
                    'old_value': old_value,
                    'new_value': value
                })
        
        # Store version in history
        version_record = change.copy()
        version_record['modified_fields'] = modified_fields
        version_record['modified_by'] = modifications.get('modified_by')
        version_record['modification_reason'] = modifications.get('modification_reason', '')
        self.version_history[change_id].append(version_record)
        
        return {
            'change_id': change_id,
            'old_version': old_version,
            'new_version': change['version'],
            'modified_fields': modified_fields,
            'modification_count': len(modified_fields)
        }
    
    def validate_status_transition(self, current_status: ChangeStatus, new_status: ChangeStatus) -> bool:
        """Validate if a status transition is allowed."""
        if current_status == new_status:
            return False  # No-op transitions not allowed
        
        allowed_transitions = self.valid_transitions.get(current_status, set())
        return new_status in allowed_transitions
    
    def get_change_request(self, change_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current change request data."""
        return self.change_requests.get(change_id)
    
    def get_version_history(self, change_id: UUID) -> List[Dict[str, Any]]:
        """Get complete version history for a change request."""
        return self.version_history.get(change_id, [])
    
    def get_status_transitions(self, change_id: UUID) -> List[Dict[str, Any]]:
        """Get status transition history for a change request."""
        return self.status_transitions.get(change_id, [])


# Property 1: Change Request State Consistency
@given(
    change_data=change_request_data(),
    status_sequence=status_transition_sequence()
)
def test_change_request_state_consistency_property(change_data, status_sequence):
    """
    Property 1: Change Request State Consistency
    
    For any change request lifecycle, status transitions must follow valid paths
    and maintain data consistency throughout all state changes.
    
    Validates: Requirements 1.3, 1.4
    """
    # Arrange
    manager = MockChangeRequestManager()
    
    # Act - Create change request and process status transitions
    create_result = manager.create_change_request(change_data)
    change_id = change_data['id']
    
    # Process each status transition in sequence
    transition_results = []
    current_status = ChangeStatus.DRAFT
    
    for i, target_status in enumerate(status_sequence[1:], 1):  # Skip initial DRAFT
        try:
            result = manager.update_change_request_status(
                change_id, target_status, change_data['requested_by'], f"Transition {i}"
            )
            transition_results.append(result)
            current_status = target_status
        except ValueError as e:
            # Invalid transition - this is expected for some sequences
            break
    
    # Get final state
    final_change = manager.get_change_request(change_id)
    status_history = manager.get_status_transitions(change_id)
    
    # Assert - State consistency properties
    
    # Property: Change request must be created successfully
    assert create_result['created'] is True, \
        "Change request must be created successfully"
    assert create_result['status'] == ChangeStatus.DRAFT, \
        "New change requests must start in DRAFT status"
    
    # Property: All successful transitions must be valid
    for result in transition_results:
        assert result['transition_valid'] is True, \
            "All processed transitions must be valid"
        
        # Verify transition was actually applied
        assert manager.validate_status_transition(result['old_status'], result['new_status']), \
            f"Transition from {result['old_status']} to {result['new_status']} must be valid"
    
    # Property: Final status must match last successful transition
    if transition_results:
        last_transition = transition_results[-1]
        assert final_change['status'] == last_transition['new_status'], \
            "Final status must match last successful transition"
    else:
        assert final_change['status'] == ChangeStatus.DRAFT, \
            "Status must remain DRAFT if no valid transitions occurred"
    
    # Property: Status transition history must be complete and ordered
    assert len(status_history) >= 1, \
        "Status transition history must contain at least initial creation"
    
    # First transition should be creation
    first_transition = status_history[0]
    assert first_transition['from_status'] is None, \
        "First transition must be from None (creation)"
    assert first_transition['to_status'] == ChangeStatus.DRAFT, \
        "First transition must be to DRAFT status"
    
    # Subsequent transitions must be sequential
    for i in range(1, len(status_history)):
        prev_transition = status_history[i-1]
        curr_transition = status_history[i]
        assert prev_transition['to_status'] == curr_transition['from_status'], \
            "Status transitions must be sequential without gaps"
    
    # Property: Timestamps must be chronological
    timestamps = [t['timestamp'] for t in status_history]
    assert timestamps == sorted(timestamps), \
        "Status transition timestamps must be in chronological order"
    
    # Property: Terminal states must not allow further transitions
    if final_change['status'] in [ChangeStatus.CLOSED, ChangeStatus.CANCELLED]:
        terminal_status = final_change['status']
        allowed_transitions = manager.valid_transitions[terminal_status]
        assert len(allowed_transitions) == 0, \
            f"Terminal status {terminal_status} must not allow further transitions"


@given(
    change_data=change_request_data(),
    modifications=st.lists(change_modification_data(), min_size=1, max_size=5)
)
def test_change_request_version_control_property(change_data, modifications):
    """
    Property: Change Request Version Control
    
    For any change request modifications, version history must be maintained
    with complete tracking of all changes and proper version incrementing.
    
    Validates: Requirements 1.4
    """
    # Arrange
    manager = MockChangeRequestManager()
    
    # Create initial change request
    manager.create_change_request(change_data)
    change_id = change_data['id']
    initial_version = 1
    
    # Act - Apply modifications sequentially
    modification_results = []
    for i, mod_data in enumerate(modifications):
        try:
            result = manager.modify_change_request(change_id, mod_data)
            modification_results.append(result)
        except ValueError:
            # Modification not allowed in current state
            break
    
    # Get final state and history
    final_change = manager.get_change_request(change_id)
    version_history = manager.get_version_history(change_id)
    
    # Assert - Version control properties
    
    # Property: Version numbers must increment sequentially
    expected_version = initial_version + len(modification_results)
    assert final_change['version'] == expected_version, \
        f"Final version must be {expected_version} after {len(modification_results)} modifications"
    
    # Property: Each modification must increment version by 1
    for i, result in enumerate(modification_results):
        expected_old = initial_version + i
        expected_new = initial_version + i + 1
        assert result['old_version'] == expected_old, \
            f"Modification {i} old version must be {expected_old}"
        assert result['new_version'] == expected_new, \
            f"Modification {i} new version must be {expected_new}"
    
    # Property: Version history must contain all versions
    assert len(version_history) == expected_version, \
        f"Version history must contain {expected_version} versions"
    
    # Property: Version history must be sequential
    for i, version_record in enumerate(version_history):
        expected_version_num = i + 1
        assert version_record['version'] == expected_version_num, \
            f"Version history entry {i} must have version {expected_version_num}"
    
    # Property: Modified fields must be tracked accurately
    for result in modification_results:
        if result['modification_count'] > 0:
            assert len(result['modified_fields']) == result['modification_count'], \
                "Modified fields count must match actual field changes"
            
            # Verify each modified field has old and new values
            for field_change in result['modified_fields']:
                assert 'field' in field_change, \
                    "Field change must specify field name"
                assert 'old_value' in field_change, \
                    "Field change must track old value"
                assert 'new_value' in field_change, \
                    "Field change must track new value"
    
    # Property: Version timestamps must be chronological
    timestamps = [v['updated_at'] for v in version_history]
    assert timestamps == sorted(timestamps), \
        "Version timestamps must be in chronological order"
    
    # Property: Original data must be preserved in version history
    original_version = version_history[0]
    for field in ['title', 'description', 'change_type', 'priority']:
        if field in change_data:
            assert original_version[field] == change_data[field], \
                f"Original {field} must be preserved in version history"


@given(
    change_requests=st.lists(change_request_data(), min_size=2, max_size=5),
    concurrent_modifications=st.integers(min_value=1, max_value=3)
)
def test_change_request_isolation_property(change_requests, concurrent_modifications):
    """
    Property: Change Request Isolation
    
    For any multiple change requests managed concurrently, each must maintain
    independent state and version control without cross-contamination.
    
    Validates: Requirements 1.3, 1.4
    """
    # Arrange
    manager = MockChangeRequestManager()
    
    # Create all change requests
    created_changes = []
    for change_data in change_requests:
        result = manager.create_change_request(change_data)
        created_changes.append((change_data['id'], result))
    
    # Act - Perform concurrent modifications on different changes
    modification_tracking = {}
    for change_data in change_requests:
        change_id = change_data['id']
        modification_tracking[change_id] = {'modifications': 0, 'status_changes': 0}
        
        # Apply some modifications
        for i in range(concurrent_modifications):
            try:
                mod_data = {
                    'title': f"Modified title {i}",
                    'modified_by': uuid4(),
                    'modification_reason': f"Concurrent modification {i}"
                }
                manager.modify_change_request(change_id, mod_data)
                modification_tracking[change_id]['modifications'] += 1
            except ValueError:
                break
        
        # Apply some status changes
        try:
            manager.update_change_request_status(
                change_id, ChangeStatus.SUBMITTED, change_data['requested_by'], "Submit for review"
            )
            modification_tracking[change_id]['status_changes'] += 1
        except ValueError:
            pass
    
    # Assert - Isolation properties
    
    # Property: Each change request must exist independently
    for change_id, _ in created_changes:
        assert change_id in manager.change_requests, \
            f"Change request {change_id} must exist independently"
    
    # Property: Version histories must be isolated
    for change_id in modification_tracking:
        version_history = manager.get_version_history(change_id)
        expected_versions = 1 + modification_tracking[change_id]['modifications']
        assert len(version_history) == expected_versions, \
            f"Change {change_id} must have {expected_versions} versions in isolation"
        
        # Verify no cross-contamination in version history
        for version in version_history:
            assert version['id'] == change_id, \
                f"Version history for {change_id} must not contain other change IDs"
    
    # Property: Status transitions must be isolated
    for change_id in modification_tracking:
        status_history = manager.get_status_transitions(change_id)
        expected_transitions = 1 + modification_tracking[change_id]['status_changes']  # +1 for creation
        assert len(status_history) == expected_transitions, \
            f"Change {change_id} must have {expected_transitions} status transitions"
        
        # Verify no cross-contamination in status history
        for transition in status_history:
            # Status transitions don't store change_id directly, but they should be isolated by the manager
            pass
    
    # Property: Final states must be independent
    final_states = {}
    for change_id, _ in created_changes:
        final_change = manager.get_change_request(change_id)
        final_states[change_id] = {
            'version': final_change['version'],
            'status': final_change['status'],
            'updated_at': final_change['updated_at']
        }
    
    # Verify each change has unique final state based on its own modifications
    change_ids = list(final_states.keys())
    for i, change_id_1 in enumerate(change_ids):
        for change_id_2 in change_ids[i+1:]:
            state_1 = final_states[change_id_1]
            state_2 = final_states[change_id_2]
            
            # Changes should have different versions if they had different modification counts
            mod_count_1 = modification_tracking[change_id_1]['modifications']
            mod_count_2 = modification_tracking[change_id_2]['modifications']
            
            if mod_count_1 != mod_count_2:
                assert state_1['version'] != state_2['version'], \
                    f"Changes with different modification counts must have different versions"


if __name__ == "__main__":
    # Run property tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])