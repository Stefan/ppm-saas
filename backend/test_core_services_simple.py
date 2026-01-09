"""
Simplified Core Services Checkpoint Test

Tests core service functionality without requiring existing project data.
Focuses on service instantiation, method availability, and basic validation.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any

# Import all core services
from services.schedule_manager import ScheduleManager
from services.task_dependency_engine import TaskDependencyEngine
from services.wbs_manager import WBSManager
from services.milestone_tracker import MilestoneTracker
from services.resource_assignment_service import ResourceAssignmentService
from services.baseline_manager import BaselineManager

# Import models
from models.schedule import (
    ScheduleCreate, TaskCreate, TaskDependencyCreate, DependencyType,
    WBSElementCreate, MilestoneCreate, ResourceAssignmentCreate,
    ScheduleBaselineCreate, TaskStatus, MilestoneStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCoreServicesTest:
    """
    Simplified test suite that validates core service functionality
    without requiring complex database setup.
    """
    
    def __init__(self):
        self.test_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "overall_status": "unknown"
        }
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all simplified tests."""
        logger.info("Starting Simplified Core Services Tests")
        
        # Test 1: Service Instantiation
        await self.test_service_instantiation()
        
        # Test 2: Model Validation
        await self.test_model_validation()
        
        # Test 3: Method Availability
        await self.test_method_availability()
        
        # Test 4: Database Connection
        await self.test_database_connections()
        
        # Test 5: Business Logic Validation
        await self.test_business_logic_validation()
        
        # Determine overall status
        self.test_results["overall_status"] = self._determine_status()
        
        return self.test_results
    
    async def test_service_instantiation(self):
        """Test that all services can be instantiated."""
        logger.info("Testing service instantiation...")
        
        services_to_test = [
            ("ScheduleManager", ScheduleManager),
            ("TaskDependencyEngine", TaskDependencyEngine),
            ("WBSManager", WBSManager),
            ("MilestoneTracker", MilestoneTracker),
            ("ResourceAssignmentService", ResourceAssignmentService),
            ("BaselineManager", BaselineManager)
        ]
        
        for service_name, service_class in services_to_test:
            try:
                service_instance = service_class()
                self.test_results["services"][service_name] = {
                    "instantiation": "success",
                    "has_db_connection": hasattr(service_instance, 'db') and service_instance.db is not None,
                    "methods": [],
                    "errors": []
                }
                logger.info(f"✓ {service_name} instantiated successfully")
            except Exception as e:
                self.test_results["services"][service_name] = {
                    "instantiation": "failed",
                    "error": str(e),
                    "methods": [],
                    "errors": [str(e)]
                }
                logger.error(f"✗ {service_name} instantiation failed: {e}")
    
    async def test_model_validation(self):
        """Test that Pydantic models work correctly."""
        logger.info("Testing model validation...")
        
        model_tests = []
        
        try:
            # Test ScheduleCreate model
            schedule_data = ScheduleCreate(
                project_id=uuid4(),
                name="Test Schedule",
                description="Test description",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30)
            )
            model_tests.append(("ScheduleCreate", "success"))
            
            # Test TaskCreate model
            task_data = TaskCreate(
                wbs_code="1.0",
                name="Test Task",
                description="Test task description",
                planned_start_date=date.today(),
                planned_end_date=date.today() + timedelta(days=5),
                duration_days=5,
                planned_effort_hours=40.0,
                deliverables=["Test Deliverable"]
            )
            model_tests.append(("TaskCreate", "success"))
            
            # Test TaskDependencyCreate model
            dependency_data = TaskDependencyCreate(
                predecessor_task_id=uuid4(),
                successor_task_id=uuid4(),
                dependency_type=DependencyType.FINISH_TO_START,
                lag_days=0
            )
            model_tests.append(("TaskDependencyCreate", "success"))
            
            # Test WBSElementCreate model
            wbs_data = WBSElementCreate(
                wbs_code="1.0",
                name="Test WBS Element",
                description="Test WBS description"
            )
            model_tests.append(("WBSElementCreate", "success"))
            
            # Test MilestoneCreate model
            milestone_data = MilestoneCreate(
                name="Test Milestone",
                description="Test milestone description",
                target_date=date.today() + timedelta(days=15),
                deliverables=["Milestone Deliverable"]
            )
            model_tests.append(("MilestoneCreate", "success"))
            
            # Test ResourceAssignmentCreate model
            resource_data = ResourceAssignmentCreate(
                resource_id=uuid4(),
                allocation_percentage=75,
                planned_hours=30.0
            )
            model_tests.append(("ResourceAssignmentCreate", "success"))
            
            # Test ScheduleBaselineCreate model
            baseline_data = ScheduleBaselineCreate(
                baseline_name="Test Baseline",
                baseline_date=date.today(),
                description="Test baseline description",
                baseline_data={"version": "1.0"}
            )
            model_tests.append(("ScheduleBaselineCreate", "success"))
            
        except Exception as e:
            model_tests.append(("ModelValidation", f"failed: {str(e)}"))
        
        self.test_results["model_validation"] = model_tests
        
        success_count = len([t for t in model_tests if t[1] == "success"])
        logger.info(f"✓ Model validation: {success_count}/{len(model_tests)} models validated")
    
    async def test_method_availability(self):
        """Test that required methods are available on each service."""
        logger.info("Testing method availability...")
        
        method_requirements = {
            "ScheduleManager": [
                "create_schedule", "create_task", "update_task", "get_schedule_with_tasks",
                "update_task_progress", "calculate_task_rollup_progress"
            ],
            "TaskDependencyEngine": [
                "create_dependency", "calculate_critical_path", "detect_circular_dependencies",
                "calculate_task_dates", "recalculate_schedule"
            ],
            "WBSManager": [
                "create_wbs_element", "get_wbs_hierarchy", "validate_wbs_structure",
                "generate_wbs_code"
            ],
            "MilestoneTracker": [
                "create_milestone", "update_milestone_status", "get_milestone_status_report",
                "get_at_risk_milestones"
            ],
            "ResourceAssignmentService": [
                "assign_resource_to_task", "detect_resource_conflicts",
                "calculate_resource_utilization"
            ],
            "BaselineManager": [
                "create_baseline", "calculate_schedule_variance",
                "calculate_earned_value_metrics", "get_baseline_versions"
            ]
        }
        
        for service_name, required_methods in method_requirements.items():
            if service_name in self.test_results["services"]:
                service_result = self.test_results["services"][service_name]
                
                try:
                    if service_result["instantiation"] == "success":
                        service_class = globals()[service_name.replace("Manager", "Manager").replace("Service", "Service").replace("Engine", "Engine").replace("Tracker", "Tracker")]
                        service_instance = service_class()
                        
                        available_methods = []
                        missing_methods = []
                        
                        for method_name in required_methods:
                            if hasattr(service_instance, method_name) and callable(getattr(service_instance, method_name)):
                                available_methods.append(method_name)
                            else:
                                missing_methods.append(method_name)
                        
                        service_result["methods"] = {
                            "available": available_methods,
                            "missing": missing_methods,
                            "coverage": len(available_methods) / len(required_methods) * 100
                        }
                        
                        if missing_methods:
                            logger.warning(f"⚠ {service_name}: Missing methods {missing_methods}")
                        else:
                            logger.info(f"✓ {service_name}: All required methods available")
                
                except Exception as e:
                    service_result["errors"].append(f"Method availability test failed: {str(e)}")
    
    async def test_database_connections(self):
        """Test database connections for all services."""
        logger.info("Testing database connections...")
        
        for service_name, service_data in self.test_results["services"].items():
            if service_data["instantiation"] == "success":
                try:
                    service_class = {
                        "ScheduleManager": ScheduleManager,
                        "TaskDependencyEngine": TaskDependencyEngine,
                        "WBSManager": WBSManager,
                        "MilestoneTracker": MilestoneTracker,
                        "ResourceAssignmentService": ResourceAssignmentService,
                        "BaselineManager": BaselineManager
                    }[service_name]
                    
                    service_instance = service_class()
                    
                    # Check if database connection exists
                    if hasattr(service_instance, 'db') and service_instance.db is not None:
                        service_data["database_connection"] = "available"
                        logger.info(f"✓ {service_name}: Database connection available")
                    else:
                        service_data["database_connection"] = "unavailable"
                        logger.warning(f"⚠ {service_name}: Database connection unavailable")
                
                except Exception as e:
                    service_data["database_connection"] = f"error: {str(e)}"
                    service_data["errors"].append(f"Database connection test failed: {str(e)}")
    
    async def test_business_logic_validation(self):
        """Test basic business logic validation."""
        logger.info("Testing business logic validation...")
        
        validation_tests = []
        
        try:
            # Test 1: Date validation in models
            try:
                invalid_schedule = ScheduleCreate(
                    project_id=uuid4(),
                    name="Invalid Schedule",
                    start_date=date.today(),
                    end_date=date.today() - timedelta(days=1)  # End before start
                )
                validation_tests.append(("Date validation", "failed - should have caught invalid dates"))
            except Exception:
                validation_tests.append(("Date validation", "success - caught invalid dates"))
            
            # Test 2: Self-dependency validation
            try:
                task_id = uuid4()
                invalid_dependency = TaskDependencyCreate(
                    predecessor_task_id=task_id,
                    successor_task_id=task_id,  # Self-dependency
                    dependency_type=DependencyType.FINISH_TO_START
                )
                validation_tests.append(("Self-dependency validation", "failed - should have caught self-dependency"))
            except Exception:
                validation_tests.append(("Self-dependency validation", "success - caught self-dependency"))
            
            # Test 3: Percentage validation
            try:
                invalid_resource = ResourceAssignmentCreate(
                    resource_id=uuid4(),
                    allocation_percentage=150,  # Over 100%
                    planned_hours=40.0
                )
                validation_tests.append(("Percentage validation", "failed - should have caught invalid percentage"))
            except Exception:
                validation_tests.append(("Percentage validation", "success - caught invalid percentage"))
            
            # Test 4: WBS Manager code generation
            try:
                wbs_manager = WBSManager()
                generated_code = wbs_manager.generate_wbs_code("1.0", 3)
                if generated_code == "1.0.3":
                    validation_tests.append(("WBS code generation", "success"))
                else:
                    validation_tests.append(("WBS code generation", f"failed - got {generated_code}"))
            except Exception as e:
                validation_tests.append(("WBS code generation", f"error: {str(e)}"))
            
        except Exception as e:
            validation_tests.append(("Business logic validation", f"error: {str(e)}"))
        
        self.test_results["business_logic_validation"] = validation_tests
        
        success_count = len([t for t in validation_tests if "success" in t[1]])
        logger.info(f"✓ Business logic validation: {success_count}/{len(validation_tests)} tests passed")
    
    def _determine_status(self) -> str:
        """Determine overall test status."""
        services = self.test_results.get("services", {})
        
        if not services:
            return "no_services_tested"
        
        successful_instantiations = len([s for s in services.values() if s.get("instantiation") == "success"])
        total_services = len(services)
        
        success_rate = (successful_instantiations / total_services) * 100
        
        # Check method coverage
        method_coverage_scores = []
        for service_data in services.values():
            if "methods" in service_data and "coverage" in service_data["methods"]:
                method_coverage_scores.append(service_data["methods"]["coverage"])
        
        avg_method_coverage = sum(method_coverage_scores) / len(method_coverage_scores) if method_coverage_scores else 0
        
        # Check business logic validation
        validation_tests = self.test_results.get("business_logic_validation", [])
        validation_success_rate = len([t for t in validation_tests if "success" in t[1]]) / len(validation_tests) * 100 if validation_tests else 0
        
        # Determine overall status
        if success_rate == 100 and avg_method_coverage >= 90 and validation_success_rate >= 75:
            return "excellent"
        elif success_rate >= 80 and avg_method_coverage >= 75:
            return "good"
        elif success_rate >= 60:
            return "fair"
        else:
            return "poor"


