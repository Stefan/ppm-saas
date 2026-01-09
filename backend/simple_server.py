#!/usr/bin/env python3
"""
Simplified FastAPI server for development
Updated: 2026-01-09 - Added comprehensive feedback and admin endpoints
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://orka-ppm.vercel.app",           # Production frontend
        "https://ppm-saas.vercel.app",           # Alternative URL
        "https://ppm-saas-git-main.vercel.app",  # Git branch deployments
        "https://ppm-saas-*.vercel.app",         # Preview deployments
        "https://*.vercel.app",                  # All Vercel deployments
        "http://localhost:3000",                 # Local development
        "http://127.0.0.1:3000",
        "https://localhost:3000"
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
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/info")
async def debug_info():
    """Debug endpoint to check server status"""
    return {
        "status": "running",
        "server": "simple_server.py",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/",
            "/health", 
            "/projects",
            "/projects/{id}/scenarios",
            "/debug/info"
        ]
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
            },
            {
                "id": "scenario-2",
                "project_id": project_id,
                "name": "Budget Optimization",
                "description": "Reduce costs by 15% through resource optimization",
                "base_scenario_id": None,
                "parameter_changes": {
                    "budget": 127500,
                    "resource_allocations": {
                        "developers": 5,
                        "designers": 2
                    }
                },
                "timeline_impact": {
                    "original_duration": 120,
                    "new_duration": 135,
                    "duration_change": 15,
                    "critical_path_affected": True,
                    "affected_milestones": ["Phase 2 Complete"]
                },
                "cost_impact": {
                    "original_cost": 150000,
                    "new_cost": 127500,
                    "cost_change": -22500,
                    "cost_change_percentage": -15.0,
                    "affected_categories": ["Labor"]
                },
                "resource_impact": {
                    "utilization_changes": {
                        "developers": -20.0,
                        "designers": -25.0
                    },
                    "over_allocated_resources": [],
                    "under_allocated_resources": ["developers", "designers"],
                    "new_resource_requirements": []
                },
                "created_by": "user-1",
                "created_at": "2024-01-07T14:30:00Z",
                "updated_at": "2024-01-07T14:30:00Z",
                "is_active": True,
                "is_baseline": False
            },
            {
                "id": "scenario-3",
                "project_id": project_id,
                "name": "Risk Mitigation",
                "description": "Add buffer time and resources for high-risk activities",
                "base_scenario_id": None,
                "parameter_changes": {
                    "end_date": "2024-07-15",
                    "budget": 175000,
                    "risk_adjustments": {
                        "technical_complexity": {"probability": 0.3, "impact": 0.4},
                        "resource_availability": {"probability": 0.2, "impact": 0.3}
                    }
                },
                "timeline_impact": {
                    "original_duration": 120,
                    "new_duration": 140,
                    "duration_change": 20,
                    "critical_path_affected": False,
                    "affected_milestones": ["Final Delivery"]
                },
                "cost_impact": {
                    "original_cost": 150000,
                    "new_cost": 175000,
                    "cost_change": 25000,
                    "cost_change_percentage": 16.7,
                    "affected_categories": ["Labor", "Contingency"]
                },
                "resource_impact": {
                    "utilization_changes": {
                        "developers": 10.0,
                        "qa_engineers": 50.0
                    },
                    "over_allocated_resources": [],
                    "under_allocated_resources": [],
                    "new_resource_requirements": ["risk_manager", "qa_engineer"]
                },
                "created_by": "user-1",
                "created_at": "2024-01-06T09:15:00Z",
                "updated_at": "2024-01-06T09:15:00Z",
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
        },
        {
            "id": "res-3",
            "name": "Carol Davis",
            "email": "carol.davis@company.com",
            "role": "Project Manager",
            "capacity": 40,
            "availability": 100,
            "hourly_rate": 80,
            "skills": ["Agile", "Scrum", "Risk Management", "Stakeholder Communication"],
            "location": "Chicago",
            "current_projects": ["proj-2", "proj-3"],
            "utilization_percentage": 110,
            "available_hours": -4,
            "allocated_hours": 44,
            "capacity_hours": 40,
            "availability_status": "overallocated",
            "can_take_more_work": False,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z"
        },
        {
            "id": "res-4",
            "name": "David Wilson",
            "email": "david.wilson@company.com",
            "role": "DevOps Engineer",
            "capacity": 40,
            "availability": 90,
            "hourly_rate": 85,
            "skills": ["Docker", "Kubernetes", "CI/CD", "Monitoring"],
            "location": "Austin",
            "current_projects": ["proj-1", "proj-3"],
            "utilization_percentage": 75,
            "available_hours": 10,
            "allocated_hours": 30,
            "capacity_hours": 40,
            "availability_status": "available",
            "can_take_more_work": True,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z"
        },
        {
            "id": "res-5",
            "name": "Eva Martinez",
            "email": "eva.martinez@company.com",
            "role": "QA Engineer",
            "capacity": 40,
            "availability": 80,
            "hourly_rate": 60,
            "skills": ["Test Automation", "Selenium", "API Testing", "Performance Testing"],
            "location": "Remote",
            "current_projects": ["proj-2"],
            "utilization_percentage": 50,
            "available_hours": 20,
            "allocated_hours": 20,
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
        },
        {
            "id": "risk-2",
            "project_id": "2",
            "project_name": "Residential Tower A",
            "title": "Budget Overrun Risk",
            "description": "Material costs increasing faster than anticipated",
            "category": "financial",
            "probability": 0.6,
            "impact": 0.9,
            "risk_score": 5.4,
            "status": "analyzing",
            "owner": "Bob Smith",
            "created_at": "2024-01-03T10:00:00Z",
            "updated_at": "2024-01-07T10:00:00Z",
            "mitigation_plan": "Lock in material prices with suppliers, explore alternative materials",
            "due_date": "2024-01-20T00:00:00Z",
            "tags": ["budget", "materials", "cost"]
        },
        {
            "id": "risk-3",
            "project_id": "1",
            "project_name": "Office Complex Phase 1",
            "title": "Resource Availability Risk",
            "description": "Key team members may not be available during critical phases",
            "category": "resource",
            "probability": 0.4,
            "impact": 0.7,
            "risk_score": 2.8,
            "status": "identified",
            "owner": "Carol Davis",
            "created_at": "2024-01-02T10:00:00Z",
            "updated_at": "2024-01-06T10:00:00Z",
            "mitigation_plan": "Cross-train team members and identify backup resources",
            "due_date": "2024-02-01T00:00:00Z",
            "tags": ["resources", "team", "availability"]
        },
        {
            "id": "risk-4",
            "project_id": "3",
            "project_name": "Shopping Center Renovation",
            "title": "Schedule Delay Risk",
            "description": "Weather conditions may impact construction timeline",
            "category": "schedule",
            "probability": 0.5,
            "impact": 0.6,
            "risk_score": 3.0,
            "status": "mitigating",
            "owner": "David Wilson",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z",
            "mitigation_plan": "Build weather contingency into schedule, prepare indoor work alternatives",
            "due_date": "2024-03-01T00:00:00Z",
            "tags": ["schedule", "weather", "construction"]
        },
        {
            "id": "risk-5",
            "project_id": "2",
            "project_name": "Residential Tower A",
            "title": "Regulatory Compliance Risk",
            "description": "New building codes may require design changes",
            "category": "external",
            "probability": 0.3,
            "impact": 0.8,
            "risk_score": 2.4,
            "status": "closed",
            "owner": "Eva Martinez",
            "created_at": "2023-12-15T10:00:00Z",
            "updated_at": "2024-01-05T10:00:00Z",
            "mitigation_plan": "Regular consultation with regulatory authorities, design flexibility",
            "due_date": "2024-01-15T00:00:00Z",
            "tags": ["regulatory", "compliance", "design"]
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
            },
            {
                "id": "alert-2", 
                "project_id": "proj-3",
                "project_name": "Shopping Center Renovation",
                "alert_type": "budget_overrun",
                "severity": "medium",
                "variance_amount": -12000,
                "variance_percentage": -8.5,
                "threshold_exceeded": "budget_variance_5_percent",
                "created_at": "2024-01-08T09:30:00Z",
                "status": "active"
            }
        ],
        "total_alerts": 2,
        "high_severity": 1,
        "medium_severity": 1,
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
            },
            {
                "month": "2024-03",
                "total_variance": -15000,
                "variance_percentage": -1.8,
                "projects_count": 12
            }
        ],
        "project_trends": [
            {
                "project_id": "proj-1",
                "project_name": "Office Complex Phase 1",
                "variance_history": [
                    {"date": "2024-01-01", "variance": -5000},
                    {"date": "2024-02-01", "variance": -15000},
                    {"date": "2024-03-01", "variance": -25000}
                ]
            }
        ]
    }

# Monte Carlo Simulation endpoints
@app.post("/monte-carlo/simulations")
async def create_monte_carlo_simulation(simulation_data: dict):
    """Create a new Monte Carlo simulation"""
    try:
        simulation_id = f"sim_{len(simulation_data.get('name', 'simulation'))}"
        
        return {
            "id": simulation_id,
            "name": simulation_data.get("name", "Monte Carlo Simulation"),
            "project_id": simulation_data.get("project_id"),
            "config": simulation_data.get("config", {}),
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to create simulation: {str(e)}"}

@app.post("/monte-carlo/simulations/run")
async def run_monte_carlo_simulation_direct(simulation_data: dict):
    """Run a Monte Carlo simulation directly (without creating first)"""
    try:
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "simulation_id": simulation_id,
            "status": "running",
            "progress": 0,
            "estimated_completion": datetime.now().isoformat(),
            "config": simulation_data.get("config", {}),
            "results": {
                "iterations_completed": 0,
                "total_iterations": simulation_data.get("config", {}).get("iterations", 10000)
            },
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to run simulation: {str(e)}"}

@app.post("/monte-carlo/simulations/{simulation_id}/run")
async def run_monte_carlo_simulation(simulation_id: str, config: dict = None):
    """Run a Monte Carlo simulation"""
    try:
        return {
            "simulation_id": simulation_id,
            "status": "running",
            "progress": 0,
            "estimated_completion": datetime.now().isoformat(),
            "results": {
                "iterations_completed": 0,
                "total_iterations": config.get("iterations", 10000) if config else 10000
            }
        }
    except Exception as e:
        return {"error": f"Failed to run simulation: {str(e)}"}

@app.get("/monte-carlo/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Get Monte Carlo simulation status"""
    try:
        return {
            "simulation_id": simulation_id,
            "status": "completed",
            "progress": 100,
            "results": {
                "iterations_completed": 10000,
                "total_iterations": 10000,
                "completion_time": datetime.now().isoformat(),
                "summary": {
                    "mean_cost": 125000,
                    "std_cost": 15000,
                    "min_cost": 95000,
                    "max_cost": 180000,
                    "percentiles": {
                        "p10": 105000,
                        "p25": 115000,
                        "p50": 125000,
                        "p75": 135000,
                        "p90": 145000
                    }
                }
            }
        }
    except Exception as e:
        return {"error": f"Failed to get simulation status: {str(e)}"}

