#!/usr/bin/env python3
"""
Property-based test runner for integrated change management system

This script runs all property-based tests and generates a comprehensive report
validating the universal correctness properties of the change management system.
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple


def run_test_file(test_file: Path) -> Tuple[bool, str, float]:
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_file.name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=test_file.parent
        )
        
        duration = time.time() - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        return success, result.stdout, duration
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Error running {test_file.name}: {str(e)}"
        print(error_msg)
        return False, error_msg, duration


def generate_report(results: Dict[str, Tuple[bool, str, float]]) -> str:
    """Generate a comprehensive test report"""
    total_tests = len(results)
    passed_tests = sum(1 for success, _, _ in results.values() if success)
    failed_tests = total_tests - passed_tests
    total_duration = sum(duration for _, _, duration in results.values())
    
    report = f"""
{'='*80}
PROPERTY-BASED TEST REPORT - INTEGRATED CHANGE MANAGEMENT SYSTEM
{'='*80}

SUMMARY:
--------
Total Test Files: {total_tests}
Passed: {passed_tests}
Failed: {failed_tests}
Success Rate: {(passed_tests/total_tests)*100:.1f}%
Total Duration: {total_duration:.2f} seconds

PROPERTY VALIDATION RESULTS:
---------------------------
"""
    
    # Property mapping
    property_mapping = {
        'test_change_request_lifecycle.py': [
            'Property 1: Change Request State Consistency'
        ],
        'test_approval_workflows.py': [
            'Property 4: Approval Workflow Integrity',
            'Property 5: Authority Validation Consistency'
        ],
        'test_emergency_processes.py': [
            'Property 14: Emergency Process Integrity',
            'Property 15: Post-Implementation Compliance'
        ],
        'test_audit_system.py': [
            'Property 16: Audit Trail Completeness',
            'Property 17: Compliance Data Integrity'
        ]
    }
    
    for test_file, (success, output, duration) in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        report += f"\n{test_file}: {status} ({duration:.2f}s)\n"
        
        if test_file in property_mapping:
            for prop in property_mapping[test_file]:
                prop_status = "✅" if success else "❌"
                report += f"  {prop_status} {prop}\n"
        
        if not success:
            report += f"  Error Details: {output[:200]}...\n"
    
    report += f"\n{'='*80}\n"
    
    if failed_tests == 0:
        report += """
🎉 ALL PROPERTY TESTS PASSED! 🎉

The integrated change management system successfully validates all universal 
correctness properties:

✅ Change Request State Consistency (Property 1)
✅ Approval Workflow Integrity (Property 4) 
✅ Authority Validation Consistency (Property 5)
✅ Emergency Process Integrity (Property 14)
✅ Post-Implementation Compliance (Property 15)
✅ Audit Trail Completeness (Property 16)
✅ Compliance Data Integrity (Property 17)

The system is ready for production deployment with confidence in its
correctness across all change management workflows.
"""
    else:
        report += f"""
⚠️  {failed_tests} PROPERTY TEST(S) FAILED ⚠️

The system has validation issues that must be addressed before deployment.
Please review the failed tests and fix the underlying issues to ensure
system correctness and compliance.
"""
    
    report += f"\n{'='*80}\n"
    return report


def main():
    """Main test runner"""
    print("🚀 Starting Property-Based Test Suite for Integrated Change Management")
    print("📋 Testing universal correctness properties...")
    
    # Find all test files
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    if not test_files:
        print("❌ No test files found!")
        return 1
    
    print(f"📁 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"   • {test_file.name}")
    
    # Run all tests
    results = {}
    overall_start = time.time()
    
    for test_file in test_files:
        success, output, duration = run_test_file(test_file)
        results[test_file.name] = (success, output, duration)
    
    overall_duration = time.time() - overall_start
    
    # Generate and display report
    report = generate_report(results)
    print(report)
    
    # Save report to file
    report_file = test_dir / "property_test_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📄 Full report saved to: {report_file}")
    print(f"⏱️  Total execution time: {overall_duration:.2f} seconds")
    
    # Return appropriate exit code
    failed_count = sum(1 for success, _, _ in results.values() if not success)
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())