"""
Schedule Management API Endpoints

Provides REST API endpoints for:
- Schedule CRUD operations
- Task management
- Baseline management and variance analysis
- Schedule performance metrics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
import logging

from auth.dependencies import get_current_user
from services.schedule_manager import ScheduleManager
from services.baseline_manager import BaselineManager
from models.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    TaskCreate, TaskUpdate, TaskResponse, TaskProgressUpdate,
    ScheduleBaselineCreate, ScheduleBaselineResponse,
    ScheduleWithTasksResponse, TaskHierarchyResponse,
    PaginationParams, ScheduleFilter, TaskFilter
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])

# Initialize services
schedule_manager = ScheduleManager()
baseline_manager = BaselineManager()

# =====================================================
# SCHEDULE CRUD ENDPOINTS
# =====================================================

@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    project_id: UUID,
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project schedule."""
    try:
        schedule = await schedule_manager.create_schedule(
            project_id, schedule_data, UUID(current_user["id"])
        )
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")

@router.get("/{schedule_id}", response_model=ScheduleWithTasksResponse)
async def get_schedule_with_tasks(
    schedule_id: UUID,
    include_dependencies: bool = Query(True, description="Include task dependencies"),
    current_user: dict = Depends(get_current_user)
):
    """Get a schedule with all its tasks and related data."""
    try:
        schedule = await schedule_manager.get_schedule_with_tasks(
            schedule_id, include_dependencies
        )
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule")

@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    updates: ScheduleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing schedule."""
    try:
        # This would need to be implemented in ScheduleManager
        raise HTTPException(status_code=501, detail="Schedule update not implemented yet")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule and all its tasks."""
    try:
        success = await schedule_manager.delete_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Schedule deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")

