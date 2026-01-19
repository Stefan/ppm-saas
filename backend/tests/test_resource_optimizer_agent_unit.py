"""
Unit Tests for Resource Optimizer Agent Edge Cases
Feature: ai-empowered-ppm-features
Tests edge cases for Requirements 2.2, 2.5, 2.6
"""

import pytest
from unittest.mock import Mock
import uuid
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_agents import ResourceOptimizerAgent


def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestResourceOptimizerEdgeCases:
    """Unit tests for Resource Optimizer Agent edge cases"""
    
    def test_zero_resources(self):
        """
        Test with zero resources
        Requirements: 2.5
        
        When no resources are available, the optimizer should return
        an error message indicating missing resources.
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        resources = []
        projects = [{
            "id": str(uuid.uuid4()),
            "name": "Project_1",
            "organization_id": organization_id,
            "required_skills": ["python"],
            "required_hours": 80,
            "estimated_effort": 80
        }]
        
        # Mock Supabase client
        mock_supabase = Mock()
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock methods
        async def mock_get_resources(org_id):
            return resources
        
        async def mock_get_projects(org_id):
            return projects
        
        async def mock_log_audit(*args, **kwargs):
            pass
        
        agent._get_resources_by_organization = mock_get_resources
        agent._get_projects_by_organization = mock_get_projects
        agent._log_audit = mock_log_audit
        
        # Act
        result = run_async(agent.optimize_resources(organization_id, user_id))
        
        # Assert
        assert "error" in result
        assert "resource" in result["error"].lower()
        assert result["recommendations"] == []
        assert result["model_confidence"] == 0.0
        assert result["constraints_satisfied"] == False
    
    def test_conflicting_constraints(self):
        """
        Test with conflicting constraints
        Requirements: 2.2, 2.6
        
        When project requirements exceed available resource capacity,
        the optimizer should return an infeasibility message.
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Resources with limited capacity
        resources = [{
            "id": str(uuid.uuid4()),
            "name": "Resource_1",
            "organization_id": organization_id,
            "skills": ["python"],
            "hourly_rate": 100,
            "capacity": 40,  # Very limited capacity
            "available_hours": 40
        }]
        
        # Projects requiring more hours than available
        projects = [
            {
                "id": str(uuid.uuid4()),
                "name": "Project_1",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,  # Requires more than available
                "estimated_effort": 80
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Project_2",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,  # Requires more than available
                "estimated_effort": 80
            }
        ]
        
        # Mock Supabase client
        mock_supabase = Mock()
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock methods
        async def mock_get_resources(org_id):
            return resources
        
        async def mock_get_projects(org_id):
            return projects
        
        async def mock_log_audit(*args, **kwargs):
            pass
        
        agent._get_resources_by_organization = mock_get_resources
        agent._get_projects_by_organization = mock_get_projects
        agent._log_audit = mock_log_audit
        
        # Act
        result = run_async(agent.optimize_resources(organization_id, user_id))
        
        # Assert
        assert "error" in result or result["solver_status"] == "Infeasible"
        if "error" in result:
            assert "feasible" in result["error"].lower() or "capacity" in result["error"].lower()
    
    def test_optimal_solution_scenario(self):
        """
        Test with optimal solution scenarios
        Requirements: 2.2
        
        When resources perfectly match project requirements,
        the optimizer should find an optimal solution.
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Resources with sufficient capacity
        resources = [
            {
                "id": str(uuid.uuid4()),
                "name": "Resource_1",
                "organization_id": organization_id,
                "skills": ["python", "javascript"],
                "hourly_rate": 100,
                "capacity": 160,
                "available_hours": 160
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Resource_2",
                "organization_id": organization_id,
                "skills": ["python", "java"],
                "hourly_rate": 120,
                "capacity": 160,
                "available_hours": 160
            }
        ]
        
        # Projects with reasonable requirements
        projects = [
            {
                "id": str(uuid.uuid4()),
                "name": "Project_1",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Project_2",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            }
        ]
        
        # Mock Supabase client
        mock_supabase = Mock()
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock methods
        async def mock_get_resources(org_id):
            return resources
        
        async def mock_get_projects(org_id):
            return projects
        
        async def mock_log_audit(*args, **kwargs):
            pass
        
        agent._get_resources_by_organization = mock_get_resources
        agent._get_projects_by_organization = mock_get_projects
        agent._log_audit = mock_log_audit
        
        # Act
        result = run_async(agent.optimize_resources(organization_id, user_id))
        
        # Assert
        assert "recommendations" in result
        assert result["constraints_satisfied"] == True
        assert result["solver_status"] == "Optimal"
        assert result["model_confidence"] > 0.5
        
        # Verify recommendations exist
        assert len(result["recommendations"]) > 0
        
        # Verify all projects are allocated
        project_allocations = {}
        for rec in result["recommendations"]:
            project_id = rec["project_id"]
            if project_id not in project_allocations:
                project_allocations[project_id] = 0
            project_allocations[project_id] += rec["allocated_hours"]
        
        # Each project should get at least its required hours
        for project in projects:
            allocated = project_allocations.get(project["id"], 0)
            assert allocated >= project["required_hours"], \
                f"Project {project['name']} requires {project['required_hours']} hours but only got {allocated}"
    
    def test_skill_mismatch_constraint(self):
        """
        Test with skill mismatch constraints
        Requirements: 2.6
        
        When resources don't have required skills, the optimizer
        should not allocate them to those projects.
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Resources with specific skills
        resources = [{
            "id": str(uuid.uuid4()),
            "name": "Resource_1",
            "organization_id": organization_id,
            "skills": ["java", "sql"],  # No Python skills
            "hourly_rate": 100,
            "capacity": 160,
            "available_hours": 160
        }]
        
        # Project requiring Python skills
        projects = [{
            "id": str(uuid.uuid4()),
            "name": "Project_1",
            "organization_id": organization_id,
            "required_skills": ["python"],  # Requires Python
            "required_hours": 80,
            "estimated_effort": 80
        }]
        
        # Mock Supabase client
        mock_supabase = Mock()
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock methods
        async def mock_get_resources(org_id):
            return resources
        
        async def mock_get_projects(org_id):
            return projects
        
        async def mock_log_audit(*args, **kwargs):
            pass
        
        agent._get_resources_by_organization = mock_get_resources
        agent._get_projects_by_organization = mock_get_projects
        agent._log_audit = mock_log_audit
        
        # Act
        result = run_async(agent.optimize_resources(organization_id, user_id))
        
        # Assert
        # Should be infeasible due to skill mismatch
        assert "error" in result or result["solver_status"] == "Infeasible"
        if "error" in result:
            assert "skill" in result["error"].lower() or "feasible" in result["error"].lower()
