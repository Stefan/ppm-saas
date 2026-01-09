"""
WBS Manager Service

Handles Work Breakdown Structure (WBS) management operations including:
- WBS element creation with hierarchy support
- WBS code generation and validation
- WBS structure management operations
- WBS element movement and restructuring
- Work package definition and tracking
- Deliverable management and acceptance criteria
- Work package manager assignment
- Work package progress tracking
"""

import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Set, Tuple
from uuid import UUID, uuid4
from enum import Enum
import logging
import json
from decimal import Decimal

from config.database import supabase
from models.schedule import (
    WBSElementCreate, WBSElementResponse, WBSHierarchy, WBSValidationResult
)

logger = logging.getLogger(__name__)

class WBSManager:
    """
    Handles all Work Breakdown Structure (WBS) management operations.
    
    Provides:
    - WBS element creation with hierarchy support
    - WBS code generation and validation
    - WBS structure management operations
    - WBS element movement and restructuring
    - Work package definition and tracking
    - Deliverable management and acceptance criteria
    - Work package manager assignment
    - Work package progress tracking
    """
    
    def __init__(self):
        self.db = supabase
        if not self.db:
            raise RuntimeError("Database connection not available")
    
    async def create_wbs_element(
        self,
        schedule_id: UUID,
        wbs_data: WBSElementCreate,
        created_by: UUID
    ) -> WBSElementResponse:
        """
        Create a new WBS element with hierarchy support.
        
        Args:
            schedule_id: ID of the schedule
            wbs_data: WBS element creation data
            created_by: ID of the user creating the element
            
        Returns:
            WBSElementResponse: Created WBS element data
        """
        try:
            # Validate schedule exists
            schedule_result = self.db.table("schedules").select("id").eq("id", str(schedule_id)).execute()
            if not schedule_result.data:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            # Validate parent element if specified
            parent_level = 0
            if wbs_data.parent_element_id:
                parent_result = self.db.table("wbs_elements").select("id, wbs_code, level_number").eq(
                    "id", str(wbs_data.parent_element_id)
                ).eq("schedule_id", str(schedule_id)).execute()
                
                if not parent_result.data:
                    raise ValueError(f"Parent WBS element {wbs_data.parent_element_id} not found in schedule")
                
                parent_level = parent_result.data[0]["level_number"]
            
            # Validate WBS code uniqueness within schedule
            existing_wbs = self.db.table("wbs_elements").select("id").eq(
                "schedule_id", str(schedule_id)
            ).eq("wbs_code", wbs_data.wbs_code).execute()
            
            if existing_wbs.data:
                raise ValueError(f"WBS code {wbs_data.wbs_code} already exists in schedule")
            
            # Validate work package manager if specified
            if wbs_data.work_package_manager:
                user_result = self.db.table("auth.users").select("id").eq(
                    "id", str(wbs_data.work_package_manager)
                ).execute()
                
                if not user_result.data:
                    raise ValueError(f"Work package manager {wbs_data.work_package_manager} not found")
            
            # Calculate sort order for this level
            sort_order = await self._calculate_next_sort_order(
                schedule_id, wbs_data.parent_element_id
            )
            
            # Prepare WBS element data
            wbs_record = {
                "id": str(uuid4()),
                "schedule_id": str(schedule_id),
                "parent_element_id": str(wbs_data.parent_element_id) if wbs_data.parent_element_id else None,
                "task_id": None,  # Will be linked when tasks are created
                "wbs_code": wbs_data.wbs_code,
                "name": wbs_data.name,
                "description": wbs_data.description,
                "level_number": parent_level + 1,
                "sort_order": sort_order,
                "work_package_manager": str(wbs_data.work_package_manager) if wbs_data.work_package_manager else None,
                "deliverable_description": wbs_data.deliverable_description,
                "acceptance_criteria": wbs_data.acceptance_criteria,
                "progress_percentage": 0,
                "created_by": str(created_by),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert WBS element
            result = self.db.table("wbs_elements").insert(wbs_record).execute()
            
            if not result.data:
                raise RuntimeError("Failed to create WBS element")
            
            created_element = result.data[0]
            
            # Convert to response model
            return self._convert_wbs_element_to_response(created_element)
            
        except Exception as e:
            logger.error(f"Error creating WBS element: {e}")
            raise RuntimeError(f"Failed to create WBS element: {str(e)}")
    
    async def get_wbs_hierarchy(
        self,
        schedule_id: UUID,
        max_depth: Optional[int] = None
    ) -> WBSHierarchy:
        """
        Get WBS hierarchy for a schedule.
        
        Args:
            schedule_id: ID of the schedule
            max_depth: Maximum depth to retrieve (None for unlimited)
            
        Returns:
            WBSHierarchy: Hierarchical WBS structure
        """
        try:
            # Get all WBS elements for the schedule
            elements_result = self.db.table("wbs_elements").select("*").eq(
                "schedule_id", str(schedule_id)
            ).order("level_number", desc=False).order("sort_order", desc=False).execute()
            
            if not elements_result.data:
                return WBSHierarchy(
                    schedule_id=str(schedule_id),
                    elements=[],
                    max_depth=0
                )
            
            elements = elements_result.data
            
            # Filter by max depth if specified
            if max_depth is not None:
                elements = [e for e in elements if e["level_number"] <= max_depth]
            
            # Convert to response models
            wbs_elements = [self._convert_wbs_element_to_response(element) for element in elements]
            
            # Calculate actual max depth
            actual_max_depth = max((e["level_number"] for e in elements), default=0)
            
            return WBSHierarchy(
                schedule_id=str(schedule_id),
                elements=wbs_elements,
                max_depth=actual_max_depth
            )
            
        except Exception as e:
            logger.error(f"Error getting WBS hierarchy for schedule {schedule_id}: {e}")
            raise RuntimeError(f"Failed to get WBS hierarchy: {str(e)}")
    
    async def move_wbs_element(
        self,
        element_id: UUID,
        new_parent_id: Optional[UUID],
        new_position: int
    ) -> WBSElementResponse:
        """
        Move a WBS element to a new parent and position.
        
        Args:
            element_id: ID of the element to move
            new_parent_id: ID of the new parent (None for root level)
            new_position: New position within the parent's children
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Get existing element
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {element_id} not found")
            
            existing_element = existing_result.data[0]
            schedule_id = UUID(existing_element["schedule_id"])
            
            # Validate new parent if specified
            new_level = 1
            if new_parent_id:
                parent_result = self.db.table("wbs_elements").select("id, level_number").eq(
                    "id", str(new_parent_id)
                ).eq("schedule_id", str(schedule_id)).execute()
                
                if not parent_result.data:
                    raise ValueError(f"New parent WBS element {new_parent_id} not found")
                
                new_level = parent_result.data[0]["level_number"] + 1
                
                # Check for circular reference
                if await self._would_create_circular_reference(element_id, new_parent_id):
                    raise ValueError("Cannot move element: would create circular reference")
            
            # Update sort orders for siblings in old location
            await self._update_sibling_sort_orders(
                schedule_id, 
                UUID(existing_element["parent_element_id"]) if existing_element.get("parent_element_id") else None,
                existing_element["sort_order"],
                -1  # Decrement sort orders after the moved element
            )
            
            # Update sort orders for siblings in new location
            await self._update_sibling_sort_orders(
                schedule_id,
                new_parent_id,
                new_position,
                1  # Increment sort orders at and after the new position
            )
            
            # Update the element
            update_data = {
                "parent_element_id": str(new_parent_id) if new_parent_id else None,
                "level_number": new_level,
                "sort_order": new_position,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to move WBS element")
            
            updated_element = result.data[0]
            
            # Update level numbers for all descendants
            await self._update_descendant_levels(element_id, new_level)
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error moving WBS element {element_id}: {e}")
            raise RuntimeError(f"Failed to move WBS element: {str(e)}")
    
    def generate_wbs_code(
        self,
        parent_code: Optional[str],
        position: int
    ) -> str:
        """
        Generate a WBS code based on parent code and position.
        
        Args:
            parent_code: WBS code of the parent element (None for root)
            position: Position within the parent's children
            
        Returns:
            str: Generated WBS code
        """
        try:
            if parent_code is None:
                # Root level element
                return str(position)
            else:
                # Child element
                return f"{parent_code}.{position}"
                
        except Exception as e:
            logger.error(f"Error generating WBS code: {e}")
            raise RuntimeError(f"Failed to generate WBS code: {str(e)}")
    
    async def validate_wbs_structure(
        self,
        schedule_id: UUID
    ) -> WBSValidationResult:
        """
        Validate the WBS structure for consistency and completeness.
        
        Args:
            schedule_id: ID of the schedule
            
        Returns:
            WBSValidationResult: Validation results with errors and warnings
        """
        try:
            errors = []
            warnings = []
            
            # Get all WBS elements for the schedule
            elements_result = self.db.table("wbs_elements").select("*").eq(
                "schedule_id", str(schedule_id)
            ).execute()
            
            if not elements_result.data:
                return WBSValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=["No WBS elements found in schedule"]
                )
            
            elements = elements_result.data
            element_map = {e["id"]: e for e in elements}
            
            # Check for orphaned elements
            for element in elements:
                parent_id = element.get("parent_element_id")
                if parent_id and parent_id not in element_map:
                    errors.append(f"WBS element {element['wbs_code']} has invalid parent reference")
            
            # Check for duplicate WBS codes
            wbs_codes = [e["wbs_code"] for e in elements]
            duplicate_codes = set([code for code in wbs_codes if wbs_codes.count(code) > 1])
            for code in duplicate_codes:
                errors.append(f"Duplicate WBS code found: {code}")
            
            # Check for circular references
            for element in elements:
                if await self._has_circular_reference(UUID(element["id"]), element_map):
                    errors.append(f"Circular reference detected for WBS element {element['wbs_code']}")
            
            # Check for inconsistent level numbers
            for element in elements:
                parent_id = element.get("parent_element_id")
                expected_level = 1
                
                if parent_id and parent_id in element_map:
                    expected_level = element_map[parent_id]["level_number"] + 1
                
                if element["level_number"] != expected_level:
                    errors.append(f"Inconsistent level number for WBS element {element['wbs_code']}")
            
            # Check for elements without work package managers at leaf level
            for element in elements:
                # Check if this is a leaf element (no children)
                has_children = any(e.get("parent_element_id") == element["id"] for e in elements)
                
                if not has_children and not element.get("work_package_manager"):
                    warnings.append(f"Leaf WBS element {element['wbs_code']} has no work package manager assigned")
            
            # Check for elements without deliverable descriptions
            for element in elements:
                if not element.get("deliverable_description"):
                    warnings.append(f"WBS element {element['wbs_code']} has no deliverable description")
            
            is_valid = len(errors) == 0
            
            return WBSValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error validating WBS structure for schedule {schedule_id}: {e}")
            raise RuntimeError(f"Failed to validate WBS structure: {str(e)}")
    
    async def update_wbs_element(
        self,
        element_id: UUID,
        updates: Dict[str, Any],
        updated_by: UUID
    ) -> WBSElementResponse:
        """
        Update a WBS element.
        
        Args:
            element_id: ID of the element to update
            updates: Dictionary of fields to update
            updated_by: ID of the user updating the element
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Get existing element
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {element_id} not found")
            
            # Prepare update data
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update allowed fields
            allowed_fields = [
                "name", "description", "work_package_manager", 
                "deliverable_description", "acceptance_criteria"
            ]
            
            for field in allowed_fields:
                if field in updates:
                    update_data[field] = updates[field]
            
            # Validate work package manager if being updated
            if "work_package_manager" in updates and updates["work_package_manager"]:
                user_result = self.db.table("auth.users").select("id").eq(
                    "id", str(updates["work_package_manager"])
                ).execute()
                
                if not user_result.data:
                    raise ValueError(f"Work package manager {updates['work_package_manager']} not found")
            
            # Update element
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to update WBS element")
            
            updated_element = result.data[0]
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error updating WBS element {element_id}: {e}")
            raise RuntimeError(f"Failed to update WBS element: {str(e)}")
    
    async def delete_wbs_element(
        self,
        element_id: UUID
    ) -> bool:
        """
        Delete a WBS element and all its children.
        
        Args:
            element_id: ID of the element to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Get element to check for children and get sort order info
            element_result = self.db.table("wbs_elements").select("*").eq("id", str(element_id)).execute()
            
            if not element_result.data:
                return False
            
            element_data = element_result.data[0]
            schedule_id = UUID(element_data["schedule_id"])
            parent_id = UUID(element_data["parent_element_id"]) if element_data.get("parent_element_id") else None
            sort_order = element_data["sort_order"]
            
            # Delete element (children will be deleted by CASCADE)
            result = self.db.table("wbs_elements").delete().eq("id", str(element_id)).execute()
            
            # Update sort orders for remaining siblings
            await self._update_sibling_sort_orders(
                schedule_id,
                parent_id,
                sort_order,
                -1  # Decrement sort orders after the deleted element
            )
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error deleting WBS element {element_id}: {e}")
            return False
    
    async def get_wbs_element(
        self,
        element_id: UUID
    ) -> Optional[WBSElementResponse]:
        """
        Get a single WBS element by ID.
        
        Args:
            element_id: ID of the element
            
        Returns:
            WBSElementResponse or None if not found
        """
        try:
            result = self.db.table("wbs_elements").select("*").eq("id", str(element_id)).execute()
            
            if not result.data:
                return None
            
            return self._convert_wbs_element_to_response(result.data[0])
            
        except Exception as e:
            logger.error(f"Error getting WBS element {element_id}: {e}")
            return None
    
    async def get_wbs_elements_by_schedule(
        self,
        schedule_id: UUID,
        parent_id: Optional[UUID] = None
    ) -> List[WBSElementResponse]:
        """
        Get WBS elements for a schedule, optionally filtered by parent.
        
        Args:
            schedule_id: ID of the schedule
            parent_id: ID of the parent element (None for root elements)
            
        Returns:
            List[WBSElementResponse]: List of WBS elements
        """
        try:
            query = self.db.table("wbs_elements").select("*").eq("schedule_id", str(schedule_id))
            
            if parent_id is None:
                query = query.is_("parent_element_id", "null")
            else:
                query = query.eq("parent_element_id", str(parent_id))
            
            result = query.order("sort_order", desc=False).execute()
            
            if not result.data:
                return []
            
            return [self._convert_wbs_element_to_response(element) for element in result.data]
            
        except Exception as e:
            logger.error(f"Error getting WBS elements for schedule {schedule_id}: {e}")
            return []
    
    async def update_wbs_element_progress(
        self,
        element_id: UUID,
        progress_percentage: int
    ) -> WBSElementResponse:
        """
        Update progress for a WBS element and trigger parent rollup.
        
        Args:
            element_id: ID of the element
            progress_percentage: Progress percentage (0-100)
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Validate progress percentage
            if not 0 <= progress_percentage <= 100:
                raise ValueError("Progress percentage must be between 0 and 100")
            
            # Get existing element
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {element_id} not found")
            
            existing_element = existing_result.data[0]
            
            # Update progress
            update_data = {
                "progress_percentage": progress_percentage,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to update WBS element progress")
            
            updated_element = result.data[0]
            
            # Trigger parent progress rollup if element has parent
            if existing_element.get("parent_element_id"):
                await self._update_parent_wbs_progress_rollup(UUID(existing_element["parent_element_id"]))
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error updating WBS element progress {element_id}: {e}")
            raise RuntimeError(f"Failed to update WBS element progress: {str(e)}")
    
    # Private helper methods
    
    def _convert_wbs_element_to_response(self, element_data: Dict[str, Any]) -> WBSElementResponse:
        """Convert database WBS element record to WBSElementResponse model."""
        return WBSElementResponse(
            id=element_data["id"],
            schedule_id=element_data["schedule_id"],
            parent_element_id=element_data.get("parent_element_id"),
            task_id=element_data.get("task_id"),
            wbs_code=element_data["wbs_code"],
            name=element_data["name"],
            description=element_data.get("description"),
            level_number=element_data["level_number"],
            sort_order=element_data["sort_order"],
            work_package_manager=element_data.get("work_package_manager"),
            deliverable_description=element_data.get("deliverable_description"),
            acceptance_criteria=element_data.get("acceptance_criteria"),
            progress_percentage=element_data["progress_percentage"],
            created_by=element_data["created_by"],
            created_at=datetime.fromisoformat(element_data["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(element_data["updated_at"].replace('Z', '+00:00'))
        )
    
    async def _calculate_next_sort_order(
        self,
        schedule_id: UUID,
        parent_element_id: Optional[UUID]
    ) -> int:
        """Calculate the next sort order for a new element."""
        try:
            query = self.db.table("wbs_elements").select("sort_order").eq("schedule_id", str(schedule_id))
            
            if parent_element_id is None:
                query = query.is_("parent_element_id", "null")
            else:
                query = query.eq("parent_element_id", str(parent_element_id))
            
            result = query.order("sort_order", desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]["sort_order"] + 1
            else:
                return 1
                
        except Exception as e:
            logger.error(f"Error calculating next sort order: {e}")
            return 1
    
    async def _update_sibling_sort_orders(
        self,
        schedule_id: UUID,
        parent_element_id: Optional[UUID],
        from_position: int,
        increment: int
    ) -> None:
        """Update sort orders for sibling elements."""
        try:
            query = self.db.table("wbs_elements").select("id").eq("schedule_id", str(schedule_id))
            
            if parent_element_id is None:
                query = query.is_("parent_element_id", "null")
            else:
                query = query.eq("parent_element_id", str(parent_element_id))
            
            if increment > 0:
                # Increment sort orders at and after the position
                query = query.gte("sort_order", from_position)
            else:
                # Decrement sort orders after the position
                query = query.gt("sort_order", from_position)
            
            elements_result = query.execute()
            
            if elements_result.data:
                for element in elements_result.data:
                    # Update each element's sort order
                    current_result = self.db.table("wbs_elements").select("sort_order").eq(
                        "id", element["id"]
                    ).execute()
                    
                    if current_result.data:
                        current_sort_order = current_result.data[0]["sort_order"]
                        new_sort_order = current_sort_order + increment
                        
                        self.db.table("wbs_elements").update({
                            "sort_order": new_sort_order,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", element["id"]).execute()
            
        except Exception as e:
            logger.error(f"Error updating sibling sort orders: {e}")
    
    async def _update_descendant_levels(
        self,
        element_id: UUID,
        new_parent_level: int
    ) -> None:
        """Update level numbers for all descendants of an element."""
        try:
            # Get all descendants
            descendants_result = self.db.table("wbs_elements").select("id, level_number").eq(
                "parent_element_id", str(element_id)
            ).execute()
            
            if descendants_result.data:
                for descendant in descendants_result.data:
                    new_level = new_parent_level + 1
                    
                    # Update descendant level
                    self.db.table("wbs_elements").update({
                        "level_number": new_level,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", descendant["id"]).execute()
                    
                    # Recursively update descendants of this descendant
                    await self._update_descendant_levels(UUID(descendant["id"]), new_level)
            
        except Exception as e:
            logger.error(f"Error updating descendant levels: {e}")
    
    async def _would_create_circular_reference(
        self,
        element_id: UUID,
        new_parent_id: UUID
    ) -> bool:
        """Check if moving an element would create a circular reference."""
        try:
            # Check if new_parent_id is a descendant of element_id
            current_parent_id = new_parent_id
            
            while current_parent_id:
                if current_parent_id == element_id:
                    return True
                
                # Get parent of current parent
                parent_result = self.db.table("wbs_elements").select("parent_element_id").eq(
                    "id", str(current_parent_id)
                ).execute()
                
                if not parent_result.data or not parent_result.data[0].get("parent_element_id"):
                    break
                
                current_parent_id = UUID(parent_result.data[0]["parent_element_id"])
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circular reference: {e}")
            return True  # Err on the side of caution
    
    async def _has_circular_reference(
        self,
        element_id: UUID,
        element_map: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Check if an element has a circular reference in its hierarchy."""
        try:
            visited = set()
            current_id = str(element_id)
            
            while current_id and current_id in element_map:
                if current_id in visited:
                    return True
                
                visited.add(current_id)
                parent_id = element_map[current_id].get("parent_element_id")
                current_id = parent_id
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circular reference: {e}")
            return True  # Err on the side of caution
    
    async def _update_parent_wbs_progress_rollup(self, parent_element_id: UUID) -> None:
        """
        Update parent WBS element progress based on child element completion.
        
        Args:
            parent_element_id: ID of the parent element to update
        """
        try:
            # Get child elements
            children_result = self.db.table("wbs_elements").select(
                "progress_percentage"
            ).eq("parent_element_id", str(parent_element_id)).execute()
            
            if not children_result.data:
                return
            
            children = children_result.data
            
            # Calculate average progress (simple average for WBS elements)
            total_progress = sum(child.get("progress_percentage", 0) for child in children)
            average_progress = total_progress / len(children)
            
            # Update parent progress
            update_data = {
                "progress_percentage": int(round(average_progress)),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(parent_element_id)).execute()
            
            if result.data:
                # Check if this parent has its own parent and continue rollup
                parent_data = result.data[0]
                if parent_data.get("parent_element_id"):
                    await self._update_parent_wbs_progress_rollup(UUID(parent_data["parent_element_id"]))
            
        except Exception as e:
            logger.error(f"Error updating parent WBS progress rollup for element {parent_element_id}: {e}")
    
    # Work Package Management Methods
    
    async def create_work_package(
        self,
        wbs_element_id: UUID,
        work_package_data: Dict[str, Any],
        created_by: UUID
    ) -> WBSElementResponse:
        """
        Create or update a work package definition for a WBS element.
        
        Args:
            wbs_element_id: ID of the WBS element
            work_package_data: Work package definition data
            created_by: ID of the user creating the work package
            
        Returns:
            WBSElementResponse: Updated WBS element with work package data
        """
        try:
            # Get existing WBS element
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(wbs_element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {wbs_element_id} not found")
            
            existing_element = existing_result.data[0]
            
            # Validate work package manager if specified
            if work_package_data.get("work_package_manager"):
                user_result = self.db.table("auth.users").select("id").eq(
                    "id", str(work_package_data["work_package_manager"])
                ).execute()
                
                if not user_result.data:
                    raise ValueError(f"Work package manager {work_package_data['work_package_manager']} not found")
            
            # Prepare work package update data
            update_data = {
                "work_package_manager": str(work_package_data["work_package_manager"]) if work_package_data.get("work_package_manager") else None,
                "deliverable_description": work_package_data.get("deliverable_description"),
                "acceptance_criteria": work_package_data.get("acceptance_criteria"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update WBS element with work package data
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(wbs_element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to create work package")
            
            updated_element = result.data[0]
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error creating work package for WBS element {wbs_element_id}: {e}")
            raise RuntimeError(f"Failed to create work package: {str(e)}")
    
    async def assign_work_package_manager(
        self,
        wbs_element_id: UUID,
        manager_id: UUID,
        assigned_by: UUID
    ) -> WBSElementResponse:
        """
        Assign a work package manager to a WBS element.
        
        Args:
            wbs_element_id: ID of the WBS element
            manager_id: ID of the user to assign as work package manager
            assigned_by: ID of the user making the assignment
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Validate WBS element exists
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(wbs_element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {wbs_element_id} not found")
            
            # Validate manager exists
            user_result = self.db.table("auth.users").select("id").eq("id", str(manager_id)).execute()
            if not user_result.data:
                raise ValueError(f"User {manager_id} not found")
            
            # Update work package manager assignment
            update_data = {
                "work_package_manager": str(manager_id),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(wbs_element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to assign work package manager")
            
            updated_element = result.data[0]
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error assigning work package manager to WBS element {wbs_element_id}: {e}")
            raise RuntimeError(f"Failed to assign work package manager: {str(e)}")
    
    async def update_work_package_deliverables(
        self,
        wbs_element_id: UUID,
        deliverable_description: str,
        acceptance_criteria: Optional[str] = None,
        updated_by: UUID = None
    ) -> WBSElementResponse:
        """
        Update deliverable description and acceptance criteria for a work package.
        
        Args:
            wbs_element_id: ID of the WBS element
            deliverable_description: Description of the deliverables
            acceptance_criteria: Acceptance criteria for the deliverables
            updated_by: ID of the user making the update
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Validate WBS element exists
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(wbs_element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {wbs_element_id} not found")
            
            # Update deliverable information
            update_data = {
                "deliverable_description": deliverable_description,
                "acceptance_criteria": acceptance_criteria,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(wbs_element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to update work package deliverables")
            
            updated_element = result.data[0]
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error updating work package deliverables for WBS element {wbs_element_id}: {e}")
            raise RuntimeError(f"Failed to update work package deliverables: {str(e)}")
    
    async def get_work_packages_by_manager(
        self,
        manager_id: UUID,
        schedule_id: Optional[UUID] = None
    ) -> List[WBSElementResponse]:
        """
        Get all work packages assigned to a specific manager.
        
        Args:
            manager_id: ID of the work package manager
            schedule_id: Optional schedule ID to filter by
            
        Returns:
            List[WBSElementResponse]: List of work packages assigned to the manager
        """
        try:
            query = self.db.table("wbs_elements").select("*").eq("work_package_manager", str(manager_id))
            
            if schedule_id:
                query = query.eq("schedule_id", str(schedule_id))
            
            result = query.order("schedule_id", desc=False).order("wbs_code", desc=False).execute()
            
            if not result.data:
                return []
            
            return [self._convert_wbs_element_to_response(element) for element in result.data]
            
        except Exception as e:
            logger.error(f"Error getting work packages for manager {manager_id}: {e}")
            return []
    
    async def get_work_package_progress_summary(
        self,
        schedule_id: UUID,
        manager_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get work package progress summary for a schedule.
        
        Args:
            schedule_id: ID of the schedule
            manager_id: Optional manager ID to filter by
            
        Returns:
            Dict with work package progress summary
        """
        try:
            query = self.db.table("wbs_elements").select("*").eq("schedule_id", str(schedule_id))
            
            if manager_id:
                query = query.eq("work_package_manager", str(manager_id))
            
            result = query.execute()
            
            if not result.data:
                return {
                    "total_work_packages": 0,
                    "assigned_work_packages": 0,
                    "unassigned_work_packages": 0,
                    "completed_work_packages": 0,
                    "in_progress_work_packages": 0,
                    "not_started_work_packages": 0,
                    "average_progress": 0.0,
                    "work_packages_by_manager": {}
                }
            
            elements = result.data
            total_work_packages = len(elements)
            
            # Count work packages by status
            assigned_count = 0
            unassigned_count = 0
            completed_count = 0
            in_progress_count = 0
            not_started_count = 0
            total_progress = 0
            
            work_packages_by_manager = {}
            
            for element in elements:
                progress = element.get("progress_percentage", 0)
                manager = element.get("work_package_manager")
                
                # Count assignment status
                if manager:
                    assigned_count += 1
                    
                    # Group by manager
                    if manager not in work_packages_by_manager:
                        work_packages_by_manager[manager] = {
                            "count": 0,
                            "total_progress": 0,
                            "completed": 0,
                            "in_progress": 0,
                            "not_started": 0
                        }
                    
                    work_packages_by_manager[manager]["count"] += 1
                    work_packages_by_manager[manager]["total_progress"] += progress
                    
                    if progress == 100:
                        work_packages_by_manager[manager]["completed"] += 1
                    elif progress > 0:
                        work_packages_by_manager[manager]["in_progress"] += 1
                    else:
                        work_packages_by_manager[manager]["not_started"] += 1
                else:
                    unassigned_count += 1
                
                # Count progress status
                if progress == 100:
                    completed_count += 1
                elif progress > 0:
                    in_progress_count += 1
                else:
                    not_started_count += 1
                
                total_progress += progress
            
            # Calculate average progress for each manager
            for manager_data in work_packages_by_manager.values():
                if manager_data["count"] > 0:
                    manager_data["average_progress"] = manager_data["total_progress"] / manager_data["count"]
                else:
                    manager_data["average_progress"] = 0.0
            
            average_progress = total_progress / total_work_packages if total_work_packages > 0 else 0.0
            
            return {
                "total_work_packages": total_work_packages,
                "assigned_work_packages": assigned_count,
                "unassigned_work_packages": unassigned_count,
                "completed_work_packages": completed_count,
                "in_progress_work_packages": in_progress_count,
                "not_started_work_packages": not_started_count,
                "average_progress": round(average_progress, 2),
                "work_packages_by_manager": work_packages_by_manager
            }
            
        except Exception as e:
            logger.error(f"Error getting work package progress summary for schedule {schedule_id}: {e}")
            raise RuntimeError(f"Failed to get work package progress summary: {str(e)}")
    
    async def track_work_package_progress(
        self,
        wbs_element_id: UUID,
        progress_percentage: int,
        progress_notes: Optional[str] = None,
        updated_by: Optional[UUID] = None
    ) -> WBSElementResponse:
        """
        Track progress for a work package.
        
        Args:
            wbs_element_id: ID of the WBS element (work package)
            progress_percentage: Progress percentage (0-100)
            progress_notes: Optional progress notes
            updated_by: ID of the user updating progress
            
        Returns:
            WBSElementResponse: Updated WBS element data
        """
        try:
            # Validate progress percentage
            if not 0 <= progress_percentage <= 100:
                raise ValueError("Progress percentage must be between 0 and 100")
            
            # Get existing WBS element
            existing_result = self.db.table("wbs_elements").select("*").eq("id", str(wbs_element_id)).execute()
            if not existing_result.data:
                raise ValueError(f"WBS element {wbs_element_id} not found")
            
            existing_element = existing_result.data[0]
            
            # Update progress
            update_data = {
                "progress_percentage": progress_percentage,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.table("wbs_elements").update(update_data).eq("id", str(wbs_element_id)).execute()
            
            if not result.data:
                raise RuntimeError("Failed to update work package progress")
            
            updated_element = result.data[0]
            
            # Create progress tracking record (if progress notes provided)
            if progress_notes:
                await self._create_work_package_progress_record(
                    wbs_element_id, progress_percentage, progress_notes, updated_by
                )
            
            # Trigger parent progress rollup if element has parent
            if existing_element.get("parent_element_id"):
                await self._update_parent_wbs_progress_rollup(UUID(existing_element["parent_element_id"]))
            
            return self._convert_wbs_element_to_response(updated_element)
            
        except Exception as e:
            logger.error(f"Error tracking work package progress for WBS element {wbs_element_id}: {e}")
            raise RuntimeError(f"Failed to track work package progress: {str(e)}")
    
    async def get_work_package_deliverables_status(
        self,
        wbs_element_id: UUID
    ) -> Dict[str, Any]:
        """
        Get deliverables status for a work package.
        
        Args:
            wbs_element_id: ID of the WBS element (work package)
            
        Returns:
            Dict with deliverables status information
        """
        try:
            # Get WBS element
            element_result = self.db.table("wbs_elements").select("*").eq("id", str(wbs_element_id)).execute()
            if not element_result.data:
                raise ValueError(f"WBS element {wbs_element_id} not found")
            
            element = element_result.data[0]
            
            # Get linked tasks if any
            linked_tasks = []
            if element.get("task_id"):
                task_result = self.db.table("tasks").select("*").eq("id", element["task_id"]).execute()
                if task_result.data:
                    linked_tasks = task_result.data
            
            # Calculate deliverables status
            has_deliverable_description = bool(element.get("deliverable_description"))
            has_acceptance_criteria = bool(element.get("acceptance_criteria"))
            has_work_package_manager = bool(element.get("work_package_manager"))
            progress_percentage = element.get("progress_percentage", 0)
            
            # Determine overall status
            if progress_percentage == 100:
                status = "completed"
            elif progress_percentage > 0:
                status = "in_progress"
            elif has_deliverable_description and has_work_package_manager:
                status = "ready_to_start"
            else:
                status = "not_ready"
            
            return {
                "wbs_element_id": str(wbs_element_id),
                "wbs_code": element["wbs_code"],
                "name": element["name"],
                "status": status,
                "progress_percentage": progress_percentage,
                "has_deliverable_description": has_deliverable_description,
                "has_acceptance_criteria": has_acceptance_criteria,
                "has_work_package_manager": has_work_package_manager,
                "deliverable_description": element.get("deliverable_description"),
                "acceptance_criteria": element.get("acceptance_criteria"),
                "work_package_manager": element.get("work_package_manager"),
                "linked_tasks_count": len(linked_tasks),
                "linked_tasks": linked_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting work package deliverables status for WBS element {wbs_element_id}: {e}")
            raise RuntimeError(f"Failed to get work package deliverables status: {str(e)}")
    
    async def bulk_assign_work_package_managers(
        self,
        assignments: List[Dict[str, Any]],
        assigned_by: UUID
    ) -> Dict[str, Any]:
        """
        Bulk assign work package managers to multiple WBS elements.
        
        Args:
            assignments: List of assignment dictionaries with wbs_element_id and manager_id
            assigned_by: ID of the user making the assignments
            
        Returns:
            Dict with assignment results
        """
        try:
            successful_assignments = []
            failed_assignments = []
            
            for assignment in assignments:
                try:
                    wbs_element_id = UUID(assignment["wbs_element_id"])
                    manager_id = UUID(assignment["manager_id"])
                    
                    updated_element = await self.assign_work_package_manager(
                        wbs_element_id, manager_id, assigned_by
                    )
                    
                    successful_assignments.append({
                        "wbs_element_id": str(wbs_element_id),
                        "manager_id": str(manager_id),
                        "success": True,
                        "updated_element": updated_element
                    })
                    
                except Exception as e:
                    failed_assignments.append({
                        "wbs_element_id": assignment.get("wbs_element_id", "unknown"),
                        "manager_id": assignment.get("manager_id", "unknown"),
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "total_assignments": len(assignments),
                "successful_assignments": len(successful_assignments),
                "failed_assignments": len(failed_assignments),
                "results": successful_assignments + failed_assignments
            }
            
        except Exception as e:
            logger.error(f"Error in bulk assign work package managers: {e}")
            raise RuntimeError(f"Failed to bulk assign work package managers: {str(e)}")
    
    async def get_work_package_hierarchy_with_progress(
        self,
        schedule_id: UUID
    ) -> Dict[str, Any]:
        """
        Get WBS hierarchy with work package progress information.
        
        Args:
            schedule_id: ID of the schedule
            
        Returns:
            Dict with hierarchical work package structure and progress
        """
        try:
            # Get WBS hierarchy
            hierarchy = await self.get_wbs_hierarchy(schedule_id)
            
            if not hierarchy.elements:
                return {
                    "schedule_id": str(schedule_id),
                    "hierarchy": [],
                    "summary": {
                        "total_work_packages": 0,
                        "assigned_work_packages": 0,
                        "average_progress": 0.0
                    }
                }
            
            # Build hierarchical structure with progress
            elements_by_id = {e.id: e for e in hierarchy.elements}
            root_elements = [e for e in hierarchy.elements if not e.parent_element_id]
            
            def build_hierarchy_with_progress(element: WBSElementResponse) -> Dict[str, Any]:
                children = [e for e in hierarchy.elements if e.parent_element_id == element.id]
                children_data = [build_hierarchy_with_progress(child) for child in children]
                
                return {
                    "id": element.id,
                    "wbs_code": element.wbs_code,
                    "name": element.name,
                    "description": element.description,
                    "level_number": element.level_number,
                    "progress_percentage": element.progress_percentage,
                    "work_package_manager": element.work_package_manager,
                    "deliverable_description": element.deliverable_description,
                    "acceptance_criteria": element.acceptance_criteria,
                    "has_work_package_manager": bool(element.work_package_manager),
                    "has_deliverables": bool(element.deliverable_description),
                    "children": children_data,
                    "children_count": len(children_data)
                }
            
            hierarchy_data = [build_hierarchy_with_progress(root) for root in root_elements]
            
            # Calculate summary statistics
            total_elements = len(hierarchy.elements)
            assigned_elements = len([e for e in hierarchy.elements if e.work_package_manager])
            total_progress = sum(e.progress_percentage for e in hierarchy.elements)
            average_progress = total_progress / total_elements if total_elements > 0 else 0.0
            
            return {
                "schedule_id": str(schedule_id),
                "hierarchy": hierarchy_data,
                "summary": {
                    "total_work_packages": total_elements,
                    "assigned_work_packages": assigned_elements,
                    "unassigned_work_packages": total_elements - assigned_elements,
                    "average_progress": round(average_progress, 2),
                    "max_depth": hierarchy.max_depth
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting work package hierarchy with progress for schedule {schedule_id}: {e}")
            raise RuntimeError(f"Failed to get work package hierarchy with progress: {str(e)}")
    
    # Private helper methods for work package management
    
    async def _create_work_package_progress_record(
        self,
        wbs_element_id: UUID,
        progress_percentage: int,
        progress_notes: str,
        updated_by: Optional[UUID]
    ) -> None:
        """
        Create a work package progress record for audit trail.
        
        Args:
            wbs_element_id: ID of the WBS element
            progress_percentage: Progress percentage
            progress_notes: Progress notes
            updated_by: ID of the user who made the update
        """
        try:
            # This would typically insert into a work_package_progress_history table
            # For now, just log the progress update
            logger.info(
                f"Work package progress update for WBS element {wbs_element_id}: {progress_percentage}%"
                f"{f' by user {updated_by}' if updated_by else ''}"
                f" - Notes: {progress_notes}"
            )
            
        except Exception as e:
            logger.error(f"Error creating work package progress record: {e}")