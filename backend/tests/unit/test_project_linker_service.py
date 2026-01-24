"""
Unit tests for Project Linker Service

Tests the project linking functionality for actuals and commitments imports.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from services.project_linker import ProjectLinker


class TestProjectLinker:
    """Test suite for ProjectLinker"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client"""
        mock_client = Mock()
        mock_client.table = Mock()
        return mock_client
    
    @pytest.fixture
    def project_linker(self, mock_supabase):
        """Create a ProjectLinker instance with mock client"""
        return ProjectLinker(mock_supabase)
    
    @pytest.mark.asyncio
    async def test_get_or_create_project_returns_existing_project(self, project_linker, mock_supabase):
        """Test that existing project is returned when found"""
        existing_id = uuid4()
        project_nr = "P0001"
        
        # Mock the database response for finding existing project
        mock_response = Mock()
        mock_response.data = [{"id": str(existing_id)}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await project_linker.get_or_create_project(project_nr)
        
        assert result == existing_id
        assert project_nr in project_linker.project_cache
        assert project_linker.project_cache[project_nr] == existing_id
    
    @pytest.mark.asyncio
    async def test_get_or_create_project_creates_new_project(self, project_linker, mock_supabase):
        """Test that new project is created when not found"""
        project_nr = "P0002"
        
        # Mock the database response for not finding project
        mock_find_response = Mock()
        mock_find_response.data = []
        
        # Mock the database response for creating project
        mock_create_response = Mock()
        mock_create_response.data = [{"id": "new-project-id"}]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_find_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_create_response
        
        result = await project_linker.get_or_create_project(project_nr)
        
        assert isinstance(result, UUID)
        assert project_nr in project_linker.project_cache
    
    @pytest.mark.asyncio
    async def test_get_or_create_project_uses_cache(self, project_linker, mock_supabase):
        """Test that cached project is returned without database query"""
        project_nr = "P0003"
        cached_id = uuid4()
        
        # Pre-populate cache
        project_linker.project_cache[project_nr] = cached_id
        
        result = await project_linker.get_or_create_project(project_nr)
        
        assert result == cached_id
        # Verify no database calls were made
        mock_supabase.table.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_or_create_project_with_wbs_element(self, project_linker, mock_supabase):
        """Test that WBS element is used in project description"""
        project_nr = "P0004"
        wbs_element = "WBS-001"
        
        # Mock the database response for not finding project
        mock_find_response = Mock()
        mock_find_response.data = []
        
        # Mock the database response for creating project
        mock_create_response = Mock()
        mock_create_response.data = [{"id": "new-project-id"}]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_find_response
        mock_insert = mock_supabase.table.return_value.insert
        mock_insert.return_value.execute.return_value = mock_create_response
        
        result = await project_linker.get_or_create_project(project_nr, wbs_element)
        
        # Verify insert was called with WBS element in description
        assert mock_insert.called
        insert_data = mock_insert.call_args[0][0]
        assert "WBS-001" in insert_data["description"]
    
    @pytest.mark.asyncio
    async def test_find_project_by_nr_returns_uuid(self, project_linker, mock_supabase):
        """Test that _find_project_by_nr returns UUID when project exists"""
        project_nr = "P0005"
        expected_id = uuid4()
        
        # Mock the database response
        mock_response = Mock()
        mock_response.data = [{"id": str(expected_id)}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await project_linker._find_project_by_nr(project_nr)
        
        assert result == expected_id
    
    @pytest.mark.asyncio
    async def test_find_project_by_nr_returns_none_when_not_found(self, project_linker, mock_supabase):
        """Test that _find_project_by_nr returns None when project doesn't exist"""
        project_nr = "P0006"
        
        # Mock the database response for not finding project
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await project_linker._find_project_by_nr(project_nr)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_project_sets_default_values(self, project_linker, mock_supabase):
        """Test that _create_project sets status='active' and health='green'"""
        project_nr = "P0007"
        
        # Mock the database response
        mock_response = Mock()
        mock_response.data = [{"id": "new-project-id"}]
        mock_insert = mock_supabase.table.return_value.insert
        mock_insert.return_value.execute.return_value = mock_response
        
        result = await project_linker._create_project(project_nr, None)
        
        # Verify insert was called with correct default values
        assert mock_insert.called
        insert_data = mock_insert.call_args[0][0]
        assert insert_data["status"] == "active"
        assert insert_data["health"] == "green"
        assert insert_data["name"] == project_nr
    
    @pytest.mark.asyncio
    async def test_create_project_uses_project_nr_as_name(self, project_linker, mock_supabase):
        """Test that _create_project uses project_nr as the project name"""
        project_nr = "P0008"
        
        # Mock the database response
        mock_response = Mock()
        mock_response.data = [{"id": "new-project-id"}]
        mock_insert = mock_supabase.table.return_value.insert
        mock_insert.return_value.execute.return_value = mock_response
        
        result = await project_linker._create_project(project_nr, None)
        
        # Verify project name matches project_nr
        insert_data = mock_insert.call_args[0][0]
        assert insert_data["name"] == project_nr
    
    @pytest.mark.asyncio
    async def test_create_project_without_wbs_element(self, project_linker, mock_supabase):
        """Test that _create_project handles None WBS element"""
        project_nr = "P0009"
        
        # Mock the database response
        mock_response = Mock()
        mock_response.data = [{"id": "new-project-id"}]
        mock_insert = mock_supabase.table.return_value.insert
        mock_insert.return_value.execute.return_value = mock_response
        
        result = await project_linker._create_project(project_nr, None)
        
        # Verify description is None when no WBS element
        insert_data = mock_insert.call_args[0][0]
        assert insert_data["description"] is None
    
    @pytest.mark.asyncio
    async def test_create_project_raises_on_failure(self, project_linker, mock_supabase):
        """Test that _create_project raises exception on database error"""
        project_nr = "P0010"
        
        # Mock database error
        mock_supabase.table.return_value.insert.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await project_linker._create_project(project_nr, None)
        
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multiple_projects_cached_correctly(self, project_linker, mock_supabase):
        """Test that multiple projects are cached correctly"""
        project_nr1 = "P0011"
        project_nr2 = "P0012"
        id1 = uuid4()
        id2 = uuid4()
        
        # Mock responses for both projects
        mock_response1 = Mock()
        mock_response1.data = [{"id": str(id1)}]
        
        mock_response2 = Mock()
        mock_response2.data = [{"id": str(id2)}]
        
        # Setup mock to return different responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_response1,
            mock_response2
        ]
        
        result1 = await project_linker.get_or_create_project(project_nr1)
        result2 = await project_linker.get_or_create_project(project_nr2)
        
        assert result1 == id1
        assert result2 == id2
        assert project_linker.project_cache[project_nr1] == id1
        assert project_linker.project_cache[project_nr2] == id2
