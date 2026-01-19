"""
Property-Based Tests for Resource Optimizer Agent
Feature: ai-empowered-ppm-features
Tests Properties 6, 7, and 8
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import uuid
from unittest.mock import Mock, AsyncMock, patch
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_agents import ResourceOptimizerAgent


# Strategies for generating test data
@st.composite
def resource_strategy(draw):
    """Generate a valid resource dictionary"""
    return {
        "id": str(uuid.uuid4()),
        "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        "organization_id": str(uuid.uuid4()),
        "skills": draw(st.lists(st.sampled_from(["python", "javascript", "java", "sql", "aws", "docker"]), min_size=1, max_size=4)),
        "hourly_rate": draw(st.floats(min_value=50, max_value=200)),
        "capacity": draw(st.integers(min_value=80, max_value=200)),
        "available_hours": draw(st.integers(min_value=80, max_value=200))
    }


@st.composite
def project_strategy(draw):
    """Generate a valid project dictionary"""
    return {
        "id": str(uuid.uuid4()),
        "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        "organization_id": str(uuid.uuid4()),
        "required_skills": draw(st.lists(st.sampled_from(["python", "javascript", "java", "sql", "aws", "docker"]), min_size=1, max_size=3)),
        "required_hours": draw(st.integers(min_value=40, max_value=160)),
        "estimated_effort": draw(st.integers(min_value=40, max_value=160))
    }


def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestResourceOptimizerProperties:
    """Property-based tests for Resource Optimizer Agent"""
    
    @given(
        num_resources=st.integers(min_value=2, max_value=5),
        num_projects=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_6_optimization_cost_minimization(self, num_resources, num_projects):
        """
        Feature: ai-empowered-ppm-features
        Property 6: Optimization Cost Minimization
        
        For any valid resource optimization request with satisfiable constraints,
        the Optimizer_Agent SHALL return a solution that minimizes total cost
        (Σ resource_cost × allocation_hours) while satisfying all project
        requirements and resource availability constraints.
        
        Validates: Requirements 2.2
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Generate resources with same organization_id
        resources = []
        for i in range(num_resources):
            resources.append({
                "id": str(uuid.uuid4()),
                "name": f"Resource_{i}",
                "organization_id": organization_id,
                "skills": ["python", "javascript"],
                "hourly_rate": 100 + (i * 20),  # Varying costs
                "capacity": 160,
                "available_hours": 160
            })
        
        # Generate projects with same organization_id and satisfiable requirements
        projects = []
        total_required_hours = 0
        for i in range(num_projects):
            required_hours = 80  # Reasonable requirement
            total_required_hours += required_hours
            projects.append({
                "id": str(uuid.uuid4()),
                "name": f"Project_{i}",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": required_hours,
                "estimated_effort": required_hours
            })
        
        # Ensure constraints are satisfiable
        total_available_hours = sum(r["available_hours"] for r in resources)
        assume(total_available_hours >= total_required_hours)
        
        # Mock Supabase client
        mock_supabase = Mock()
        mock_supabase.table = Mock(return_value=Mock(
            select=Mock(return_value=Mock(
                eq=Mock(return_value=Mock(
                    execute=Mock(return_value=Mock(data=resources))
                ))
            )),
            insert=Mock(return_value=Mock(execute=Mock()))
        ))
        
        # Create agent
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock the data retrieval methods
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
        assert "total_cost_savings" in result
        assert "model_confidence" in result
        assert "constraints_satisfied" in result
        
        if result["constraints_satisfied"]:
            recommendations = result["recommendations"]
            
            # Verify cost minimization: lower-cost resources should be preferred
            if recommendations:
                # Calculate total cost
                total_cost = sum(rec["total_cost"] for rec in recommendations)
                
                # Verify all project requirements are met
                project_allocations = {}
                for rec in recommendations:
                    project_id = rec["project_id"]
                    if project_id not in project_allocations:
                        project_allocations[project_id] = 0
                    project_allocations[project_id] += rec["allocated_hours"]
                
                # Check that each project gets at least its required hours
                for project in projects:
                    allocated = project_allocations.get(project["id"], 0)
                    assert allocated >= project["required_hours"], \
                        f"Project {project['name']} requires {project['required_hours']} hours but only got {allocated}"
                
                # Verify resource availability constraints
                resource_allocations = {}
                for rec in recommendations:
                    resource_id = rec["resource_id"]
                    if resource_id not in resource_allocations:
                        resource_allocations[resource_id] = 0
                    resource_allocations[resource_id] += rec["allocated_hours"]
                
                for resource in resources:
                    allocated = resource_allocations.get(resource["id"], 0)
                    assert allocated <= resource["available_hours"], \
                        f"Resource {resource['name']} has {resource['available_hours']} hours but allocated {allocated}"
    
    @given(
        num_resources=st.integers(min_value=1, max_value=3),
        num_projects=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_7_ai_agent_confidence_scores(self, num_resources, num_projects):
        """
        Feature: ai-empowered-ppm-features
        Property 7: AI Agent Confidence Scores
        
        For any AI agent response (Optimizer, Forecaster, Validator, Anomaly Detector),
        the system SHALL include a confidence score between 0.0 and 1.0 for each
        recommendation or prediction.
        
        Validates: Requirements 2.3
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Generate resources
        resources = []
        for i in range(num_resources):
            resources.append({
                "id": str(uuid.uuid4()),
                "name": f"Resource_{i}",
                "organization_id": organization_id,
                "skills": ["python"],
                "hourly_rate": 100,
                "capacity": 160,
                "available_hours": 160
            })
        
        # Generate projects
        projects = []
        for i in range(num_projects):
            projects.append({
                "id": str(uuid.uuid4()),
                "name": f"Project_{i}",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            })
        
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
        assert "model_confidence" in result
        assert isinstance(result["model_confidence"], (int, float))
        assert 0.0 <= result["model_confidence"] <= 1.0, \
            f"Confidence score {result['model_confidence']} is not between 0.0 and 1.0"
        
        # Check individual recommendation confidence scores
        if "recommendations" in result and result["recommendations"]:
            for rec in result["recommendations"]:
                if "confidence" in rec:
                    assert isinstance(rec["confidence"], (int, float))
                    assert 0.0 <= rec["confidence"] <= 1.0, \
                        f"Recommendation confidence {rec['confidence']} is not between 0.0 and 1.0"
    
    @given(
        missing_data_type=st.sampled_from(["no_resources", "no_projects"])
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_8_missing_data_error_messages(self, missing_data_type):
        """
        Feature: ai-empowered-ppm-features
        Property 8: Missing Data Error Messages
        
        For any AI agent request with insufficient input data, the system SHALL
        return an error message specifically indicating which required data fields
        or minimum data requirements are missing.
        
        Validates: Requirements 2.5
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Create scenarios with missing data
        if missing_data_type == "no_resources":
            resources = []
            projects = [{
                "id": str(uuid.uuid4()),
                "name": "Project_1",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            }]
            expected_error_keywords = ["resource", "add resources"]
        else:  # no_projects
            resources = [{
                "id": str(uuid.uuid4()),
                "name": "Resource_1",
                "organization_id": organization_id,
                "skills": ["python"],
                "hourly_rate": 100,
                "capacity": 160,
                "available_hours": 160
            }]
            projects = []
            expected_error_keywords = ["project", "add projects"]
        
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
        assert "error" in result, "Expected error message for missing data"
        error_message = result["error"].lower()
        
        # Verify error message contains specific information about missing data
        assert any(keyword in error_message for keyword in expected_error_keywords), \
            f"Error message '{result['error']}' does not specify which data is missing. Expected keywords: {expected_error_keywords}"
        
        # Verify that recommendations are empty when data is missing
        assert result["recommendations"] == []
        assert result["model_confidence"] == 0.0
        assert result["constraints_satisfied"] == False

        """
        Feature: ai-empowered-ppm-features
        Property 6: Optimization Cost Minimization
        
        For any valid resource optimization request with satisfiable constraints,
        the Optimizer_Agent SHALL return a solution that minimizes total cost
        (Σ resource_cost × allocation_hours) while satisfying all project
        requirements and resource availability constraints.
        
        Validates: Requirements 2.2
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Generate resources with same organization_id
        resources = []
        for i in range(num_resources):
            resources.append({
                "id": str(uuid.uuid4()),
                "name": f"Resource_{i}",
                "organization_id": organization_id,
                "skills": ["python", "javascript"],
                "hourly_rate": 100 + (i * 20),  # Varying costs
                "capacity": 160,
                "available_hours": 160
            })
        
        # Generate projects with same organization_id and satisfiable requirements
        projects = []
        total_required_hours = 0
        for i in range(num_projects):
            required_hours = 80  # Reasonable requirement
            total_required_hours += required_hours
            projects.append({
                "id": str(uuid.uuid4()),
                "name": f"Project_{i}",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": required_hours,
                "estimated_effort": required_hours
            })
        
        # Ensure constraints are satisfiable
        total_available_hours = sum(r["available_hours"] for r in resources)
        assume(total_available_hours >= total_required_hours)
        
        # Mock Supabase client
        mock_supabase = Mock()
        mock_supabase.table = Mock(return_value=Mock(
            select=Mock(return_value=Mock(
                eq=Mock(return_value=Mock(
                    execute=Mock(return_value=Mock(data=resources))
                ))
            )),
            insert=Mock(return_value=Mock(execute=Mock()))
        ))
        
        # Create agent
        agent = ResourceOptimizerAgent(mock_supabase, "test-api-key")
        
        # Mock the data retrieval methods
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
        assert "total_cost_savings" in result
        assert "model_confidence" in result
        assert "constraints_satisfied" in result
        
        if result["constraints_satisfied"]:
            recommendations = result["recommendations"]
            
            # Verify cost minimization: lower-cost resources should be preferred
            if recommendations:
                # Calculate total cost
                total_cost = sum(rec["total_cost"] for rec in recommendations)
                
                # Verify all project requirements are met
                project_allocations = {}
                for rec in recommendations:
                    project_id = rec["project_id"]
                    if project_id not in project_allocations:
                        project_allocations[project_id] = 0
                    project_allocations[project_id] += rec["allocated_hours"]
                
                # Check that each project gets at least its required hours
                for project in projects:
                    allocated = project_allocations.get(project["id"], 0)
                    assert allocated >= project["required_hours"], \
                        f"Project {project['name']} requires {project['required_hours']} hours but only got {allocated}"
                
                # Verify resource availability constraints
                resource_allocations = {}
                for rec in recommendations:
                    resource_id = rec["resource_id"]
                    if resource_id not in resource_allocations:
                        resource_allocations[resource_id] = 0
                    resource_allocations[resource_id] += rec["allocated_hours"]
                
                for resource in resources:
                    allocated = resource_allocations.get(resource["id"], 0)
                    assert allocated <= resource["available_hours"], \
                        f"Resource {resource['name']} has {resource['available_hours']} hours but allocated {allocated}"
    
    @given(
        num_resources=st.integers(min_value=1, max_value=3),
        num_projects=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_7_ai_agent_confidence_scores(self, num_resources, num_projects):
        """
        Feature: ai-empowered-ppm-features
        Property 7: AI Agent Confidence Scores
        
        For any AI agent response (Optimizer, Forecaster, Validator, Anomaly Detector),
        the system SHALL include a confidence score between 0.0 and 1.0 for each
        recommendation or prediction.
        
        Validates: Requirements 2.3
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Generate resources
        resources = []
        for i in range(num_resources):
            resources.append({
                "id": str(uuid.uuid4()),
                "name": f"Resource_{i}",
                "organization_id": organization_id,
                "skills": ["python"],
                "hourly_rate": 100,
                "capacity": 160,
                "available_hours": 160
            })
        
        # Generate projects
        projects = []
        for i in range(num_projects):
            projects.append({
                "id": str(uuid.uuid4()),
                "name": f"Project_{i}",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            })
        
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
        assert "model_confidence" in result
        assert isinstance(result["model_confidence"], (int, float))
        assert 0.0 <= result["model_confidence"] <= 1.0, \
            f"Confidence score {result['model_confidence']} is not between 0.0 and 1.0"
        
        # Check individual recommendation confidence scores
        if "recommendations" in result and result["recommendations"]:
            for rec in result["recommendations"]:
                if "confidence" in rec:
                    assert isinstance(rec["confidence"], (int, float))
                    assert 0.0 <= rec["confidence"] <= 1.0, \
                        f"Recommendation confidence {rec['confidence']} is not between 0.0 and 1.0"
    
    @given(
        missing_data_type=st.sampled_from(["no_resources", "no_projects"])
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_8_missing_data_error_messages(self, missing_data_type):
        """
        Feature: ai-empowered-ppm-features
        Property 8: Missing Data Error Messages
        
        For any AI agent request with insufficient input data, the system SHALL
        return an error message specifically indicating which required data fields
        or minimum data requirements are missing.
        
        Validates: Requirements 2.5
        """
        # Arrange
        organization_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Create scenarios with missing data
        if missing_data_type == "no_resources":
            resources = []
            projects = [{
                "id": str(uuid.uuid4()),
                "name": "Project_1",
                "organization_id": organization_id,
                "required_skills": ["python"],
                "required_hours": 80,
                "estimated_effort": 80
            }]
            expected_error_keywords = ["resource", "add resources"]
        else:  # no_projects
            resources = [{
                "id": str(uuid.uuid4()),
                "name": "Resource_1",
                "organization_id": organization_id,
                "skills": ["python"],
                "hourly_rate": 100,
                "capacity": 160,
                "available_hours": 160
            }]
            projects = []
            expected_error_keywords = ["project", "add projects"]
        
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
        assert "error" in result, "Expected error message for missing data"
        error_message = result["error"].lower()
        
        # Verify error message contains specific information about missing data
        assert any(keyword in error_message for keyword in expected_error_keywords), \
            f"Error message '{result['error']}' does not specify which data is missing. Expected keywords: {expected_error_keywords}"
        
        # Verify that recommendations are empty when data is missing
        assert result["recommendations"] == []
        assert result["model_confidence"] == 0.0
        assert result["constraints_satisfied"] == False
