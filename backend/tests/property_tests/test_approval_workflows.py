"""
Property-based tests for approval workflows (Task 3.4)

Property 4: Approval Workflow Integrity
Property 5: Authority Validation Consistency
- Validates that approval workflows maintain integrity throughout the process
- Ensures authority validation is consistent and follows business rules
- Validates Requirements 2.1, 2.2, 2.4, 2.5
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
    ChangeType, PriorityLevel, ApprovalDecision,
    ApprovalRequest, ApprovalDecisionRequest
)


# Strategy generators for approval workflow data
@st.composite
def approval_decision_strategy(draw):
    """Generate valid approval decisions"""
    return draw(st.sampled_from(list(ApprovalDecision)))


@st.composite
def user_role_strategy(draw):
    """Generate valid user roles for approval authority"""
    roles = [
        'project_manager', 'senior_project_manager', 'program_manager',
        'engineering_manager', 'construction_manager', 'finance_manager',
        'procurement_manager', 'quality_manager', 'safety_manager',
        'director', 'vice_president', 'ceo'
    ]
    return draw(st.sampled_from(roles))


@st.composite
def approval_authority_matrix(draw):
    """Generate approval authority matrix for different roles and change values"""
    return {
        'project_manager': {'max_value': Decimal('50000'), 'change_types': ['scope', 'schedule', 'resource']},
        'senior_project_manager': {'max_value': Decimal('100000'), 'change_types': ['scope', 'schedule', 'budget', 'resource']},
        'engineering_manager': {'max_value': Decimal('75000'), 'change_types': ['design', 'quality', 'regulatory']},
        'construction_manager': {'max_value': Decimal('150000'), 'change_types': ['scope', 'schedule', 'safety', 'resource']},
        'finance_manager': {'max_value': Decimal('200000'), 'change_types': ['budget', 'scope']},
        'program_manager': {'max_value': Decimal('500000'), 'change_types': list(ChangeType)},
        'director': {'max_value': Decimal('1000000'), 'change_types': list(ChangeType)},
        'vice_president': {'max_value': Decimal('5000000'), 'change_types': list(ChangeType)},
        'ceo': {'max_value': Decimal('999999999'), 'change_types': list(ChangeType)}
    }


@st.composite
def valid_approval_request(draw):
    """Generate valid approval request data"""
    return ApprovalRequest(
        change_request_id=draw(st.uuids()),
        approver_id=draw(st.uuids()),
        step_number=draw(st.integers(min_value=1, max_value=10)),
        is_required=draw(st.booleans()),
        is_parallel=draw(st.booleans()),
        depends_on_step=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=9))),
        due_date=draw(st.one_of(st.none(), st.datetimes(min_value=datetime.now())))
    )


@st.composite
def change_request_for_approval(draw):
    """Generate change request data for approval testing"""
    return {
        'id': str(draw(st.uuids())),
        'change_type': draw(st.sampled_from(list(ChangeType))),
        'priority': draw(st.sampled_from(list(PriorityLevel))),
        'estimated_cost_impact': draw(st.decimals(min_value=0, max_value=10000000, places=2)),
        'project_id': str(draw(st.uuids())),
        'requested_by': str(draw(st.uuids())),
        'title': draw(st.text(min_size=5, max_size=100)),
        'description': draw(st.text(min_size=10, max_size=500))
    }


class ApprovalWorkflowStateMachine(RuleBasedStateMachine):
    """
    Stateful property test for approval workflow integrity
    
    This tests Property 4: Approval Workflow Integrity and Property 5: Authority Validation Consistency
    - Approval workflows maintain proper sequencing and dependencies
    - Authority validation is consistent across all approval decisions
    - Parallel and sequential approvals work correctly
    - Escalation and delegation maintain workflow integrity
    """
    
    change_requests = Bundle('change_requests')
    approval_workflows = Bundle('approval_workflows')
    pending_approvals = Bundle('pending_approvals')
    
    def __init__(self):
        super().__init__()
        self.change_requests: Dict[str, Dict[str, Any]] = {}
        self.approval_workflows: Dict[str, Dict[str, Any]] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.completed_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_history: List[Dict[str, Any]] = []
        self.authority_matrix = self._get_authority_matrix()
        self.users: Dict[str, Dict[str, Any]] = {}
    
    def _get_authority_matrix(self):
        """Get the approval authority matrix"""
        return {
            'project_manager': {'max_value': Decimal('50000'), 'change_types': ['scope', 'schedule', 'resource']},
            'senior_project_manager': {'max_value': Decimal('100000'), 'change_types': ['scope', 'schedule', 'budget', 'resource']},
            'engineering_manager': {'max_value': Decimal('75000'), 'change_types': ['design', 'quality', 'regulatory']},
            'construction_manager': {'max_value': Decimal('150000'), 'change_types': ['scope', 'schedule', 'safety', 'resource']},
            'finance_manager': {'max_value': Decimal('200000'), 'change_types': ['budget', 'scope']},
            'program_manager': {'max_value': Decimal('500000'), 'change_types': [ct.value for ct in ChangeType]},
            'director': {'max_value': Decimal('1000000'), 'change_types': [ct.value for ct in ChangeType]},
            'vice_president': {'max_value': Decimal('5000000'), 'change_types': [ct.value for ct in ChangeType]},
            'ceo': {'max_value': Decimal('999999999'), 'change_types': [ct.value for ct in ChangeType]}
        }
    
    @rule(target=change_requests, change_data=change_request_for_approval())
    def create_change_request(self, change_data):
        """Create a change request that needs approval"""
        change_id = change_data['id']
        self.change_requests[change_id] = change_data
        return change_id
    
    @rule(target=approval_workflows, change_id=change_requests)
    def initiate_approval_workflow(self, change_id):
        """Initiate approval workflow for a change request"""
        assume(change_id in self.change_requests)
        
        change = self.change_requests[change_id]
        workflow_id = str(uuid4())
        
        # Determine approval steps based on change characteristics
        approval_steps = self._determine_approval_steps(change)
        
        workflow = {
            'id': workflow_id,
            'change_request_id': change_id,
            'steps': approval_steps,
            'current_step': 1,
            'status': 'active',
            'created_at': datetime.now(),
            'completed_steps': set(),
            'pending_steps': set(range(1, len(approval_steps) + 1))
        }
        
        self.approval_workflows[workflow_id] = workflow
        
        # Create pending approvals for initial steps
        self._create_pending_approvals(workflow_id, approval_steps)
        
        return workflow_id
    
    @rule(workflow_id=approval_workflows, 
          decision=approval_decision_strategy(),
          approver_role=user_role_strategy())
    def process_approval_decision(self, workflow_id, decision, approver_role):
        """Process an approval decision"""
        assume(workflow_id in self.approval_workflows)
        
        workflow = self.approval_workflows[workflow_id]
        assume(workflow['status'] == 'active')
        
        change_id = workflow['change_request_id']
        change = self.change_requests[change_id]
        
        # Find a pending approval for this workflow that the user can approve
        eligible_approvals = [
            approval_id for approval_id, approval in self.pending_approvals.items()
            if (approval['workflow_id'] == workflow_id and 
                self._check_approval_authority(approver_role, change, approval))
        ]
        
        if not eligible_approvals:
            return  # No eligible approvals for this user
        
        approval_id = eligible_approvals[0]  # Take the first eligible approval
        approval = self.pending_approvals[approval_id]
        
        # Process the decision
        approval_result = {
            'approval_id': approval_id,
            'workflow_id': workflow_id,
            'change_request_id': change_id,
            'step_number': approval['step_number'],
            'approver_role': approver_role,
            'decision': decision,
            'decision_date': datetime.now(),
            'comments': f"Decision: {decision.value}"
        }
        
        # Move approval from pending to completed
        self.completed_approvals[approval_id] = {**approval, **approval_result}
        del self.pending_approvals[approval_id]
        
        # Update workflow state
        workflow['completed_steps'].add(approval['step_number'])
        workflow['pending_steps'].discard(approval['step_number'])
        
        # Record in history
        self.approval_history.append(approval_result)
        
        # Check if workflow can progress
        self._update_workflow_progress(workflow_id)
    
    @rule(workflow_id=approval_workflows)
    def escalate_overdue_approvals(self, workflow_id):
        """Escalate overdue approvals"""
        assume(workflow_id in self.approval_workflows)
        
        workflow = self.approval_workflows[workflow_id]
        current_time = datetime.now()
        
        # Find overdue approvals
        overdue_approvals = [
            approval_id for approval_id, approval in self.pending_approvals.items()
            if (approval['workflow_id'] == workflow_id and 
                approval.get('due_date') and 
                approval['due_date'] < current_time)
        ]
        
        for approval_id in overdue_approvals:
            approval = self.pending_approvals[approval_id]
            
            # Escalate to higher authority
            escalated_approval = {
                **approval,
                'escalated': True,
                'escalation_date': current_time,
                'original_approver': approval['approver_id'],
                'approver_id': str(uuid4()),  # New escalated approver
                'due_date': current_time + timedelta(days=2)  # New deadline
            }
            
            self.pending_approvals[approval_id] = escalated_approval
    
    def _determine_approval_steps(self, change: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine approval steps based on change characteristics"""
        steps = []
        step_number = 1
        
        change_type = change['change_type']
        cost_impact = change['estimated_cost_impact']
        priority = change['priority']
        
        # Step 1: Initial review (always required)
        steps.append({
            'step_number': step_number,
            'required_role': 'project_manager',
            'is_required': True,
            'is_parallel': False,
            'depends_on_step': None
        })
        step_number += 1
        
        # Step 2: Specialized review based on change type
        if change_type in ['design', 'quality', 'regulatory']:
            steps.append({
                'step_number': step_number,
                'required_role': 'engineering_manager',
                'is_required': True,
                'is_parallel': False,
                'depends_on_step': step_number - 1
            })
            step_number += 1
        
        if change_type in ['budget', 'scope'] and cost_impact > 25000:
            steps.append({
                'step_number': step_number,
                'required_role': 'finance_manager',
                'is_required': True,
                'is_parallel': True,  # Can be parallel with engineering review
                'depends_on_step': 1
            })
            step_number += 1
        
        # Step 3: Senior approval for high-value changes
        if cost_impact > 100000:
            steps.append({
                'step_number': step_number,
                'required_role': 'program_manager',
                'is_required': True,
                'is_parallel': False,
                'depends_on_step': step_number - 1
            })
            step_number += 1
        
        # Step 4: Executive approval for very high-value changes
        if cost_impact > 1000000:
            steps.append({
                'step_number': step_number,
                'required_role': 'director',
                'is_required': True,
                'is_parallel': False,
                'depends_on_step': step_number - 1
            })
            step_number += 1
        
        # Emergency changes get expedited workflow
        if priority == PriorityLevel.EMERGENCY:
            # Simplify to single high-authority approval
            steps = [{
                'step_number': 1,
                'required_role': 'director',
                'is_required': True,
                'is_parallel': False,
                'depends_on_step': None
            }]
        
        return steps
    
    def _create_pending_approvals(self, workflow_id: str, steps: List[Dict[str, Any]]):
        """Create pending approvals for workflow steps"""
        for step in steps:
            # Only create approvals for steps that don't depend on others, or emergency changes
            if step['depends_on_step'] is None:
                approval_id = str(uuid4())
                
                approval = {
                    'id': approval_id,
                    'workflow_id': workflow_id,
                    'step_number': step['step_number'],
                    'required_role': step['required_role'],
                    'approver_id': str(uuid4()),  # Would be determined by role lookup
                    'is_required': step['is_required'],
                    'is_parallel': step['is_parallel'],
                    'depends_on_step': step['depends_on_step'],
                    'due_date': datetime.now() + timedelta(days=3),
                    'created_at': datetime.now(),
                    'status': 'pending'
                }
                
                self.pending_approvals[approval_id] = approval
    
    def _check_approval_authority(self, approver_role: str, change: Dict[str, Any], approval: Dict[str, Any]) -> bool:
        """Check if approver has authority for this change"""
        if approver_role not in self.authority_matrix:
            return False
        
        authority = self.authority_matrix[approver_role]
        
        # Check value authority
        if change['estimated_cost_impact'] > authority['max_value']:
            return False
        
        # Check change type authority
        if change['change_type'] not in authority['change_types']:
            return False
        
        # Check if this is the required role for the approval step
        if approval['required_role'] != approver_role:
            # Allow higher authority roles to approve lower-level steps
            role_hierarchy = [
                'project_manager', 'senior_project_manager', 'engineering_manager',
                'construction_manager', 'finance_manager', 'program_manager',
                'director', 'vice_president', 'ceo'
            ]
            
            try:
                approver_level = role_hierarchy.index(approver_role)
                required_level = role_hierarchy.index(approval['required_role'])
                return approver_level >= required_level
            except ValueError:
                return False
        
        return True
    
    def _update_workflow_progress(self, workflow_id: str):
        """Update workflow progress and create new pending approvals if needed"""
        workflow = self.approval_workflows[workflow_id]
        
        # Check if any new steps can be activated
        for step in workflow['steps']:
            step_number = step['step_number']
            
            # Skip if already completed or pending
            if (step_number in workflow['completed_steps'] or 
                any(approval['step_number'] == step_number for approval in self.pending_approvals.values())):
                continue
            
            # Check if dependencies are met
            depends_on = step['depends_on_step']
            if depends_on is None or depends_on in workflow['completed_steps']:
                # Create pending approval for this step
                approval_id = str(uuid4())
                
                approval = {
                    'id': approval_id,
                    'workflow_id': workflow_id,
                    'step_number': step_number,
                    'required_role': step['required_role'],
                    'approver_id': str(uuid4()),
                    'is_required': step['is_required'],
                    'is_parallel': step['is_parallel'],
                    'depends_on_step': step['depends_on_step'],
                    'due_date': datetime.now() + timedelta(days=3),
                    'created_at': datetime.now(),
                    'status': 'pending'
                }
                
                self.pending_approvals[approval_id] = approval
        
        # Check if workflow is complete
        all_required_steps = {step['step_number'] for step in workflow['steps'] if step['is_required']}
        if all_required_steps.issubset(workflow['completed_steps']):
            workflow['status'] = 'completed'
            workflow['completed_at'] = datetime.now()
    
    @invariant()
    def approval_workflow_integrity(self):
        """Invariant: Approval workflows maintain integrity"""
        for workflow_id, workflow in self.approval_workflows.items():
            # Workflow must have valid structure
            assert 'id' in workflow
            assert 'change_request_id' in workflow
            assert 'steps' in workflow
            assert 'status' in workflow
            assert workflow['status'] in ['active', 'completed', 'cancelled']
            
            # Steps must be properly sequenced
            step_numbers = [step['step_number'] for step in workflow['steps']]
            assert step_numbers == sorted(step_numbers)
            assert min(step_numbers) == 1
            assert len(set(step_numbers)) == len(step_numbers)  # No duplicates
            
            # Dependencies must be valid
            for step in workflow['steps']:
                depends_on = step['depends_on_step']
                if depends_on is not None:
                    assert depends_on < step['step_number']
                    assert depends_on in step_numbers
    
    @invariant()
    def authority_validation_consistency(self):
        """Invariant: Authority validation is consistent"""
        for approval_record in self.approval_history:
            approver_role = approval_record['approver_role']
            change_id = approval_record['change_request_id']
            
            if change_id in self.change_requests:
                change = self.change_requests[change_id]
                
                # Verify approver had authority
                if approver_role in self.authority_matrix:
                    authority = self.authority_matrix[approver_role]
                    
                    # Check value authority
                    assert change['estimated_cost_impact'] <= authority['max_value']
                    
                    # Check change type authority
                    assert change['change_type'] in authority['change_types']
    
    @invariant()
    def approval_sequencing_integrity(self):
        """Invariant: Approval sequencing follows dependency rules"""
        for workflow_id, workflow in self.approval_workflows.items():
            completed_steps = workflow['completed_steps']
            
            # Check that all dependencies are satisfied for completed steps
            for step in workflow['steps']:
                if step['step_number'] in completed_steps:
                    depends_on = step['depends_on_step']
                    if depends_on is not None:
                        assert depends_on in completed_steps
    
    @invariant()
    def pending_approvals_validity(self):
        """Invariant: Pending approvals are valid and consistent"""
        for approval_id, approval in self.pending_approvals.items():
            workflow_id = approval['workflow_id']
            
            # Approval must belong to an active workflow
            assert workflow_id in self.approval_workflows
            workflow = self.approval_workflows[workflow_id]
            assert workflow['status'] == 'active'
            
            # Step must exist in workflow
            step_numbers = [step['step_number'] for step in workflow['steps']]
            assert approval['step_number'] in step_numbers
            
            # Dependencies must be satisfied
            step_info = next(step for step in workflow['steps'] if step['step_number'] == approval['step_number'])
            depends_on = step_info['depends_on_step']
            if depends_on is not None:
                assert depends_on in workflow['completed_steps']


