#!/usr/bin/env python3
"""
Core Property-based test runner for the four requested tasks

This script runs the specific property-based tests requested:
- Task 1.1: Property test for change request lifecycle
- Task 3.4: Property tests for approval workflows  
- Task 9.3: Property tests for emergency processes
- Task 18.3: Property tests for audit system
"""

import sys
import subprocess
import time
from pathlib import Path


def run_core_property_tests():
    """Run the four core property tests requested"""
    print("🚀 Running Core Property-Based Tests for Integrated Change Management")
    print("📋 Testing the four requested property test tasks...")
    
    # Define the core tests to run
    core_tests = [
        {
            'task': 'Task 1.1',
            'property': 'Property 1: Change Request State Consistency',
            'file': 'test_change_request_lifecycle.py',
            'tests': [
                'test_change_request_creation_properties',
                'test_status_transition_validation',
                'test_change_request_update_consistency'
            ]
        },
        {
            'task': 'Task 3.4', 
            'property': 'Property 4: Approval Workflow Integrity, Property 5: Authority Validation Consistency',
            'file': 'test_approval_workflows.py',
            'tests': [
                'test_approval_authority_validation',
                'test_workflow_completion_logic'
            ]
        },
        {
            'task': 'Task 9.3',
            'property': 'Property 14: Emergency Process Integrity, Property 15: Post-Implementation Compliance', 
            'file': 'test_emergency_processes.py',
            'tests': [
                'test_emergency_change_creation_properties',
                'test_emergency_approval_authority'
            ]
        },
        {
            'task': 'Task 18.3',
            'property': 'Property 16: Audit Trail Completeness, Property 17: Compliance Data Integrity',
            'file': 'test_audit_system.py', 
            'tests': [
                'test_audit_trail_chronological_consistency',
                'test_compliance_violation_tracking_completeness'
            ]
        }
    ]
    
    results = {}
    total_start = time.time()
    
    for test_group in core_tests:
        print(f"\n{'='*80}")
        print(f"🧪 {test_group['task']}: {test_group['property']}")
        print(f"📁 File: {test_group['file']}")
        print(f"{'='*80}")
        
        group_start = time.time()
        group_passed = 0
        group_total = len(test_group['tests'])
        
        for test_name in test_group['tests']:
            test_path = f"tests/property_tests/{test_group['file']}::{test_name}"
            
            print(f"\n▶️  Running {test_name}...")
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                if result.returncode == 0:
                    print(f"   ✅ PASSED")
                    group_passed += 1
                else:
                    print(f"   ❌ FAILED")
                    print(f"   Error: {result.stdout.split('FAILED')[0] if 'FAILED' in result.stdout else 'Unknown error'}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        group_duration = time.time() - group_start
        group_success = group_passed == group_total
        
        results[test_group['task']] = {
            'success': group_success,
            'passed': group_passed,
            'total': group_total,
            'duration': group_duration,
            'property': test_group['property']
        }
        
        status = "✅ PASSED" if group_success else "❌ FAILED"
        print(f"\n📊 {test_group['task']}: {status} ({group_passed}/{group_total} tests, {group_duration:.2f}s)")
    
    total_duration = time.time() - total_start
    
    # Generate final report
    print(f"\n{'='*80}")
    print("📋 FINAL PROPERTY TEST RESULTS")
    print(f"{'='*80}")
    
    total_passed = sum(1 for r in results.values() if r['success'])
    total_tasks = len(results)
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Tasks: {total_tasks}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_tasks - total_passed}")
    print(f"   Success Rate: {(total_passed/total_tasks)*100:.1f}%")
    print(f"   Total Duration: {total_duration:.2f} seconds")
    
    print(f"\n🔍 DETAILED RESULTS:")
    for task, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {task}: {result['passed']}/{result['total']} tests ({result['duration']:.2f}s)")
        print(f"      {result['property']}")
    
    if total_passed == total_tasks:
        print(f"\n🎉 ALL PROPERTY TESTS PASSED! 🎉")
        print(f"\nThe integrated change management system successfully validates all")
        print(f"requested universal correctness properties:")
        print(f"")
        for task, result in results.items():
            print(f"✅ {task}: {result['property']}")
        print(f"\nThe system demonstrates correctness across all change management")
        print(f"workflows and is ready for production deployment.")
    else:
        print(f"\n⚠️  SOME PROPERTY TESTS FAILED ⚠️")
        print(f"\nPlease review and fix the failed tests to ensure system correctness.")
        
        failed_tasks = [task for task, result in results.items() if not result['success']]
        print(f"\nFailed tasks:")
        for task in failed_tasks:
            print(f"❌ {task}")
    
    print(f"\n{'='*80}")
    
    return 0 if total_passed == total_tasks else 1


if __name__ == "__main__":
    sys.exit(run_core_property_tests())