@app.post("/monte-carlo/simulations/{simulation_id}/visualizations/generate")
async def generate_monte_carlo_visualizations(simulation_id: str, config: dict = None):
    """Generate visualizations for Monte Carlo simulation results"""
    try:
        return {
            "simulation_id": simulation_id,
            "visualizations": {
                "histogram": {
                    "type": "histogram",
                    "data": [
                        {"bin": "95k-105k", "count": 150, "percentage": 1.5},
                        {"bin": "105k-115k", "count": 850, "percentage": 8.5},
                        {"bin": "115k-125k", "count": 3200, "percentage": 32.0},
                        {"bin": "125k-135k", "count": 3600, "percentage": 36.0},
                        {"bin": "135k-145k", "count": 1800, "percentage": 18.0},
                        {"bin": "145k-155k", "count": 350, "percentage": 3.5},
                        {"bin": "155k+", "count": 50, "percentage": 0.5}
                    ],
                    "title": "Cost Distribution",
                    "x_axis": "Cost Range",
                    "y_axis": "Frequency"
                },
                "cumulative": {
                    "type": "cumulative",
                    "data": [
                        {"value": 95000, "probability": 0.01},
                        {"value": 105000, "probability": 0.10},
                        {"value": 115000, "probability": 0.25},
                        {"value": 125000, "probability": 0.50},
                        {"value": 135000, "probability": 0.75},
                        {"value": 145000, "probability": 0.90},
                        {"value": 180000, "probability": 0.99}
                    ],
                    "title": "Cumulative Probability",
                    "x_axis": "Cost",
                    "y_axis": "Probability"
                },
                "sensitivity": {
                    "type": "tornado",
                    "data": [
                        {"factor": "Labor Costs", "impact": 0.45, "low": -15000, "high": 18000},
                        {"factor": "Material Costs", "impact": 0.35, "low": -12000, "high": 14000},
                        {"factor": "Schedule Risk", "impact": 0.25, "low": -8000, "high": 12000},
                        {"factor": "Quality Risk", "impact": 0.15, "low": -5000, "high": 8000}
                    ],
                    "title": "Sensitivity Analysis",
                    "x_axis": "Impact Range",
                    "y_axis": "Risk Factors"
                }
            },
            "generated_at": datetime.now().isoformat(),
            "config": config or {}
        }
    except Exception as e:
        return {"error": f"Failed to generate visualizations: {str(e)}"}

