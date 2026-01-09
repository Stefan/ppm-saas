# Monte Carlo Risk Simulation API Documentation

**Version:** 1.0  
**Base URL:** `/api/v1/monte-carlo`  
**Authentication:** Required (Bearer token)  

## Overview

The Monte Carlo Risk Simulation API provides comprehensive probabilistic risk analysis capabilities for construction and engineering projects. The API enables users to run Monte Carlo simulations, analyze results, compare scenarios, and export findings in multiple formats.

## Authentication

All API endpoints require authentication using a Bearer token:

```http
Authorization: Bearer <your-token>
```

## Core Endpoints

### 1. Run Simulation

Execute a Monte Carlo simulation with specified risks and parameters.

**Endpoint:** `POST /simulations/run`

**Request Body:**
```json
{
  "risks": [
    {
      "id": "RISK_001",
      "name": "Foundation Cost Overrun",
      "category": "cost",
      "impact_type": "cost",
      "distribution_type": "triangular",
      "distribution_parameters": {
        "min": 25000,
        "mode": 75000,
        "max": 150000
      },
      "baseline_impact": 75000,
      "correlation_dependencies": ["RISK_002"],
      "mitigation_strategies": [
        {
          "id": "MIT_001",
          "name": "Soil Survey",
          "description": "Comprehensive geotechnical analysis",
          "cost": 15000,
          "effectiveness": 0.6,
          "implementation_time": 14
        }
      ]
    }
  ],
  "iterations": 10000,
  "correlations": {
    "RISK_001": {
      "RISK_002": 0.6
    }
  },
  "random_seed": 42,
  "baseline_costs": {
    "project_baseline": 1000000
  },
  "schedule_data": {
    "project_baseline_duration": 90,
    "milestones": [],
    "activities": [],
    "resource_constraints": []
  }
}
```

**Response:**
```json
{
  "simulation_id": "bf79e547-e9cf-46f8-8de9-58f836fc9b33",
  "status": "completed",
  "timestamp": "2026-01-09T11:41:23.123456",
  "iteration_count": 10000,
  "execution_time": 2.45,
  "convergence_status": true,
  "storage_status": "success",
  "performance_info": {
    "performance_tier": "normal",
    "estimated_time": 2.5
  },
  "summary": {
    "cost_statistics": {
      "mean": 125000.50,
      "std": 35000.25,
      "min": 25000.00,
      "max": 149999.99
    },
    "schedule_statistics": {
      "mean": 15.5,
      "std": 8.2,
      "min": 2.1,
      "max": 45.8
    }
  }
}
```

### 2. Get Simulation Results

Retrieve detailed results from a completed simulation.

**Endpoint:** `GET /simulations/{simulation_id}/results`

**Query Parameters:**
- `include_raw_data` (boolean, optional): Include raw simulation data in response

**Response:**
```json
{
  "simulation_id": "bf79e547-e9cf-46f8-8de9-58f836fc9b33",
  "timestamp": "2026-01-09T11:41:23.123456",
  "iteration_count": 10000,
  "execution_time": 2.45,
  "convergence_metrics": {
    "converged": true,
    "mean_stability": 0.001,
    "variance_stability": 0.002,
    "iterations_to_convergence": 8500
  },
  "cost_analysis": {
    "percentiles": {
      "10": 85000.00,
      "25": 95000.00,
      "50": 125000.00,
      "75": 155000.00,
      "90": 175000.00,
      "95": 185000.00,
      "99": 195000.00
    },
    "mean": 125000.50,
    "median": 125000.00,
    "std_dev": 35000.25,
    "coefficient_of_variation": 0.28
  },
  "confidence_intervals": {
    "0.8": {"lower": 95000.00, "upper": 155000.00},
    "0.9": {"lower": 90000.00, "upper": 160000.00},
    "0.95": {"lower": 85000.00, "upper": 165000.00}
  },
  "risk_contributions": [
    {
      "risk_id": "RISK_001",
      "risk_name": "Foundation Cost Overrun",
      "contribution_percentage": 65.5,
      "variance_contribution": 0.655
    }
  ]
}
```

### 3. Get Simulation Progress

