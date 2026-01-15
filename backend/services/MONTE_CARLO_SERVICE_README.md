# Monte Carlo Analysis Service

## Overview

The Monte Carlo Analysis Service provides predictive simulations for budget variance, schedule variance, and resource risk analysis specifically for Project Monthly Reports (PMR) in the Enhanced PMR feature.

## Features

### 1. Budget Variance Analysis
- Analyzes cost-related risks and uncertainties
- Calculates probability of staying within budget
- Provides percentile analysis and confidence intervals
- Identifies risk contributions to budget variance

### 2. Schedule Variance Analysis
- Analyzes schedule-related risks and delays
- Calculates probability of on-time completion
- Includes critical path analysis
- Provides timeline variance predictions

### 3. Resource Risk Analysis
- Analyzes resource allocation and utilization
- Identifies resource conflicts and over-allocation risks
- Provides recommendations for resource management
- Calculates resource impact on project outcomes

## Usage

```python
from services.monte_carlo_service import MonteCarloAnalysisService
from supabase import create_client
from uuid import UUID
from datetime import datetime

# Initialize service
supabase = create_client(url, key)
service = MonteCarloAnalysisService(supabase)

# Run comprehensive analysis
project_id = UUID("...")
report_month = datetime(2024, 1, 1)

results = await service.analyze_project_for_pmr(
    project_id=project_id,
    report_month=report_month,
    iterations=10000,
    confidence_level=0.95
)

# Access results
print(f"Budget Risk: {results['budget_analysis']['variance_percentage']:.1f}%")
print(f"Schedule Risk: {results['schedule_analysis']['variance_percentage']:.1f}%")
print(f"Overall Risk Level: {results['summary']['overall_risk_level']}")
```

## Configuration

### Iterations
- Default: 10,000 iterations
- Minimum: 10,000 (enforced by Monte Carlo engine)
- Recommended: 50,000+ for higher accuracy

### Confidence Level
- Default: 0.95 (95% confidence)
- Range: 0.0 to 1.0

## Integration

The service integrates with:
- **Monte Carlo Engine**: Core simulation engine from `backend/monte_carlo/`
- **Supabase**: Database access for project data
- **Project Data Models**: Risks, milestones, resources, financials

## Output Structure

```json
{
  "project_id": "uuid",
  "report_month": "2024-01-01",
  "analysis_timestamp": "2024-01-15T10:30:00",
  "iterations": 10000,
  "confidence_level": 0.95,
  "budget_analysis": {
    "baseline_budget": 1000000.0,
    "expected_final_cost": 1050000.0,
    "variance_percentage": 5.0,
    "probability_within_budget": 0.65,
    "percentiles": {...},
    "risk_contributions": [...]
  },
  "schedule_analysis": {
    "baseline_duration": 365.0,
    "expected_final_duration": 380.0,
    "variance_percentage": 4.1,
    "probability_on_time": 0.70,
    "critical_path_analysis": {...}
  },
  "resource_analysis": {
    "total_resources": 5,
    "conflict_probability": 0.25,
    "recommendations": [...]
  },
  "summary": {
    "overall_risk_level": "medium",
    "budget_risk_level": "medium",
    "schedule_risk_level": "low",
    "resource_risk_level": "low",
    "key_insights": [...],
    "probability_of_success": 0.65
  }
}
```

## Testing

Run tests with:
```bash
cd backend
python -m pytest test_monte_carlo_service.py -v
```

All 16 tests should pass, covering:
- Service initialization
- Risk creation from project data
- Statistical calculations
- Budget/schedule/resource analysis
- Recommendation generation
- Edge cases and empty data handling

## Dependencies

- `numpy`: Statistical calculations
- `monte_carlo.engine`: Core Monte Carlo simulation
- `monte_carlo.models`: Risk and simulation data models
- `supabase`: Database client

## Notes

- The service automatically creates default risks if no project risks are found
- All simulations use a minimum of 10,000 iterations for statistical validity
- Risk distributions can be triangular, normal, uniform, beta, or lognormal
- The service handles missing or incomplete data gracefully
