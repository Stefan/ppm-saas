#!/usr/bin/env python3
"""
Vercel-compatible FastAPI server for ORKA-PPM API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Create FastAPI application
app = FastAPI(
    title="ORKA-PPM API",
    description="Portfolio Project Management API",
    version="1.0.0"
)

# Add CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://orka-ppm.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Basic endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ORKA-PPM API Server",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "production"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Mock dashboard data
@app.get("/optimized/dashboard/quick-stats")
async def get_quick_stats():
    """Mock dashboard quick stats"""
    return {
        "quick_stats": {
            "total_projects": 12,
            "active_projects": 8,
            "health_distribution": {
                "green": 6,
                "yellow": 4,
                "red": 2
            },
            "critical_alerts": 2,
            "at_risk_projects": 4
        },
        "kpis": {
            "project_success_rate": 85,
            "budget_performance": 92,
            "timeline_performance": 78,
            "average_health_score": 2.1,
            "resource_efficiency": 88,
            "active_projects_ratio": 67
        }
    }

@app.get("/optimized/dashboard/projects-summary")
async def get_projects_summary(limit: int = 5):
    """Mock dashboard projects summary"""
    projects = [
        {
            "id": "1",
            "name": "Office Complex Phase 1",
            "status": "active",
            "health": "green",
            "budget": 150000,
            "actual": 145000,
            "variance": -5000,
            "variance_percentage": -3.3,
            "created_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": "2", 
            "name": "Residential Tower A",
            "status": "active",
            "health": "yellow",
            "budget": 200000,
            "actual": 210000,
            "variance": 10000,
            "variance_percentage": 5.0,
            "created_at": "2024-01-20T10:00:00Z"
        },
        {
            "id": "3",
            "name": "Shopping Center Renovation", 
            "status": "active",
            "health": "red",
            "budget": 80000,
            "actual": 95000,
            "variance": 15000,
            "variance_percentage": 18.8,
            "created_at": "2024-02-01T10:00:00Z"
        },
        {
            "id": "4",
            "name": "Parking Garage Construction",
            "status": "active", 
            "health": "green",
            "budget": 120000,
            "actual": 115000,
            "variance": -5000,
            "variance_percentage": -4.2,
            "created_at": "2024-02-10T10:00:00Z"
        },
        {
            "id": "5",
            "name": "Landscape Development",
            "status": "active",
            "health": "yellow", 
            "budget": 60000,
            "actual": 62000,
            "variance": 2000,
            "variance_percentage": 3.3,
            "created_at": "2024-02-15T10:00:00Z"
        }
    ]
    return projects[:limit]

@app.get("/projects")
async def get_projects():
    """Mock projects endpoint"""
    return [
        {
            "id": "1",
            "name": "Office Complex Phase 1",
            "status": "active",
            "health": "green",
            "budget": 150000,
            "created_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": "2", 
            "name": "Residential Tower A",
            "status": "active",
            "health": "yellow",
            "budget": 200000,
            "created_at": "2024-01-20T10:00:00Z"
        },
        {
            "id": "3",
            "name": "Shopping Center Renovation", 
            "status": "active",
            "health": "red",
            "budget": 80000,
            "created_at": "2024-02-01T10:00:00Z"
        }
    ]

@app.get("/projects/{project_id}/scenarios")
async def get_project_scenarios(project_id: str):
    """Mock project scenarios endpoint"""
    return {
        "scenarios": [
            {
                "id": "scenario-1",
                "project_id": project_id,
                "name": "Accelerated Timeline",
                "description": "Complete project 2 weeks earlier by adding resources",
                "base_scenario_id": None,
                "parameter_changes": {
                    "end_date": "2024-06-15",
                    "resource_allocations": {
                        "developers": 8,
                        "designers": 3
                    }
                },
                "timeline_impact": {
                    "original_duration": 120,
                    "new_duration": 106,
                    "duration_change": -14,
                    "critical_path_affected": True,
                    "affected_milestones": ["Phase 1 Complete", "Testing Complete"]
                },
                "cost_impact": {
                    "original_cost": 150000,
                    "new_cost": 165000,
                    "cost_change": 15000,
                    "cost_change_percentage": 10.0,
                    "affected_categories": ["Labor", "Equipment"]
                },
                "resource_impact": {
                    "utilization_changes": {
                        "developers": 25.0,
                        "designers": 15.0
                    },
                    "over_allocated_resources": ["developers"],
                    "under_allocated_resources": [],
                    "new_resource_requirements": ["senior_developer"]
                },
                "created_by": "user-1",
                "created_at": "2024-01-08T10:00:00Z",
                "updated_at": "2024-01-08T10:00:00Z",
                "is_active": True,
                "is_baseline": False
            }
        ]
    }

@app.get("/resources/")
async def get_resources():
    """Mock resources endpoint"""
    return [
        {
            "id": "res-1",
            "name": "Alice Johnson",
            "email": "alice.johnson@company.com",
            "role": "Senior Developer",
            "capacity": 40,
            "availability": 85,
            "hourly_rate": 75,
            "skills": ["Python", "React", "PostgreSQL", "AWS"],
            "location": "New York",
            "current_projects": ["proj-1", "proj-2"],
            "utilization_percentage": 85,
            "available_hours": 6,
            "allocated_hours": 34,
            "capacity_hours": 40,
            "availability_status": "available",
            "can_take_more_work": True,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z"
        },
        {
            "id": "res-2",
            "name": "Bob Smith",
            "email": "bob.smith@company.com",
            "role": "UI/UX Designer",
            "capacity": 40,
            "availability": 95,
            "hourly_rate": 65,
            "skills": ["Figma", "Adobe Creative Suite", "User Research", "Prototyping"],
            "location": "San Francisco",
            "current_projects": ["proj-1"],
            "utilization_percentage": 60,
            "available_hours": 16,
            "allocated_hours": 24,
            "capacity_hours": 40,
            "availability_status": "available",
            "can_take_more_work": True,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z"
        }
    ]

@app.get("/risks/")
async def get_risks():
    """Mock risks endpoint"""
    return [
        {
            "id": "risk-1",
            "project_id": "1",
            "project_name": "Office Complex Phase 1",
            "title": "Technical Complexity Risk",
            "description": "Integration challenges with legacy systems may cause delays",
            "category": "technical",
            "probability": 0.7,
            "impact": 0.8,
            "risk_score": 5.6,
            "status": "mitigating",
            "owner": "Alice Johnson",
            "created_at": "2024-01-05T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z",
            "mitigation_plan": "Conduct thorough system analysis and create integration roadmap",
            "due_date": "2024-02-15T00:00:00Z",
            "tags": ["integration", "legacy", "technical"]
        }
    ]

@app.get("/portfolios/metrics")
async def get_portfolio_metrics():
    """Mock portfolio metrics"""
    return {
        "project_success_rate": 85,
        "budget_performance": 92,
        "timeline_performance": 78,
        "average_health_score": 2.1,
        "resource_efficiency": 88,
        "active_projects_ratio": 67
    }

# Variance endpoints
@app.get("/variance/kpis")
async def get_variance_kpis():
    """Mock variance KPIs"""
    return {
        "total_budget": 1250000,
        "total_actual": 1180000,
        "total_variance": -70000,
        "variance_percentage": -5.6,
        "projects_over_budget": 3,
        "projects_under_budget": 5,
        "projects_on_budget": 4,
        "average_variance_percentage": -2.3,
        "largest_positive_variance": 25000,
        "largest_negative_variance": -45000,
        "variance_trend": "improving",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/variance/alerts")
async def get_variance_alerts():
    """Mock variance alerts"""
    return {
        "alerts": [
            {
                "id": "alert-1",
                "project_id": "proj-1",
                "project_name": "Office Complex Phase 1",
                "alert_type": "budget_overrun",
                "severity": "high",
                "variance_amount": -45000,
                "variance_percentage": -15.2,
                "threshold_exceeded": "budget_variance_10_percent",
                "created_at": "2024-01-08T10:00:00Z",
                "status": "active"
            }
        ],
        "total_alerts": 1,
        "high_severity": 1,
        "medium_severity": 0,
        "low_severity": 0
    }

@app.get("/variance/trends")
async def get_variance_trends():
    """Mock variance trends"""
    return {
        "monthly_trends": [
            {
                "month": "2024-01",
                "total_variance": -25000,
                "variance_percentage": -2.1,
                "projects_count": 8
            },
            {
                "month": "2024-02", 
                "total_variance": -35000,
                "variance_percentage": -3.2,
                "projects_count": 10
            }
        ]
    }

# Financial tracking endpoints
@app.get("/projects/{project_id}/budget-variance")
async def get_project_budget_variance(project_id: str, currency: str = "USD"):
    """Mock project budget variance"""
    return {
        "project_id": project_id,
        "total_planned": 150000,
        "total_actual": 165000,
        "variance_amount": 15000,
        "variance_percentage": 10.0,
        "currency": currency,
        "status": "over_budget"
    }

@app.get("/financial-tracking/budget-alerts")
async def get_financial_alerts(threshold_percentage: float = 80):
    """Mock financial alerts"""
    return {
        "alerts": [
            {
                "project_id": "1",
                "project_name": "Office Complex Phase 1",
                "budget": 150000,
                "actual_cost": 165000,
                "utilization_percentage": 110.0,
                "variance_amount": 15000,
                "alert_level": "critical",
                "message": "Project has exceeded budget by 10%"
            }
        ]
    }

@app.get("/financial-tracking/comprehensive-report")
async def get_comprehensive_financial_report(currency: str = "USD", include_trends: bool = True):
    """Mock comprehensive financial report"""
    return {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "currency": currency,
            "projects_included": 3,
            "includes_trends": include_trends
        },
        "summary": {
            "total_budget": 530000,
            "total_actual": 590000,
            "total_variance": 60000,
            "variance_percentage": 11.3,
            "currency": currency
        }
    }

# CSV Import endpoints
@app.get("/csv-import/variances")
async def get_csv_variances():
    """Mock CSV import variances"""
    return {
        "variances": [
            {
                "id": "var-1",
                "project_id": "proj-1",
                "project_name": "Office Complex Phase 1",
                "budget": 300000,
                "actual": 345000,
                "total_commitment": 300000,
                "total_actual": 345000,
                "variance": -45000,
                "variance_percentage": -15.0,
                "category": "construction",
                "date": "2024-01-08",
                "status": "over"
            }
        ],
        "summary": {
            "total_budget": 300000,
            "total_actual": 345000,
            "total_variance": -45000,
            "variance_percentage": -15.0,
            "projects_over_budget": 1,
            "projects_under_budget": 0,
            "projects_on_budget": 0
        },
        "last_updated": datetime.now().isoformat()
    }

# Vercel handler
handler = app