# =====================================================
# TASK MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/{schedule_id}/tasks", response_model=TaskResponse)
async def create_task(
    schedule_id: UUID,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new task in the schedule."""
    try:
        task = await schedule_manager.create_task(
            schedule_id, task_data, UUID(current_user["id"])
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    updates: TaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing task."""
    try:
        task = await schedule_manager.update_task(
            task_id, updates, UUID(current_user["id"])
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.post("/tasks/{task_id}/progress", response_model=TaskResponse)
async def update_task_progress(
    task_id: UUID,
    progress_data: TaskProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update task progress with actual dates and percentage completion."""
    try:
        task = await schedule_manager.update_task_progress(
            task_id, progress_data, UUID(current_user["id"])
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task progress")

@router.get("/{schedule_id}/tasks/hierarchy", response_model=List[TaskHierarchyResponse])
async def get_task_hierarchy(
    schedule_id: UUID,
    max_depth: Optional[int] = Query(None, description="Maximum hierarchy depth"),
    current_user: dict = Depends(get_current_user)
):
    """Get task hierarchy for a schedule."""
    try:
        hierarchy = await schedule_manager.get_task_hierarchy(schedule_id, max_depth)
        return hierarchy
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting task hierarchy: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task hierarchy")

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Delete a task and all its children."""
    try:
        success = await schedule_manager.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

# =====================================================
# BASELINE MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/{schedule_id}/baselines", response_model=ScheduleBaselineResponse)
async def create_baseline(
    schedule_id: UUID,
    baseline_data: ScheduleBaselineCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new baseline for the schedule."""
    try:
        baseline = await baseline_manager.create_baseline(
            schedule_id, baseline_data, UUID(current_user["id"])
        )
        return baseline
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating baseline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create baseline")

@router.get("/{schedule_id}/baselines", response_model=List[ScheduleBaselineResponse])
async def get_baseline_versions(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get all baseline versions for a schedule."""
    try:
        baselines = await baseline_manager.get_baseline_versions(schedule_id)
        return baselines
    except Exception as e:
        logger.error(f"Error getting baseline versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get baseline versions")

@router.get("/baselines/{baseline_id}", response_model=ScheduleBaselineResponse)
async def get_baseline(
    baseline_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific baseline by ID."""
    try:
        baseline = await baseline_manager.get_baseline(baseline_id)
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        return baseline
    except Exception as e:
        logger.error(f"Error getting baseline: {e}")
        raise HTTPException(status_code=500, detail="Failed to get baseline")

@router.post("/baselines/{baseline_id}/approve", response_model=ScheduleBaselineResponse)
async def approve_baseline(
    baseline_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Approve a baseline and set it as the official project baseline."""
    try:
        baseline = await baseline_manager.approve_baseline(
            baseline_id, UUID(current_user["id"])
        )
        return baseline
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving baseline: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve baseline")

@router.delete("/baselines/{baseline_id}")
async def delete_baseline(
    baseline_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Delete a baseline (only if not approved)."""
    try:
        success = await baseline_manager.delete_baseline(baseline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Baseline not found or cannot be deleted")
        return {"message": "Baseline deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting baseline: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete baseline")

# =====================================================
# VARIANCE AND PERFORMANCE ANALYSIS ENDPOINTS
# =====================================================

@router.get("/{schedule_id}/variance", response_model=Dict[str, Any])
async def get_schedule_variance(
    schedule_id: UUID,
    baseline_id: Optional[UUID] = Query(None, description="Specific baseline ID (uses latest approved if not provided)"),
    current_user: dict = Depends(get_current_user)
):
    """Get schedule variance analysis against baseline."""
    try:
        variance = await baseline_manager.calculate_schedule_variance(schedule_id, baseline_id)
        return variance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating schedule variance: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate schedule variance")

@router.get("/{schedule_id}/performance", response_model=Dict[str, Any])
async def get_schedule_performance(
    schedule_id: UUID,
    baseline_id: Optional[UUID] = Query(None, description="Specific baseline ID"),
    status_date: Optional[date] = Query(None, description="Status date for calculations"),
    current_user: dict = Depends(get_current_user)
):
    """Get schedule performance metrics including earned value analysis."""
    try:
        performance = await baseline_manager.calculate_earned_value_metrics(
            schedule_id, baseline_id, status_date
        )
        return performance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating schedule performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate schedule performance")

@router.get("/{schedule_id}/progress", response_model=Dict[str, Any])
async def get_schedule_progress(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get overall schedule progress and health metrics."""
    try:
        progress = await schedule_manager.calculate_schedule_progress(schedule_id)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating schedule progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate schedule progress")

# =====================================================
# BULK OPERATIONS ENDPOINTS
# =====================================================

@router.post("/tasks/bulk-progress", response_model=Dict[str, Any])
async def bulk_update_task_progress(
    progress_updates: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user)
):
    """Update progress for multiple tasks in a single operation."""
    try:
        result = await schedule_manager.bulk_update_task_progress(
            progress_updates, UUID(current_user["id"])
        )
        return result
    except Exception as e:
        logger.error(f"Error in bulk update task progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk update task progress")

@router.post("/{schedule_id}/recalculate-progress")
async def recalculate_all_parent_progress(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Recalculate progress for all parent tasks in a schedule."""
    try:
        result = await schedule_manager.recalculate_all_parent_progress(schedule_id)
        return result
    except Exception as e:
        logger.error(f"Error recalculating parent progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to recalculate parent progress")

# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@router.get("/tasks/{task_id}/children-progress", response_model=Dict[str, Any])
async def get_task_children_progress(
    task_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed progress information for all children of a parent task."""
    try:
        progress = await schedule_manager.get_task_children_progress(task_id)
        return progress
    except Exception as e:
        logger.error(f"Error getting task children progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task children progress")

@router.post("/{schedule_id}/update-performance-index")
async def update_schedule_performance_index(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Update the schedule's performance index based on current progress."""
    try:
        await schedule_manager.update_schedule_performance_index(schedule_id)
        return {"message": "Schedule performance index updated successfully"}
    except Exception as e:
        logger.error(f"Error updating schedule performance index: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule performance index")