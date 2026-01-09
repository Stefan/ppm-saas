"""
Property-based tests for approval workflow functionality.

These tests validate universal correctness properties for multi-level approval workflows
using pytest and Hypothesis to ensure comprehensive coverage across all possible
approval scenarios.

Feature: integrated-change-management
Task: 3.4 Write property tests for approval workflows
Requirements: 2.1, 2.2, 2.4, 2.5
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from decimal import Decimal
from enum import Enum

class ApprovalDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"
    DELEGATED = "delegated"

class WorkflowType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

class ChangeType(Enum):
    SCOPE = "scope"
    SCHEDULE = "schedule"
    BUDGET = "budget"
    DESIGN = "design"
    REGULATORY = "regulatory"

@st.composite
def approval_step_data(draw):
    """Generate approval step data for testing."""
    roles = ['project_manager', 'technical_lead', 'finance_manager', 'client_representative', 'executive']
    return {
        'step_number': draw(st.integers(min_value=1, max_value=10)),
        'approver_role': draw(st.sampled_from(roles)),
        'approver_id': draw(st.uuids()),
        'is_required': draw(st.booleans()),
        'is_parallel': draw(st.booleans()),
        'depends_on_step': draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5))),
        'authority_limit': draw(st.decimals(min_value=1000, max_value=1000000, places=2)),
        'due_date': datetime.now(timezone.utc) + timedelta(days=draw(st.integers(min_value=1, max_value=14)))
    }

@st.composite
def change_request_data(draw):
    """Generate change request data for approval testing."""
    return {
        'id': draw(st.uuids()),
        'change_number': f"CR-2024-{draw(st.integers(min_value=1000, max_value=9999))}",
        'title': draw(st.text(min_size=10, max_size=100)),
        'description': draw(st.text(min_size=20, max_size=500)),
        'change_type': draw(st.sampled_from(list(ChangeType))),
        'estimated_cost_impact': draw(st.decimals(min_value=0, max_value=1000000, places=2)),
        'estimated_schedule_impact_days': draw(st.integers(min_value=0, max_value=365)),
        'project_phase': draw(st.sampled_from(['planning', 'design', 'construction', 'testing', 'closure'])),
        'requested_by': draw(st.uuids()),
        'project_id': draw(st.uuids())
    }

@st.composite
def workflow_configuration(draw):
    """Generate workflow configuration for testing."""
    return {
        'workflow_type': draw(st.sampled_from(list(WorkflowType))),
        'cost_thresholds': {
            'low': draw(st.decimals(min_value=1000, max_value=10000, places=2)),
            'medium': draw(st.decimals(min_value=10000, max_value=100000, places=2)),
            'high': draw(st.decimals(min_value=100000, max_value=1000000, places=2))
        },
        'phase_requirements': {
            'planning': ['project_manager'],
            'design': ['project_manager', 'technical_lead'],
            'construction': ['project_manager', 'technical_lead', 'finance_manager'],
            'testing': ['project_manager', 'technical_lead'],
            'closure': ['project_manager', 'client_representative']
        },
        'parallel_approval_roles': ['technical_lead', 'finance_manager'],
        'mandatory_roles': ['project_manager']
    }

class MockApprovalWorkflowEngine:
    """Mock approval workflow engine for property testing."""
    
    def __init__(self):
        self.workflows: Dict[UUID, Dict[str, Any]] = {}
        self.approval_steps: Dict[UUID, List[Dict[str, Any]]] = {}
        self.approval_decisions: List[Dict[str, Any]] = []
        self.workflow_configs: Dict[str, Any] = {}
    
    def determine_approval_path(self, change_request: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine required approval path based on change characteristics."""
        cost_impact = change_request['estimated_cost_impact']
        project_phase = change_request['project_phase']
        change_type = change_request['change_type']
        
        # Determine cost threshold level
        if cost_impact <= config['cost_thresholds']['low']:
            threshold_level = 'low'
        elif cost_impact <= config['cost_thresholds']['medium']:
            threshold_level = 'medium'
        else:
            threshold_level = 'high'
        
        # Get base approvers for project phase
        base_approvers = config['phase_requirements'].get(project_phase, ['project_manager'])
        
        # Add additional approvers based on cost threshold
        required_approvers = base_approvers.copy()
        if threshold_level in ['medium', 'high']:
            required_approvers.append('finance_manager')
        if threshold_level == 'high':
            required_approvers.append('executive')
        
        # Create approval steps
        approval_steps = []
        for i, role in enumerate(required_approvers, 1):
            step = {
                'step_number': i,
                'approver_role': role,
                'is_required': role in config['mandatory_roles'] or threshold_level == 'high',
                'is_parallel': role in config.get('parallel_approval_roles', []),
                'authority_limit': config['cost_thresholds'][threshold_level],
                'depends_on_step': None if i == 1 else (i - 1 if role not in config.get('parallel_approval_roles', []) else 1)
            }
            approval_steps.append(step)
        
        return approval_steps
    
    def initiate_approval_workflow(self, change_id: UUID, change_request: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate approval workflow for a change request."""
        # Determine approval path
        approval_steps = self.determine_approval_path(change_request, config)
        
        # Create workflow instance
        workflow = {
            'id': uuid4(),
            'change_id': change_id,
            'workflow_type': config['workflow_type'],
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'total_steps': len(approval_steps),
            'completed_steps': 0,
            'current_step': 1 if approval_steps else None
        }
        
        # Store workflow and steps
        self.workflows[change_id] = workflow
        self.approval_steps[change_id] = approval_steps
        
        return {
            'workflow_id': workflow['id'],
            'total_steps': len(approval_steps),
            'approval_path': approval_steps,
            'workflow_initiated': True
        }
    
    def process_approval_decision(self, change_id: UUID, step_number: int, approver_id: UUID, decision: ApprovalDecision, comments: str = "") -> Dict[str, Any]:
        """Process an approval decision for a specific step."""
        if change_id not in self.workflows:
            raise ValueError("Workflow not found for change request")
        
        workflow = self.workflows[change_id]
        steps = self.approval_steps[change_id]
        
        # Find the approval step
        step = next((s for s in steps if s['step_number'] == step_number), None)
        if not step:
            raise ValueError(f"Approval step {step_number} not found")
        
        # Validate approver authority
        change_request = {'estimated_cost_impact': step['authority_limit']}  # Simplified for testing
        if not self.check_approval_authority(approver_id, change_request['estimated_cost_impact'], step['approver_role']):
            raise ValueError("Approver lacks sufficient authority")
        
        # Record approval decision
        approval_record = {
            'id': uuid4(),
            'change_id': change_id,
            'step_number': step_number,
            'approver_id': approver_id,
            'approver_role': step['approver_role'],
            'decision': decision,
            'comments': comments,
            'decision_date': datetime.now(timezone.utc),
            'is_required': step['is_required']
        }
        self.approval_decisions.append(approval_record)
        
        # Update workflow progress
        if decision == ApprovalDecision.APPROVED:
            workflow['completed_steps'] += 1
            
            # Check if workflow is complete
            required_steps = [s for s in steps if s['is_required']]
            completed_required = [
                d for d in self.approval_decisions 
                if d['change_id'] == change_id and d['decision'] == ApprovalDecision.APPROVED and d['is_required']
            ]
            
            if len(completed_required) >= len(required_steps):
                workflow['status'] = 'completed'
                workflow['completed_at'] = datetime.now(timezone.utc)
            else:
                # Advance to next step
                workflow['current_step'] = self._get_next_step(change_id, step_number)
        
        elif decision == ApprovalDecision.REJECTED:
            workflow['status'] = 'rejected'
            workflow['rejected_at'] = datetime.now(timezone.utc)
        
        return {
            'approval_id': approval_record['id'],
            'decision': decision,
            'workflow_status': workflow['status'],
            'next_step': workflow.get('current_step'),
            'workflow_complete': workflow['status'] in ['completed', 'rejected']
        }
    
    def check_approval_authority(self, approver_id: UUID, change_value: Decimal, approver_role: str) -> bool:
        """Check if approver has sufficient authority for the change value."""
        # Simplified authority check for testing
        authority_limits = {
            'project_manager': Decimal('50000'),
            'technical_lead': Decimal('25000'),
            'finance_manager': Decimal('100000'),
            'client_representative': Decimal('75000'),
            'executive': Decimal('1000000')
        }
        
        limit = authority_limits.get(approver_role, Decimal('0'))
        return change_value <= limit
    
    def get_pending_approvals(self, change_id: UUID) -> List[Dict[str, Any]]:
        """Get pending approval steps for a change request."""
        if change_id not in self.workflows:
            return []
        
        workflow = self.workflows[change_id]
        if workflow['status'] != 'active':
            return []
        
        steps = self.approval_steps[change_id]
        completed_decisions = {
            d['step_number'] for d in self.approval_decisions 
            if d['change_id'] == change_id and d['decision'] == ApprovalDecision.APPROVED
        }
        
        pending_steps = []
        for step in steps:
            if step['step_number'] not in completed_decisions:
                # Check if dependencies are met
                if step['depends_on_step'] is None or step['depends_on_step'] in completed_decisions:
                    pending_steps.append(step)
        
        return pending_steps
    
    def _get_next_step(self, change_id: UUID, current_step: int) -> Optional[int]:
        """Get the next step number in the workflow."""
        steps = self.approval_steps[change_id]
        completed_decisions = {
            d['step_number'] for d in self.approval_decisions 
            if d['change_id'] == change_id and d['decision'] == ApprovalDecision.APPROVED
        }
        
        # Find next available step
        for step in steps:
            if (step['step_number'] not in completed_decisions and 
                (step['depends_on_step'] is None or step['depends_on_step'] in completed_decisions)):
                return step['step_number']
        
        return None


# Property 4: Approval Workflow Integrity
@given(
    change_request=change_request_data(),
    workflow_config=workflow_configuration()
)
def test_approval_workflow_integrity_property(change_request, workflow_config):
    """
    Property 4: Approval Workflow Integrity
    
    For any change request submission, the approval workflow must be determined
    based on change characteristics and configured rules with proper step sequencing.
    
    Validates: Requirements 2.1, 2.2
    """
    # Arrange
    engine = MockApprovalWorkflowEngine()
    change_id = change_request['id']
    
    # Act - Initiate approval workflow
    result = engine.initiate_approval_workflow(change_id, change_request, workflow_config)
    
    # Assert - Workflow integrity properties
    
    # Property: Workflow must be successfully initiated
    assert result['workflow_initiated'] is True, \
        "Approval workflow must be successfully initiated for valid change requests"
    
    # Property: Approval path must be determined based on change characteristics
    approval_path = result['approval_path']
    assert len(approval_path) > 0, \
        "Approval path must contain at least one approval step"
    
    # Property: Step numbers must be sequential and unique
    step_numbers = [step['step_number'] for step in approval_path]
    assert step_numbers == sorted(set(step_numbers)), \
        "Approval step numbers must be sequential and unique"
    
    # Property: Required approvers must be included based on cost impact
    cost_impact = change_request['estimated_cost_impact']
    approver_roles = [step['approver_role'] for step in approval_path]
    
    # High-cost changes must include finance manager
    if cost_impact > workflow_config['cost_thresholds']['medium']:
        assert 'finance_manager' in approver_roles, \
            "High-cost changes must include finance manager approval"
    
    # Very high-cost changes must include executive
    if cost_impact > workflow_config['cost_thresholds']['high']:
        assert 'executive' in approver_roles, \
            "Very high-cost changes must include executive approval"
    
    # Property: Mandatory roles must be marked as required
    mandatory_roles = workflow_config.get('mandatory_roles', [])
    for step in approval_path:
        if step['approver_role'] in mandatory_roles:
            assert step['is_required'] is True, \
                f"Mandatory role {step['approver_role']} must be marked as required"
    
    # Property: Workflow must be stored and trackable
    assert change_id in engine.workflows, \
        "Workflow must be stored for tracking and management"
    
    stored_workflow = engine.workflows[change_id]
    assert stored_workflow['status'] == 'active', \
        "New workflow must have active status"
    assert stored_workflow['total_steps'] == len(approval_path), \
        "Stored workflow must track correct number of steps"


# Property 5: Authority Validation Consistency
@given(
    change_requests=st.lists(change_request_data(), min_size=2, max_size=5),
    approvers=st.lists(
        st.tuples(st.uuids(), st.sampled_from(['project_manager', 'technical_lead', 'finance_manager', 'executive'])),
        min_size=3, max_size=8
    )
)
def test_authority_validation_consistency_property(change_requests, approvers):
    """
    Property 5: Authority Validation Consistency
    
    For any approval decision, authority limits must be enforced consistently
    based on user roles and change request value thresholds.
    
    Validates: Requirements 2.4, 2.5
    """
    # Arrange
    engine = MockApprovalWorkflowEngine()
    
    # Test authority validation for each combination
    for change_request in change_requests:
        cost_impact = change_request['estimated_cost_impact']
        
        for approver_id, approver_role in approvers:
            # Act - Check approval authority
            has_authority = engine.check_approval_authority(approver_id, cost_impact, approver_role)
            
            # Assert - Authority validation properties
            
            # Property: Authority must be consistent with role limits
            authority_limits = {
                'project_manager': Decimal('50000'),
                'technical_lead': Decimal('25000'),
                'finance_manager': Decimal('100000'),
                'client_representative': Decimal('75000'),
                'executive': Decimal('1000000')
            }
            
            expected_limit = authority_limits.get(approver_role, Decimal('0'))
            expected_authority = cost_impact <= expected_limit
            
            assert has_authority == expected_authority, \
                f"Authority validation must be consistent: {approver_role} with limit {expected_limit} " \
                f"for change value {cost_impact} should be {expected_authority}"
            
            # Property: Higher roles must have higher or equal authority
            if approver_role == 'executive':
                assert has_authority is True or cost_impact > Decimal('1000000'), \
                    "Executive role must have highest authority level"
            
            # Property: Authority validation must be deterministic
            # Same inputs should always produce same result
            second_check = engine.check_approval_authority(approver_id, cost_impact, approver_role)
            assert has_authority == second_check, \
                "Authority validation must be deterministic for same inputs"


@given(
    change_request=change_request_data(),
    workflow_config=workflow_configuration(),
    approval_decisions=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),  # step_number
            st.uuids(),  # approver_id
            st.sampled_from(list(ApprovalDecision))  # decision
        ),
        min_size=1, max_size=8
    )
)
def test_workflow_progression_property(change_request, workflow_config, approval_decisions):
    """
    Property: Workflow Progression Integrity
    
    For any sequence of approval decisions, workflow progression must follow
    configured rules with proper dependency checking and status updates.
    
    Validates: Requirements 2.1, 2.2, 2.4, 2.5
    """
    # Arrange
    engine = MockApprovalWorkflowEngine()
    change_id = change_request['id']
    
    # Initiate workflow
    init_result = engine.initiate_approval_workflow(change_id, change_request, workflow_config)
    approval_path = init_result['approval_path']
    
    # Filter decisions to only include valid step numbers
    valid_decisions = [
        (step_num, approver_id, decision) 
        for step_num, approver_id, decision in approval_decisions
        if step_num <= len(approval_path)
    ]
    
    assume(len(valid_decisions) > 0)  # Ensure we have at least one valid decision
    
    # Act - Process approval decisions in sequence
    decision_results = []
    for step_num, approver_id, decision in valid_decisions:
        try:
            # Only process if step is available and dependencies are met
            pending_steps = engine.get_pending_approvals(change_id)
            pending_step_numbers = [s['step_number'] for s in pending_steps]
            
            if step_num in pending_step_numbers:
                result = engine.process_approval_decision(
                    change_id, step_num, approver_id, decision, f"Decision: {decision.value}"
                )
                decision_results.append((step_num, decision, result))
        except ValueError:
            # Skip invalid decisions (e.g., insufficient authority)
            continue
    
    # Assert - Workflow progression properties
    
    if decision_results:  # Only test if we processed some decisions
        
        # Property: Workflow status must reflect decision outcomes
        workflow = engine.workflows[change_id]
        
        # Check for rejection
        rejected_decisions = [d for _, d, _ in decision_results if d == ApprovalDecision.REJECTED]
        if rejected_decisions:
            assert workflow['status'] == 'rejected', \
                "Workflow must be marked as rejected when any required step is rejected"
        
        # Property: Completed steps must be tracked accurately
        approved_decisions = [
            (step_num, decision) for step_num, decision, _ in decision_results 
            if decision == ApprovalDecision.APPROVED
        ]
        
        if approved_decisions and workflow['status'] != 'rejected':
            assert workflow['completed_steps'] >= len(approved_decisions), \
                "Completed steps count must reflect approved decisions"
        
        # Property: Workflow completion must require all mandatory steps
        if workflow['status'] == 'completed':
            required_steps = [s for s in approval_path if s['is_required']]
            completed_required = [
                d for d in engine.approval_decisions 
                if (d['change_id'] == change_id and 
                    d['decision'] == ApprovalDecision.APPROVED and 
                    d['is_required'])
            ]
            
            assert len(completed_required) >= len(required_steps), \
                "Workflow completion must require all mandatory approval steps"
        
        # Property: Decision records must maintain audit trail
        for step_num, decision, result in decision_results:
            matching_records = [
                d for d in engine.approval_decisions 
                if (d['change_id'] == change_id and 
                    d['step_number'] == step_num and 
                    d['decision'] == decision)
            ]
            assert len(matching_records) >= 1, \
                f"Decision for step {step_num} must be recorded in audit trail"


if __name__ == "__main__":
    # Run property tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])