Monitor the progress of a running simulation.

**Endpoint:** `GET /simulations/{simulation_id}/progress`

**Response:**
```json
{
  "simulation_id": "bf79e547-e9cf-46f8-8de9-58f836fc9b33",
  "status": "running",
  "progress": 75.5,
  "current_iteration": 7550,
  "total_iterations": 10000,
  "elapsed_time": 1.85,
  "estimated_remaining_time": 0.62
}
```

## Scenario Management

### 4. Create Scenario

Create a new risk scenario for analysis.

**Endpoint:** `POST /scenarios`

**Request Body:**
```json
{
  "name": "Mitigation Scenario",
  "description": "With key risk mitigation strategies applied",
  "base_risks": [
    {
      "id": "RISK_001",
      "name": "Foundation Cost Overrun",
      "category": "cost",
      "impact_type": "cost",
      "distribution_type": "triangular",
      "distribution_parameters": {
        "min": 25000,
        "mode": 75000,
        "max": 150000
      },
      "baseline_impact": 75000
    }
  ],
  "modifications": {
    "RISK_001": {
      "parameter_changes": {
        "mode": 50000,
        "max": 100000
      },
      "mitigation_applied": "MIT_001"
    }
  }
}
```

**Response:**
```json
{
  "scenario_id": "scenario_123",
  "name": "Mitigation Scenario",
  "description": "With key risk mitigation strategies applied",
  "risk_count": 1,
  "modification_count": 1,
  "created_at": "2026-01-09T11:45:00.000000"
}
```

### 5. Compare Scenarios

Compare multiple scenarios and their simulation results.

**Endpoint:** `POST /scenarios/compare`

**Request Body:**
```json
{
  "scenario_ids": ["scenario_123", "scenario_456"],
  "comparison_metrics": ["cost", "schedule", "risk_contribution"]
}
```

**Response:**
```json
{
  "comparison_timestamp": "2026-01-09T11:50:00.000000",
  "scenarios_compared": 2,
  "comparison_metrics": ["cost", "schedule", "risk_contribution"],
  "pairwise_comparisons": [
    {
      "scenario_a_id": "scenario_123",
      "scenario_a_name": "Baseline Scenario",
      "scenario_b_id": "scenario_456",
      "scenario_b_name": "Mitigation Scenario",
      "cost_difference": {
        "mean_difference": -25000.00,
        "percentage_change": -16.7
      },
      "schedule_difference": {
        "mean_difference": -2.5,
        "percentage_change": -8.3
      },
      "statistical_significance": {
        "p_value": 0.001,
        "significant": true
      },
      "effect_size": {
        "cohens_d": 0.85,
        "interpretation": "large"
      }
    }
  ]
}
```

## Export and Validation

### 6. Export Results

Export simulation results in various formats.

**Endpoint:** `POST /export`

**Request Body:**
```json
{
  "simulation_id": "bf79e547-e9cf-46f8-8de9-58f836fc9b33",
  "format": "json",
  "include_charts": true,
  "include_raw_data": false
}
```

**Response:** File download with appropriate content-type header.

### 7. Validate Parameters

Validate simulation parameters before execution.

**Endpoint:** `POST /validate`

