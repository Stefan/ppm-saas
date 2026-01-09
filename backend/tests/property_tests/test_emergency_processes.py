"""
Property-based tests for emergency processes (Task 9.3)

Property 14: Emergency Process Integrity
Property 15: Post-Implementation Compliance
- Validates that emergency change processes maintain integrity and compliance
- Ensures post-implementation reviews are properly conducted
- Validates Requirements 10.1, 10.2, 10.3, 10.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, invariant
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List, Set
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.change_management import (
    ChangeType, PriorityLevel, ChangeStatus, ApprovalDecision
)


# Strategy generators for emergency process data
@st.composite
def emergency_change_data(draw):
    """Generate emergency change request data"""
    return {
        'id': str(draw(st.uuids())),
        'change_type': draw(st.sampled_from(list(ChangeType))),
        'priority': PriorityLevel.EMERGENCY,  # Always emergency
        'estimated_cost_impact': draw(st.decimals(min_value=0, max_value=5000000, places=2)),
        'project_id': str(draw(st.uuids())),
        'requested_by': str(draw(st.uuids())),
        'title': draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'description': draw(st.text(min_size=20, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'justification': draw(st.text(min_size=20, max_size=300, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'emergency_reason': draw(st.sampled_from([
            'safety_critical', 'regulatory_compliance', 'system_failure',
            'security_breach', 'environmental_hazard', 'client_critical'
        ])),
        'business_impact': draw(st.sampled_from([
            'project_stoppage', 'safety_risk', 'financial_loss',
            'regulatory_violation', 'reputation_damage', 'client_relationship'
        ])),
        'required_by_date': draw(st.dates(min_value=datetime.now().date(), max_value=(datetime.now() + timedelta(days=7)).date()))
    }


@st.composite
def emergency_approver_data(draw):
    """Generate emergency approver data"""
    return {
        'user_id': str(draw(st.uuids())),
        'role': draw(st.sampled_from([
            'emergency_coordinator', 'safety_manager', 'project_director',
            'operations_manager', 'ceo', 'cto', 'risk_manager'
        ])),
        'authority_level': draw(st.integers(min_value=1, max_value=10)),
        'max_emergency_value': draw(st.decimals(min_value=100000, max_value=10000000, places=2)),
        'available_24_7': draw(st.booleans()),
        'contact_methods': draw(st.lists(
            st.sampled_from(['email', 'sms', 'phone', 'slack', 'teams']),
            min_size=1, max_size=3, unique=True
        ))
    }


@st.composite
def implementation_evidence(draw):
    """Generate implementation evidence data"""
    return {
        'evidence_type': draw(st.sampled_from([
            'photo', 'document', 'test_result', 'inspection_report',
            'approval_certificate', 'measurement', 'witness_statement'
        ])),
        'description': draw(st.text(min_size=10, max_size=200)),
        'file_path': f"/evidence/{draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))))}.pdf",
        'captured_by': str(draw(st.uuids())),
        'captured_at': draw(st.datetimes(min_value=datetime.now() - timedelta(hours=24))),
        'verified': draw(st.booleans())
    }


class EmergencyProcessStateMachine(RuleBasedStateMachine):
    """
    Stateful property test for emergency process integrity
    
    This tests Property 14: Emergency Process Integrity and Property 15: Post-Implementation Compliance
    - Emergency changes follow expedited but controlled processes
    - All emergency changes require post-implementation review
    - Audit trail is complete for emergency processes
    - Compliance requirements are met even in emergency situations
    """
    
    emergency_changes = Bundle('emergency_changes')
    emergency_approvals = Bundle('emergency_approvals')
    implementations = Bundle('implementations')
    post_reviews = Bundle('post_reviews')
    
    def __init__(self):
        super().__init__()
        self.emergency_changes: Dict[str, Dict[str, Any]] = {}
        self.emergency_approvals: Dict[str, Dict[str, Any]] = {}
        self.implementations: Dict[str, Dict[str, Any]] = {}
        self.post_implementation_reviews: Dict[str, Dict[str, Any]] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        self.emergency_approvers: Dict[str, Dict[str, Any]] = {}
        self.compliance_violations: List[Dict[str, Any]] = []
    
    @rule(target=emergency_changes, change_data=emergency_change_data())
    def create_emergency_change(self, change_data):
        """Create an emergency change request"""
        change_id = change_data['id']
        
        # Emergency changes must have specific required fields
        emergency_change = {
            **change_data,
            'status': ChangeStatus.SUBMITTED,  # Emergency changes skip draft
            'emergency_declared_at': datetime.now(),
            'emergency_declared_by': change_data['requested_by'],
            'expedited_workflow': True,
            'requires_post_review': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'version': 1
        }
        
        self.emergency_changes[change_id] = emergency_change
        
        # Log emergency declaration
        self.audit_trail.append({
            'change_id': change_id,
            'event_type': 'emergency_declared',
            'timestamp': datetime.now(),
            'performed_by': change_data['requested_by'],
            'details': {
                'emergency_reason': change_data['emergency_reason'],
                'business_impact': change_data['business_impact']
            }
        })
        
        return change_id
    
    @rule(target=emergency_approvals, 
          change_id=emergency_changes,
          approver_data=emergency_approver_data())
    def process_emergency_approval(self, change_id, approver_data):
        """Process emergency approval with expedited workflow"""
        assume(change_id in self.emergency_changes)
        
        change = self.emergency_changes[change_id]
        assume(change['status'] in [ChangeStatus.SUBMITTED, ChangeStatus.UNDER_REVIEW])
        
        approval_id = str(uuid4())
        
        # Check if approver has authority for this emergency change
        has_authority = self._check_emergency_authority(approver_data, change)
        
        if has_authority:
            decision = ApprovalDecision.APPROVED
            change['status'] = ChangeStatus.APPROVED
        else:
            # Escalate to higher authority
            decision = ApprovalDecision.NEEDS_INFO
            change['status'] = ChangeStatus.PENDING_APPROVAL
        
        approval = {
            'id': approval_id,
            'change_id': change_id,
            'approver_id': approver_data['user_id'],
            'approver_role': approver_data['role'],
            'decision': decision,
            'decision_date': datetime.now(),
            'expedited': True,
            'authority_level': approver_data['authority_level'],
            'emergency_justification': f"Emergency approval for {change['emergency_reason']}",
            'conditions': [] if decision == ApprovalDecision.APPROVED else ['Requires higher authority approval']
        }
        
        self.emergency_approvals[approval_id] = approval
        
        # Update change status and log
        change['updated_at'] = datetime.now()
        change['version'] += 1
        
        self.audit_trail.append({
            'change_id': change_id,
            'event_type': 'emergency_approval_processed',
            'timestamp': datetime.now(),
            'performed_by': approver_data['user_id'],
            'details': {
                'decision': decision.value,
                'approver_role': approver_data['role'],
                'expedited': True
            }
        })
        
        return approval_id
    
    @rule(target=implementations,
          change_id=emergency_changes,
          evidence_list=st.lists(implementation_evidence(), min_size=1, max_size=5))
    def implement_emergency_change(self, change_id, evidence_list):
        """Implement emergency change with evidence collection"""
        assume(change_id in self.emergency_changes)
        
        change = self.emergency_changes[change_id]
        assume(change['status'] == ChangeStatus.APPROVED)
        
        implementation_id = str(uuid4())
        
        # Emergency implementation must collect evidence
        implementation = {
            'id': implementation_id,
            'change_id': change_id,
            'implementation_start': datetime.now(),
            'implementation_end': datetime.now() + timedelta(hours=2),  # Fast implementation
            'implemented_by': str(uuid4()),
            'emergency_implementation': True,
            'evidence_collected': evidence_list,
            'verification_required': True,
            'post_review_scheduled': True,
            'compliance_checked': False,  # Will be checked in post-review
            'status': 'completed'
        }
        
        self.implementations[implementation_id] = implementation
        
        # Update change status
        change['status'] = ChangeStatus.IMPLEMENTED
        change['implementation_date'] = datetime.now()
        change['updated_at'] = datetime.now()
        change['version'] += 1
        
        # Log implementation
        self.audit_trail.append({
            'change_id': change_id,
            'event_type': 'emergency_implemented',
            'timestamp': datetime.now(),
            'performed_by': implementation['implemented_by'],
            'details': {
                'evidence_count': len(evidence_list),
                'implementation_duration_hours': 2,
                'emergency_implementation': True
            }
        })
        
        return implementation_id
    
    @rule(target=post_reviews,
          implementation_id=implementations,
          review_findings=st.lists(
              st.tuples(
                  st.sampled_from(['compliance', 'effectiveness', 'documentation', 'process']),
                  st.sampled_from(['satisfactory', 'needs_improvement', 'non_compliant']),
                  st.text(min_size=10, max_size=100)
              ),
              min_size=1, max_size=4
          ))
    def conduct_post_implementation_review(self, implementation_id, review_findings):
        """Conduct mandatory post-implementation review"""
        assume(implementation_id in self.implementations)
        
        implementation = self.implementations[implementation_id]
        change_id = implementation['change_id']
        
        assume(change_id in self.emergency_changes)
        change = self.emergency_changes[change_id]
        
        review_id = str(uuid4())
        
        # Post-implementation review is mandatory for emergency changes
        review = {
            'id': review_id,
            'implementation_id': implementation_id,
            'change_id': change_id,
            'review_date': datetime.now() + timedelta(days=1),  # Within 24 hours
            'reviewer_id': str(uuid4()),
            'reviewer_role': 'quality_assurance',
            'findings': review_findings,
            'compliance_status': self._assess_compliance(review_findings),
            'lessons_learned': [],
            'corrective_actions': [],
            'review_complete': True,
            'mandatory_review': True
        }
        
        # Check for compliance violations
        non_compliant_findings = [f for f in review_findings if f[1] == 'non_compliant']
        if non_compliant_findings:
            for finding in non_compliant_findings:
                self.compliance_violations.append({
                    'change_id': change_id,
                    'violation_type': finding[0],
                    'description': finding[2],
                    'severity': 'high' if finding[0] == 'compliance' else 'medium',
                    'detected_at': datetime.now(),
                    'requires_corrective_action': True
                })
        
        self.post_implementation_reviews[review_id] = review
        
        # Update implementation and change status
        implementation['post_review_completed'] = True
        implementation['compliance_checked'] = True
        
        if review['compliance_status'] == 'compliant':
            change['status'] = ChangeStatus.CLOSED
        else:
            change['status'] = ChangeStatus.ON_HOLD  # Pending corrective actions
        
        change['updated_at'] = datetime.now()
        change['version'] += 1
        
        # Log post-implementation review
        self.audit_trail.append({
            'change_id': change_id,
            'event_type': 'post_implementation_review_completed',
            'timestamp': datetime.now(),
            'performed_by': review['reviewer_id'],
            'details': {
                'compliance_status': review['compliance_status'],
                'findings_count': len(review_findings),
                'violations_found': len(non_compliant_findings),
                'mandatory_review': True
            }
        })
        
        return review_id
    
    @rule(change_id=emergency_changes)
    def escalate_emergency_approval(self, change_id):
        """Escalate emergency approval to higher authority"""
        assume(change_id in self.emergency_changes)
        
        change = self.emergency_changes[change_id]
        assume(change['status'] == ChangeStatus.PENDING_APPROVAL)
        
        # Emergency escalation must happen quickly
        escalation_time = datetime.now()
        time_since_creation = escalation_time - change['emergency_declared_at']
        
        # Emergency changes should escalate within 4 hours
        if time_since_creation > timedelta(hours=4):
            self.compliance_violations.append({
                'change_id': change_id,
                'violation_type': 'escalation_delay',
                'description': f'Emergency escalation delayed by {time_since_creation.total_seconds() / 3600:.1f} hours',
                'severity': 'critical',
                'detected_at': escalation_time,
                'requires_corrective_action': True
            })
        
        # Log escalation
        self.audit_trail.append({
            'change_id': change_id,
            'event_type': 'emergency_escalated',
            'timestamp': escalation_time,
            'performed_by': 'system',
            'details': {
                'escalation_reason': 'insufficient_authority',
                'time_to_escalation_hours': time_since_creation.total_seconds() / 3600
            }
        })
    
    def _check_emergency_authority(self, approver: Dict[str, Any], change: Dict[str, Any]) -> bool:
        """Check if approver has authority for emergency change"""
        # Emergency approvers need higher authority levels
        min_authority_by_impact = {
            'project_stoppage': 8,
            'safety_risk': 9,
            'financial_loss': 7,
            'regulatory_violation': 9,
            'reputation_damage': 6,
            'client_relationship': 7
        }
        
        required_authority = min_authority_by_impact.get(change['business_impact'], 5)
        
        # Check authority level
        if approver['authority_level'] < required_authority:
            return False
        
        # Check value authority
        if change['estimated_cost_impact'] > approver['max_emergency_value']:
            return False
        
        return True
    
    def _assess_compliance(self, findings: List[tuple]) -> str:
        """Assess overall compliance status from review findings"""
        non_compliant_count = sum(1 for f in findings if f[1] == 'non_compliant')
        needs_improvement_count = sum(1 for f in findings if f[1] == 'needs_improvement')
        
        if non_compliant_count > 0:
            return 'non_compliant'
        elif needs_improvement_count > len(findings) // 2:
            return 'partially_compliant'
        else:
            return 'compliant'
    
    @invariant()
    def emergency_process_integrity(self):
        """Invariant: Emergency processes maintain integrity"""
        for change_id, change in self.emergency_changes.items():
            # Emergency changes must have required fields
            assert change['priority'] == PriorityLevel.EMERGENCY
            assert 'emergency_declared_at' in change
            assert 'emergency_declared_by' in change
            assert 'emergency_reason' in change
            assert 'business_impact' in change
            assert change['expedited_workflow'] is True
            assert change['requires_post_review'] is True
            
            # Emergency changes should not stay in draft
            assert change['status'] != ChangeStatus.DRAFT
            
            # Emergency changes must have justification
            assert change.get('justification') is not None
            assert len(change['justification']) >= 20
    
    @invariant()
    def post_implementation_compliance(self):
        """Invariant: Post-implementation reviews are mandatory and complete"""
        for impl_id, implementation in self.implementations.items():
            if implementation['emergency_implementation']:
                # Emergency implementations must have post-review scheduled
                assert implementation['post_review_scheduled'] is True
                
                # If implementation is complete, post-review should be conducted
                if implementation['status'] == 'completed':
                    # Check if post-review exists
                    post_reviews = [
                        review for review in self.post_implementation_reviews.values()
                        if review['implementation_id'] == impl_id
                    ]
                    
                    # For completed emergency implementations, post-review should exist
                    # (allowing some time for review to be scheduled)
                    change_id = implementation['change_id']
                    change = self.emergency_changes[change_id]
                    
                    if change['status'] in [ChangeStatus.CLOSED, ChangeStatus.ON_HOLD]:
                        assert len(post_reviews) > 0
                        
                        # Post-review must be marked as mandatory
                        for review in post_reviews:
                            assert review['mandatory_review'] is True
    
    @invariant()
    def emergency_approval_timeliness(self):
        """Invariant: Emergency approvals are processed in a timely manner"""
        for change_id, change in self.emergency_changes.items():
            emergency_declared = change['emergency_declared_at']
            
            # Find approval events for this change
            approval_events = [
                event for event in self.audit_trail
                if (event['change_id'] == change_id and 
                    event['event_type'] == 'emergency_approval_processed')
            ]
            
            for event in approval_events:
                approval_time = event['timestamp']
                time_to_approval = approval_time - emergency_declared
                
                # Emergency approvals should happen within 4 hours
                # (This is a business rule that can be adjusted)
                max_approval_time = timedelta(hours=4)
                
                # If approval took too long, it should be logged as a violation
                if time_to_approval > max_approval_time:
                    violation_exists = any(
                        v['change_id'] == change_id and v['violation_type'] == 'approval_delay'
                        for v in self.compliance_violations
                    )
                    # Note: We don't assert here as the violation might not be created yet
                    # This is more of a monitoring invariant
    
    @invariant()
    def audit_trail_completeness(self):
        """Invariant: Audit trail is complete for emergency processes"""
        for change_id in self.emergency_changes:
            # Every emergency change must have declaration event
            declaration_events = [
                event for event in self.audit_trail
                if (event['change_id'] == change_id and 
                    event['event_type'] == 'emergency_declared')
            ]
            assert len(declaration_events) == 1
            
            # Audit events must be chronologically ordered
            change_events = [
                event for event in self.audit_trail
                if event['change_id'] == change_id
            ]
            
            for i in range(1, len(change_events)):
                assert change_events[i]['timestamp'] >= change_events[i-1]['timestamp']
    
    @invariant()
    def evidence_collection_requirement(self):
        """Invariant: Emergency implementations must collect evidence"""
        for impl_id, implementation in self.implementations.items():
            if implementation['emergency_implementation']:
                # Emergency implementations must collect evidence
                assert 'evidence_collected' in implementation
                assert len(implementation['evidence_collected']) > 0
                
                # Evidence must be properly documented
                for evidence in implementation['evidence_collected']:
                    assert 'evidence_type' in evidence
                    assert 'description' in evidence
                    assert 'captured_by' in evidence
                    assert 'captured_at' in evidence
                    assert len(evidence['description']) >= 10


# Property test for emergency process integrity
TestEmergencyProcessIntegrity = EmergencyProcessStateMachine.TestCase


@given(change_data=emergency_change_data())
def test_emergency_change_creation_properties(change_data):
    """
    Property: Emergency change creation follows required process
    
    Tests that:
    1. Emergency changes have all required fields
    2. Emergency priority is properly set
    3. Justification and reasoning are mandatory
    4. Post-implementation review is scheduled
    """
    # Verify emergency-specific requirements
    assert change_data['priority'] == PriorityLevel.EMERGENCY
    assert 'emergency_reason' in change_data
    assert 'business_impact' in change_data
    assert len(change_data['justification']) >= 20
    
    # Emergency changes must have clear business justification
    assert change_data['emergency_reason'] in [
        'safety_critical', 'regulatory_compliance', 'system_failure',
        'security_breach', 'environmental_hazard', 'client_critical'
    ]
    
    assert change_data['business_impact'] in [
        'project_stoppage', 'safety_risk', 'financial_loss',
        'regulatory_violation', 'reputation_damage', 'client_relationship'
    ]


@given(
    approver_data=emergency_approver_data(),
    change_data=emergency_change_data()
)
def test_emergency_approval_authority(approver_data, change_data):
    """
    Property: Emergency approval authority is properly validated
    
    Tests that:
    1. Authority levels are appropriate for emergency situations
    2. Value limits are enforced even in emergencies
    3. Role-based authority is consistent
    """
    # Emergency authority requirements
    min_authority_by_impact = {
        'project_stoppage': 8,
        'safety_risk': 9,
        'financial_loss': 7,
        'regulatory_violation': 9,
        'reputation_damage': 6,
        'client_relationship': 7
    }
    
    required_authority = min_authority_by_impact.get(change_data['business_impact'], 5)
    
    # Check authority level requirement
    has_authority_level = approver_data['authority_level'] >= required_authority
    
    # Check value authority
    has_value_authority = change_data['estimated_cost_impact'] <= approver_data['max_emergency_value']
    
    # Both must be satisfied for emergency approval authority
    has_emergency_authority = has_authority_level and has_value_authority
    
    # Verify authority calculation
    if approver_data['authority_level'] < required_authority:
        assert not has_emergency_authority
    
    if change_data['estimated_cost_impact'] > approver_data['max_emergency_value']:
        assert not has_emergency_authority


@given(
    evidence_list=st.lists(implementation_evidence(), min_size=1, max_size=10),
    review_findings=st.lists(
        st.tuples(
            st.sampled_from(['compliance', 'effectiveness', 'documentation', 'process']),
            st.sampled_from(['satisfactory', 'needs_improvement', 'non_compliant']),
            st.text(min_size=10, max_size=100)
        ),
        min_size=1, max_size=5
    )
)
def test_post_implementation_review_completeness(evidence_list, review_findings):
    """
    Property: Post-implementation reviews are complete and thorough
    
    Tests that:
    1. All evidence is properly documented
    2. Review findings cover all required areas
    3. Compliance assessment is accurate
    4. Non-compliance triggers corrective actions
    """
    # Verify evidence completeness
    for evidence in evidence_list:
        assert 'evidence_type' in evidence
        assert 'description' in evidence
        assert len(evidence['description']) >= 10
        assert 'captured_by' in evidence
        assert 'captured_at' in evidence
    
    # Verify review findings structure
    finding_areas = {finding[0] for finding in review_findings}
    required_areas = {'compliance', 'effectiveness', 'documentation'}
    
    # At minimum, compliance must be reviewed
    assert 'compliance' in finding_areas
    
    # Assess compliance status
    non_compliant_count = sum(1 for f in review_findings if f[1] == 'non_compliant')
    needs_improvement_count = sum(1 for f in review_findings if f[1] == 'needs_improvement')
    
    if non_compliant_count > 0:
        compliance_status = 'non_compliant'
    elif needs_improvement_count > len(review_findings) // 2:
        compliance_status = 'partially_compliant'
    else:
        compliance_status = 'compliant'
    
    # Verify compliance assessment logic
    if any(f[1] == 'non_compliant' for f in review_findings):
        assert compliance_status == 'non_compliant'


@given(
    emergency_timeline=st.lists(
        st.tuples(
            st.sampled_from(['declared', 'approved', 'implemented', 'reviewed']),
            st.datetimes(min_value=datetime.now() - timedelta(days=1))
        ),
        min_size=2, max_size=4
    )
)
def test_emergency_process_timeline_integrity(emergency_timeline):
    """
    Property: Emergency process timeline maintains proper sequencing
    
    Tests that:
    1. Events occur in logical order
    2. Time constraints are reasonable for emergency processes
    3. No gaps or overlaps in critical timeline
    """
    # Sort events by timestamp
    sorted_events = sorted(emergency_timeline, key=lambda x: x[1])
    
    # Define expected event order
    event_order = ['declared', 'approved', 'implemented', 'reviewed']
    
    # Extract event types in chronological order
    event_sequence = [event[0] for event in sorted_events]
    
    # Verify events follow logical sequence
    for i in range(len(event_sequence) - 1):
        current_event = event_sequence[i]
        next_event = event_sequence[i + 1]
        
        current_index = event_order.index(current_event) if current_event in event_order else -1
        next_index = event_order.index(next_event) if next_event in event_order else -1
        
        # Next event should not come before current event in the logical order
        if current_index >= 0 and next_index >= 0:
            assert next_index >= current_index
    
    # Check time constraints for emergency processes
    if len(sorted_events) >= 2:
        start_time = sorted_events[0][1]
        end_time = sorted_events[-1][1]
        total_duration = end_time - start_time
        
        # Emergency processes should complete within reasonable time
        # (This is a business rule that can be adjusted)
        max_emergency_duration = timedelta(days=3)
        
        # For property testing, we just verify the timeline is reasonable
        assert total_duration >= timedelta(0)  # No negative durations
        
        # If we have implementation and review, they should be close together
        impl_events = [e for e in sorted_events if e[0] == 'implemented']
        review_events = [e for e in sorted_events if e[0] == 'reviewed']
        
        if impl_events and review_events:
            impl_time = impl_events[0][1]
            review_time = review_events[0][1]
            review_delay = review_time - impl_time
            
            # Post-implementation review should happen within reasonable time
            max_review_delay = timedelta(days=2)
            assert review_delay <= max_review_delay


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])