async def run_simple_tests():
    """Run the simplified core services tests."""
    test_runner = SimpleCoreServicesTest()
    results = await test_runner.run_tests()
    
    # Print results
    print("\n" + "="*80)
    print("SIMPLIFIED CORE SERVICES TEST RESULTS")
    print("="*80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Test Timestamp: {results['test_timestamp']}")
    
    print("\nService Instantiation Results:")
    for service_name, service_data in results.get("services", {}).items():
        status_icon = "✓" if service_data.get("instantiation") == "success" else "✗"
        db_status = "DB: ✓" if service_data.get("has_db_connection") else "DB: ✗"
        
        print(f"  {status_icon} {service_name} - {db_status}")
        
        if "methods" in service_data:
            coverage = service_data["methods"].get("coverage", 0)
            missing = len(service_data["methods"].get("missing", []))
            print(f"    Method Coverage: {coverage:.1f}% ({missing} missing)")
        
        if service_data.get("errors"):
            for error in service_data["errors"][:2]:  # Show first 2 errors
                print(f"    Error: {error}")
    
    print("\nModel Validation Results:")
    for model_name, status in results.get("model_validation", []):
        status_icon = "✓" if status == "success" else "✗"
        print(f"  {status_icon} {model_name}: {status}")
    
    print("\nBusiness Logic Validation Results:")
    for test_name, status in results.get("business_logic_validation", []):
        status_icon = "✓" if "success" in status else "✗"
        print(f"  {status_icon} {test_name}: {status}")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Run the simplified tests
    results = asyncio.run(run_simple_tests())
    
    # Exit with appropriate code
    if results['overall_status'] in ['excellent', 'good']:
        exit(0)
    elif results['overall_status'] == 'fair':
        exit(1)
    else:
        exit(2)