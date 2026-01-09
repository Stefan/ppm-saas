#!/usr/bin/env python3
"""
Test Schedule Management Data Models
Validates the Pydantic models for schedule management
"""

import sys
from pathlib import Path
from datetime import date, datetime
from uuid import uuid4

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from models.schedule import (
    ScheduleCreate, TaskCreate, TaskDependencyCreate, WBSElementCreate,
    MilestoneCreate, ResourceAssignmentCreate, ScheduleBaselineCreate,
    TaskUpdate, TaskProgressUpdate, ScheduleResponse, TaskResponse,
    DependencyType, TaskStatus, MilestoneStatus
)

def test_schedule_models():
    """Test all schedule management data models"""
    
    print("🧪 Testing Schedule Management Data Models...")
    
    try:
        # Test ScheduleCreate model
        print("\n📋 Testing ScheduleCreate model...")
        schedule_data = ScheduleCreate(
            project_id=uuid4(),
            name="Test Project Schedule",
            description="A test schedule for validation",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        print(f"✅ ScheduleCreate: {schedule_data.name}")
        
        # Test TaskCreate model
        print("\n📋 Testing TaskCreate model...")
        task_data = TaskCreate(
            wbs_code="1.1",
            name="Test Task",
            description="A test task for validation",
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 1, 15),
            duration_days=14,
            planned_effort_hours=112.0,
            deliverables=["Deliverable 1", "Deliverable 2"],
            acceptance_criteria="Task must meet quality standards"
        )
        print(f"✅ TaskCreate: {task_data.name} (WBS: {task_data.wbs_code})")
        
        # Test TaskDependencyCreate model
        print("\n📋 Testing TaskDependencyCreate model...")
        dependency_data = TaskDependencyCreate(
            predecessor_task_id=uuid4(),
            successor_task_id=uuid4(),
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=2
        )
        print(f"✅ TaskDependencyCreate: {dependency_data.dependency_type}")
        
        # Test WBSElementCreate model
        print("\n📋 Testing WBSElementCreate model...")
        wbs_data = WBSElementCreate(
            wbs_code="1.0",
            name="Test Work Package",
            description="A test work package",
            deliverable_description="Work package deliverable",
            acceptance_criteria="Must meet specifications"
        )
        print(f"✅ WBSElementCreate: {wbs_data.name} (WBS: {wbs_data.wbs_code})")
        
        # Test MilestoneCreate model
        print("\n📋 Testing MilestoneCreate model...")
        milestone_data = MilestoneCreate(
            name="Project Kickoff",
            description="Official project start",
            target_date=date(2024, 1, 1),
            success_criteria="All stakeholders present",
            deliverables=["Kickoff presentation", "Project charter"],
            approval_required=True
        )
        print(f"✅ MilestoneCreate: {milestone_data.name}")
        
        # Test ResourceAssignmentCreate model
        print("\n📋 Testing ResourceAssignmentCreate model...")
        assignment_data = ResourceAssignmentCreate(
            resource_id=uuid4(),
            allocation_percentage=75,
            planned_hours=84.0,
            assignment_start_date=date(2024, 1, 1),
            assignment_end_date=date(2024, 1, 15)
        )
        print(f"✅ ResourceAssignmentCreate: {assignment_data.allocation_percentage}% allocation")
        
        # Test ScheduleBaselineCreate model
        print("\n📋 Testing ScheduleBaselineCreate model...")
        baseline_data = ScheduleBaselineCreate(
            baseline_name="Initial Baseline",
            baseline_date=date(2024, 1, 1),
            description="Initial project baseline",
            baseline_data={"version": "1.0", "tasks": []}
        )
        print(f"✅ ScheduleBaselineCreate: {baseline_data.baseline_name}")
        
        # Test TaskUpdate model
        print("\n📋 Testing TaskUpdate model...")
        task_update = TaskUpdate(
            name="Updated Task Name",
            progress_percentage=50,
            status=TaskStatus.IN_PROGRESS,
            actual_start_date=date(2024, 1, 2)
        )
        print(f"✅ TaskUpdate: {task_update.progress_percentage}% complete")
        
        # Test TaskProgressUpdate model
        print("\n📋 Testing TaskProgressUpdate model...")
        progress_update = TaskProgressUpdate(
            progress_percentage=75,
            status=TaskStatus.IN_PROGRESS,
            actual_start_date=date(2024, 1, 2),
            actual_effort_hours=60.0,
            notes="Good progress on deliverables"
        )
        print(f"✅ TaskProgressUpdate: {progress_update.progress_percentage}% complete")
        
        # Test Response models
        print("\n📋 Testing Response models...")
        schedule_response = ScheduleResponse(
            id=str(uuid4()),
            project_id=str(uuid4()),
            name="Test Schedule Response",
            description="Test description",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            baseline_start_date=None,
            baseline_end_date=None,
            status="active",
            schedule_performance_index=None,
            schedule_variance_days=None,
            created_by=str(uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print(f"✅ ScheduleResponse: {schedule_response.name}")
        
        task_response = TaskResponse(
            id=str(uuid4()),
            schedule_id=str(uuid4()),
            parent_task_id=None,
            wbs_code="1.1",
            name="Test Task Response",
            description="Test task description",
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 1, 15),
            actual_start_date=None,
            actual_end_date=None,
            duration_days=14,
            baseline_start_date=None,
            baseline_end_date=None,
            baseline_duration_days=None,
            progress_percentage=0,
            status="not_started",
            planned_effort_hours=112.0,
            actual_effort_hours=None,
            remaining_effort_hours=112.0,
            is_critical=False,
            total_float_days=0,
            free_float_days=0,
            early_start_date=None,
            early_finish_date=None,
            late_start_date=None,
            late_finish_date=None,
            deliverables=["Deliverable 1"],
            acceptance_criteria="Quality standards",
            created_by=str(uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print(f"✅ TaskResponse: {task_response.name} (WBS: {task_response.wbs_code})")
        
        # Test enum values
        print("\n📋 Testing Enum values...")
        print(f"✅ DependencyType values: {[e.value for e in DependencyType]}")
        print(f"✅ TaskStatus values: {[e.value for e in TaskStatus]}")
        print(f"✅ MilestoneStatus values: {[e.value for e in MilestoneStatus]}")
        
        # Test validation
        print("\n📋 Testing validation...")
        
        # Test date validation
        try:
            invalid_schedule = ScheduleCreate(
                project_id=uuid4(),
                name="Invalid Schedule",
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1)  # End before start
            )
            print("❌ Date validation failed - should have caught invalid dates")
        except ValueError as e:
            print(f"✅ Date validation working: {e}")
        
        # Test self-dependency validation
        try:
            task_id = uuid4()
            invalid_dependency = TaskDependencyCreate(
                predecessor_task_id=task_id,
                successor_task_id=task_id  # Self dependency
            )
            print("❌ Self-dependency validation failed")
        except ValueError as e:
            print(f"✅ Self-dependency validation working: {e}")
        
        print("\n🎉 All schedule management data models validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    
    print("=" * 60)
    print("🧪 SCHEDULE MANAGEMENT DATA MODEL TESTS")
    print("=" * 60)
    
    success = test_schedule_models()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n📋 Data models are ready for:")
        print("   - Schedule management API endpoints")
        print("   - Task hierarchy management")
        print("   - Dependency tracking")
        print("   - WBS structure management")
        print("   - Resource assignment")
        print("   - Milestone tracking")
        print("   - Baseline management")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)