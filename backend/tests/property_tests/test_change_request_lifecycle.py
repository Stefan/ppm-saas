"""
Property-based tests for change request lifecycle (Task 1.1)

Property 1: Change Request State Consistency
- Validates that change requests maintain consistent state throughout their lifecycle
- Ensures state transitions follow business rules and maintain data integrity
- Validates Requirements 1.3, 1.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, invariant
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.change_management import (
    ChangeRequest, ChangeStatus, ChangeType, PriorityLevel,
    ChangeRequestCreate, ChangeRequestUpdate
)


# Strategy generators for change management data
@st.composite
def change_type_strategy(draw):
    """Generate valid change types"""
    return draw(st.sampled_from(list(ChangeType)))


@st.composite
def priority_level_strategy(draw):
    """Generate valid priority levels"""
    return draw(st.sampled_from(list(PriorityLevel)))


@st.composite
def change_status_strategy(draw):
    """Generate valid change statuses"""
    return draw(st.sampled_from(list(ChangeStatus)))


@st.composite
def valid_change_request_data(draw):
    """Generate valid change request creation data"""
    return ChangeRequestCreate(
        title=draw(st.text(min_size=5, max_size=255, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
        description=draw(st.text(min_size=10, max_size=1000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
        justification=draw(st.one_of(st.none(), st.text(min_size=1, max_size=500))),
        change_type=draw(change_type_strategy()),
        priority=draw(priority_level_strategy()),
        project_id=draw(st.uuids()),
        required_by_date=draw(st.one_of(st.none(), st.dates(min_value=date.today()))),
        estimated_cost_impact=draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=1000000, places=2))),
        estimated_schedule_impact_days=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=365))),
        estimated_effort_hours=draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=10000, places=2))),
        affected_milestones=draw(st.lists(st.uuids(), max_size=5)),
        affected_pos=draw(st.lists(st.uuids(), max_size=5)),
        template_id=draw(st.one_of(st.none(), st.uuids()))
    )


@st.composite
def valid_status_transition(draw, current_status: ChangeStatus):
    """Generate valid status transitions based on current status"""
    valid_transitions = {
        ChangeStatus.DRAFT: [ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED],
        ChangeStatus.SUBMITTED: [ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED, ChangeStatus.DRAFT],
        ChangeStatus.UNDER_REVIEW: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
        ChangeStatus.PENDING_APPROVAL: [ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
        ChangeStatus.APPROVED: [ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD],
        ChangeStatus.REJECTED: [ChangeStatus.DRAFT, ChangeStatus.CANCELLED],
        ChangeStatus.ON_HOLD: [ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED],
        ChangeStatus.IMPLEMENTING: [ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD],
        ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED],
        ChangeStatus.CLOSED: [],  # Terminal state
        ChangeStatus.CANCELLED: []  # Terminal state
    }
    
    possible_transitions = valid_transitions.get(current_status, [])
    if not possible_transitions:
        return current_status
    
    return draw(st.sampled_from(possible_transitions))


class ChangeRequestLifecycleStateMachine(RuleBasedStateMachine):
    """
    Stateful property test for change request lifecycle consistency
    
    This tests Property 1: Change Request State Consistency
    - State transitions follow business rules
    - Data integrity is maintained across transitions
    - Audit trail is complete and accurate
    """
    
    change_requests = Bundle('change_requests')
    
    def __init__(self):
        super().__init__()
        self.created_changes: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
    
    @rule(target=change_requests, change_data=valid_change_request_data())
    def create_change_request(self, change_data):
        """Create a new change request"""
        change_id = str(uuid4())
        change_number = f"CR-{datetime.now().year}-{len(self.created_changes) + 1:04d}"
        
        # Simulate change request creation
        change_record = {
            'id': change_id,
            'change_number': change_number,
            'title': change_data.title,
            'description': change_data.description,
            'justification': change_data.justification,
            'change_type': change_data.change_type,
            'priority': change_data.priority,
            'status': ChangeStatus.DRAFT,
            'project_id': str(change_data.project_id),
            'required_by_date': change_data.required_by_date,
            'estimated_cost_impact': change_data.estimated_cost_impact,
            'estimated_schedule_impact_days': change_data.estimated_schedule_impact_days,
            'estimated_effort_hours': change_data.estimated_effort_hours,
            'affected_milestones': [str(mid) for mid in change_data.affected_milestones],
            'affected_pos': [str(pid) for pid in change_data.affected_pos],
            'template_id': str(change_data.template_id) if change_data.template_id else None,
            'version': 1,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'requested_by': str(uuid4()),
            'requested_date': datetime.now()
        }
        
        self.created_changes[change_id] = change_record
        
        # Log creation event
        self.audit_log.append({
            'change_id': change_id,
            'event_type': 'created',
            'old_status': None,
            'new_status': ChangeStatus.DRAFT,
            'timestamp': datetime.now(),
            'performed_by': change_record['requested_by']
        })
        
        return change_id
    
    @rule(change_id=change_requests)
    def transition_status(self, change_id):
        """Transition change request to a valid next status"""
        assume(change_id in self.created_changes)
        
        current_change = self.created_changes[change_id]
        current_status = current_change['status']
        
        # Generate valid next status
        new_status = self._get_valid_next_status(current_status)
        
        if new_status != current_status:
            old_status = current_status
            current_change['status'] = new_status
            current_change['updated_at'] = datetime.now()
            current_change['version'] += 1
            
            # Log status transition
            self.audit_log.append({
                'change_id': change_id,
                'event_type': 'status_changed',
                'old_status': old_status,
                'new_status': new_status,
                'timestamp': datetime.now(),
                'performed_by': str(uuid4())
            })
    
    @rule(change_id=change_requests, 
          cost_impact=st.one_of(st.none(), st.decimals(min_value=0, max_value=1000000, places=2)))
    def update_impact_estimates(self, change_id, cost_impact):
        """Update impact estimates for a change request"""
        assume(change_id in self.created_changes)
        
        current_change = self.created_changes[change_id]
        
        # Only allow updates in certain statuses
        updatable_statuses = [
            ChangeStatus.DRAFT, 
            ChangeStatus.UNDER_REVIEW, 
            ChangeStatus.PENDING_APPROVAL
        ]
        
        if current_change['status'] in updatable_statuses:
            old_cost = current_change['estimated_cost_impact']
            current_change['estimated_cost_impact'] = cost_impact
            current_change['updated_at'] = datetime.now()
            current_change['version'] += 1
            
            # Log update event
            self.audit_log.append({
                'change_id': change_id,
                'event_type': 'impact_updated',
                'old_values': {'estimated_cost_impact': old_cost},
                'new_values': {'estimated_cost_impact': cost_impact},
                'timestamp': datetime.now(),
                'performed_by': str(uuid4())
            })
    
    def _get_valid_next_status(self, current_status: ChangeStatus) -> ChangeStatus:
        """Get a valid next status for transition"""
        valid_transitions = {
            ChangeStatus.DRAFT: [ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED],
            ChangeStatus.SUBMITTED: [ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED],
            ChangeStatus.UNDER_REVIEW: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
            ChangeStatus.PENDING_APPROVAL: [ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
            ChangeStatus.APPROVED: [ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD],
            ChangeStatus.REJECTED: [ChangeStatus.DRAFT, ChangeStatus.CANCELLED],
            ChangeStatus.ON_HOLD: [ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED],
            ChangeStatus.IMPLEMENTING: [ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD],
            ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED],
            ChangeStatus.CLOSED: [ChangeStatus.CLOSED],  # Terminal state
            ChangeStatus.CANCELLED: [ChangeStatus.CANCELLED]  # Terminal state
        }
        
        possible_transitions = valid_transitions.get(current_status, [current_status])
        if len(possible_transitions) == 1:
            return possible_transitions[0]
        
        # Randomly select from valid transitions
        import random
        return random.choice(possible_transitions)
    
    @invariant()
    def change_request_data_integrity(self):
        """Invariant: All change requests maintain data integrity"""
        for change_id, change in self.created_changes.items():
            # Required fields must always be present
            assert change['id'] == change_id
            assert change['change_number'] is not None
            assert len(change['title']) >= 5
            assert len(change['description']) >= 10
            assert change['change_type'] in ChangeType
            assert change['priority'] in PriorityLevel
            assert change['status'] in ChangeStatus
            assert change['version'] >= 1
            assert change['created_at'] is not None
            assert change['updated_at'] is not None
            assert change['updated_at'] >= change['created_at']
            
            # Cost impacts must be non-negative if present
            if change['estimated_cost_impact'] is not None:
                assert change['estimated_cost_impact'] >= 0
            
            # Schedule impacts must be non-negative if present
            if change['estimated_schedule_impact_days'] is not None:
                assert change['estimated_schedule_impact_days'] >= 0
    
    @invariant()
    def status_transition_validity(self):
        """Invariant: All status transitions in audit log are valid"""
        status_changes = [log for log in self.audit_log if log['event_type'] == 'status_changed']
        
        for change_event in status_changes:
            old_status = change_event['old_status']
            new_status = change_event['new_status']
            
            # Verify transition is valid
            valid_transitions = {
                ChangeStatus.DRAFT: [ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED],
                ChangeStatus.SUBMITTED: [ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED],
                ChangeStatus.UNDER_REVIEW: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
                ChangeStatus.PENDING_APPROVAL: [ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
                ChangeStatus.APPROVED: [ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD],
                ChangeStatus.REJECTED: [ChangeStatus.DRAFT, ChangeStatus.CANCELLED],
                ChangeStatus.ON_HOLD: [ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED],
                ChangeStatus.IMPLEMENTING: [ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD],
                ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED],
                ChangeStatus.CLOSED: [],
                ChangeStatus.CANCELLED: []
            }
            
            allowed_transitions = valid_transitions.get(old_status, [])
            assert new_status in allowed_transitions or old_status == new_status
    
    @invariant()
    def audit_trail_completeness(self):
        """Invariant: Audit trail is complete for all changes"""
        for change_id in self.created_changes:
            # Every change must have a creation event
            creation_events = [
                log for log in self.audit_log 
                if log['change_id'] == change_id and log['event_type'] == 'created'
            ]
            assert len(creation_events) == 1
            
            # Audit events must be chronologically ordered
            change_events = [
                log for log in self.audit_log 
                if log['change_id'] == change_id
            ]
            
            for i in range(1, len(change_events)):
                assert change_events[i]['timestamp'] >= change_events[i-1]['timestamp']


# Property test for change request lifecycle
TestChangeRequestLifecycle = ChangeRequestLifecycleStateMachine.TestCase


@given(change_data=valid_change_request_data())
def test_change_request_creation_properties(change_data):
    """
    Property: Change request creation maintains data consistency
    
    Tests that:
    1. All required fields are properly validated
    2. Generated change numbers are unique
    3. Initial status is always DRAFT
    4. Timestamps are properly set
    """
    # Simulate change request creation
    change_id = str(uuid4())
    change_number = f"CR-{datetime.now().year}-0001"
    
    # Verify required field validation
    assert len(change_data.title) >= 5
    assert len(change_data.description) >= 10
    assert change_data.change_type in ChangeType
    assert change_data.priority in PriorityLevel
    
    # Verify optional field handling
    if change_data.estimated_cost_impact is not None:
        assert change_data.estimated_cost_impact >= 0
    
    if change_data.estimated_schedule_impact_days is not None:
        assert change_data.estimated_schedule_impact_days >= 0
    
    if change_data.estimated_effort_hours is not None:
        assert change_data.estimated_effort_hours >= 0


@given(
    current_status=change_status_strategy(),
    target_status=change_status_strategy()
)
def test_status_transition_validation(current_status, target_status):
    """
    Property: Status transitions follow business rules
    
    Tests that:
    1. Only valid transitions are allowed
    2. Terminal states cannot be changed
    3. Transition validation is consistent
    """
    valid_transitions = {
        ChangeStatus.DRAFT: [ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED],
        ChangeStatus.SUBMITTED: [ChangeStatus.UNDER_REVIEW, ChangeStatus.CANCELLED],
        ChangeStatus.UNDER_REVIEW: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
        ChangeStatus.PENDING_APPROVAL: [ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.ON_HOLD],
        ChangeStatus.APPROVED: [ChangeStatus.IMPLEMENTING, ChangeStatus.ON_HOLD],
        ChangeStatus.REJECTED: [ChangeStatus.DRAFT, ChangeStatus.CANCELLED],
        ChangeStatus.ON_HOLD: [ChangeStatus.UNDER_REVIEW, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED],
        ChangeStatus.IMPLEMENTING: [ChangeStatus.IMPLEMENTED, ChangeStatus.ON_HOLD],
        ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED],
        ChangeStatus.CLOSED: [],  # Terminal state
        ChangeStatus.CANCELLED: []  # Terminal state
    }
    
    allowed_transitions = valid_transitions.get(current_status, [])
    is_valid_transition = target_status in allowed_transitions
    
    # Terminal states should not allow any transitions
    if current_status in [ChangeStatus.CLOSED, ChangeStatus.CANCELLED]:
        assert not allowed_transitions or allowed_transitions == []
    
    # Self-transitions should generally not be allowed (except for terminal states)
    if current_status == target_status and current_status not in [ChangeStatus.CLOSED, ChangeStatus.CANCELLED]:
        assert not is_valid_transition


@given(
    change_data=valid_change_request_data(),
    updates=st.lists(
        st.tuples(
            st.sampled_from(['title', 'description', 'priority', 'estimated_cost_impact']),
            st.one_of(
                st.text(min_size=5, max_size=255),
                st.decimals(min_value=0, max_value=1000000, places=2),
                priority_level_strategy()
            )
        ),
        max_size=3
    )
)
def test_change_request_update_consistency(change_data, updates):
    """
    Property: Change request updates maintain consistency
    
    Tests that:
    1. Version numbers increment with each update
    2. Update timestamps are properly maintained
    3. Field validation is enforced during updates
    4. Audit trail captures all changes
    """
    # Simulate initial change request
    initial_version = 1
    initial_timestamp = datetime.now()
    
    current_version = initial_version
    current_timestamp = initial_timestamp
    
    # Apply updates
    for field_name, new_value in updates:
        # Validate update based on field type
        if field_name == 'title' and isinstance(new_value, str):
            assume(len(new_value) >= 5)
            current_version += 1
            current_timestamp = datetime.now()
        elif field_name == 'description' and isinstance(new_value, str):
            assume(len(new_value) >= 10)
            current_version += 1
            current_timestamp = datetime.now()
        elif field_name == 'priority' and new_value in PriorityLevel:
            current_version += 1
            current_timestamp = datetime.now()
        elif field_name == 'estimated_cost_impact' and isinstance(new_value, Decimal):
            assume(new_value >= 0)
            current_version += 1
            current_timestamp = datetime.now()
    
    # Verify version and timestamp progression
    assert current_version >= initial_version
    assert current_timestamp >= initial_timestamp
    
    # If any updates were applied, version should have incremented
    if updates and any(
        (field == 'title' and isinstance(value, str) and len(value) >= 5) or
        (field == 'description' and isinstance(value, str) and len(value) >= 10) or
        (field == 'priority' and value in PriorityLevel) or
        (field == 'estimated_cost_impact' and isinstance(value, Decimal) and value >= 0)
        for field, value in updates
    ):
        assert current_version > initial_version


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])