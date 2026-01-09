"""
Baseline Manager Service

Handles all baseline management operations including:
- Baseline creation and versioning
- Baseline comparison and variance calculations
- Baseline approval workflow
- Schedule performance index calculations
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from enum import Enum
import logging
import json
from decimal import Decimal

from config.database import supabase
from models.schedule import (
    ScheduleBaselineCreate, ScheduleBaselineResponse,
    ScheduleResponse, TaskResponse, ScheduleWithTasksResponse
)

logger = logging.getLogger(__name__)

class BaselineManager:
    """
    Handles all baseline management operations.
    
    Provides:
    - Baseline creation and versioning
    - Baseline comparison and variance calculations
    - Baseline approval workflow
    - Schedule performance index calculations
    """
    
    def __init__(self):
        self.db = supabase
        if not self.db:
            raise RuntimeError("Database connection not available")
    
    async def create_baseline(
        self,
        schedule_id: UUID,
        baseline_data: ScheduleBaselineCreate,
        created_by: UUID
    ) -> ScheduleBaselineResponse:
        """
        Create a new schedule baseline with complete schedule snapshot.
        
        Args:
            schedule_id: ID of the schedule
            baseline_data: Baseline creation data
            created_by: ID of the user creating the baseline
            
        Returns:
            ScheduleBaselineResponse: Created baseline data
        """
        try:
            # Validate schedule exists
            schedule_result = self.db.table("schedules").select("*").eq("id", str(schedule_id)).execute()
            if not schedule_result.data:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            schedule = schedule_result.data[0]
            
            # Get all tasks for the schedule
            tasks_result = self.db.table("tasks").select("*").eq("schedule_id", str(schedule_id)).execute()
            tasks = tasks_result.data or []
            
            # Get all dependencies
            if tasks:
                task_ids = [task["id"] for task in tasks]
                deps_result = self.db.table("task_dependencies").select("*").execute()
                dependencies = []
                if deps_result.data:
                    dependencies = [
                        dep for dep in deps_result.data
                        if dep["predecessor_task_id"] in task_ids or dep["successor_task_id"] in task_ids
                    ]
            else:
                dependencies = []
            
            # Get milestones
            milestones_result = self.db.table("milestones").select("*").eq("schedule_id", str(schedule_id)).execute()
            milestones = milestones_result.data or []
            
            # Create baseline snapshot
            baseline_snapshot = {
                "schedule": schedule,
                "tasks": tasks,
                "dependencies": dependencies,
                "milestones": milestones,
                "baseline_metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": str(created_by),
                    "total_tasks": len(tasks),
                    "total_dependencies": len(dependencies),
                    "total_milestones": len(milestones)
                }
            }
            
            # Merge with provided baseline data
            final_baseline_data = {
                **baseline_data.baseline_data,
                "snapshot": baseline_snapshot
            }
            
            # Prepare baseline record
            baseline_record = {
                "id": str(uuid4()),
                "schedule_id": str(schedule_id),
                "baseline_name": baseline_data.baseline_name,
                "baseline_date": baseline_data.baseline_date.isoformat(),
                "description": baseline_data.description,
                "baseline_data": json.dumps(final_baseline_data),
                "is_approved": False,
                "created_by": str(created_by),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert baseline
            result = self.db.table("schedule_baselines").insert(baseline_record).execute()
            
            if not result.data:
                raise RuntimeError("Failed to create baseline")
            
            created_baseline = result.data[0]
            
            # Update schedule with baseline dates if this is the first approved baseline
            await self._update_schedule_baseline_dates(schedule_id, baseline_data.baseline_date)
            
            return self._convert_baseline_to_response(created_baseline)
            
        except Exception as e:
            logger.error(f"Error creating baseline: {e}")
            raise RuntimeError(f"Failed to create baseline: {str(e)}")
    
    async def approve_baseline(
        self,
        baseline_id: UUID,
        approved_by: UUID
    ) -> ScheduleBaselineResponse:
        """
        Approve a baseline and set it as the official project baseline.
        
        Args:
            baseline_id: ID of the baseline to approve
            approved_by: ID of the user approving the baseline
            
        Returns:
            ScheduleBaselineResponse: Approved baseline data
        """
        try:
            # Get existing baseline
            existing_result = self.db.table("schedule_baselines").select("*").eq("id", str(baseline_id)).execute()
            if not existing_result.data:
                raise ValueError(f"Baseline {baseline_id} not found")
            
            existing_baseline = existing_result.data[0]
            
            # Update baseline approval
            update_data = {
                "is_approved": True,
                "approved_by": str(approved_by),
                "approved_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("schedule_baselines").update(update_data).eq("id", str(baseline_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to approve baseline")
            
            approved_baseline = result.data[0]
            
            # Update schedule and tasks with baseline data
            await self._apply_baseline_to_schedule(
                UUID(existing_baseline["schedule_id"]), 
                json.loads(existing_baseline["baseline_data"])
            )
            
            return self._convert_baseline_to_response(approved_baseline)
            
        except Exception as e:
            logger.error(f"Error approving baseline {baseline_id}: {e}")
            raise RuntimeError(f"Failed to approve baseline: {str(e)}")
    
    async def calculate_schedule_variance(
        self,
        schedule_id: UUID,
        baseline_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculate schedule variance against baseline.
        
        Args:
            schedule_id: ID of the schedule
            baseline_id: ID of specific baseline (uses latest approved if None)
            
        Returns:
            Dict with variance calculations
        """
        try:
            # Get baseline
            if baseline_id:
                baseline_result = self.db.table("schedule_baselines").select("*").eq("id", str(baseline_id)).execute()
            else:
                # Get latest approved baseline
                baseline_result = self.db.table("schedule_baselines").select("*").eq(
                    "schedule_id", str(schedule_id)
                ).eq("is_approved", True).order("created_at", desc=True).limit(1).execute()
            
            if not baseline_result.data:
                raise ValueError("No baseline found for variance calculation")
            
            baseline = baseline_result.data[0]
            baseline_data = json.loads(baseline["baseline_data"])
            baseline_tasks = baseline_data["snapshot"]["tasks"]
            
            # Get current schedule and tasks
            current_schedule_result = self.db.table("schedules").select("*").eq("id", str(schedule_id)).execute()
            if not current_schedule_result.data:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            current_schedule = current_schedule_result.data[0]
            
            current_tasks_result = self.db.table("tasks").select("*").eq("schedule_id", str(schedule_id)).execute()
            current_tasks = current_tasks_result.data or []
            
            # Calculate variances
            task_variances = []
            total_baseline_duration = 0
            total_current_duration = 0
            total_schedule_variance_days = 0
            
            # Create lookup for current tasks
            current_tasks_map = {task["id"]: task for task in current_tasks}
            
            for baseline_task in baseline_tasks:
                task_id = baseline_task["id"]
                current_task = current_tasks_map.get(task_id)
                
                if current_task:
                    # Calculate date variances
                    baseline_start = date.fromisoformat(baseline_task["planned_start_date"])
                    baseline_end = date.fromisoformat(baseline_task["planned_end_date"])
                    current_start = date.fromisoformat(current_task["planned_start_date"])
                    current_end = date.fromisoformat(current_task["planned_end_date"])
                    
                    start_variance_days = (current_start - baseline_start).days
                    end_variance_days = (current_end - baseline_end).days
                    duration_variance_days = current_task["duration_days"] - baseline_task["duration_days"]
                    
                    # Calculate progress variance
                    baseline_progress = baseline_task.get("progress_percentage", 0)
                    current_progress = current_task.get("progress_percentage", 0)
                    progress_variance = current_progress - baseline_progress
                    
                    task_variance = {
                        "task_id": task_id,
                        "task_name": current_task["name"],
                        "wbs_code": current_task["wbs_code"],
                        "start_variance_days": start_variance_days,
                        "end_variance_days": end_variance_days,
                        "duration_variance_days": duration_variance_days,
                        "progress_variance": progress_variance,
                        "baseline_start_date": baseline_start.isoformat(),
                        "baseline_end_date": baseline_end.isoformat(),
                        "current_start_date": current_start.isoformat(),
                        "current_end_date": current_end.isoformat(),
                        "is_critical": current_task.get("is_critical", False)
                    }
                    
                    task_variances.append(task_variance)
                    total_baseline_duration += baseline_task["duration_days"]
                    total_current_duration += current_task["duration_days"]
                    total_schedule_variance_days += duration_variance_days
            
            # Calculate overall schedule variance
            baseline_schedule_start = date.fromisoformat(baseline_data["snapshot"]["schedule"]["start_date"])
            baseline_schedule_end = date.fromisoformat(baseline_data["snapshot"]["schedule"]["end_date"])
            current_schedule_start = date.fromisoformat(current_schedule["start_date"])
            current_schedule_end = date.fromisoformat(current_schedule["end_date"])
            
            schedule_start_variance_days = (current_schedule_start - baseline_schedule_start).days
            schedule_end_variance_days = (current_schedule_end - baseline_schedule_end).days
            
            # Calculate schedule performance index (SPI)
            spi = self._calculate_schedule_performance_index(current_tasks, baseline_tasks)
            
            return {
                "schedule_id": str(schedule_id),
                "baseline_id": baseline["id"],
                "baseline_name": baseline["baseline_name"],
                "variance_calculation_date": datetime.utcnow().isoformat(),
                "schedule_variance": {
                    "start_variance_days": schedule_start_variance_days,
                    "end_variance_days": schedule_end_variance_days,
                    "total_duration_variance_days": total_schedule_variance_days,
                    "schedule_performance_index": spi
                },
                "task_variances": task_variances,
                "summary": {
                    "total_tasks_analyzed": len(task_variances),
                    "tasks_ahead_of_schedule": len([t for t in task_variances if t["end_variance_days"] < 0]),
                    "tasks_behind_schedule": len([t for t in task_variances if t["end_variance_days"] > 0]),
                    "tasks_on_schedule": len([t for t in task_variances if t["end_variance_days"] == 0]),
                    "average_duration_variance": total_schedule_variance_days / len(task_variances) if task_variances else 0,
                    "critical_tasks_with_variance": len([t for t in task_variances if t["is_critical"] and t["end_variance_days"] != 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating schedule variance: {e}")
            raise RuntimeError(f"Failed to calculate schedule variance: {str(e)}")
    
    async def get_baseline_versions(
        self,
        schedule_id: UUID
    ) -> List[ScheduleBaselineResponse]:
        """
        Get all baseline versions for a schedule.
        
        Args:
            schedule_id: ID of the schedule
            
        Returns:
            List of baseline versions
        """
        try:
            result = self.db.table("schedule_baselines").select("*").eq(
                "schedule_id", str(schedule_id)
            ).order("created_at", desc=True).execute()
            
            if not result.data:
                return []
            
            return [self._convert_baseline_to_response(baseline) for baseline in result.data]
            
        except Exception as e:
            logger.error(f"Error getting baseline versions for schedule {schedule_id}: {e}")
            raise RuntimeError(f"Failed to get baseline versions: {str(e)}")
    
    async def get_baseline(
        self,
        baseline_id: UUID
    ) -> Optional[ScheduleBaselineResponse]:
        """
        Get a specific baseline by ID.
        
        Args:
            baseline_id: ID of the baseline
            
        Returns:
            ScheduleBaselineResponse or None if not found
        """
        try:
            result = self.db.table("schedule_baselines").select("*").eq("id", str(baseline_id)).execute()
            
            if not result.data:
                return None
            
            return self._convert_baseline_to_response(result.data[0])
            
        except Exception as e:
            logger.error(f"Error getting baseline {baseline_id}: {e}")
            return None
    
    async def delete_baseline(
        self,
        baseline_id: UUID
    ) -> bool:
        """
        Delete a baseline (only if not approved).
        
        Args:
            baseline_id: ID of the baseline to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Check if baseline is approved
            existing_result = self.db.table("schedule_baselines").select("is_approved").eq("id", str(baseline_id)).execute()
            if not existing_result.data:
                return False
            
            if existing_result.data[0]["is_approved"]:
                raise ValueError("Cannot delete approved baseline")
            
            # Delete baseline
            result = self.db.table("schedule_baselines").delete().eq("id", str(baseline_id)).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error deleting baseline {baseline_id}: {e}")
            return False
    
    async def calculate_earned_value_metrics(
        self,
        schedule_id: UUID,
        baseline_id: Optional[UUID] = None,
        status_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate earned value metrics for schedule performance.
        
        Args:
            schedule_id: ID of the schedule
            baseline_id: ID of specific baseline (uses latest approved if None)
            status_date: Date for calculations (uses today if None)
            
        Returns:
            Dict with earned value metrics
        """
        try:
            if not status_date:
                status_date = date.today()
            
            # Get baseline
            if baseline_id:
                baseline_result = self.db.table("schedule_baselines").select("*").eq("id", str(baseline_id)).execute()
            else:
                baseline_result = self.db.table("schedule_baselines").select("*").eq(
                    "schedule_id", str(schedule_id)
                ).eq("is_approved", True).order("created_at", desc=True).limit(1).execute()
            
            if not baseline_result.data:
                raise ValueError("No baseline found for earned value calculation")
            
            baseline = baseline_result.data[0]
            baseline_data = json.loads(baseline["baseline_data"])
            baseline_tasks = baseline_data["snapshot"]["tasks"]
            
            # Get current tasks
            current_tasks_result = self.db.table("tasks").select("*").eq("schedule_id", str(schedule_id)).execute()
            current_tasks = current_tasks_result.data or []
            current_tasks_map = {task["id"]: task for task in current_tasks}
            
            # Calculate earned value metrics
            total_planned_value = 0.0  # BCWS - Budgeted Cost of Work Scheduled
            total_earned_value = 0.0   # BCWP - Budgeted Cost of Work Performed
            total_actual_cost = 0.0    # ACWP - Actual Cost of Work Performed
            
            task_metrics = []
            
            for baseline_task in baseline_tasks:
                task_id = baseline_task["id"]
                current_task = current_tasks_map.get(task_id)
                
                if current_task:
                    # Calculate planned value (should be done by status date)
                    baseline_start = date.fromisoformat(baseline_task["planned_start_date"])
                    baseline_end = date.fromisoformat(baseline_task["planned_end_date"])
                    baseline_effort = baseline_task.get("planned_effort_hours", 0) or 0
                    
                    if status_date >= baseline_end:
                        # Task should be 100% complete
                        planned_value = baseline_effort
                    elif status_date >= baseline_start:
                        # Task should be partially complete
                        total_duration = (baseline_end - baseline_start).days + 1
                        elapsed_duration = (status_date - baseline_start).days + 1
                        planned_progress = min(100, (elapsed_duration / total_duration) * 100)
                        planned_value = baseline_effort * (planned_progress / 100)
                    else:
                        # Task should not have started
                        planned_value = 0
                    
                    # Calculate earned value (actual progress * baseline effort)
                    current_progress = current_task.get("progress_percentage", 0)
                    earned_value = baseline_effort * (current_progress / 100)
                    
                    # Calculate actual cost (actual effort hours)
                    actual_cost = current_task.get("actual_effort_hours", 0) or 0
                    
                    task_metric = {
                        "task_id": task_id,
                        "task_name": current_task["name"],
                        "wbs_code": current_task["wbs_code"],
                        "planned_value": planned_value,
                        "earned_value": earned_value,
                        "actual_cost": actual_cost,
                        "schedule_variance": earned_value - planned_value,
                        "cost_variance": earned_value - actual_cost,
                        "schedule_performance_index": earned_value / planned_value if planned_value > 0 else 0,
                        "cost_performance_index": earned_value / actual_cost if actual_cost > 0 else 0
                    }
                    
                    task_metrics.append(task_metric)
                    total_planned_value += planned_value
                    total_earned_value += earned_value
                    total_actual_cost += actual_cost
            
            # Calculate overall metrics
            schedule_variance = total_earned_value - total_planned_value
            cost_variance = total_earned_value - total_actual_cost
            schedule_performance_index = total_earned_value / total_planned_value if total_planned_value > 0 else 0
            cost_performance_index = total_earned_value / total_actual_cost if total_actual_cost > 0 else 0
            
            # Calculate estimates
            estimate_at_completion = total_actual_cost / cost_performance_index if cost_performance_index > 0 else 0
            estimate_to_complete = estimate_at_completion - total_actual_cost
            variance_at_completion = total_planned_value - estimate_at_completion
            
            return {
                "schedule_id": str(schedule_id),
                "baseline_id": baseline["id"],
                "status_date": status_date.isoformat(),
                "calculation_timestamp": datetime.utcnow().isoformat(),
                "summary_metrics": {
                    "planned_value": round(total_planned_value, 2),
                    "earned_value": round(total_earned_value, 2),
                    "actual_cost": round(total_actual_cost, 2),
                    "schedule_variance": round(schedule_variance, 2),
                    "cost_variance": round(cost_variance, 2),
                    "schedule_performance_index": round(schedule_performance_index, 3),
                    "cost_performance_index": round(cost_performance_index, 3),
                    "estimate_at_completion": round(estimate_at_completion, 2),
                    "estimate_to_complete": round(estimate_to_complete, 2),
                    "variance_at_completion": round(variance_at_completion, 2)
                },
                "task_metrics": task_metrics,
                "performance_indicators": {
                    "schedule_status": self._get_performance_status(schedule_performance_index),
                    "cost_status": self._get_performance_status(cost_performance_index),
                    "overall_health": self._get_overall_health(schedule_performance_index, cost_performance_index)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating earned value metrics: {e}")
            raise RuntimeError(f"Failed to calculate earned value metrics: {str(e)}")
    
    # Private helper methods
    
    def _convert_baseline_to_response(self, baseline_data: Dict[str, Any]) -> ScheduleBaselineResponse:
        """Convert database baseline record to ScheduleBaselineResponse model."""
        return ScheduleBaselineResponse(
            id=baseline_data["id"],
            schedule_id=baseline_data["schedule_id"],
            baseline_name=baseline_data["baseline_name"],
            baseline_date=date.fromisoformat(baseline_data["baseline_date"]),
            description=baseline_data.get("description"),
            baseline_data=json.loads(baseline_data["baseline_data"]),
            is_approved=baseline_data["is_approved"],
            approved_by=baseline_data.get("approved_by"),
            approved_at=datetime.fromisoformat(baseline_data["approved_at"].replace('Z', '+00:00')) if baseline_data.get("approved_at") else None,
            created_by=baseline_data["created_by"],
            created_at=datetime.fromisoformat(baseline_data["created_at"].replace('Z', '+00:00'))
        )
    
    async def _update_schedule_baseline_dates(self, schedule_id: UUID, baseline_date: date) -> None:
        """
        Update schedule with baseline dates.
        
        Args:
            schedule_id: ID of the schedule
            baseline_date: Date of the baseline
        """
        try:
            # Get current schedule
            schedule_result = self.db.table("schedules").select("*").eq("id", str(schedule_id)).execute()
            if not schedule_result.data:
                return
            
            schedule = schedule_result.data[0]
            
            # Update baseline dates if not already set
            update_data = {}
            if not schedule.get("baseline_start_date"):
                update_data["baseline_start_date"] = schedule["start_date"]
            if not schedule.get("baseline_end_date"):
                update_data["baseline_end_date"] = schedule["end_date"]
            
            if update_data:
                self.db.table("schedules").update(update_data).eq("id", str(schedule_id)).execute()
                
        except Exception as e:
            logger.error(f"Error updating schedule baseline dates: {e}")
    
    async def _apply_baseline_to_schedule(self, schedule_id: UUID, baseline_data: Dict[str, Any]) -> None:
        """
        Apply baseline data to schedule and tasks.
        
        Args:
            schedule_id: ID of the schedule
            baseline_data: Baseline data to apply
        """
        try:
            baseline_tasks = baseline_data["snapshot"]["tasks"]
            
            # Update tasks with baseline data
            for baseline_task in baseline_tasks:
                task_id = baseline_task["id"]
                
                update_data = {
                    "baseline_start_date": baseline_task["planned_start_date"],
                    "baseline_end_date": baseline_task["planned_end_date"],
                    "baseline_duration_days": baseline_task["duration_days"]
                }
                
                self.db.table("tasks").update(update_data).eq("id", task_id).execute()
                
        except Exception as e:
            logger.error(f"Error applying baseline to schedule: {e}")
    
    def _calculate_schedule_performance_index(
        self, 
        current_tasks: List[Dict[str, Any]], 
        baseline_tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate Schedule Performance Index (SPI).
        
        Args:
            current_tasks: Current task data
            baseline_tasks: Baseline task data
            
        Returns:
            float: Schedule Performance Index
        """
        try:
            current_tasks_map = {task["id"]: task for task in current_tasks}
            
            total_earned_value = 0.0
            total_planned_value = 0.0
            
            for baseline_task in baseline_tasks:
                task_id = baseline_task["id"]
                current_task = current_tasks_map.get(task_id)
                
                if current_task:
                    baseline_effort = baseline_task.get("planned_effort_hours", 1) or 1
                    current_progress = current_task.get("progress_percentage", 0)
                    
                    # Earned value = baseline effort * actual progress
                    earned_value = baseline_effort * (current_progress / 100)
                    
                    # Planned value = baseline effort * planned progress (simplified to 100% for completed baseline)
                    planned_value = baseline_effort
                    
                    total_earned_value += earned_value
                    total_planned_value += planned_value
            
            return total_earned_value / total_planned_value if total_planned_value > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating schedule performance index: {e}")
            return 0.0
    
    def _get_performance_status(self, performance_index: float) -> str:
        """
        Get performance status based on performance index.
        
        Args:
            performance_index: Performance index value
            
        Returns:
            str: Performance status
        """
        if performance_index >= 1.0:
            return "on_track"
        elif performance_index >= 0.9:
            return "minor_concern"
        elif performance_index >= 0.8:
            return "at_risk"
        else:
            return "critical"
    
    def _get_overall_health(self, schedule_pi: float, cost_pi: float) -> str:
        """
        Get overall project health based on schedule and cost performance.
        
        Args:
            schedule_pi: Schedule Performance Index
            cost_pi: Cost Performance Index
            
        Returns:
            str: Overall health status
        """
        if schedule_pi >= 0.95 and cost_pi >= 0.95:
            return "excellent"
        elif schedule_pi >= 0.9 and cost_pi >= 0.9:
            return "good"
        elif schedule_pi >= 0.8 and cost_pi >= 0.8:
            return "fair"
        elif schedule_pi >= 0.7 or cost_pi >= 0.7:
            return "at_risk"
        else:
            return "critical"