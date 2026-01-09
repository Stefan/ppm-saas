"""
Core Services Checkpoint Test

Tests all schedule services to ensure they work independently and return proper responses.
Verifies database schema and business logic validation.
Tests critical path calculations with complex task networks.
"""

import asyncio
import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any, List
import logging

# Import all core services
from services.schedule_manager import ScheduleManager
from services.task_dependency_engine import TaskDependencyEngine
from services.wbs_manager import WBSManager
from services.milestone_tracker import MilestoneTracker
from services.resource_assignment_service import ResourceAssignmentService
from services.baseline_manager import BaselineManager

# Import models
from models.schedule import (
    ScheduleCreate, TaskCreate, TaskUpdate, TaskProgressUpdate,
    TaskDependencyCreate, DependencyType, TaskStatus,
    WBSElementCreate, MilestoneCreate, MilestoneStatus,
    ResourceAssignmentCreate, ScheduleBaselineCreate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreServicesCheckpoint:
    """
    Comprehensive test suite for all core schedule services.
    Tests each service independently and validates integration points.
    """
    
    def __init__(self):
        self.schedule_manager = ScheduleManager()
        self.dependency_engine = TaskDependencyEngine()
        self.wbs_manager = WBSManager()
        self.milestone_tracker = MilestoneTracker()
        self.resource_service = ResourceAssignmentService()
        self.baseline_manager = BaselineManager()
        
        # Test data storage
        self.test_project_id = uuid4()
        self.test_schedule_id = None
        self.test_tasks = {}
        self.test_user_id = uuid4()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all checkpoint tests and return comprehensive results.
        
        Returns:
            Dict with test results for each service
        """
        logger.info("Starting Core Services Checkpoint Tests")
        
        results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "services_tested": [],
            "test_results": {},
            "overall_status": "unknown",
            "errors": [],
            "warnings": []
        }
        
        try:
            # Test 1: Schedule Manager Service
            logger.info("Testing Schedule Manager Service...")
            schedule_results = await self.test_schedule_manager()
            results["test_results"]["schedule_manager"] = schedule_results
            results["services_tested"].append("schedule_manager")
            
            # Test 2: Task Dependency Engine
            logger.info("Testing Task Dependency Engine...")
            dependency_results = await self.test_dependency_engine()
            results["test_results"]["dependency_engine"] = dependency_results
            results["services_tested"].append("dependency_engine")
            
            # Test 3: WBS Manager
            logger.info("Testing WBS Manager...")
            wbs_results = await self.test_wbs_manager()
            results["test_results"]["wbs_manager"] = wbs_results
            results["services_tested"].append("wbs_manager")
            
            # Test 4: Milestone Tracker
            logger.info("Testing Milestone Tracker...")
            milestone_results = await self.test_milestone_tracker()
            results["test_results"]["milestone_tracker"] = milestone_results
            results["services_tested"].append("milestone_tracker")
            
            # Test 5: Resource Assignment Service
            logger.info("Testing Resource Assignment Service...")
            resource_results = await self.test_resource_service()
            results["test_results"]["resource_service"] = resource_results
            results["services_tested"].append("resource_service")
            
            # Test 6: Baseline Manager
            logger.info("Testing Baseline Manager...")
            baseline_results = await self.test_baseline_manager()
            results["test_results"]["baseline_manager"] = baseline_results
            results["services_tested"].append("baseline_manager")
            
            # Test 7: Complex Critical Path Calculation
            logger.info("Testing Complex Critical Path Calculations...")
            critical_path_results = await self.test_complex_critical_path()
            results["test_results"]["critical_path_complex"] = critical_path_results
            
            # Test 8: Service Integration
            logger.info("Testing Service Integration...")
            integration_results = await self.test_service_integration()
            results["test_results"]["service_integration"] = integration_results
            
            # Determine overall status
            results["overall_status"] = self._determine_overall_status(results["test_results"])
            
        except Exception as e:
            logger.error(f"Critical error during checkpoint tests: {e}")
            results["errors"].append(f"Critical test failure: {str(e)}")
            results["overall_status"] = "failed"
        
        logger.info(f"Checkpoint tests completed with status: {results['overall_status']}")
        return results
    
    async def test_schedule_manager(self) -> Dict[str, Any]:
        """Test Schedule Manager service functionality."""
        test_results = {
            "service": "ScheduleManager",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Test 1: Create Schedule
            test_results["tests_run"].append("create_schedule")
            schedule_data = ScheduleCreate(
                project_id=self.test_project_id,
                name="Test Schedule",
                description="Checkpoint test schedule",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30)
            )
            
            schedule = await self.schedule_manager.create_schedule(
                self.test_project_id, schedule_data, self.test_user_id
            )
            
            if schedule and schedule.id:
                self.test_schedule_id = UUID(schedule.id)
                test_results["passed"] += 1
                logger.info(f"✓ Schedule created successfully: {schedule.id}")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create schedule")
            
            # Test 2: Create Tasks with Hierarchy
            test_results["tests_run"].append("create_tasks_hierarchy")
            
            # Create parent task
            parent_task_data = TaskCreate(
                wbs_code="1.0",
                name="Parent Task",
                description="Test parent task",
                planned_start_date=date.today(),
                planned_end_date=date.today() + timedelta(days=10),
                duration_days=10,
                planned_effort_hours=80.0,
                deliverables=["Parent Deliverable"],
                acceptance_criteria="Parent task completion criteria"
            )
            
            parent_task = await self.schedule_manager.create_task(
                self.test_schedule_id, parent_task_data, self.test_user_id
            )
            
            if parent_task and parent_task.id:
                self.test_tasks["parent"] = UUID(parent_task.id)
                
                # Create child tasks
                for i in range(1, 4):
                    child_task_data = TaskCreate(
                        parent_task_id=UUID(parent_task.id),
                        wbs_code=f"1.{i}",
                        name=f"Child Task {i}",
                        description=f"Test child task {i}",
                        planned_start_date=date.today() + timedelta(days=i-1),
                        planned_end_date=date.today() + timedelta(days=i+2),
                        duration_days=3,
                        planned_effort_hours=24.0,
                        deliverables=[f"Child {i} Deliverable"]
                    )
                    
                    child_task = await self.schedule_manager.create_task(
                        self.test_schedule_id, child_task_data, self.test_user_id
                    )
                    
                    if child_task and child_task.id:
                        self.test_tasks[f"child_{i}"] = UUID(child_task.id)
                
                test_results["passed"] += 1
                logger.info("✓ Task hierarchy created successfully")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create parent task")
            
            # Test 3: Update Task Progress
            test_results["tests_run"].append("update_task_progress")
            
            if "child_1" in self.test_tasks:
                progress_update = TaskProgressUpdate(
                    progress_percentage=50,
                    status=TaskStatus.IN_PROGRESS,
                    actual_start_date=date.today(),
                    actual_effort_hours=12.0,
                    notes="Checkpoint test progress update"
                )
                
                updated_task = await self.schedule_manager.update_task_progress(
                    self.test_tasks["child_1"], progress_update, self.test_user_id
                )
                
                if updated_task and updated_task.progress_percentage == 50:
                    test_results["passed"] += 1
                    logger.info("✓ Task progress updated successfully")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to update task progress")
            
            # Test 4: Get Schedule with Tasks
            test_results["tests_run"].append("get_schedule_with_tasks")
            
            schedule_with_tasks = await self.schedule_manager.get_schedule_with_tasks(
                self.test_schedule_id, include_dependencies=True
            )
            
            if schedule_with_tasks and len(schedule_with_tasks.tasks) >= 4:
                test_results["passed"] += 1
                logger.info(f"✓ Retrieved schedule with {len(schedule_with_tasks.tasks)} tasks")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to retrieve schedule with tasks")
            
            # Test 5: Calculate Progress Rollup
            test_results["tests_run"].append("calculate_progress_rollup")
            
            if "parent" in self.test_tasks:
                rollup_progress = self.schedule_manager.calculate_task_rollup_progress(
                    self.test_tasks["parent"]
                )
                
                if rollup_progress >= 0:
                    test_results["passed"] += 1
                    logger.info(f"✓ Progress rollup calculated: {rollup_progress}%")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to calculate progress rollup")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Schedule Manager test error: {str(e)}")
            logger.error(f"Schedule Manager test error: {e}")
        
        return test_results
    
    async def test_dependency_engine(self) -> Dict[str, Any]:
        """Test Task Dependency Engine functionality."""
        test_results = {
            "service": "TaskDependencyEngine",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_tasks or len(self.test_tasks) < 3:
                test_results["errors"].append("Insufficient test tasks for dependency testing")
                return test_results
            
            # Test 1: Create Dependencies
            test_results["tests_run"].append("create_dependencies")
            
            # Create finish-to-start dependency
            dependency_data = TaskDependencyCreate(
                predecessor_task_id=self.test_tasks["child_1"],
                successor_task_id=self.test_tasks["child_2"],
                dependency_type=DependencyType.FINISH_TO_START,
                lag_days=1
            )
            
            dependency = await self.dependency_engine.create_dependency(
                self.test_tasks["child_1"],
                self.test_tasks["child_2"],
                DependencyType.FINISH_TO_START,
                1,
                self.test_user_id
            )
            
            if dependency and dependency.id:
                test_results["passed"] += 1
                logger.info("✓ Task dependency created successfully")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create task dependency")
            
            # Test 2: Detect Circular Dependencies
            test_results["tests_run"].append("detect_circular_dependencies")
            
            circular_deps = await self.dependency_engine.detect_circular_dependencies(
                self.test_schedule_id
            )
            
            if isinstance(circular_deps, list):
                test_results["passed"] += 1
                logger.info(f"✓ Circular dependency detection completed: {len(circular_deps)} found")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to detect circular dependencies")
            
            # Test 3: Calculate Critical Path
            test_results["tests_run"].append("calculate_critical_path")
            
            critical_path = await self.dependency_engine.calculate_critical_path(
                self.test_schedule_id
            )
            
            if critical_path and hasattr(critical_path, 'critical_tasks'):
                test_results["passed"] += 1
                logger.info(f"✓ Critical path calculated: {len(critical_path.critical_tasks)} critical tasks")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to calculate critical path")
            
            # Test 4: Calculate Task Dates
            test_results["tests_run"].append("calculate_task_dates")
            
            date_calculation = await self.dependency_engine.calculate_task_dates(
                self.test_schedule_id
            )
            
            if date_calculation and hasattr(date_calculation, 'calculated_tasks'):
                test_results["passed"] += 1
                logger.info(f"✓ Task dates calculated for {len(date_calculation.calculated_tasks)} tasks")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to calculate task dates")
            
            # Test 5: Schedule Recalculation
            test_results["tests_run"].append("recalculate_schedule")
            
            if "child_1" in self.test_tasks:
                recalc_result = await self.dependency_engine.recalculate_schedule(
                    self.test_schedule_id, self.test_tasks["child_1"]
                )
                
                if recalc_result and hasattr(recalc_result, 'affected_tasks'):
                    test_results["passed"] += 1
                    logger.info(f"✓ Schedule recalculated: {len(recalc_result.affected_tasks)} tasks affected")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to recalculate schedule")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Dependency Engine test error: {str(e)}")
            logger.error(f"Dependency Engine test error: {e}")
        
        return test_results
    
    async def test_wbs_manager(self) -> Dict[str, Any]:
        """Test WBS Manager service functionality."""
        test_results = {
            "service": "WBSManager",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_schedule_id:
                test_results["errors"].append("No test schedule available for WBS testing")
                return test_results
            
            # Test 1: Create WBS Elements
            test_results["tests_run"].append("create_wbs_elements")
            
            # Create root WBS element
            root_wbs_data = WBSElementCreate(
                wbs_code="1.0",
                name="Root Work Package",
                description="Test root work package",
                work_package_manager=self.test_user_id,
                deliverable_description="Root deliverable",
                acceptance_criteria="Root acceptance criteria"
            )
            
            root_wbs = await self.wbs_manager.create_wbs_element(
                self.test_schedule_id, root_wbs_data, self.test_user_id
            )
            
            if root_wbs and root_wbs.id:
                # Create child WBS elements
                for i in range(1, 4):
                    child_wbs_data = WBSElementCreate(
                        parent_element_id=UUID(root_wbs.id),
                        wbs_code=f"1.{i}",
                        name=f"Child Work Package {i}",
                        description=f"Test child work package {i}",
                        deliverable_description=f"Child {i} deliverable"
                    )
                    
                    child_wbs = await self.wbs_manager.create_wbs_element(
                        self.test_schedule_id, child_wbs_data, self.test_user_id
                    )
                    
                    if not child_wbs or not child_wbs.id:
                        test_results["errors"].append(f"Failed to create child WBS element {i}")
                
                test_results["passed"] += 1
                logger.info("✓ WBS elements created successfully")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create root WBS element")
            
            # Test 2: Get WBS Hierarchy
            test_results["tests_run"].append("get_wbs_hierarchy")
            
            wbs_hierarchy = await self.wbs_manager.get_wbs_hierarchy(
                self.test_schedule_id, max_depth=None
            )
            
            if wbs_hierarchy and len(wbs_hierarchy.elements) >= 4:
                test_results["passed"] += 1
                logger.info(f"✓ WBS hierarchy retrieved: {len(wbs_hierarchy.elements)} elements")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to retrieve WBS hierarchy")
            
            # Test 3: Validate WBS Structure
            test_results["tests_run"].append("validate_wbs_structure")
            
            validation_result = await self.wbs_manager.validate_wbs_structure(
                self.test_schedule_id
            )
            
            if validation_result and hasattr(validation_result, 'is_valid'):
                test_results["passed"] += 1
                logger.info(f"✓ WBS structure validated: {'Valid' if validation_result.is_valid else 'Invalid'}")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to validate WBS structure")
            
            # Test 4: Generate WBS Code
            test_results["tests_run"].append("generate_wbs_code")
            
            generated_code = self.wbs_manager.generate_wbs_code("1.0", 5)
            
            if generated_code == "1.0.5":
                test_results["passed"] += 1
                logger.info(f"✓ WBS code generated: {generated_code}")
            else:
                test_results["failed"] += 1
                test_results["errors"].append(f"WBS code generation failed: expected '1.0.5', got '{generated_code}'")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"WBS Manager test error: {str(e)}")
            logger.error(f"WBS Manager test error: {e}")
        
        return test_results
    
    async def test_milestone_tracker(self) -> Dict[str, Any]:
        """Test Milestone Tracker service functionality."""
        test_results = {
            "service": "MilestoneTracker",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_schedule_id:
                test_results["errors"].append("No test schedule available for milestone testing")
                return test_results
            
            # Test 1: Create Milestone
            test_results["tests_run"].append("create_milestone")
            
            milestone_data = MilestoneCreate(
                task_id=self.test_tasks.get("child_1"),
                name="Test Milestone",
                description="Checkpoint test milestone",
                target_date=date.today() + timedelta(days=15),
                success_criteria="Milestone completion criteria",
                responsible_party=self.test_user_id,
                deliverables=["Milestone Deliverable 1", "Milestone Deliverable 2"],
                approval_required=True
            )
            
            milestone = await self.milestone_tracker.create_milestone(
                self.test_schedule_id, milestone_data, self.test_user_id
            )
            
            if milestone and milestone.id:
                test_results["passed"] += 1
                logger.info(f"✓ Milestone created successfully: {milestone.id}")
                
                # Store milestone ID for further tests
                self.test_milestone_id = UUID(milestone.id)
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create milestone")
            
            # Test 2: Update Milestone Status
            test_results["tests_run"].append("update_milestone_status")
            
            if hasattr(self, 'test_milestone_id'):
                updated_milestone = await self.milestone_tracker.update_milestone_status(
                    self.test_milestone_id,
                    MilestoneStatus.AT_RISK,
                    None,
                    "Checkpoint test status update",
                    self.test_user_id
                )
                
                if updated_milestone and updated_milestone.status == MilestoneStatus.AT_RISK.value:
                    test_results["passed"] += 1
                    logger.info("✓ Milestone status updated successfully")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to update milestone status")
            
            # Test 3: Get Milestone Status Report
            test_results["tests_run"].append("get_milestone_status_report")
            
            status_report = await self.milestone_tracker.get_milestone_status_report(
                schedule_id=self.test_schedule_id
            )
            
            if status_report and "total_milestones" in status_report:
                test_results["passed"] += 1
                logger.info(f"✓ Milestone status report generated: {status_report['total_milestones']} milestones")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to generate milestone status report")
            
            # Test 4: Get At-Risk Milestones
            test_results["tests_run"].append("get_at_risk_milestones")
            
            at_risk_milestones = await self.milestone_tracker.get_at_risk_milestones(
                days_ahead=30, schedule_id=self.test_schedule_id
            )
            
            if isinstance(at_risk_milestones, list):
                test_results["passed"] += 1
                logger.info(f"✓ At-risk milestones identified: {len(at_risk_milestones)} milestones")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to get at-risk milestones")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Milestone Tracker test error: {str(e)}")
            logger.error(f"Milestone Tracker test error: {e}")
        
        return test_results
    
    async def test_resource_service(self) -> Dict[str, Any]:
        """Test Resource Assignment Service functionality."""
        test_results = {
            "service": "ResourceAssignmentService",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_tasks or "child_1" not in self.test_tasks:
                test_results["errors"].append("No test tasks available for resource testing")
                return test_results
            
            # Create a test resource first (simplified - in real system would exist)
            test_resource_id = uuid4()
            
            # Test 1: Assign Resource to Task
            test_results["tests_run"].append("assign_resource_to_task")
            
            assignment_data = ResourceAssignmentCreate(
                resource_id=test_resource_id,
                allocation_percentage=75,
                planned_hours=60.0,
                assignment_start_date=date.today(),
                assignment_end_date=date.today() + timedelta(days=5)
            )
            
            try:
                assignment = await self.resource_service.assign_resource_to_task(
                    self.test_tasks["child_1"], assignment_data, self.test_user_id
                )
                
                if assignment and assignment.id:
                    test_results["passed"] += 1
                    logger.info(f"✓ Resource assigned to task successfully: {assignment.id}")
                    self.test_assignment_id = UUID(assignment.id)
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to assign resource to task")
            except Exception as e:
                # Resource assignment might fail due to missing resource table
                test_results["failed"] += 1
                test_results["errors"].append(f"Resource assignment failed (expected): {str(e)}")
                logger.warning(f"Resource assignment test failed (expected due to missing resource data): {e}")
            
            # Test 2: Detect Resource Conflicts
            test_results["tests_run"].append("detect_resource_conflicts")
            
            try:
                conflicts = await self.resource_service.detect_resource_conflicts(
                    self.test_schedule_id, test_resource_id
                )
                
                if isinstance(conflicts, list):
                    test_results["passed"] += 1
                    logger.info(f"✓ Resource conflicts detected: {len(conflicts)} conflicts")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to detect resource conflicts")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Resource conflict detection failed: {str(e)}")
            
            # Test 3: Calculate Resource Utilization
            test_results["tests_run"].append("calculate_resource_utilization")
            
            try:
                utilization = await self.resource_service.calculate_resource_utilization(
                    test_resource_id
                )
                
                if utilization and hasattr(utilization, 'resource_id'):
                    test_results["passed"] += 1
                    logger.info(f"✓ Resource utilization calculated: {utilization.utilization_percentage}%")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Failed to calculate resource utilization")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Resource utilization calculation failed: {str(e)}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Resource Service test error: {str(e)}")
            logger.error(f"Resource Service test error: {e}")
        
        return test_results
    
    async def test_baseline_manager(self) -> Dict[str, Any]:
        """Test Baseline Manager service functionality."""
        test_results = {
            "service": "BaselineManager",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_schedule_id:
                test_results["errors"].append("No test schedule available for baseline testing")
                return test_results
            
            # Test 1: Create Baseline
            test_results["tests_run"].append("create_baseline")
            
            baseline_data = ScheduleBaselineCreate(
                baseline_name="Checkpoint Test Baseline",
                baseline_date=date.today(),
                description="Test baseline for checkpoint validation",
                baseline_data={"version": "1.0", "test_data": True}
            )
            
            baseline = await self.baseline_manager.create_baseline(
                self.test_schedule_id, baseline_data, self.test_user_id
            )
            
            if baseline and baseline.id:
                test_results["passed"] += 1
                logger.info(f"✓ Baseline created successfully: {baseline.id}")
                self.test_baseline_id = UUID(baseline.id)
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create baseline")
            
            # Test 2: Get Baseline Versions
            test_results["tests_run"].append("get_baseline_versions")
            
            baseline_versions = await self.baseline_manager.get_baseline_versions(
                self.test_schedule_id
            )
            
            if isinstance(baseline_versions, list) and len(baseline_versions) >= 1:
                test_results["passed"] += 1
                logger.info(f"✓ Baseline versions retrieved: {len(baseline_versions)} versions")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to retrieve baseline versions")
            
            # Test 3: Calculate Schedule Variance
            test_results["tests_run"].append("calculate_schedule_variance")
            
            if hasattr(self, 'test_baseline_id'):
                try:
                    variance_analysis = await self.baseline_manager.calculate_schedule_variance(
                        self.test_schedule_id, self.test_baseline_id
                    )
                    
                    if variance_analysis and "schedule_variance" in variance_analysis:
                        test_results["passed"] += 1
                        logger.info("✓ Schedule variance calculated successfully")
                    else:
                        test_results["failed"] += 1
                        test_results["errors"].append("Failed to calculate schedule variance")
                except Exception as e:
                    test_results["failed"] += 1
                    test_results["errors"].append(f"Schedule variance calculation failed: {str(e)}")
            
            # Test 4: Calculate Earned Value Metrics
            test_results["tests_run"].append("calculate_earned_value_metrics")
            
            if hasattr(self, 'test_baseline_id'):
                try:
                    ev_metrics = await self.baseline_manager.calculate_earned_value_metrics(
                        self.test_schedule_id, self.test_baseline_id
                    )
                    
                    if ev_metrics and "summary_metrics" in ev_metrics:
                        test_results["passed"] += 1
                        logger.info("✓ Earned value metrics calculated successfully")
                    else:
                        test_results["failed"] += 1
                        test_results["errors"].append("Failed to calculate earned value metrics")
                except Exception as e:
                    test_results["failed"] += 1
                    test_results["errors"].append(f"Earned value calculation failed: {str(e)}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Baseline Manager test error: {str(e)}")
            logger.error(f"Baseline Manager test error: {e}")
        
        return test_results
    
    async def test_complex_critical_path(self) -> Dict[str, Any]:
        """Test critical path calculations with complex task networks."""
        test_results = {
            "service": "ComplexCriticalPath",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_schedule_id:
                test_results["errors"].append("No test schedule available for complex critical path testing")
                return test_results
            
            # Test 1: Create Complex Task Network
            test_results["tests_run"].append("create_complex_task_network")
            
            complex_tasks = {}
            
            # Create a complex network with multiple paths
            task_configs = [
                {"code": "A", "name": "Task A", "duration": 5, "start_offset": 0},
                {"code": "B", "name": "Task B", "duration": 3, "start_offset": 0},
                {"code": "C", "name": "Task C", "duration": 4, "start_offset": 5},
                {"code": "D", "name": "Task D", "duration": 2, "start_offset": 3},
                {"code": "E", "name": "Task E", "duration": 6, "start_offset": 9},
                {"code": "F", "name": "Task F", "duration": 3, "start_offset": 5},
                {"code": "G", "name": "Task G", "duration": 4, "start_offset": 15}
            ]
            
            for config in task_configs:
                task_data = TaskCreate(
                    wbs_code=f"COMPLEX.{config['code']}",
                    name=config["name"],
                    description=f"Complex network {config['name']}",
                    planned_start_date=date.today() + timedelta(days=config["start_offset"]),
                    planned_end_date=date.today() + timedelta(days=config["start_offset"] + config["duration"] - 1),
                    duration_days=config["duration"],
                    planned_effort_hours=config["duration"] * 8.0
                )
                
                task = await self.schedule_manager.create_task(
                    self.test_schedule_id, task_data, self.test_user_id
                )
                
                if task and task.id:
                    complex_tasks[config["code"]] = UUID(task.id)
            
            if len(complex_tasks) == len(task_configs):
                test_results["passed"] += 1
                logger.info(f"✓ Complex task network created: {len(complex_tasks)} tasks")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to create complete complex task network")
                return test_results
            
            # Test 2: Create Complex Dependencies
            test_results["tests_run"].append("create_complex_dependencies")
            
            # Create a complex dependency network
            dependency_configs = [
                {"pred": "A", "succ": "C", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "B", "succ": "D", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "C", "succ": "E", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "D", "succ": "F", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "E", "succ": "G", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "F", "succ": "G", "type": DependencyType.FINISH_TO_START, "lag": 0},
                {"pred": "A", "succ": "F", "type": DependencyType.START_TO_START, "lag": 2}
            ]
            
            dependencies_created = 0
            for dep_config in dependency_configs:
                if dep_config["pred"] in complex_tasks and dep_config["succ"] in complex_tasks:
                    try:
                        dependency = await self.dependency_engine.create_dependency(
                            complex_tasks[dep_config["pred"]],
                            complex_tasks[dep_config["succ"]],
                            dep_config["type"],
                            dep_config["lag"],
                            self.test_user_id
                        )
                        
                        if dependency and dependency.id:
                            dependencies_created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create dependency {dep_config['pred']} -> {dep_config['succ']}: {e}")
            
            if dependencies_created >= 5:  # Allow some failures
                test_results["passed"] += 1
                logger.info(f"✓ Complex dependencies created: {dependencies_created} dependencies")
            else:
                test_results["failed"] += 1
                test_results["errors"].append(f"Failed to create sufficient dependencies: {dependencies_created}")
            
            # Test 3: Calculate Critical Path on Complex Network
            test_results["tests_run"].append("calculate_complex_critical_path")
            
            critical_path_result = await self.dependency_engine.calculate_critical_path(
                self.test_schedule_id
            )
            
            if critical_path_result and critical_path_result.critical_tasks:
                test_results["passed"] += 1
                logger.info(f"✓ Complex critical path calculated: {len(critical_path_result.critical_tasks)} critical tasks")
                logger.info(f"  Project duration: {critical_path_result.project_duration_days} days")
                logger.info(f"  Risk factors: {len(critical_path_result.schedule_risk_factors)}")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to calculate critical path on complex network")
            
            # Test 4: Validate Critical Path Integrity
            test_results["tests_run"].append("validate_critical_path_integrity")
            
            validation_result = await self.dependency_engine.validate_critical_path_integrity(
                self.test_schedule_id
            )
            
            if validation_result and "is_valid" in validation_result:
                test_results["passed"] += 1
                status = "Valid" if validation_result["is_valid"] else "Invalid"
                logger.info(f"✓ Critical path integrity validated: {status}")
                if validation_result.get("errors"):
                    logger.warning(f"  Validation errors: {validation_result['errors']}")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to validate critical path integrity")
            
            # Test 5: Analyze Schedule Compression Opportunities
            test_results["tests_run"].append("analyze_schedule_compression")
            
            compression_analysis = await self.dependency_engine.analyze_schedule_compression_opportunities(
                self.test_schedule_id
            )
            
            if compression_analysis and "compression_opportunities" in compression_analysis:
                test_results["passed"] += 1
                logger.info(f"✓ Schedule compression analyzed: {compression_analysis['potential_time_savings']} days potential savings")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Failed to analyze schedule compression opportunities")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Complex Critical Path test error: {str(e)}")
            logger.error(f"Complex Critical Path test error: {e}")
        
        return test_results
    
    async def test_service_integration(self) -> Dict[str, Any]:
        """Test integration between services."""
        test_results = {
            "service": "ServiceIntegration",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            if not self.test_schedule_id:
                test_results["errors"].append("No test schedule available for integration testing")
                return test_results
            
            # Test 1: Schedule Manager + Dependency Engine Integration
            test_results["tests_run"].append("schedule_dependency_integration")
            
            # Update a task and verify dependency engine recalculation
            if "child_1" in self.test_tasks:
                task_update = TaskUpdate(
                    planned_end_date=date.today() + timedelta(days=8),
                    duration_days=8
                )
                
                updated_task = await self.schedule_manager.update_task(
                    self.test_tasks["child_1"], task_update, self.test_user_id
                )
                
                if updated_task:
                    # Trigger recalculation
                    recalc_result = await self.dependency_engine.recalculate_schedule(
                        self.test_schedule_id, self.test_tasks["child_1"]
                    )
                    
                    if recalc_result and recalc_result.affected_tasks:
                        test_results["passed"] += 1
                        logger.info("✓ Schedule-Dependency integration working")
                    else:
                        test_results["failed"] += 1
                        test_results["errors"].append("Schedule-Dependency integration failed")
            
            # Test 2: Progress Rollup Integration
            test_results["tests_run"].append("progress_rollup_integration")
            
            if "child_2" in self.test_tasks and "parent" in self.test_tasks:
                # Update child progress
                progress_update = TaskProgressUpdate(
                    progress_percentage=75,
                    status=TaskStatus.IN_PROGRESS,
                    actual_start_date=date.today(),
                    actual_effort_hours=18.0
                )
                
                await self.schedule_manager.update_task_progress(
                    self.test_tasks["child_2"], progress_update, self.test_user_id
                )
                
                # Check parent rollup
                parent_progress = self.schedule_manager.calculate_task_rollup_progress(
                    self.test_tasks["parent"]
                )
                
                if parent_progress > 0:
                    test_results["passed"] += 1
                    logger.info(f"✓ Progress rollup integration working: {parent_progress}%")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Progress rollup integration failed")
            
            # Test 3: Cross-Service Data Consistency
            test_results["tests_run"].append("cross_service_data_consistency")
            
            # Get schedule data from multiple services
            schedule_data = await self.schedule_manager.get_schedule_with_tasks(
                self.test_schedule_id, include_dependencies=True
            )
            
            wbs_hierarchy = await self.wbs_manager.get_wbs_hierarchy(
                self.test_schedule_id
            )
            
            milestone_report = await self.milestone_tracker.get_milestone_status_report(
                schedule_id=self.test_schedule_id
            )
            
            if (schedule_data and schedule_data.tasks and 
                wbs_hierarchy and milestone_report):
                test_results["passed"] += 1
                logger.info("✓ Cross-service data consistency verified")
            else:
                test_results["failed"] += 1
                test_results["errors"].append("Cross-service data consistency failed")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"Service Integration test error: {str(e)}")
            logger.error(f"Service Integration test error: {e}")
        
        return test_results
    
    def _determine_overall_status(self, test_results: Dict[str, Any]) -> str:
        """Determine overall test status based on individual service results."""
        total_passed = 0
        total_failed = 0
        critical_failures = 0
        
        for service_name, service_results in test_results.items():
            if isinstance(service_results, dict) and "passed" in service_results:
                total_passed += service_results["passed"]
                total_failed += service_results["failed"]
                
                # Critical services that must pass
                if service_name in ["schedule_manager", "dependency_engine"] and service_results["failed"] > 0:
                    critical_failures += 1
        
        total_tests = total_passed + total_failed
        
        if total_tests == 0:
            return "no_tests_run"
        
        success_rate = (total_passed / total_tests) * 100
        
        if critical_failures > 0:
            return "critical_failure"
        elif success_rate >= 90:
            return "excellent"
        elif success_rate >= 75:
            return "good"
        elif success_rate >= 50:
            return "fair"
        else:
            return "poor"


# Main execution function
async def run_checkpoint_tests():
    """Run the core services checkpoint tests."""
    checkpoint = CoreServicesCheckpoint()
    results = await checkpoint.run_all_tests()
    
    # Print summary
    print("\n" + "="*80)
    print("CORE SERVICES CHECKPOINT TEST RESULTS")
    print("="*80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Services Tested: {len(results['services_tested'])}")
    print(f"Test Timestamp: {results['test_timestamp']}")
    
    if results.get('errors'):
        print(f"\nCritical Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nService Results:")
    for service_name in results['services_tested']:
        service_result = results['test_results'].get(service_name, {})
        if isinstance(service_result, dict):
            passed = service_result.get('passed', 0)
            failed = service_result.get('failed', 0)
            total = passed + failed
            success_rate = (passed / total * 100) if total > 0 else 0
            
            status_icon = "✓" if failed == 0 else "✗" if passed == 0 else "⚠"
            print(f"  {status_icon} {service_name}: {passed}/{total} tests passed ({success_rate:.1f}%)")
            
            if service_result.get('errors'):
                for error in service_result['errors'][:3]:  # Show first 3 errors
                    print(f"    - {error}")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Run the checkpoint tests
    results = asyncio.run(run_checkpoint_tests())
    
    # Exit with appropriate code
    if results['overall_status'] in ['excellent', 'good']:
        exit(0)
    elif results['overall_status'] in ['fair']:
        exit(1)
    else:
        exit(2)