**Request Body:** Same as simulation request

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "High correlation coefficient detected between RISK_001 and RISK_002"
  ],
  "recommendations": [
    "Consider reducing correlation to avoid overestimation"
  ],
  "estimated_execution_time": 2.5,
  "risk_count": 4,
  "iteration_count": 10000
}
```

### 8. Get Default Configuration

Retrieve default simulation configuration parameters.

**Endpoint:** `GET /config/defaults`

**Response:**
```json
{
  "default_iterations": 10000,
  "convergence_threshold": 0.01,
  "max_execution_time": 300,
  "parameter_change_sensitivity": 0.05,
  "supported_distributions": [
    "normal", "triangular", "uniform", "beta", "lognormal"
  ],
  "supported_risk_categories": [
    "technical", "schedule", "cost", "resource", "external", "quality", "regulatory"
  ],
  "supported_impact_types": [
    "cost", "schedule", "both"
  ],
  "performance_limits": {
    "max_risks": 100,
    "max_iterations": 1000000,
    "max_execution_time_seconds": 300
  }
}
```

## Data Models

### Risk Object
```json
{
  "id": "string",
  "name": "string",
  "category": "cost|schedule|technical|resource|external|quality|regulatory",
  "impact_type": "cost|schedule|both",
  "distribution_type": "normal|triangular|uniform|beta|lognormal",
  "distribution_parameters": {
    "normal": {"mean": "number", "std": "number"},
    "triangular": {"min": "number", "mode": "number", "max": "number"},
    "uniform": {"min": "number", "max": "number"},
    "beta": {"alpha": "number", "beta": "number", "scale": "number"},
    "lognormal": {"mu": "number", "sigma": "number"}
  },
  "baseline_impact": "number",
  "correlation_dependencies": ["string"],
  "mitigation_strategies": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "cost": "number",
      "effectiveness": "number (0.0-1.0)",
      "implementation_time": "number (days)"
    }
  ]
}
```

### Correlation Matrix
```json
{
  "RISK_ID_1": {
    "RISK_ID_2": "number (-1.0 to 1.0)"
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid risk parameters provided",
    "details": {
      "field": "distribution_parameters.std",
      "issue": "Standard deviation must be positive",
      "provided_value": -500
    },
    "timestamp": "2026-01-09T11:55:00.000000",
    "request_id": "req_123456"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `SIMULATION_NOT_FOUND` | 404 | Simulation ID not found |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SIMULATION_FAILED` | 500 | Simulation execution failed |
| `EXTERNAL_SYSTEM_ERROR` | 503 | External dependency unavailable |

## Rate Limits

- **Simulation Execution**: 10 requests per minute per user
- **Results Retrieval**: 100 requests per minute per user
- **Scenario Management**: 50 requests per minute per user

## Best Practices

### 1. Risk Definition
- Use meaningful risk IDs and names
- Ensure distribution parameters are realistic
- Validate correlation coefficients are between -1 and 1
- Include mitigation strategies for comprehensive analysis

### 2. Performance Optimization
- Use minimum required iterations (10,000 is usually sufficient)
- Limit risk count to under 50 for optimal performance
- Use random seeds for reproducible results during testing
- Cache simulation results for repeated analysis

### 3. Error Handling
- Always validate parameters before running simulations
- Handle async operations with proper timeout handling
- Implement retry logic for transient failures
- Monitor simulation progress for long-running operations

### 4. Security
- Never expose sensitive project data in logs
- Use HTTPS for all API communications
- Implement proper authentication and authorization
- Validate all user inputs thoroughly

## SDK Examples

### Python SDK Example
```python
import requests
import json

class MonteCarloAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def run_simulation(self, risks, iterations=10000):
        payload = {
            "risks": risks,
            "iterations": iterations
        }
        response = requests.post(
            f"{self.base_url}/simulations/run",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_results(self, simulation_id):
        response = requests.get(
            f"{self.base_url}/simulations/{simulation_id}/results",
            headers=self.headers
        )
        return response.json()

# Usage
api = MonteCarloAPI("https://api.example.com/api/v1/monte-carlo", "your-token")
result = api.run_simulation(risks_data)
```

### JavaScript SDK Example
```javascript
class MonteCarloAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async runSimulation(risks, iterations = 10000) {
        const response = await fetch(`${this.baseUrl}/simulations/run`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ risks, iterations })
        });
        return response.json();
    }
    
    async getResults(simulationId) {
        const response = await fetch(
            `${this.baseUrl}/simulations/${simulationId}/results`,
            { headers: this.headers }
        );
        return response.json();
    }
}

// Usage
const api = new MonteCarloAPI('https://api.example.com/api/v1/monte-carlo', 'your-token');
const result = await api.runSimulation(risksData);
```

## Support

For API support and questions:
- **Documentation**: [Internal Wiki Link]
- **Issue Tracking**: [Internal Issue Tracker]
- **Team Contact**: monte-carlo-dev@company.com

---

**Last Updated:** January 9, 2026  
**API Version:** 1.0  
**Documentation Version:** 1.0