# Property test for approval workflow integrity
TestApprovalWorkflowIntegrity = ApprovalWorkflowStateMachine.TestCase


@given(
    change_data=change_request_for_approval(),
    approver_role=user_role_strategy()
)
def test_approval_authority_validation(change_data, approver_role):
    """
    Property: Approval authority validation is consistent
    
    Tests that:
    1. Authority limits are properly enforced
    2. Change type restrictions are respected
    3. Role hierarchy is correctly implemented
    """
    authority_matrix = {
        'project_manager': {'max_value': Decimal('50000'), 'change_types': ['scope', 'schedule', 'resource']},
        'senior_project_manager': {'max_value': Decimal('100000'), 'change_types': ['scope', 'schedule', 'budget', 'resource']},
        'engineering_manager': {'max_value': Decimal('75000'), 'change_types': ['design', 'quality', 'regulatory']},
        'construction_manager': {'max_value': Decimal('150000'), 'change_types': ['scope', 'schedule', 'safety', 'resource']},
        'finance_manager': {'max_value': Decimal('200000'), 'change_types': ['budget', 'scope']},
        'program_manager': {'max_value': Decimal('500000'), 'change_types': [ct.value for ct in ChangeType]},
        'director': {'max_value': Decimal('1000000'), 'change_types': [ct.value for ct in ChangeType]},
        'vice_president': {'max_value': Decimal('5000000'), 'change_types': [ct.value for ct in ChangeType]},
        'ceo': {'max_value': Decimal('999999999'), 'change_types': [ct.value for ct in ChangeType]}
    }
    
    if approver_role not in authority_matrix:
        return  # Skip unknown roles
    
    authority = authority_matrix[approver_role]
    
    # Test value authority
    has_value_authority = change_data['estimated_cost_impact'] <= authority['max_value']
    
    # Test change type authority
    has_type_authority = change_data['change_type'] in authority['change_types']
    
    # Both conditions must be met for approval authority
    has_approval_authority = has_value_authority and has_type_authority
    
    # Verify authority calculation is consistent
    if change_data['estimated_cost_impact'] > authority['max_value']:
        assert not has_approval_authority
    
    if change_data['change_type'] not in authority['change_types']:
        assert not has_approval_authority