@app.get("/monte-carlo/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: str):
    """Get detailed Monte Carlo simulation results"""
    try:
        return {
            "simulation_id": simulation_id,
            "status": "completed",
            "results": {
                "summary": {
                    "total_iterations": 10000,
                    "mean": 125000,
                    "median": 124500,
                    "std_dev": 15000,
                    "variance": 225000000,
                    "skewness": 0.12,
                    "kurtosis": 2.95,
                    "min_value": 95000,
                    "max_value": 180000
                },
                "percentiles": {
                    "p1": 98000,
                    "p5": 102000,
                    "p10": 105000,
                    "p25": 115000,
                    "p50": 125000,
                    "p75": 135000,
                    "p90": 145000,
                    "p95": 152000,
                    "p99": 165000
                },
                "confidence_intervals": {
                    "90%": {"lower": 105000, "upper": 145000},
                    "95%": {"lower": 102000, "upper": 152000},
                    "99%": {"lower": 98000, "upper": 165000}
                },
                "risk_metrics": {
                    "probability_over_budget": 0.25,
                    "expected_overrun": 8500,
                    "value_at_risk_95": 152000,
                    "conditional_value_at_risk": 158000
                }
            },
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to get simulation results: {str(e)}"}

# What-If Scenario endpoints
@app.post("/simulations/what-if")
async def create_scenario(scenario_data: dict):
    """Create a new what-if scenario analysis"""
    try:
        # Mock scenario creation
        scenario_id = f"scenario-{len(scenario_data.get('config', {}).get('name', 'default'))}"
        
        return {
            "id": scenario_id,
            "project_id": scenario_data.get("project_id"),
            "name": scenario_data.get("config", {}).get("name", "New Scenario"),
            "description": scenario_data.get("config", {}).get("description", ""),
            "parameter_changes": scenario_data.get("config", {}).get("parameter_changes", {}),
            "timeline_impact": {
                "original_duration": 120,
                "new_duration": 110,
                "duration_change": -10,
                "critical_path_affected": True,
                "affected_milestones": ["Phase 1 Complete"]
            },
            "cost_impact": {
                "original_cost": 150000,
                "new_cost": 165000,
                "cost_change": 15000,
                "cost_change_percentage": 10.0,
                "affected_categories": ["Labor", "Equipment"]
            },
            "resource_impact": {
                "utilization_changes": {"developers": 0.2, "designers": 0.1},
                "over_allocated_resources": [],
                "under_allocated_resources": ["qa_engineers"],
                "new_resource_requirements": ["senior_developer"]
            },
            "created_by": "mock-user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True,
            "is_baseline": False
        }
    except Exception as e:
        return {"error": f"Failed to create scenario: {str(e)}"}

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
        "categories": [
            {
                "category": "Development",
                "planned": 80000,
                "actual": 90000,
                "variance": 10000,
                "variance_percentage": 12.5
            },
            {
                "category": "Infrastructure", 
                "planned": 40000,
                "actual": 45000,
                "variance": 5000,
                "variance_percentage": 12.5
            },
            {
                "category": "Marketing",
                "planned": 30000,
                "actual": 30000,
                "variance": 0,
                "variance_percentage": 0.0
            }
        ],
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
            },
            {
                "project_id": "2",
                "project_name": "Residential Tower A", 
                "budget": 200000,
                "actual_cost": 180000,
                "utilization_percentage": 90.0,
                "variance_amount": -20000,
                "alert_level": "warning",
                "message": "Project is approaching budget threshold"
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
        },
        "project_analysis": [
            {
                "project_id": "1",
                "project_name": "Office Complex Phase 1",
                "budget": 150000,
                "actual_cost": 165000,
                "variance_amount": 15000,
                "variance_percentage": 10.0,
                "utilization_percentage": 110.0,
                "status": "over_budget",
                "health": "yellow"
            },
            {
                "project_id": "2",
                "project_name": "Residential Tower A",
                "budget": 200000,
                "actual_cost": 220000,
                "variance_amount": 20000,
                "variance_percentage": 10.0,
                "utilization_percentage": 110.0,
                "status": "over_budget", 
                "health": "red"
            },
            {
                "project_id": "3",
                "project_name": "Shopping Center Renovation",
                "budget": 180000,
                "actual_cost": 205000,
                "variance_amount": 25000,
                "variance_percentage": 13.9,
                "utilization_percentage": 113.9,
                "status": "over_budget",
                "health": "red"
            }
        ],
        "category_spending": [
            {
                "category": "Development",
                "total_spending": 315000,
                "transaction_count": 45,
                "average_per_transaction": 7000
            },
            {
                "category": "Infrastructure",
                "total_spending": 180000,
                "transaction_count": 20,
                "average_per_transaction": 9000
            },
            {
                "category": "Marketing",
                "total_spending": 95000,
                "transaction_count": 15,
                "average_per_transaction": 6333
            }
        ],
        "trend_projections": [
            {
                "month": "2024-02",
                "projected_spending": 200000,
                "projected_variance": 15000,
                "confidence": 0.85
            },
            {
                "month": "2024-03",
                "projected_spending": 220000,
                "projected_variance": 20000,
                "confidence": 0.80
            }
        ],
        "risk_indicators": {
            "projects_over_budget": 3,
            "projects_at_risk": 1,
            "critical_projects": 1,
            "average_utilization": 111.3
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
            },
            {
                "id": "var-2",
                "project_id": "proj-2", 
                "project_name": "Residential Tower A",
                "budget": 250000,
                "actual": 235000,
                "total_commitment": 250000,
                "total_actual": 235000,
                "variance": 15000,
                "variance_percentage": 6.0,
                "category": "materials",
                "date": "2024-01-08",
                "status": "under"
            },
            {
                "id": "var-3",
                "project_id": "proj-3",
                "project_name": "Shopping Center Renovation",
                "budget": 150000,
                "actual": 162000,
                "total_commitment": 150000,
                "total_actual": 162000,
                "variance": -12000,
                "variance_percentage": -8.0,
                "category": "labor",
                "date": "2024-01-08", 
                "status": "over"
            }
        ],
        "summary": {
            "total_budget": 700000,
            "total_actual": 742000,
            "total_variance": -42000,
            "variance_percentage": -6.0,
            "projects_over_budget": 2,
            "projects_under_budget": 1,
            "projects_on_budget": 0
        },
        "last_updated": datetime.now().isoformat()
    }

