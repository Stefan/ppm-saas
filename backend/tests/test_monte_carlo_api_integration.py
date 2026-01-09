"""
Integration tests for Monte Carlo Risk Simulation API endpoints.

These tests validate:
- End-to-end simulation workflows
- Error handling and edge cases
- Performance with varying project sizes
- API response formats and validation
"""

import pytest
import asyncio
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Import the FastAPI app and dependencies
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from monte_carlo.models import RiskCategory, ImpactType, DistributionType
from auth.dependencies import get_current_user

# Test client
client = TestClient(app)

# Mock user for authentication
def mock_get_current_user():
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "admin"
    }

# Override the dependency
app.dependency_overrides[get_current_user] = mock_get_current_user

class TestMonteCarloAPIIntegration:
    """Integration tests for Monte Carlo API endpoints."""
    
    @pytest.fixture
    def sample_risk_data(self):
        """Sample risk data for testing."""
        return {
            "id": "risk-001",
            "name": "Construction Delay Risk",
            "category": RiskCategory.SCHEDULE.value,
            "impact_type": ImpactType.BOTH.value,
            "distribution_type": DistributionType.TRIANGULAR.value,
            "distribution_parameters": {
                "min": 1000.0,
                "mode": 5000.0,
                "max": 10000.0
            },
            "baseline_impact": 5000.0,
            "correlation_dependencies": [],
            "mitigation_strategies": [
                {
                    "id": "mitigation-001",
                    "name": "Early Planning",
                    "description": "Implement early planning to reduce delays",
                    "cost": 2000.0,
                    "effectiveness": 0.3,
                    "implementation_time": 30
                }
            ]
        }
    
    @pytest.fixture
    def sample_simulation_request(self, sample_risk_data):
        """Sample simulation request for testing."""
        return {
            "risks": [sample_risk_data],
            "iterations": 10000,
            "correlations": None,
            "random_seed": 42,
            "baseline_costs": {"construction": 100000.0},
            "schedule_data": None
        }
    
    @pytest.fixture
    def multiple_risks_request(self):
        """Simulation request with multiple risks for testing."""
        risks = []
        for i in range(5):
            risk = {
                "id": f"risk-{i:03d}",
                "name": f"Risk {i}",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {
                    "mean": 1000.0 * (i + 1),
                    "std": 200.0 * (i + 1)
                },
                "baseline_impact": 1000.0 * (i + 1),
                "correlation_dependencies": [],
                "mitigation_strategies": []
            }
            risks.append(risk)
        
        return {
            "risks": risks,
            "iterations": 15000,
            "correlations": {
                "risk-000": {"risk-001": 0.3, "risk-002": 0.2},
                "risk-001": {"risk-002": 0.4}
            },
            "random_seed": 123,
            "baseline_costs": {"total": 50000.0}
        }
    
    def test_simulation_run_success(self, sample_simulation_request):
        """Test successful simulation execution."""
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json=sample_simulation_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "simulation_id" in data
        assert "status" in data
        assert "timestamp" in data
        assert "iteration_count" in data
        assert "execution_time" in data
        assert "convergence_status" in data
        assert "summary" in data
        
        # Validate simulation results
        assert data["status"] == "completed"
        assert data["iteration_count"] == 10000
        assert isinstance(data["execution_time"], (int, float))
        assert data["execution_time"] > 0
        
        # Validate summary statistics
        summary = data["summary"]
        assert "cost_statistics" in summary
        assert "schedule_statistics" in summary
        
        cost_stats = summary["cost_statistics"]
        assert all(key in cost_stats for key in ["mean", "std", "min", "max"])
        assert all(isinstance(cost_stats[key], (int, float)) for key in cost_stats)
        
        return data["simulation_id"]  # Return for use in other tests
    
    def test_simulation_run_with_multiple_risks(self, multiple_risks_request):
        """Test simulation with multiple correlated risks."""
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json=multiple_risks_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert data["status"] == "completed"
        assert data["iteration_count"] == 15000
        
        # Validate performance info is included
        assert "performance_info" in data
        perf_info = data["performance_info"]
        assert "complexity_score" in perf_info
        assert "estimated_execution_time" in perf_info
        assert "performance_tier" in perf_info
        
        return data["simulation_id"]
    
    def test_simulation_validation_errors(self):
        """Test various validation error scenarios."""
        # Test empty risks list
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json={"risks": [], "iterations": 10000}
        )
        assert response.status_code == 400
        
        # Test invalid iterations
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json={
                "risks": [{
                    "id": "test-risk",
                    "name": "Test Risk",
                    "category": "invalid_category",
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 1000, "std": 200},
                    "baseline_impact": 1000
                }],
                "iterations": 5000  # Below minimum
            }
        )
        assert response.status_code == 400
        
        # Test invalid distribution parameters
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json={
                "risks": [{
                    "id": "test-risk",
                    "name": "Test Risk",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.TRIANGULAR.value,
                    "distribution_parameters": {
                        "min": 1000,
                        "mode": 500,  # Invalid: mode < min
                        "max": 2000
                    },
                    "baseline_impact": 1000
                }],
                "iterations": 10000
            }
        )
        assert response.status_code == 400
    
    def test_simulation_progress_tracking(self, sample_simulation_request):
        """Test simulation progress tracking."""
        # Start a simulation
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json=sample_simulation_request
        )
        assert response.status_code == 200
        simulation_id = response.json()["simulation_id"]
        
        # Check progress (simulation should be completed quickly for test)
        response = client.get(f"/api/v1/monte-carlo/simulations/{simulation_id}/progress")
        assert response.status_code == 200
        
        progress_data = response.json()
        assert "simulation_id" in progress_data
        assert "status" in progress_data
        assert "progress" in progress_data
        assert progress_data["simulation_id"] == simulation_id
    
    def test_simulation_results_retrieval(self, sample_simulation_request):
        """Test retrieving simulation results."""
        # Run simulation first
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json=sample_simulation_request
        )
        assert response.status_code == 200
        simulation_id = response.json()["simulation_id"]
        
        # Retrieve results without raw data
        response = client.get(f"/api/v1/monte-carlo/simulations/{simulation_id}/results")
        assert response.status_code == 200
        
        results_data = response.json()
        assert "simulation_id" in results_data
        assert "cost_analysis" in results_data
        assert "confidence_intervals" in results_data
        assert "risk_contributions" in results_data
        
        # Validate cost analysis
        cost_analysis = results_data["cost_analysis"]
        assert "percentiles" in cost_analysis
        assert "mean" in cost_analysis
        assert "median" in cost_analysis
        assert "std_dev" in cost_analysis
        
        # Validate confidence intervals
        confidence_intervals = results_data["confidence_intervals"]
        assert "0.8" in confidence_intervals
        assert "0.9" in confidence_intervals
        assert "0.95" in confidence_intervals
        
        # Retrieve results with raw data
        response = client.get(
            f"/api/v1/monte-carlo/simulations/{simulation_id}/results?include_raw_data=true"
        )
        assert response.status_code == 200
        
        raw_data_results = response.json()
        assert "raw_data" in raw_data_results
        raw_data = raw_data_results["raw_data"]
        assert "cost_outcomes" in raw_data
        assert "schedule_outcomes" in raw_data
        assert "risk_contributions" in raw_data
        
        # Validate raw data structure
        assert isinstance(raw_data["cost_outcomes"], list)
        assert len(raw_data["cost_outcomes"]) == sample_simulation_request["iterations"]
    
    def test_scenario_creation_and_management(self, sample_risk_data):
        """Test scenario creation and management."""
        scenario_request = {
            "name": "Test Scenario",
            "description": "A test scenario for validation",
            "base_risks": [sample_risk_data],
            "modifications": {
                "risk-001": {
                    "parameter_changes": {"mode": 7000.0},
                    "mitigation_applied": "mitigation-001"
                }
            }
        }
        
        # Create scenario
        response = client.post("/api/v1/monte-carlo/scenarios", json=scenario_request)
        assert response.status_code == 200
        
        scenario_data = response.json()
        assert "scenario_id" in scenario_data
        assert scenario_data["name"] == "Test Scenario"
        assert scenario_data["risk_count"] == 1
        assert scenario_data["modification_count"] == 1
        
        scenario_id = scenario_data["scenario_id"]
        
        # Retrieve scenario
        response = client.get(f"/api/v1/monte-carlo/scenarios/{scenario_id}")
        assert response.status_code == 200
        
        retrieved_scenario = response.json()
        assert retrieved_scenario["scenario_id"] == scenario_id
        assert retrieved_scenario["name"] == "Test Scenario"
        assert len(retrieved_scenario["risks"]) == 1
        assert len(retrieved_scenario["modifications"]) == 1
        
        return scenario_id
    
    def test_scenario_listing(self, sample_risk_data):
        """Test scenario listing with pagination."""
        # Create multiple scenarios
        scenario_ids = []
        for i in range(3):
            scenario_request = {
                "name": f"Test Scenario {i}",
                "description": f"Test scenario {i} for pagination testing",
                "base_risks": [sample_risk_data],
                "modifications": {}
            }
            
            response = client.post("/api/v1/monte-carlo/scenarios", json=scenario_request)
            assert response.status_code == 200
            scenario_ids.append(response.json()["scenario_id"])
        
        # List scenarios
        response = client.get("/api/v1/monte-carlo/scenarios")
        assert response.status_code == 200
        
        scenarios_data = response.json()
        assert "scenarios" in scenarios_data
        assert "total_count" in scenarios_data
        assert "limit" in scenarios_data
        assert "offset" in scenarios_data
        
        scenarios = scenarios_data["scenarios"]
        assert len(scenarios) >= 3  # At least the ones we created
        
        # Test pagination
        response = client.get("/api/v1/monte-carlo/scenarios?limit=2&offset=0")
        assert response.status_code == 200
        
        paginated_data = response.json()
        assert len(paginated_data["scenarios"]) <= 2
        assert paginated_data["limit"] == 2
        assert paginated_data["offset"] == 0
    
    def test_export_functionality(self, sample_simulation_request):
        """Test result export in different formats."""
        # Run simulation first
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json=sample_simulation_request
        )
        assert response.status_code == 200
        simulation_id = response.json()["simulation_id"]
        
        # Test JSON export
        export_request = {
            "simulation_id": simulation_id,
            "format": "json",
            "include_charts": False,
            "include_raw_data": True
        }
        
        response = client.post("/api/v1/monte-carlo/export", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Test CSV export
        export_request["format"] = "csv"
        export_request["include_raw_data"] = False
        
        response = client.post("/api/v1/monte-carlo/export", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_validation_endpoint(self, sample_simulation_request):
        """Test parameter validation endpoint."""
        response = client.post(
            "/api/v1/monte-carlo/validate",
            json=sample_simulation_request
        )
        
        assert response.status_code == 200
        validation_data = response.json()
        
        assert "is_valid" in validation_data
        assert "errors" in validation_data
        assert "warnings" in validation_data
        assert "recommendations" in validation_data
        assert "estimated_execution_time" in validation_data
        assert "risk_count" in validation_data
        assert "iteration_count" in validation_data
        
        assert validation_data["is_valid"] is True
        assert validation_data["risk_count"] == 1
        assert validation_data["iteration_count"] == 10000
    
    def test_validation_with_invalid_parameters(self):
        """Test validation endpoint with invalid parameters."""
        invalid_request = {
            "risks": [{
                "id": "invalid-risk",
                "name": "Invalid Risk",
                "category": "invalid_category",
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {"mean": "invalid", "std": -1},  # Invalid parameters
                "baseline_impact": 1000
            }],
            "iterations": 5000  # Below minimum
        }
        
        response = client.post("/api/v1/monte-carlo/validate", json=invalid_request)
        assert response.status_code == 200
        
        validation_data = response.json()
        assert validation_data["is_valid"] is False
        assert len(validation_data["errors"]) > 0
    
    def test_default_configuration_endpoint(self):
        """Test default configuration retrieval."""
        response = client.get("/api/v1/monte-carlo/config/defaults")
        assert response.status_code == 200
        
        config_data = response.json()
        assert "default_iterations" in config_data
        assert "convergence_threshold" in config_data
        assert "max_execution_time" in config_data
        assert "supported_distributions" in config_data
        assert "supported_risk_categories" in config_data
        assert "supported_impact_types" in config_data
        assert "performance_limits" in config_data
        
        # Validate supported types
        assert DistributionType.NORMAL.value in config_data["supported_distributions"]
        assert RiskCategory.COST.value in config_data["supported_risk_categories"]
        assert ImpactType.COST.value in config_data["supported_impact_types"]
    
    def test_error_handling_with_invalid_simulation_id(self):
        """Test error handling with invalid simulation IDs."""
        # Test invalid format
        response = client.get("/api/v1/monte-carlo/simulations/invalid-id/progress")
        assert response.status_code == 400
        
        # Test non-existent simulation
        response = client.get("/api/v1/monte-carlo/simulations/00000000-0000-0000-0000-000000000000/progress")
        assert response.status_code == 404
        
        # Test results retrieval with invalid ID
        response = client.get("/api/v1/monte-carlo/simulations/invalid-id/results")
        assert response.status_code == 400
    
    def test_performance_with_large_simulation(self):
        """Test performance with larger simulation parameters."""
        # Create a larger simulation request
        large_risks = []
        for i in range(20):  # 20 risks
            risk = {
                "id": f"large-risk-{i:03d}",
                "name": f"Large Risk {i}",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {
                    "mean": 1000.0 * (i + 1),
                    "std": 200.0
                },
                "baseline_impact": 1000.0 * (i + 1),
                "correlation_dependencies": [],
                "mitigation_strategies": []
            }
            large_risks.append(risk)
        
        large_request = {
            "risks": large_risks,
            "iterations": 50000,  # Larger iteration count
            "random_seed": 42
        }
        
        # Validate first to check performance warnings
        response = client.post("/api/v1/monte-carlo/validate", json=large_request)
        assert response.status_code == 200
        
        validation_data = response.json()
        assert validation_data["is_valid"] is True
        
        # Check for performance warnings
        if validation_data.get("warnings"):
            assert any("performance" in warning.lower() for warning in validation_data["warnings"])
        
        # Run the simulation and measure time
        start_time = time.time()
        response = client.post("/api/v1/monte-carlo/simulations/run", json=large_request)
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time = end_time - start_time
        
        # Validate that execution completed within reasonable time
        assert execution_time < 60  # Should complete within 60 seconds
        
        data = response.json()
        assert data["status"] == "completed"
        assert "performance_info" in data
        
        perf_info = data["performance_info"]
        assert perf_info["performance_tier"] in ["medium", "high"]
    
    def test_concurrent_simulations(self, sample_simulation_request):
        """Test handling of concurrent simulation requests."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def run_simulation():
            try:
                response = client.post(
                    "/api/v1/monte-carlo/simulations/run",
                    json=sample_simulation_request
                )
                results_queue.put(("success", response.status_code, response.json()))
            except Exception as e:
                results_queue.put(("error", str(e), None))
        
        # Start multiple concurrent simulations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_simulation)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Validate that all simulations completed successfully
        assert len(results) == 3
        for result_type, status_or_error, data in results:
            assert result_type == "success"
            assert status_or_error == 200
            assert data["status"] == "completed"
    
    def test_api_error_response_format(self):
        """Test that API error responses follow consistent format."""
        # Trigger a validation error
        response = client.post(
            "/api/v1/monte-carlo/simulations/run",
            json={"risks": [], "iterations": 10000}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Validate error response structure
        assert "detail" in error_data
        detail = error_data["detail"]
        
        if isinstance(detail, dict):
            assert "error_type" in detail
            assert "message" in detail
            assert "timestamp" in detail
            assert "recoverable" in detail
    
    def test_graceful_degradation_simulation(self):
        """Test graceful degradation when external systems fail."""
        # This test would require mocking external system failures
        # For now, we'll test the basic structure
        
        with patch('config.database.supabase', None):
            # Run simulation without database
            sample_request = {
                "risks": [{
                    "id": "test-risk",
                    "name": "Test Risk",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 1000, "std": 200},
                    "baseline_impact": 1000
                }],
                "iterations": 10000
            }
            
            response = client.post(
                "/api/v1/monte-carlo/simulations/run",
                json=sample_request
            )
            
            # Should still work but with degraded storage
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            
            # Should indicate degraded storage
            if "storage_status" in data:
                assert data["storage_status"] in ["degraded", "failed"]
            
            if "degradation" in data:
                assert "status" in data["degradation"]
                assert data["degradation"]["status"] in ["degraded", "failed"]

class TestMonteCarloAPIPerformance:
    """Performance-focused tests for Monte Carlo API."""
    
    def test_response_time_benchmarks(self):
        """Test API response time benchmarks."""
        # Small simulation benchmark
        small_request = {
            "risks": [{
                "id": "perf-test-risk",
                "name": "Performance Test Risk",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {"mean": 1000, "std": 200},
                "baseline_impact": 1000
            }],
            "iterations": 10000
        }
        
        start_time = time.time()
        response = client.post("/api/v1/monte-carlo/simulations/run", json=small_request)
        end_time = time.time()
        
        assert response.status_code == 200
        execution_time = end_time - start_time
        
        # Should complete within reasonable time for small simulation
        assert execution_time < 10  # 10 seconds for small simulation
        
        data = response.json()
        assert data["status"] == "completed"
        
        # API execution time should be close to reported simulation time
        reported_time = data["execution_time"]
        assert abs(execution_time - reported_time) < 2  # Within 2 seconds difference
    
    def test_memory_usage_monitoring(self):
        """Test memory usage with different simulation sizes."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run medium-sized simulation
        medium_request = {
            "risks": [
                {
                    "id": f"memory-test-risk-{i}",
                    "name": f"Memory Test Risk {i}",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 1000 * i, "std": 200},
                    "baseline_impact": 1000 * i
                }
                for i in range(1, 11)  # 10 risks
            ],
            "iterations": 25000
        }
        
        response = client.post("/api/v1/monte-carlo/simulations/run", json=medium_request)
        assert response.status_code == 200
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB for this test)
        assert memory_increase < 500
        
        # Validate that performance info includes memory estimation
        data = response.json()
        if "performance_info" in data:
            perf_info = data["performance_info"]
            if "estimated_memory_mb" in perf_info:
                estimated_memory = perf_info["estimated_memory_mb"]
                # Actual usage should be in reasonable range of estimate
                assert abs(memory_increase - estimated_memory) < estimated_memory * 0.5

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])