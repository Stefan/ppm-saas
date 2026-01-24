"""
Project Linker Service for Import Actuals and Commitments

This service manages the linking of imported financial data to projects.
It searches for existing projects by project number and creates new projects
when necessary with appropriate default values.
"""

from typing import Optional, Dict
from uuid import UUID, uuid4
from supabase import Client
import logging

logger = logging.getLogger(__name__)

# Default portfolio ID for auto-created projects
DEFAULT_PORTFOLIO_ID = "7608eb53-768e-4fa8-94f7-633c92b7a6ab"


class ProjectLinker:
    """
    Service for linking imported financial data to projects.
    
    Responsibilities:
    - Find existing projects by project number
    - Create new projects when project number doesn't exist
    - Maintain project cache for performance
    - Set appropriate default values for auto-created projects
    
    Auto-created projects have:
    - status: 'active'
    - health: 'green'
    - portfolio_id: Default portfolio
    - description: Based on WBS element if provided
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize Project Linker with database client.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.project_cache: Dict[str, UUID] = {}
    
    async def get_or_create_project(
        self,
        project_nr: str,
        wbs_element: Optional[str] = None
    ) -> UUID:
        """
        Get existing project or create new one based on project number.
        
        This method first checks the in-memory cache, then searches the database
        for an existing project with the given project number. If no project is
        found, it creates a new one with default values.
        
        Args:
            project_nr: Project number to search for or create
            wbs_element: Work Breakdown Structure element (used for description)
            
        Returns:
            UUID of the existing or newly created project
            
        Example:
            >>> linker = ProjectLinker(supabase_client)
            >>> project_id = await linker.get_or_create_project("P0001", "WBS-001")
            >>> # Returns UUID of project with project_nr="P0001"
        """
        # Check cache first
        if project_nr in self.project_cache:
            logger.debug(f"Project {project_nr} found in cache")
            return self.project_cache[project_nr]
        
        # Search for existing project
        existing_id = await self._find_project_by_nr(project_nr)
        if existing_id:
            logger.info(f"Found existing project {project_nr} with ID {existing_id}")
            self.project_cache[project_nr] = existing_id
            return existing_id
        
        # Create new project
        new_project_id = await self._create_project(project_nr, wbs_element)
        logger.info(f"Created new project {project_nr} with ID {new_project_id}")
        self.project_cache[project_nr] = new_project_id
        return new_project_id
    
    async def _find_project_by_nr(self, project_nr: str) -> Optional[UUID]:
        """
        Find project by project number in database.
        
        Searches the projects table for a project with a name matching the
        project number. This assumes that auto-created projects use the
        project number as their name.
        
        Args:
            project_nr: Project number to search for
            
        Returns:
            UUID of the project if found, None otherwise
        """
        try:
            response = self.supabase.table("projects").select("id").eq(
                "name", project_nr
            ).execute()
            
            if response.data and len(response.data) > 0:
                project_id = response.data[0]["id"]
                return UUID(project_id) if isinstance(project_id, str) else project_id
            
            return None
        except Exception as e:
            logger.error(f"Error finding project by number {project_nr}: {e}")
            raise
    
    async def _create_project(
        self,
        project_nr: str,
        wbs_element: Optional[str]
    ) -> UUID:
        """
        Create new project with default values.
        
        Creates a project with:
        - name: project_nr (the anonymized project number)
        - description: Based on WBS element if provided
        - status: 'active'
        - health: 'green'
        - portfolio_id: Default portfolio
        
        Args:
            project_nr: Project number to use as project name
            wbs_element: Work Breakdown Structure element for description
            
        Returns:
            UUID of the newly created project
            
        Raises:
            Exception: If project creation fails
        """
        try:
            project_id = uuid4()
            
            # Build description from WBS element
            description = None
            if wbs_element:
                description = f"Auto-created project for WBS: {wbs_element}"
            
            project_data = {
                "id": str(project_id),
                "portfolio_id": DEFAULT_PORTFOLIO_ID,
                "name": project_nr,
                "description": description,
                "status": "active",
                "health": "green"
            }
            
            response = self.supabase.table("projects").insert(project_data).execute()
            
            if not response.data:
                raise ValueError(f"Failed to create project for {project_nr}")
            
            return project_id
        except Exception as e:
            logger.error(f"Error creating project {project_nr}: {e}")
            raise