# Admin Performance endpoints
@app.get("/admin/performance/stats")
async def get_admin_performance_stats():
    """Mock admin performance statistics"""
    return {
        "total_requests": 15420,
        "total_errors": 124,
        "slow_queries_count": 3,
        "system_performance": {
            "cpu_usage": 45.2,
            "memory_usage": 68.7,
            "disk_usage": 34.1,
            "network_io": {
                "bytes_sent": 1024000,
                "bytes_received": 2048000
            }
        },
        "api_performance": {
            "total_requests": 15420,
            "requests_per_minute": 125,
            "average_response_time": 245,
            "error_rate": 0.8,
            "success_rate": 99.2
        },
        "database_performance": {
            "active_connections": 12,
            "max_connections": 100,
            "query_performance": {
                "average_query_time": 85,
                "slow_queries": 3,
                "total_queries": 8540
            }
        },
        "cache_performance": {
            "hit_rate": 94.5,
            "miss_rate": 5.5,
            "total_keys": 2840,
            "memory_usage": "156MB",
            "evictions": 12
        },
        "endpoint_stats": {
            "GET /projects": {
                "avg_duration": 0.125,
                "total_requests": 2450,
                "error_rate": 0.2,
                "requests_per_minute": 45
            },
            "POST /projects": {
                "avg_duration": 0.235,
                "total_requests": 890,
                "error_rate": 1.1,
                "requests_per_minute": 12
            },
            "GET /feedback/features": {
                "avg_duration": 0.089,
                "total_requests": 1250,
                "error_rate": 0.1,
                "requests_per_minute": 28
            },
            "GET /admin/performance/stats": {
                "avg_duration": 0.045,
                "total_requests": 340,
                "error_rate": 0.0,
                "requests_per_minute": 8
            },
            "POST /feedback/bugs": {
                "avg_duration": 0.156,
                "total_requests": 180,
                "error_rate": 0.5,
                "requests_per_minute": 3
            }
        },
        "recent_slow_queries": [
            {
                "endpoint": "GET /projects",
                "duration": 0.456,
                "timestamp": datetime.now().isoformat()
            },
            {
                "endpoint": "POST /monte-carlo/simulations/run",
                "duration": 0.789,
                "timestamp": datetime.now().isoformat()
            },
            {
                "endpoint": "GET /variance/trends",
                "duration": 0.345,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "uptime": {
            "seconds": 86400,
            "formatted": "1 day, 0 hours, 0 minutes"
        },
        "last_updated": datetime.now().isoformat()
    }

@app.get("/admin/performance/health")
async def get_admin_performance_health():
    """Mock admin performance health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "total_requests": 15420,
            "error_rate": 0.8,
            "slow_queries": 3,
            "uptime": "1 day, 0 hours, 0 minutes"
        },
        "cache_status": "healthy",
        "services": {
            "api_server": {
                "status": "healthy",
                "response_time": 12,
                "last_check": datetime.now().isoformat()
            },
            "database": {
                "status": "healthy", 
                "response_time": 8,
                "last_check": datetime.now().isoformat()
            },
            "cache": {
                "status": "healthy",
                "response_time": 3,
                "last_check": datetime.now().isoformat()
            },
            "file_storage": {
                "status": "healthy",
                "response_time": 15,
                "last_check": datetime.now().isoformat()
            }
        },
        "alerts": [
            {
                "id": "alert-1",
                "type": "warning",
                "service": "database",
                "message": "Query response time slightly elevated",
                "created_at": datetime.now().isoformat()
            }
        ],
        "service_metrics": {
            "total_services": 4,
            "healthy_services": 4,
            "warning_services": 0,
            "critical_services": 0
        },
        "last_updated": datetime.now().isoformat()
    }

@app.get("/admin/cache/stats")
async def get_admin_cache_stats():
    """Mock admin cache statistics"""
    return {
        "type": "redis",
        "hit_rate": 94.5,
        "entries": 2840,
        "used_memory": "156MB",
        "connected_clients": 12,
        "keyspace_hits": 9450,
        "keyspace_misses": 550,
        "cache_stats": {
            "total_keys": 2840,
            "memory_usage": "156MB",
            "max_memory": "512MB",
            "memory_usage_percentage": 30.5,
            "hit_rate": 94.5,
            "miss_rate": 5.5,
            "evictions": 12,
            "expired_keys": 45
        },
        "performance": {
            "average_get_time": 0.8,
            "average_set_time": 1.2,
            "operations_per_second": 1250
        },
        "key_distribution": {
            "user_sessions": 1200,
            "api_responses": 800,
            "database_queries": 640,
            "file_metadata": 200
        },
        "recent_activity": [
            {
                "timestamp": datetime.now().isoformat(),
                "operation": "GET",
                "key": "user_session_abc123",
                "result": "hit",
                "response_time": 0.5
            },
            {
                "timestamp": datetime.now().isoformat(),
                "operation": "SET", 
                "key": "api_response_xyz789",
                "result": "success",
                "response_time": 1.1
            }
        ],
        "last_updated": datetime.now().isoformat()
    }

@app.post("/admin/cache/clear")
async def clear_admin_cache():
    """Mock admin cache clear operation"""
    return {
        "status": "success",
        "message": "Cache cleared successfully",
        "cleared_keys": 2840,
        "memory_freed": "156MB",
        "operation_time": 0.25,
        "timestamp": datetime.now().isoformat()
    }

# Feedback endpoints
@app.get("/feedback/features")
async def get_feedback_features(status_filter: str = None, priority_filter: str = None):
    """Mock feedback features endpoint"""
    features = [
        {
            "id": "feat-1",
            "title": "Dark Mode Support",
            "description": "Add dark mode theme option for better user experience during night work sessions",
            "status": "under_review",
            "priority": "medium",
            "votes": 45,
            "upvotes": 42,
            "downvotes": 3,
            "submitted_by": "john.doe@company.com",
            "assigned_to": "ui-team",
            "tags": ["ui", "theme", "accessibility"],
            "created_at": "2024-01-05T10:00:00Z",
            "updated_at": "2024-01-08T10:00:00Z"
        },
        {
            "id": "feat-2",
            "title": "Advanced Filtering Options",
            "description": "Add more granular filtering options for project lists including date ranges, custom fields, and saved filters",
            "status": "approved",
            "priority": "high",
            "votes": 38,
            "upvotes": 35,
            "downvotes": 3,
            "submitted_by": "sarah.wilson@company.com",
            "assigned_to": "backend-team",
            "tags": ["filtering", "search", "productivity"],
            "created_at": "2024-01-03T14:30:00Z",
            "updated_at": "2024-01-07T16:45:00Z"
        },
        {
            "id": "feat-3",
            "title": "Mobile App",
            "description": "Develop a mobile application for iOS and Android to access key features on the go",
            "status": "submitted",
            "priority": "low",
            "votes": 67,
            "upvotes": 58,
            "downvotes": 9,
            "submitted_by": "mike.chen@company.com",
            "tags": ["mobile", "ios", "android"],
            "created_at": "2024-01-01T09:15:00Z",
            "updated_at": "2024-01-01T09:15:00Z"
        }
    ]
    
    # Apply filters
    if status_filter:
        features = [f for f in features if f["status"] == status_filter]
    if priority_filter:
        features = [f for f in features if f["priority"] == priority_filter]
    
    return features

@app.post("/feedback/features")
async def create_feedback_feature(feature_data: dict):
    """Mock create feedback feature endpoint"""
    return {
        "id": f"feat-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": feature_data.get("title"),
        "description": feature_data.get("description"),
        "status": "submitted",
        "priority": feature_data.get("priority", "medium"),
        "votes": 1,
        "upvotes": 1,
        "downvotes": 0,
        "submitted_by": "current-user@company.com",
        "tags": feature_data.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@app.get("/feedback/bugs")
async def get_feedback_bugs(status_filter: str = None, priority_filter: str = None):
    """Mock feedback bugs endpoint"""
    bugs = [
        {
            "id": "bug-1",
            "title": "Dashboard Loading Issue",
            "description": "Dashboard takes too long to load when there are many projects",
            "steps_to_reproduce": "1. Login with account having 50+ projects\n2. Navigate to dashboard\n3. Wait for loading",
            "expected_behavior": "Dashboard should load within 3 seconds",
            "actual_behavior": "Dashboard takes 15+ seconds to load",
            "status": "confirmed",
            "priority": "high",
            "severity": "major",
            "category": "performance",
            "submitted_by": "alice.johnson@company.com",
            "assigned_to": "performance-team",
            "created_at": "2024-01-06T11:20:00Z",
            "updated_at": "2024-01-08T09:30:00Z"
        },
        {
            "id": "bug-2",
            "title": "Export Button Not Working",
            "description": "CSV export button on reports page doesn't respond to clicks",
            "steps_to_reproduce": "1. Go to Reports page\n2. Click CSV Export button\n3. Nothing happens",
            "expected_behavior": "CSV file should download",
            "actual_behavior": "Button click has no effect",
            "status": "in_progress",
            "priority": "medium",
            "severity": "major",
            "category": "functionality",
            "submitted_by": "bob.smith@company.com",
            "assigned_to": "frontend-team",
            "created_at": "2024-01-04T16:45:00Z",
            "updated_at": "2024-01-07T14:20:00Z"
        },
        {
            "id": "bug-3",
            "title": "Text Overlap in Mobile View",
            "description": "Project names overlap with status badges on mobile devices",
            "steps_to_reproduce": "1. Open app on mobile device\n2. Navigate to projects list\n3. Observe text overlap",
            "expected_behavior": "Text should be properly spaced",
            "actual_behavior": "Text overlaps making it unreadable",
            "status": "submitted",
            "priority": "low",
            "severity": "minor",
            "category": "ui",
            "submitted_by": "carol.davis@company.com",
            "created_at": "2024-01-02T13:10:00Z",
            "updated_at": "2024-01-02T13:10:00Z"
        }
    ]
    
    # Apply filters
    if status_filter:
        bugs = [b for b in bugs if b["status"] == status_filter]
    if priority_filter:
        bugs = [b for b in bugs if b["priority"] == priority_filter]
    
    return bugs

@app.post("/feedback/bugs")
async def create_feedback_bug(bug_data: dict):
    """Mock create feedback bug endpoint"""
    return {
        "id": f"bug-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": bug_data.get("title"),
        "description": bug_data.get("description"),
        "steps_to_reproduce": bug_data.get("steps_to_reproduce"),
        "expected_behavior": bug_data.get("expected_behavior"),
        "actual_behavior": bug_data.get("actual_behavior"),
        "status": "submitted",
        "priority": bug_data.get("priority", "medium"),
        "severity": bug_data.get("severity", "minor"),
        "category": bug_data.get("category", "functionality"),
        "submitted_by": "current-user@company.com",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@app.post("/feedback/features/{feature_id}/vote")
async def vote_on_feature(feature_id: str, vote_data: dict):
    """Mock feature voting endpoint"""
    vote_type = vote_data.get("vote_type", "upvote")
    return {
        "feature_id": feature_id,
        "vote_type": vote_type,
        "success": True,
        "message": f"Vote recorded successfully",
        "new_vote_counts": {
            "upvotes": 43 if vote_type == "upvote" else 42,
            "downvotes": 3 if vote_type == "upvote" else 4,
            "total_votes": 46 if vote_type == "upvote" else 46
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/notifications")
async def get_notifications(unread_only: bool = False, limit: int = 10):
    """Mock notifications endpoint"""
    notifications = [
        {
            "id": "notif-1",
            "type": "feature_update",
            "title": "Feature Request Approved",
            "message": "Your feature request 'Dark Mode Support' has been approved for development",
            "related_id": "feat-1",
            "related_type": "feature_request",
            "read": False,
            "created_at": "2024-01-08T10:00:00Z"
        },
        {
            "id": "notif-2",
            "type": "bug_update",
            "title": "Bug Report Updated",
            "message": "Bug report 'Dashboard Loading Issue' status changed to confirmed",
            "related_id": "bug-1",
            "related_type": "bug_report",
            "read": False,
            "created_at": "2024-01-08T09:30:00Z"
        },
        {
            "id": "notif-3",
            "type": "system",
            "title": "System Maintenance",
            "message": "Scheduled maintenance will occur tonight from 2-4 AM EST",
            "read": True,
            "created_at": "2024-01-07T15:00:00Z",
            "read_at": "2024-01-07T16:30:00Z"
        }
    ]
    
    if unread_only:
        notifications = [n for n in notifications if not n["read"]]
    
    return notifications[:limit]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    print(f"🚀 Starting ORKA-PPM API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)