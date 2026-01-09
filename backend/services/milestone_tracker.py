"""
Milestone Tracker Service

Handles all milestone management operations including:
- Milestone creation and management
- Milestone status tracking and calculations
- Deliverable linking and tracking
- Milestone alert and notification system
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Set, Tuple
from uuid import UUID, uuid4
from enum import Enum
import logging
import json
from decimal import Decimal

from config.database import supabase
from models.schedule import (
    MilestoneCreate, MilestoneResponse, MilestoneStatus,
    TaskResponse, ScheduleResponse
)

logger = logging.getLogger(__name__)

class MilestoneTracker:
    """
    Handles all milestone management operations.
    
    Provides:
    - Milestone creation and management
    - Milestone status tracking and calculations
    - Deliverable linking and tracking
    - Milestone alert and notification system
    """
    
    def __init__(self):
        self.db = supabase
        if not self.db:
            raise RuntimeError("Database connection not available")
    
    async def create_milestone(
        self,
        schedule_id: UUID,
        milestone_data: MilestoneCreate,
        created_by: UUID
    ) -> MilestoneResponse:
        """
        Create a new milestone with deliverable linking.
        
        Args:
            schedule_id: ID of the schedule
            milestone_data: Milestone creation data
            created_by: ID of the user creating the milestone
            
        Returns:
            MilestoneResponse: Created milestone data
        """
        try:
            # Validate schedule exists
            schedule_result = self.db.table("schedules").select("id, project_id").eq("id", str(schedule_id)).execute()
            if not schedule_result.data:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            schedule_data = schedule_result.data[0]
            project_id = schedule_data["project_id"]
            
            # Validate task if specified
            if milestone_data.task_id:
                task_result = self.db.table("tasks").select("id, name").eq(
                    "id", str(milestone_data.task_id)
                ).eq("schedule_id", str(schedule_id)).execute()
                
                if not task_result.data:
                    raise ValueError(f"Task {milestone_data.task_id} not found in schedule")
            
            # Validate responsible party if specified
            if milestone_data.responsible_party:
                user_result = self.db.table("auth.users").select("id").eq(
                    "id", str(milestone_data.responsible_party)
                ).execute()
                
                if not user_result.data:
                    raise ValueError(f"User {milestone_data.responsible_party} not found")
            
            # Prepare milestone data
            milestone_record = {
                "id": str(uuid4()),
                "project_id": project_id,
                "schedule_id": str(schedule_id),
                "task_id": str(milestone_data.task_id) if milestone_data.task_id else None,
                "name": milestone_data.name,
                "description": milestone_data.description,
                "target_date": milestone_data.target_date.isoformat(),
                "actual_date": None,
                "status": MilestoneStatus.PLANNED.value,
                "success_criteria": milestone_data.success_criteria,
                "responsible_party": str(milestone_data.responsible_party) if milestone_data.responsible_party else None,
                "deliverables": json.dumps(milestone_data.deliverables),
                "approval_required": milestone_data.approval_required,
                "approved_by": None,
                "approved_at": None,
                "created_by": str(created_by),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert milestone
            result = self.db.table("milestones").insert(milestone_record).execute()
            
            if not result.data:
                raise RuntimeError("Failed to create milestone")
            
            created_milestone = result.data[0]
            
            # Convert to response model
            return self._convert_milestone_to_response(created_milestone)
            
        except Exception as e:
            logger.error(f"Error creating milestone: {e}")
            raise RuntimeError(f"Failed to create milestone: {str(e)}")
    
    async def update_milestone_status(
        self,
        milestone_id: UUID,
        status: MilestoneStatus,
        actual_date: Optional[date] = None,
        notes: Optional[str] = None,
        updated_by: UUID = None
    ) -> MilestoneResponse:
        """
        Update milestone status with automatic date tracking.
        
        Args:
            milestone_id: ID of the milestone
            status: New milestone status
            actual_date: Actual achievement date
            notes: Status update notes
            updated_by: ID of the user updating status
            
        Returns:
            MilestoneResponse: Updated milestone data
        """
        try:
            # Get existing milestone
            existing_result = self.db.table("milestones").select("*").eq("id", str(milestone_id)).execute()
            if not existing_result.data:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            existing_milestone = existing_result.data[0]
            
            # Validate status transition
            current_status = MilestoneStatus(existing_milestone["status"])
            if not self._is_valid_milestone_status_transition(current_status, status):
                raise ValueError(f"Invalid status transition from {current_status.value} to {status.value}")
            
            # Auto-set actual date if milestone is being achieved
            if status == MilestoneStatus.ACHIEVED and not actual_date:
                actual_date = date.today()
            
            # Prepare update data
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if actual_date:
                update_data["actual_date"] = actual_date.isoformat()
            
            # Update milestone
            result = self.db.table("milestones").update(update_data).eq("id", str(milestone_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to update milestone status")
            
            updated_milestone = result.data[0]
            
            # Create status history record
            await self._create_milestone_status_history(
                milestone_id, status, actual_date, notes, updated_by
            )
            
            # Trigger notifications if milestone is at risk or achieved
            if status in [MilestoneStatus.AT_RISK, MilestoneStatus.ACHIEVED, MilestoneStatus.MISSED]:
                await self._trigger_milestone_notifications(milestone_id, status, updated_milestone)
            
            return self._convert_milestone_to_response(updated_milestone)
            
        except Exception as e:
            logger.error(f"Error updating milestone status {milestone_id}: {e}")
            raise RuntimeError(f"Failed to update milestone status: {str(e)}")
    
    async def get_milestone_status_report(
        self,
        schedule_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        status_filter: Optional[List[MilestoneStatus]] = None
    ) -> Dict[str, Any]:
        """
        Generate milestone status report showing on-time, at-risk, and overdue milestones.
        
        Args:
            schedule_id: Optional schedule ID to filter by
            project_id: Optional project ID to filter by
            status_filter: Optional list of statuses to filter by
            
        Returns:
            Dict with milestone status report
        """
        try:
            # Build query
            query = self.db.table("milestones").select("*")
            
            if schedule_id:
                query = query.eq("schedule_id", str(schedule_id))
            elif project_id:
                query = query.eq("project_id", str(project_id))
            
            if status_filter:
                status_values = [status.value for status in status_filter]
                query = query.in_("status", status_values)
            
            result = query.execute()
            
            if not result.data:
                return {
                    "total_milestones": 0,
                    "on_time": 0,
                    "at_risk": 0,
                    "overdue": 0,
                    "achieved": 0,
                    "missed": 0,
                    "milestones": []
                }
            
            milestones = result.data
            today = date.today()
            
            # Categorize milestones
            status_counts = {
                "on_time": 0,
                "at_risk": 0,
                "overdue": 0,
                "achieved": 0,
                "missed": 0
            }
            
            milestone_details = []
            
            for milestone in milestones:
                target_date = date.fromisoformat(milestone["target_date"])
                status = milestone["status"]
                days_to_target = (target_date - today).days
                
                # Calculate status category
                if status == MilestoneStatus.ACHIEVED.value:
                    category = "achieved"
                elif status == MilestoneStatus.MISSED.value:
                    category = "missed"
                elif status == MilestoneStatus.AT_RISK.value:
                    category = "at_risk"
                elif days_to_target < 0 and status == MilestoneStatus.PLANNED.value:
                    category = "overdue"
                else:
                    category = "on_time"
                
                status_counts[category] += 1
                
                milestone_details.append({
                    "id": milestone["id"],
                    "name": milestone["name"],
                    "target_date": target_date.isoformat(),
                    "actual_date": milestone.get("actual_date"),
                    "status": status,
                    "category": category,
                    "days_to_target": days_to_target,
                    "responsible_party": milestone.get("responsible_party"),
                    "deliverables": json.loads(milestone.get("deliverables", "[]")),
                    "approval_required": milestone.get("approval_required", False)
                })
            
            return {
                "total_milestones": len(milestones),
                "on_time": status_counts["on_time"],
                "at_risk": status_counts["at_risk"],
                "overdue": status_counts["overdue"],
                "achieved": status_counts["achieved"],
                "missed": status_counts["missed"],
                "milestones": milestone_details
            }
            
        except Exception as e:
            logger.error(f"Error generating milestone status report: {e}")
            raise RuntimeError(f"Failed to generate milestone status report: {str(e)}")
    
    async def link_deliverable_to_milestone(
        self,
        milestone_id: UUID,
        deliverable_name: str,
        deliverable_description: Optional[str] = None,
        linked_task_id: Optional[UUID] = None,
        created_by: UUID = None
    ) -> bool:
        """
        Link a deliverable to a milestone with task association.
        
        Args:
            milestone_id: ID of the milestone
            deliverable_name: Name of the deliverable
            deliverable_description: Optional description
            linked_task_id: Optional task ID that produces this deliverable
            created_by: ID of the user creating the link
            
        Returns:
            bool: True if linked successfully
        """
        try:
            # Get existing milestone
            milestone_result = self.db.table("milestones").select("deliverables").eq("id", str(milestone_id)).execute()
            if not milestone_result.data:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            existing_deliverables = json.loads(milestone_result.data[0].get("deliverables", "[]"))
            
            # Create new deliverable entry
            new_deliverable = {
                "name": deliverable_name,
                "description": deliverable_description,
                "linked_task_id": str(linked_task_id) if linked_task_id else None,
                "status": "pending",
                "created_by": str(created_by) if created_by else None,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to existing deliverables
            existing_deliverables.append(new_deliverable)
            
            # Update milestone
            update_data = {
                "deliverables": json.dumps(existing_deliverables),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("milestones").update(update_data).eq("id", str(milestone_id)).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error linking deliverable to milestone {milestone_id}: {e}")
            return False
    
    async def update_deliverable_status(
        self,
        milestone_id: UUID,
        deliverable_name: str,
        status: str,
        completion_date: Optional[date] = None,
        updated_by: UUID = None
    ) -> bool:
        """
        Update the status of a deliverable linked to a milestone.
        
        Args:
            milestone_id: ID of the milestone
            deliverable_name: Name of the deliverable to update
            status: New status (pending, in_progress, completed, cancelled)
            completion_date: Optional completion date
            updated_by: ID of the user updating status
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get existing milestone
            milestone_result = self.db.table("milestones").select("deliverables").eq("id", str(milestone_id)).execute()
            if not milestone_result.data:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            deliverables = json.loads(milestone_result.data[0].get("deliverables", "[]"))
            
            # Find and update the deliverable
            updated = False
            for deliverable in deliverables:
                if deliverable["name"] == deliverable_name:
                    deliverable["status"] = status
                    deliverable["updated_by"] = str(updated_by) if updated_by else None
                    deliverable["updated_at"] = datetime.utcnow().isoformat()
                    
                    if completion_date:
                        deliverable["completion_date"] = completion_date.isoformat()
                    
                    updated = True
                    break
            
            if not updated:
                raise ValueError(f"Deliverable '{deliverable_name}' not found in milestone")
            
            # Update milestone
            update_data = {
                "deliverables": json.dumps(deliverables),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("milestones").update(update_data).eq("id", str(milestone_id)).execute()
            
            # Check if all deliverables are completed and update milestone status
            await self._check_milestone_completion_status(milestone_id, deliverables)
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error updating deliverable status for milestone {milestone_id}: {e}")
            return False
    
    async def get_at_risk_milestones(
        self,
        days_ahead: int = 14,
        schedule_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get milestones that are at risk of being missed.
        
        Args:
            days_ahead: Number of days ahead to look for at-risk milestones
            schedule_id: Optional schedule ID to filter by
            project_id: Optional project ID to filter by
            
        Returns:
            List of at-risk milestone details
        """
        try:
            # Build query for planned milestones
            query = self.db.table("milestones").select("*").eq("status", MilestoneStatus.PLANNED.value)
            
            if schedule_id:
                query = query.eq("schedule_id", str(schedule_id))
            elif project_id:
                query = query.eq("project_id", str(project_id))
            
            result = query.execute()
            
            if not result.data:
                return []
            
            milestones = result.data
            today = date.today()
            risk_date = today + timedelta(days=days_ahead)
            at_risk_milestones = []
            
            for milestone in milestones:
                target_date = date.fromisoformat(milestone["target_date"])
                days_to_target = (target_date - today).days
                
                # Check if milestone is at risk
                is_at_risk = False
                risk_factors = []
                
                # Risk factor 1: Target date is within risk window
                if target_date <= risk_date:
                    is_at_risk = True
                    risk_factors.append(f"Due in {days_to_target} days")
                
                # Risk factor 2: Linked task is behind schedule
                if milestone.get("task_id"):
                    task_risk = await self._check_linked_task_risk(UUID(milestone["task_id"]))
                    if task_risk:
                        is_at_risk = True
                        risk_factors.extend(task_risk)
                
                # Risk factor 3: Deliverables are incomplete
                deliverables = json.loads(milestone.get("deliverables", "[]"))
                incomplete_deliverables = [d for d in deliverables if d.get("status") != "completed"]
                if incomplete_deliverables and days_to_target <= 7:
                    is_at_risk = True
                    risk_factors.append(f"{len(incomplete_deliverables)} incomplete deliverables")
                
                if is_at_risk:
                    at_risk_milestones.append({
                        "id": milestone["id"],
                        "name": milestone["name"],
                        "target_date": target_date.isoformat(),
                        "days_to_target": days_to_target,
                        "responsible_party": milestone.get("responsible_party"),
                        "risk_factors": risk_factors,
                        "deliverables": deliverables,
                        "linked_task_id": milestone.get("task_id")
                    })
            
            return at_risk_milestones
            
        except Exception as e:
            logger.error(f"Error getting at-risk milestones: {e}")
            return []
    
    async def trigger_milestone_alerts(
        self,
        schedule_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Trigger alerts and notifications for milestones requiring attention.
        
        Args:
            schedule_id: Optional schedule ID to filter by
            project_id: Optional project ID to filter by
            
        Returns:
            Dict with alert summary
        """
        try:
            # Get at-risk milestones
            at_risk_milestones = await self.get_at_risk_milestones(
                days_ahead=14, schedule_id=schedule_id, project_id=project_id
            )
            
            # Get overdue milestones
            overdue_milestones = await self._get_overdue_milestones(schedule_id, project_id)
            
            # Get milestones requiring approval
            approval_milestones = await self._get_milestones_requiring_approval(schedule_id, project_id)
            
            alerts_sent = 0
            notifications = []
            
            # Process at-risk milestones
            for milestone in at_risk_milestones:
                if await self._send_milestone_alert(milestone, "at_risk"):
                    alerts_sent += 1
                    notifications.append({
                        "milestone_id": milestone["id"],
                        "type": "at_risk",
                        "message": f"Milestone '{milestone['name']}' is at risk"
                    })
            
            # Process overdue milestones
            for milestone in overdue_milestones:
                if await self._send_milestone_alert(milestone, "overdue"):
                    alerts_sent += 1
                    notifications.append({
                        "milestone_id": milestone["id"],
                        "type": "overdue",
                        "message": f"Milestone '{milestone['name']}' is overdue"
                    })
            
            # Process approval milestones
            for milestone in approval_milestones:
                if await self._send_milestone_alert(milestone, "approval_required"):
                    alerts_sent += 1
                    notifications.append({
                        "milestone_id": milestone["id"],
                        "type": "approval_required",
                        "message": f"Milestone '{milestone['name']}' requires approval"
                    })
            
            return {
                "alerts_sent": alerts_sent,
                "at_risk_count": len(at_risk_milestones),
                "overdue_count": len(overdue_milestones),
                "approval_required_count": len(approval_milestones),
                "notifications": notifications
            }
            
        except Exception as e:
            logger.error(f"Error triggering milestone alerts: {e}")
            return {
                "alerts_sent": 0,
                "error": str(e)
            }
    
    async def get_milestone(self, milestone_id: UUID) -> Optional[MilestoneResponse]:
        """
        Get a single milestone by ID.
        
        Args:
            milestone_id: ID of the milestone
            
        Returns:
            MilestoneResponse or None if not found
        """
        try:
            result = self.db.table("milestones").select("*").eq("id", str(milestone_id)).execute()
            
            if not result.data:
                return None
            
            return self._convert_milestone_to_response(result.data[0])
            
        except Exception as e:
            logger.error(f"Error getting milestone {milestone_id}: {e}")
            return None
    
    async def get_milestones_by_schedule(
        self,
        schedule_id: UUID,
        status_filter: Optional[List[MilestoneStatus]] = None
    ) -> List[MilestoneResponse]:
        """
        Get all milestones for a schedule.
        
        Args:
            schedule_id: ID of the schedule
            status_filter: Optional list of statuses to filter by
            
        Returns:
            List of MilestoneResponse objects
        """
        try:
            query = self.db.table("milestones").select("*").eq("schedule_id", str(schedule_id))
            
            if status_filter:
                status_values = [status.value for status in status_filter]
                query = query.in_("status", status_values)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            return [self._convert_milestone_to_response(milestone) for milestone in result.data]
            
        except Exception as e:
            logger.error(f"Error getting milestones for schedule {schedule_id}: {e}")
            return []
    
    # Private helper methods
    
    def _convert_milestone_to_response(self, milestone_data: Dict[str, Any]) -> MilestoneResponse:
        """Convert database milestone record to MilestoneResponse model."""
        return MilestoneResponse(
            id=milestone_data["id"],
            project_id=milestone_data["project_id"],
            schedule_id=milestone_data.get("schedule_id"),
            task_id=milestone_data.get("task_id"),
            name=milestone_data["name"],
            description=milestone_data.get("description"),
            target_date=date.fromisoformat(milestone_data["target_date"]),
            actual_date=date.fromisoformat(milestone_data["actual_date"]) if milestone_data.get("actual_date") else None,
            status=milestone_data["status"],
            success_criteria=milestone_data.get("success_criteria"),
            responsible_party=milestone_data.get("responsible_party"),
            deliverables=json.loads(milestone_data.get("deliverables", "[]")),
            approval_required=milestone_data.get("approval_required", False),
            approved_by=milestone_data.get("approved_by"),
            approved_at=datetime.fromisoformat(milestone_data["approved_at"].replace('Z', '+00:00')) if milestone_data.get("approved_at") else None,
            progress_percentage=self._calculate_milestone_progress(milestone_data),
            created_by=milestone_data["created_by"],
            created_at=datetime.fromisoformat(milestone_data["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(milestone_data["updated_at"].replace('Z', '+00:00'))
        )
    
    def _calculate_milestone_progress(self, milestone_data: Dict[str, Any]) -> int:
        """
        Calculate milestone progress based on deliverables completion.
        
        Args:
            milestone_data: Milestone database record
            
        Returns:
            int: Progress percentage (0-100)
        """
        try:
            status = milestone_data["status"]
            
            # If milestone is achieved, progress is 100%
            if status == MilestoneStatus.ACHIEVED.value:
                return 100
            
            # If milestone is missed, progress is 0%
            if status == MilestoneStatus.MISSED.value:
                return 0
            
            # Calculate based on deliverables
            deliverables = json.loads(milestone_data.get("deliverables", "[]"))
            
            if not deliverables:
                return 0
            
            completed_deliverables = sum(1 for d in deliverables if d.get("status") == "completed")
            total_deliverables = len(deliverables)
            
            return int((completed_deliverables / total_deliverables) * 100)
            
        except Exception as e:
            logger.error(f"Error calculating milestone progress: {e}")
            return 0
    
    def _is_valid_milestone_status_transition(
        self,
        current_status: MilestoneStatus,
        new_status: MilestoneStatus
    ) -> bool:
        """
        Validate if a milestone status transition is allowed.
        
        Args:
            current_status: Current milestone status
            new_status: Proposed new status
            
        Returns:
            bool: True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            MilestoneStatus.PLANNED: [MilestoneStatus.AT_RISK, MilestoneStatus.ACHIEVED, MilestoneStatus.MISSED],
            MilestoneStatus.AT_RISK: [MilestoneStatus.PLANNED, MilestoneStatus.ACHIEVED, MilestoneStatus.MISSED],
            MilestoneStatus.ACHIEVED: [MilestoneStatus.PLANNED],  # Allow reopening achieved milestones
            MilestoneStatus.MISSED: [MilestoneStatus.PLANNED, MilestoneStatus.AT_RISK]  # Allow recovery from missed
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    async def _create_milestone_status_history(
        self,
        milestone_id: UUID,
        status: MilestoneStatus,
        actual_date: Optional[date],
        notes: Optional[str],
        updated_by: Optional[UUID]
    ) -> None:
        """
        Create a milestone status history record for audit trail.
        
        Args:
            milestone_id: ID of the milestone
            status: New milestone status
            actual_date: Actual achievement date
            notes: Status update notes
            updated_by: ID of the user who made the update
        """
        try:
            # This would typically insert into a milestone_status_history table
            # For now, just log the status update
            logger.info(
                f"Milestone status update for {milestone_id}: {status.value}"
                f"{f' on {actual_date}' if actual_date else ''}"
                f"{f' by user {updated_by}' if updated_by else ''}"
                f"{f' - Notes: {notes}' if notes else ''}"
            )
            
        except Exception as e:
            logger.error(f"Error creating milestone status history: {e}")
    
    async def _trigger_milestone_notifications(
        self,
        milestone_id: UUID,
        status: MilestoneStatus,
        milestone_data: Dict[str, Any]
    ) -> None:
        """
        Trigger notifications for milestone status changes.
        
        Args:
            milestone_id: ID of the milestone
            status: New milestone status
            milestone_data: Milestone database record
        """
        try:
            # This would typically integrate with a notification system
            # For now, just log the notification
            responsible_party = milestone_data.get("responsible_party")
            milestone_name = milestone_data["name"]
            
            logger.info(
                f"Milestone notification: '{milestone_name}' is now {status.value}"
                f"{f' - Notify user {responsible_party}' if responsible_party else ''}"
            )
            
        except Exception as e:
            logger.error(f"Error triggering milestone notifications: {e}")
    
    async def _check_linked_task_risk(self, task_id: UUID) -> List[str]:
        """
        Check if a linked task poses risk to milestone completion.
        
        Args:
            task_id: ID of the linked task
            
        Returns:
            List of risk factors from the linked task
        """
        try:
            task_result = self.db.table("tasks").select("*").eq("id", str(task_id)).execute()
            
            if not task_result.data:
                return []
            
            task = task_result.data[0]
            risk_factors = []
            
            # Check if task is behind schedule
            planned_end = date.fromisoformat(task["planned_end_date"])
            today = date.today()
            progress = task["progress_percentage"]
            
            if planned_end < today and progress < 100:
                days_overdue = (today - planned_end).days
                risk_factors.append(f"Linked task is {days_overdue} days overdue")
            
            # Check if task progress is insufficient
            if progress < 50 and (planned_end - today).days <= 7:
                risk_factors.append(f"Linked task only {progress}% complete")
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error checking linked task risk {task_id}: {e}")
            return []
    
    async def _check_milestone_completion_status(
        self,
        milestone_id: UUID,
        deliverables: List[Dict[str, Any]]
    ) -> None:
        """
        Check if milestone should be marked as achieved based on deliverables.
        
        Args:
            milestone_id: ID of the milestone
            deliverables: List of deliverable records
        """
        try:
            if not deliverables:
                return
            
            # Check if all deliverables are completed
            all_completed = all(d.get("status") == "completed" for d in deliverables)
            
            if all_completed:
                # Update milestone status to achieved
                await self.update_milestone_status(
                    milestone_id,
                    MilestoneStatus.ACHIEVED,
                    actual_date=date.today()
                )
            
        except Exception as e:
            logger.error(f"Error checking milestone completion status {milestone_id}: {e}")
    
    async def _get_overdue_milestones(
        self,
        schedule_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get milestones that are overdue."""
        try:
            query = self.db.table("milestones").select("*").eq("status", MilestoneStatus.PLANNED.value)
            
            if schedule_id:
                query = query.eq("schedule_id", str(schedule_id))
            elif project_id:
                query = query.eq("project_id", str(project_id))
            
            result = query.execute()
            
            if not result.data:
                return []
            
            today = date.today()
            overdue_milestones = []
            
            for milestone in result.data:
                target_date = date.fromisoformat(milestone["target_date"])
                if target_date < today:
                    days_overdue = (today - target_date).days
                    overdue_milestones.append({
                        "id": milestone["id"],
                        "name": milestone["name"],
                        "target_date": target_date.isoformat(),
                        "days_overdue": days_overdue,
                        "responsible_party": milestone.get("responsible_party")
                    })
            
            return overdue_milestones
            
        except Exception as e:
            logger.error(f"Error getting overdue milestones: {e}")
            return []
    
    async def _get_milestones_requiring_approval(
        self,
        schedule_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get milestones that require approval."""
        try:
            query = self.db.table("milestones").select("*").eq("approval_required", True).is_("approved_by", "null")
            
            if schedule_id:
                query = query.eq("schedule_id", str(schedule_id))
            elif project_id:
                query = query.eq("project_id", str(project_id))
            
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting milestones requiring approval: {e}")
            return []
    
    async def _send_milestone_alert(
        self,
        milestone: Dict[str, Any],
        alert_type: str
    ) -> bool:
        """
        Send alert for a milestone.
        
        Args:
            milestone: Milestone data
            alert_type: Type of alert (at_risk, overdue, approval_required)
            
        Returns:
            bool: True if alert was sent successfully
        """
        try:
            # This would typically integrate with an email/notification service
            # For now, just log the alert
            logger.info(
                f"Milestone alert ({alert_type}): {milestone['name']} "
                f"(ID: {milestone['id']})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending milestone alert: {e}")
            return False