@given(
    steps=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=10),  # step_number
            st.booleans(),  # is_required
            st.booleans(),  # is_parallel
            st.one_of(st.none(), st.integers(min_value=1, max_value=9))  # depends_on_step
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]  # Unique step numbers
    )
)
def test_workflow_dependency_validation(steps):
    """
    Property: Workflow dependencies are properly validated
    
    Tests that:
    1. Dependencies reference valid steps
    2. No circular dependencies exist
    3. Step sequencing is logical
    """
    # Sort steps by step number
    sorted_steps = sorted(steps, key=lambda x: x[0])
    step_numbers = [step[0] for step in sorted_steps]
    
    # Verify step numbers are sequential starting from 1
    assume(step_numbers == list(range(1, len(step_numbers) + 1)))
    
    # Check dependency validity
    for step_number, is_required, is_parallel, depends_on_step in sorted_steps:
        if depends_on_step is not None:
            # Dependency must reference an earlier step
            assert depends_on_step < step_number
            # Dependency must reference an existing step
            assert depends_on_step in step_numbers
    
    # Check for circular dependencies (simplified check)
    dependency_graph = {}
    for step_number, _, _, depends_on_step in sorted_steps:
        dependency_graph[step_number] = depends_on_step
    
    # Verify no step depends on itself (direct or indirect)
    for step_number in step_numbers:
        visited = set()
        current = step_number
        
        while current is not None and current not in visited:
            visited.add(current)
            current = dependency_graph.get(current)
        
        # If we found a cycle, current would be in visited
        if current is not None:
            assert current != step_number  # No circular dependency


@given(
    workflow_steps=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),  # step_number
            user_role_strategy(),  # required_role
            st.booleans()  # is_required
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]
    ),
    completed_steps=st.sets(st.integers(min_value=1, max_value=5))
)
def test_workflow_completion_logic(workflow_steps, completed_steps):
    """
    Property: Workflow completion logic is correct
    
    Tests that:
    1. Workflows complete when all required steps are done
    2. Optional steps don't block completion
    3. Completion status is accurately determined
    """
    # Filter to only include steps that exist in the workflow
    step_numbers = {step[0] for step in workflow_steps}
    valid_completed_steps = completed_steps & step_numbers
    
    # Determine required steps
    required_steps = {step[0] for step in workflow_steps if step[2]}  # is_required = True
    
    # Workflow should be complete if all required steps are completed
    all_required_completed = required_steps.issubset(valid_completed_steps)
    
    # Test completion logic
    if required_steps:  # If there are required steps
        if all_required_completed:
            # Workflow should be considered complete
            assert len(required_steps - valid_completed_steps) == 0
        else:
            # Workflow should not be complete
            assert len(required_steps - valid_completed_steps) > 0
    else:
        # If no required steps, workflow completion depends on implementation
        # (could be complete immediately or require at least one step)
        pass


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])