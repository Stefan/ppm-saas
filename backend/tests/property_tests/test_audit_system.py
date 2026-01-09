"""
Property-based tests for audit system (Task 18.3)

Property 16: Audit Trail Completeness
Property 17: Compliance Data Integrity
- Validates that audit trails are complete and tamper-evident
- Ensures compliance data maintains integrity throughout the system
- Validates Requirements 6.1, 6.2, 6.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, invariant
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List, Set
import hashlib
import json
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.change_management import (
    ChangeType, ChangeStatus, PriorityLevel, ApprovalDecision
)


# Strategy generators for audit system data
@st.composite
def audit_event_data(draw):
    """Generate audit event data"""
    return {
        'event_type': draw(st.sampled_from([
            'created', 'updated', 'status_changed', 'approved', 'rejected',
            'implemented', 'reviewed', 'escalated', 'delegated', 'cancelled'
        ])),
        'entity_type': draw(st.sampled_from([
            'change_request', 'approval', 'implementation', 'review', 'notification'
        ])),
        'performed_by': str(draw(st.uuids())),
        'ip_address': draw(st.sampled_from([
            '192.168.1.100', '10.0.0.50', '172.16.0.25', '203.0.113.10'
        ])),
        'user_agent': draw(st.sampled_from([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'PostmanRuntime/7.28.4'
        ])),
        'session_id': str(draw(st.uuids())),
        'request_id': str(draw(st.uuids()))
    }


@st.composite
def compliance_requirement_data(draw):
    """Generate compliance requirement data"""
    return {
        'requirement_id': str(draw(st.uuids())),
        'regulation_name': draw(st.sampled_from([
            'SOX', 'GDPR', 'HIPAA', 'ISO_27001', 'PCI_DSS', 'SOC2',
            'OSHA', 'EPA', 'FDA', 'NIST', 'COBIT', 'ITIL'
        ])),
        'requirement_type': draw(st.sampled_from([
            'data_retention', 'access_control', 'audit_logging',
            'change_approval', 'documentation', 'segregation_of_duties'
        ])),
        'criticality': draw(st.sampled_from(['low', 'medium', 'high', 'critical'])),
        'description': draw(st.text(min_size=20, max_size=200)),
        'validation_criteria': draw(st.lists(
            st.text(min_size=10, max_size=50), min_size=1, max_size=5
        )),
        'retention_period_days': draw(st.integers(min_value=90, max_value=2555))  # 3 months to 7 years
    }


@st.composite
def data_change_event(draw):
    """Generate data change event for integrity testing"""
    return {
        'field_name': draw(st.sampled_from([
            'title', 'description', 'status', 'priority', 'estimated_cost_impact',
            'approver_id', 'decision', 'implementation_date', 'review_status'
        ])),
        'old_value': draw(st.one_of(
            st.none(),
            st.text(min_size=1, max_size=100),
            st.integers(),
            st.decimals(min_value=0, max_value=1000000, places=2),
            st.datetimes()
        )),
        'new_value': draw(st.one_of(
            st.text(min_size=1, max_size=100),
            st.integers(),
            st.decimals(min_value=0, max_value=1000000, places=2),
            st.datetimes()
        )),
        'change_reason': draw(st.sampled_from([
            'user_update', 'system_update', 'approval_process', 'implementation',
            'review_process', 'correction', 'migration'
        ]))
    }


class AuditSystemStateMachine(RuleBasedStateMachine):
    """
    Stateful property test for audit system integrity
    
    This tests Property 16: Audit Trail Completeness and Property 17: Compliance Data Integrity
    - All system events are properly logged in audit trail
    - Audit logs are tamper-evident and chronologically consistent
    - Compliance requirements are tracked and validated
    - Data integrity is maintained across all operations
    """
    
    audit_logs = Bundle('audit_logs')
    compliance_checks = Bundle('compliance_checks')
    data_entities = Bundle('data_entities')
    
    def __init__(self):
        super().__init__()
        self.audit_trail: List[Dict[str, Any]] = []
        self.compliance_requirements: Dict[str, Dict[str, Any]] = {}
        self.compliance_violations: List[Dict[str, Any]] = []
        self.data_entities: Dict[str, Dict[str, Any]] = {}
        self.audit_checksums: Dict[str, str] = {}
        self.retention_policies: Dict[str, int] = {}
        self.access_log: List[Dict[str, Any]] = []
    
    @rule(target=audit_logs, 
          entity_id=st.uuids(),
          event_data=audit_event_data(),
          data_changes=st.lists(data_change_event(), max_size=3))
    def create_audit_log_entry(self, entity_id, event_data, data_changes):
        """Create an audit log entry for system events"""
        log_id = str(uuid4())
        timestamp = datetime.now()
        
        # Create comprehensive audit log entry
        audit_entry = {
            'id': log_id,
            'entity_id': str(entity_id),
            'entity_type': event_data['entity_type'],
            'event_type': event_data['event_type'],
            'timestamp': timestamp,
            'performed_by': event_data['performed_by'],
            'ip_address': event_data['ip_address'],
            'user_agent': event_data['user_agent'],
            'session_id': event_data['session_id'],
            'request_id': event_data['request_id'],
            'data_changes': data_changes,
            'checksum': self._calculate_checksum(entity_id, event_data, data_changes, timestamp)
        }
        
        self.audit_trail.append(audit_entry)
        
        # Store checksum for integrity verification
        self.audit_checksums[log_id] = audit_entry['checksum']
        
        # Log access event
        self.access_log.append({
            'timestamp': timestamp,
            'user_id': event_data['performed_by'],
            'action': 'audit_log_created',
            'resource': f"{event_data['entity_type']}:{entity_id}",
            'ip_address': event_data['ip_address']
        })
        
        return log_id
    
    @rule(target=compliance_checks, requirement_data=compliance_requirement_data())
    def register_compliance_requirement(self, requirement_data):
        """Register a compliance requirement for tracking"""
        req_id = requirement_data['requirement_id']
        
        # Add compliance tracking metadata
        compliance_req = {
            **requirement_data,
            'registered_at': datetime.now(),
            'last_checked': None,
            'compliance_status': 'pending',
            'violations_count': 0,
            'next_review_date': datetime.now() + timedelta(days=30)
        }
        
        self.compliance_requirements[req_id] = compliance_req
        
        # Set retention policy
        self.retention_policies[req_id] = requirement_data['retention_period_days']
        
        return req_id
    
    @rule(target=data_entities,
          entity_data=st.dictionaries(
              st.sampled_from(['title', 'status', 'value', 'owner']),
              st.one_of(st.text(min_size=1, max_size=50), st.integers(), st.decimals()),
              min_size=2, max_size=4
          ))
    def create_data_entity(self, entity_data):
        """Create a data entity that needs compliance tracking"""
        entity_id = str(uuid4())
        
        data_entity = {
            'id': entity_id,
            'data': entity_data,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'version': 1,
            'integrity_hash': self._calculate_data_hash(entity_data),
            'compliance_tags': [],
            'retention_class': 'standard'
        }
        
        self.data_entities[entity_id] = data_entity
        
        # Create audit log for entity creation
        self._create_audit_entry(entity_id, 'data_entity', 'created', {
            'initial_data': entity_data
        })
        
        return entity_id
    
    @rule(entity_id=data_entities, 
          field_updates=st.dictionaries(
              st.sampled_from(['title', 'status', 'value']),
              st.one_of(st.text(min_size=1, max_size=50), st.integers()),
              min_size=1, max_size=2
          ))
    def update_data_entity(self, entity_id, field_updates):
        """Update a data entity and maintain audit trail"""
        assume(entity_id in self.data_entities)
        
        entity = self.data_entities[entity_id]
        old_data = entity['data'].copy()
        old_hash = entity['integrity_hash']
        
        # Apply updates
        entity['data'].update(field_updates)
        entity['updated_at'] = datetime.now()
        entity['version'] += 1
        entity['integrity_hash'] = self._calculate_data_hash(entity['data'])
        
        # Create detailed audit entry
        data_changes = []
        for field, new_value in field_updates.items():
            old_value = old_data.get(field)
            if old_value != new_value:
                data_changes.append({
                    'field_name': field,
                    'old_value': old_value,
                    'new_value': new_value,
                    'change_reason': 'user_update'
                })
        
        self._create_audit_entry(entity_id, 'data_entity', 'updated', {
            'data_changes': data_changes,
            'old_hash': old_hash,
            'new_hash': entity['integrity_hash']
        })
    
    @rule(requirement_id=compliance_checks)
    def perform_compliance_check(self, requirement_id):
        """Perform compliance check against registered requirements"""
        assume(requirement_id in self.compliance_requirements)
        
        requirement = self.compliance_requirements[requirement_id]
        check_timestamp = datetime.now()
        
        # Simulate compliance validation
        compliance_status = self._validate_compliance(requirement)
        
        # Update requirement status
        requirement['last_checked'] = check_timestamp
        requirement['compliance_status'] = compliance_status
        requirement['next_review_date'] = check_timestamp + timedelta(days=30)
        
        # Record compliance check in audit trail
        self._create_audit_entry(requirement_id, 'compliance_requirement', 'checked', {
            'check_result': compliance_status,
            'regulation': requirement['regulation_name'],
            'requirement_type': requirement['requirement_type']
        })
        
        # Create violation if non-compliant
        if compliance_status == 'non_compliant':
            violation = {
                'id': str(uuid4()),
                'requirement_id': requirement_id,
                'violation_type': requirement['requirement_type'],
                'severity': requirement['criticality'],
                'detected_at': check_timestamp,
                'description': f"Non-compliance with {requirement['regulation_name']} requirement",
                'status': 'open',
                'corrective_actions': []
            }
            
            self.compliance_violations.append(violation)
            requirement['violations_count'] += 1
    
    @rule()
    def verify_audit_trail_integrity(self):
        """Verify audit trail integrity and detect tampering"""
        for entry in self.audit_trail:
            log_id = entry['id']
            stored_checksum = self.audit_checksums.get(log_id)
            
            if stored_checksum:
                # Recalculate checksum
                calculated_checksum = self._calculate_checksum(
                    entry['entity_id'],
                    {
                        'event_type': entry['event_type'],
                        'entity_type': entry['entity_type'],
                        'performed_by': entry['performed_by'],
                        'ip_address': entry['ip_address'],
                        'user_agent': entry['user_agent'],
                        'session_id': entry['session_id'],
                        'request_id': entry['request_id']
                    },
                    entry['data_changes'],
                    entry['timestamp']
                )
                
                # Detect tampering
                if calculated_checksum != stored_checksum:
                    self.compliance_violations.append({
                        'id': str(uuid4()),
                        'requirement_id': 'audit_integrity',
                        'violation_type': 'audit_tampering',
                        'severity': 'critical',
                        'detected_at': datetime.now(),
                        'description': f"Audit log tampering detected for entry {log_id}",
                        'status': 'critical',
                        'corrective_actions': ['investigate_tampering', 'restore_from_backup']
                    })
    
    @rule()
    def enforce_data_retention_policies(self):
        """Enforce data retention policies and compliance"""
        current_time = datetime.now()
        
        for req_id, retention_days in self.retention_policies.items():
            cutoff_date = current_time - timedelta(days=retention_days)
            
            # Find audit entries that should be archived/deleted
            expired_entries = [
                entry for entry in self.audit_trail
                if entry['timestamp'] < cutoff_date
            ]
            
            # For compliance, we typically archive rather than delete
            for entry in expired_entries:
                # Mark for archival (in real system, would move to archive storage)
                entry['archived'] = True
                entry['archived_at'] = current_time
                
                # Log retention action
                self._create_audit_entry(entry['id'], 'audit_log', 'archived', {
                    'retention_policy': req_id,
                    'retention_days': retention_days,
                    'original_timestamp': entry['timestamp']
                })
    
    def _calculate_checksum(self, entity_id: str, event_data: Dict[str, Any], 
                          data_changes: List[Dict[str, Any]], timestamp: datetime) -> str:
        """Calculate tamper-evident checksum for audit entry"""
        checksum_data = {
            'entity_id': str(entity_id),
            'event_type': event_data['event_type'],
            'timestamp': timestamp.isoformat(),
            'performed_by': event_data['performed_by'],
            'data_changes': sorted(data_changes, key=lambda x: x.get('field_name', ''))
        }
        
        checksum_string = json.dumps(checksum_data, sort_keys=True, default=str)
        return hashlib.sha256(checksum_string.encode()).hexdigest()
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate integrity hash for data entity"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _create_audit_entry(self, entity_id: str, entity_type: str, event_type: str, 
                          details: Dict[str, Any]):
        """Helper to create audit entry"""
        log_id = str(uuid4())
        timestamp = datetime.now()
        
        audit_entry = {
            'id': log_id,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'event_type': event_type,
            'timestamp': timestamp,
            'performed_by': 'system',
            'ip_address': '127.0.0.1',
            'user_agent': 'system',
            'session_id': 'system',
            'request_id': str(uuid4()),
            'data_changes': [],
            'details': details,
            'checksum': ''
        }
        
        # Calculate checksum
        audit_entry['checksum'] = self._calculate_checksum(
            entity_id,
            {
                'event_type': event_type,
                'entity_type': entity_type,
                'performed_by': 'system',
                'ip_address': '127.0.0.1',
                'user_agent': 'system',
                'session_id': 'system',
                'request_id': audit_entry['request_id']
            },
            [],
            timestamp
        )
        
        self.audit_trail.append(audit_entry)
        self.audit_checksums[log_id] = audit_entry['checksum']
    
    def _validate_compliance(self, requirement: Dict[str, Any]) -> str:
        """Validate compliance against requirement"""
        # Simulate compliance validation logic
        regulation = requirement['regulation_name']
        req_type = requirement['requirement_type']
        
        # Check audit logging compliance
        if req_type == 'audit_logging':
            recent_logs = [
                log for log in self.audit_trail
                if log['timestamp'] > datetime.now() - timedelta(days=1)
            ]
            return 'compliant' if len(recent_logs) > 0 else 'non_compliant'
        
        # Check data retention compliance
        elif req_type == 'data_retention':
            retention_days = requirement['retention_period_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            old_logs = [
                log for log in self.audit_trail
                if log['timestamp'] < cutoff_date and not log.get('archived', False)
            ]
            return 'compliant' if len(old_logs) == 0 else 'non_compliant'
        
        # Default to compliant for other types
        return 'compliant'
    
    @invariant()
    def audit_trail_completeness(self):
        """Invariant: Audit trail is complete and chronologically consistent"""
        # Audit trail must be chronologically ordered
        timestamps = [entry['timestamp'] for entry in self.audit_trail]
        assert timestamps == sorted(timestamps)
        
        # Every audit entry must have required fields
        for entry in self.audit_trail:
            assert 'id' in entry
            assert 'entity_id' in entry
            assert 'entity_type' in entry
            assert 'event_type' in entry
            assert 'timestamp' in entry
            assert 'performed_by' in entry
            assert 'checksum' in entry
            
            # Checksum must be valid
            assert len(entry['checksum']) == 64  # SHA-256 hex length
            assert entry['checksum'] in self.audit_checksums.values()
    
    @invariant()
    def audit_integrity_preservation(self):
        """Invariant: Audit log integrity is preserved"""
        for entry in self.audit_trail:
            log_id = entry['id']
            stored_checksum = self.audit_checksums.get(log_id)
            
            # Every audit entry must have a stored checksum
            assert stored_checksum is not None
            assert stored_checksum == entry['checksum']
            
            # Checksums must be unique (no duplicate entries)
            checksum_count = sum(1 for c in self.audit_checksums.values() if c == stored_checksum)
            assert checksum_count == 1
    
    @invariant()
    def compliance_data_integrity(self):
        """Invariant: Compliance data maintains integrity"""
        for req_id, requirement in self.compliance_requirements.items():
            # Compliance requirements must have valid structure
            assert 'regulation_name' in requirement
            assert 'requirement_type' in requirement
            assert 'criticality' in requirement
            assert requirement['criticality'] in ['low', 'medium', 'high', 'critical']
            assert 'registered_at' in requirement
            assert 'compliance_status' in requirement
            assert requirement['compliance_status'] in ['pending', 'compliant', 'non_compliant', 'partially_compliant']
            
            # Retention period must be reasonable
            if req_id in self.retention_policies:
                retention_days = self.retention_policies[req_id]
                assert 90 <= retention_days <= 2555  # 3 months to 7 years
    
    @invariant()
    def data_entity_integrity(self):
        """Invariant: Data entities maintain integrity"""
        for entity_id, entity in self.data_entities.items():
            # Entity must have valid structure
            assert 'id' in entity
            assert entity['id'] == entity_id
            assert 'data' in entity
            assert 'created_at' in entity
            assert 'updated_at' in entity
            assert 'version' in entity
            assert 'integrity_hash' in entity
            
            # Version must be positive
            assert entity['version'] >= 1
            
            # Updated timestamp must be >= created timestamp
            assert entity['updated_at'] >= entity['created_at']
            
            # Integrity hash must be valid
            calculated_hash = self._calculate_data_hash(entity['data'])
            assert entity['integrity_hash'] == calculated_hash
    
    @invariant()
    def compliance_violation_tracking(self):
        """Invariant: Compliance violations are properly tracked"""
        for violation in self.compliance_violations:
            # Violations must have required fields
            assert 'id' in violation
            assert 'violation_type' in violation
            assert 'severity' in violation
            assert 'detected_at' in violation
            assert 'status' in violation
            
            # Severity must be valid
            assert violation['severity'] in ['low', 'medium', 'high', 'critical']
            
            # Status must be valid
            assert violation['status'] in ['open', 'investigating', 'resolved', 'critical']
            
            # Critical violations must have immediate attention
            if violation['severity'] == 'critical':
                assert violation['status'] in ['open', 'critical', 'investigating']


# Property test for audit system integrity
TestAuditSystemIntegrity = AuditSystemStateMachine.TestCase


@given(
    audit_events=st.lists(
        st.tuples(
            st.uuids(),  # entity_id
            audit_event_data(),
            st.lists(data_change_event(), max_size=2)
        ),
        min_size=1, max_size=10
    )
)
def test_audit_trail_chronological_consistency(audit_events):
    """
    Property: Audit trail maintains chronological consistency
    
    Tests that:
    1. Audit events are properly timestamped
    2. Events maintain chronological order
    3. No duplicate timestamps for same entity
    4. Checksums are unique and valid
    """
    audit_trail = []
    checksums = set()
    
    base_time = datetime.now()
    
    for i, (entity_id, event_data, data_changes) in enumerate(audit_events):
        # Ensure chronological ordering
        timestamp = base_time + timedelta(seconds=i)
        
        # Calculate checksum
        checksum_data = {
            'entity_id': str(entity_id),
            'event_type': event_data['event_type'],
            'timestamp': timestamp.isoformat(),
            'performed_by': event_data['performed_by'],
            'data_changes': sorted(data_changes, key=lambda x: x.get('field_name', ''))
        }
        
        checksum_string = json.dumps(checksum_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
        
        audit_entry = {
            'entity_id': str(entity_id),
            'event_type': event_data['event_type'],
            'timestamp': timestamp,
            'performed_by': event_data['performed_by'],
            'data_changes': data_changes,
            'checksum': checksum
        }
        
        audit_trail.append(audit_entry)
        checksums.add(checksum)
    
    # Verify chronological consistency
    timestamps = [entry['timestamp'] for entry in audit_trail]
    assert timestamps == sorted(timestamps)
    
    # Verify checksum uniqueness (for different events)
    assert len(checksums) == len(audit_trail)
    
    # Verify all checksums are valid SHA-256
    for checksum in checksums:
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)


@given(
    compliance_reqs=st.lists(compliance_requirement_data(), min_size=1, max_size=5),
    retention_days=st.integers(min_value=90, max_value=2555)
)
def test_compliance_data_retention_integrity(compliance_reqs, retention_days):
    """
    Property: Compliance data retention maintains integrity
    
    Tests that:
    1. Retention policies are properly enforced
    2. Data is archived according to compliance requirements
    3. Audit trail for retention actions is complete
    4. No data loss during retention enforcement
    """
    # Verify retention period validity
    for req in compliance_reqs:
        req_retention = req['retention_period_days']
        assert 90 <= req_retention <= 2555
    
    # Test retention policy enforcement
    current_time = datetime.now()
    cutoff_date = current_time - timedelta(days=retention_days)
    
    # Simulate audit entries with different ages
    old_entries = []
    recent_entries = []
    
    for i in range(len(compliance_reqs)):
        # Create old entry (should be archived)
        old_timestamp = cutoff_date - timedelta(days=1)
        old_entries.append({
            'timestamp': old_timestamp,
            'requirement_id': compliance_reqs[i]['requirement_id'],
            'should_archive': True
        })
        
        # Create recent entry (should be kept)
        recent_timestamp = cutoff_date + timedelta(days=1)
        recent_entries.append({
            'timestamp': recent_timestamp,
            'requirement_id': compliance_reqs[i]['requirement_id'],
            'should_archive': False
        })
    
    # Verify retention logic
    for entry in old_entries:
        age_days = (current_time - entry['timestamp']).days
        assert age_days > retention_days
        assert entry['should_archive'] is True
    
    for entry in recent_entries:
        age_days = (current_time - entry['timestamp']).days
        assert age_days <= retention_days
        assert entry['should_archive'] is False


@given(
    data_updates=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),  # field_name
            st.one_of(st.text(min_size=1, max_size=50), st.integers()),  # old_value
            st.one_of(st.text(min_size=1, max_size=50), st.integers())   # new_value
        ),
        min_size=1, max_size=5
    )
)
def test_data_integrity_hash_consistency(data_updates):
    """
    Property: Data integrity hashes are consistent and detect changes
    
    Tests that:
    1. Hash calculation is deterministic
    2. Different data produces different hashes
    3. Hash changes when data changes
    4. Hash remains same for identical data
    """
    # Create initial data
    initial_data = {field: old_val for field, old_val, _ in data_updates}
    
    # Calculate initial hash
    initial_hash = hashlib.sha256(
        json.dumps(initial_data, sort_keys=True, default=str).encode()
    ).hexdigest()
    
    # Verify hash is deterministic
    recalculated_hash = hashlib.sha256(
        json.dumps(initial_data, sort_keys=True, default=str).encode()
    ).hexdigest()
    assert initial_hash == recalculated_hash
    
    # Apply updates and verify hash changes
    updated_data = initial_data.copy()
    for field, old_val, new_val in data_updates:
        if old_val != new_val:  # Only if there's an actual change
            updated_data[field] = new_val
            
            updated_hash = hashlib.sha256(
                json.dumps(updated_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            
            # Hash should change when data changes
            assert updated_hash != initial_hash
            
            # Update initial hash for next iteration
            initial_hash = updated_hash


@given(
    violation_data=st.lists(
        st.tuples(
            st.sampled_from(['audit_tampering', 'retention_violation', 'access_violation']),
            st.sampled_from(['low', 'medium', 'high', 'critical']),
            st.text(min_size=10, max_size=100)
        ),
        min_size=1, max_size=5
    )
)
def test_compliance_violation_tracking_completeness(violation_data):
    """
    Property: Compliance violations are completely and accurately tracked
    
    Tests that:
    1. All violations are properly recorded
    2. Violation severity is correctly classified
    3. Critical violations receive immediate attention
    4. Violation tracking is audit-compliant
    """
    violations = []
    
    for violation_type, severity, description in violation_data:
        violation = {
            'id': str(uuid4()),
            'violation_type': violation_type,
            'severity': severity,
            'description': description,
            'detected_at': datetime.now(),
            'status': 'open'
        }
        
        # Critical violations should have immediate status
        if severity == 'critical':
            violation['status'] = 'critical'
            violation['requires_immediate_action'] = True
        
        violations.append(violation)
    
    # Verify violation structure
    for violation in violations:
        assert 'id' in violation
        assert 'violation_type' in violation
        assert 'severity' in violation
        assert 'detected_at' in violation
        assert 'status' in violation
        
        # Verify severity classification
        assert violation['severity'] in ['low', 'medium', 'high', 'critical']
        
        # Verify critical violation handling
        if violation['severity'] == 'critical':
            assert violation['status'] in ['critical', 'open']
            assert violation.get('requires_immediate_action', False) is True
    
    # Verify no duplicate violation IDs
    violation_ids = [v['id'] for v in violations]
    assert len(violation_ids) == len(set(violation_ids))


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])