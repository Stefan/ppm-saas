"""
Monte Carlo Analysis Service for Enhanced PMR Feature.

This service provides predictive simulations for budget variance, schedule variance,
and resource risk analysis specifically for Project Monthly Reports (PMR).
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import numpy as np

from monte_carlo.engine import MonteCarloEngine
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, ProbabilityDistribution, 
    DistributionType, SimulationResults, ScheduleData, 
    Milestone, Activity, ResourceConstraint
)
from supabase import Client

logger = logging.getLogger(__name__)


class MonteCarloAnalysisService:
    """
    Service for running Monte Carlo simulations on project data for PMR reports.
    
    Provides predictive analytics for budget variance, schedule variance,
    and resource risk analysis with configurable parameters and confidence intervals.
    """
    
    def __init__(self, supabase: Client):
        """
        Initialize Monte Carlo Analysis Service.
        
        Args:
            supabase: Supabase client for database access
        """
        self.supabase = supabase
        self.engine = MonteCarloEngine()
        logger.info("Monte Carlo Analysis Service initialized")
    
    async def analyze_project_for_pmr(
        self,
        project_id: UUID,
        report_month: datetime,
        iterations: int = 10000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Run comprehensive Monte Carlo analysis for a project's PMR report.
        
        Args:
            project_id: UUID of the project to analyze
            report_month: Month for which the report is being generated
            iterations: Number of Monte Carlo iterations (default: 10000)
            confidence_level: Confidence level for intervals (default: 0.95)
            
        Returns:
            Dictionary containing budget, schedule, and resource risk analysis results
        """
        logger.info(f"Starting Monte Carlo analysis for project {project_id}")
        
        try:
            # Fetch project data
            project_data = await self._fetch_project_data(project_id, report_month)
            
            # Run budget variance analysis
            budget_analysis = await self.analyze_budget_variance(
                project_id, project_data, iterations, confidence_level
            )
            
            # Run schedule variance analysis
            schedule_analysis = await self.analyze_schedule_variance(
                project_id, project_data, iterations, confidence_level
            )
            
            # Run resource risk analysis
            resource_analysis = await self.analyze_resource_risks(
                project_id, project_data, iterations, confidence_level
            )
            
            # Combine results
            analysis_results = {
                "project_id": str(project_id),
                "report_month": report_month.isoformat(),
                "analysis_timestamp": datetime.now().isoformat(),
                "iterations": iterations,
                "confidence_level": confidence_level,
                "budget_analysis": budget_analysis,
                "schedule_analysis": schedule_analysis,
                "resource_analysis": resource_analysis,
                "summary": self._generate_analysis_summary(
                    budget_analysis, schedule_analysis, resource_analysis
                )
            }
            
            logger.info(f"Monte Carlo analysis completed for project {project_id}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo analysis for project {project_id}: {str(e)}")
            raise

    async def analyze_budget_variance(
        self,
        project_id: UUID,
        project_data: Dict[str, Any],
        iterations: int = 10000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Analyze budget variance using Monte Carlo simulation.
        
        Args:
            project_id: UUID of the project
            project_data: Project data including budget and financial information
            iterations: Number of simulation iterations
            confidence_level: Confidence level for intervals
            
        Returns:
            Dictionary containing budget variance analysis results
        """
        logger.info(f"Analyzing budget variance for project {project_id}")
        
        # Extract budget data
        baseline_budget = project_data.get("baseline_budget", 0.0)
        current_spend = project_data.get("current_spend", 0.0)
        remaining_budget = baseline_budget - current_spend
        
        # Create budget-related risks
        budget_risks = await self._create_budget_risks(project_data)
        
        if not budget_risks:
            logger.warning(f"No budget risks found for project {project_id}")
            return self._create_empty_budget_analysis(baseline_budget, current_spend)
        
        # Run simulation
        baseline_costs = {"baseline": remaining_budget}
        simulation_results = self.engine.run_simulation(
            risks=budget_risks,
            iterations=iterations,
            baseline_costs=baseline_costs
        )
        
        # Calculate statistics
        cost_outcomes = simulation_results.cost_outcomes
        percentiles = self._calculate_percentiles(cost_outcomes, confidence_level)
        
        # Calculate variance metrics
        expected_final_cost = current_spend + np.mean(cost_outcomes)
        variance_from_baseline = expected_final_cost - baseline_budget
        variance_percentage = (variance_from_baseline / baseline_budget * 100) if baseline_budget > 0 else 0
        
        # Calculate probability of staying within budget
        prob_within_budget = np.sum(cost_outcomes <= remaining_budget) / len(cost_outcomes)
        prob_within_10_percent = np.sum(cost_outcomes <= remaining_budget * 1.1) / len(cost_outcomes)
        
        return {
            "baseline_budget": baseline_budget,
            "current_spend": current_spend,
            "remaining_budget": remaining_budget,
            "expected_final_cost": expected_final_cost,
            "variance_from_baseline": variance_from_baseline,
            "variance_percentage": variance_percentage,
            "probability_within_budget": prob_within_budget,
            "probability_within_10_percent": prob_within_10_percent,
            "percentiles": percentiles,
            "confidence_intervals": self._calculate_confidence_intervals(
                cost_outcomes, confidence_level
            ),
            "risk_contributions": self._calculate_risk_contributions(
                simulation_results, budget_risks
            ),
            "simulation_id": simulation_results.simulation_id
        }

    async def analyze_schedule_variance(
        self,
        project_id: UUID,
        project_data: Dict[str, Any],
        iterations: int = 10000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Analyze schedule variance using Monte Carlo simulation.
        
        Args:
            project_id: UUID of the project
            project_data: Project data including schedule and milestone information
            iterations: Number of simulation iterations
            confidence_level: Confidence level for intervals
            
        Returns:
            Dictionary containing schedule variance analysis results
        """
        logger.info(f"Analyzing schedule variance for project {project_id}")
        
        # Extract schedule data
        baseline_duration = project_data.get("baseline_duration", 0.0)
        elapsed_time = project_data.get("elapsed_time", 0.0)
        remaining_duration = baseline_duration - elapsed_time
        
        # Create schedule-related risks
        schedule_risks = await self._create_schedule_risks(project_data)
        
        if not schedule_risks:
            logger.warning(f"No schedule risks found for project {project_id}")
            return self._create_empty_schedule_analysis(baseline_duration, elapsed_time)
        
        # Create schedule data structure
        schedule_data = await self._create_schedule_data(project_data)
        
        # Run simulation
        simulation_results = self.engine.run_simulation(
            risks=schedule_risks,
            iterations=iterations,
            schedule_data=schedule_data
        )
        
        # Calculate statistics
        schedule_outcomes = simulation_results.schedule_outcomes
        percentiles = self._calculate_percentiles(schedule_outcomes, confidence_level)
        
        # Calculate variance metrics
        expected_final_duration = elapsed_time + np.mean(schedule_outcomes)
        variance_from_baseline = expected_final_duration - baseline_duration
        variance_percentage = (variance_from_baseline / baseline_duration * 100) if baseline_duration > 0 else 0
        
        # Calculate probability of on-time completion
        prob_on_time = np.sum(schedule_outcomes <= remaining_duration) / len(schedule_outcomes)
        prob_within_1_week = np.sum(schedule_outcomes <= remaining_duration + 7) / len(schedule_outcomes)
        prob_within_1_month = np.sum(schedule_outcomes <= remaining_duration + 30) / len(schedule_outcomes)
        
        return {
            "baseline_duration": baseline_duration,
            "elapsed_time": elapsed_time,
            "remaining_duration": remaining_duration,
            "expected_final_duration": expected_final_duration,
            "variance_from_baseline": variance_from_baseline,
            "variance_percentage": variance_percentage,
            "probability_on_time": prob_on_time,
            "probability_within_1_week": prob_within_1_week,
            "probability_within_1_month": prob_within_1_month,
            "percentiles": percentiles,
            "confidence_intervals": self._calculate_confidence_intervals(
                schedule_outcomes, confidence_level
            ),
            "risk_contributions": self._calculate_risk_contributions(
                simulation_results, schedule_risks
            ),
            "critical_path_analysis": await self._analyze_critical_path(
                project_data, schedule_outcomes
            ),
            "simulation_id": simulation_results.simulation_id
        }

    async def analyze_resource_risks(
        self,
        project_id: UUID,
        project_data: Dict[str, Any],
        iterations: int = 10000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Analyze resource allocation risks using Monte Carlo simulation.
        
        Args:
            project_id: UUID of the project
            project_data: Project data including resource allocation information
            iterations: Number of simulation iterations
            confidence_level: Confidence level for intervals
            
        Returns:
            Dictionary containing resource risk analysis results
        """
        logger.info(f"Analyzing resource risks for project {project_id}")
        
        # Extract resource data
        resource_allocations = project_data.get("resource_allocations", [])
        
        # Create resource-related risks
        resource_risks = await self._create_resource_risks(project_data)
        
        if not resource_risks:
            logger.warning(f"No resource risks found for project {project_id}")
            return self._create_empty_resource_analysis()
        
        # Run simulation
        simulation_results = self.engine.run_simulation(
            risks=resource_risks,
            iterations=iterations
        )
        
        # Analyze resource utilization impacts
        resource_impact_analysis = await self._analyze_resource_impacts(
            resource_allocations, simulation_results
        )
        
        # Calculate resource conflict probabilities
        conflict_analysis = await self._analyze_resource_conflicts(
            project_data, simulation_results
        )
        
        return {
            "total_resources": len(resource_allocations),
            "resource_utilization": resource_impact_analysis,
            "conflict_probability": conflict_analysis,
            "risk_contributions": self._calculate_risk_contributions(
                simulation_results, resource_risks
            ),
            "recommendations": self._generate_resource_recommendations(
                resource_impact_analysis, conflict_analysis
            ),
            "simulation_id": simulation_results.simulation_id
        }

    # Helper methods for data fetching and risk creation
    
    async def _fetch_project_data(
        self, 
        project_id: UUID, 
        report_month: datetime
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive project data for Monte Carlo analysis.
        
        Args:
            project_id: UUID of the project
            report_month: Month for which data is being fetched
            
        Returns:
            Dictionary containing project data
        """
        try:
            # Fetch project basic info
            project_response = self.supabase.table("projects").select("*").eq("id", str(project_id)).execute()
            if not project_response.data:
                raise ValueError(f"Project {project_id} not found")
            
            project = project_response.data[0]
            
            # Fetch financial data
            financial_response = self.supabase.table("project_financials").select("*").eq(
                "project_id", str(project_id)
            ).execute()
            
            # Fetch risks
            risks_response = self.supabase.table("risks").select("*").eq(
                "project_id", str(project_id)
            ).eq("status", "active").execute()
            
            # Fetch milestones
            milestones_response = self.supabase.table("milestones").select("*").eq(
                "project_id", str(project_id)
            ).execute()
            
            # Fetch resource allocations
            resources_response = self.supabase.table("resource_assignments").select("*").eq(
                "project_id", str(project_id)
            ).execute()
            
            return {
                "project": project,
                "baseline_budget": project.get("baseline_budget", 0.0),
                "current_spend": project.get("actual_cost", 0.0),
                "baseline_duration": project.get("baseline_duration", 0.0),
                "elapsed_time": project.get("elapsed_days", 0.0),
                "financial_data": financial_response.data if financial_response.data else [],
                "risks": risks_response.data if risks_response.data else [],
                "milestones": milestones_response.data if milestones_response.data else [],
                "resource_allocations": resources_response.data if resources_response.data else []
            }
            
        except Exception as e:
            logger.error(f"Error fetching project data for {project_id}: {str(e)}")
            raise

    async def _create_budget_risks(self, project_data: Dict[str, Any]) -> List[Risk]:
        """
        Create Risk objects for budget-related uncertainties.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            List of Risk objects for budget analysis
        """
        risks = []
        risk_data = project_data.get("risks", [])
        
        for risk_item in risk_data:
            # Only include cost-related risks
            if risk_item.get("impact_type") in ["cost", "both"]:
                try:
                    # Create probability distribution based on risk data
                    distribution = self._create_distribution_from_risk(risk_item)
                    
                    risk = Risk(
                        id=risk_item.get("id", f"risk_{len(risks)}"),
                        name=risk_item.get("name", "Unnamed Risk"),
                        category=self._map_risk_category(risk_item.get("category", "cost")),
                        impact_type=ImpactType.COST,
                        probability_distribution=distribution,
                        baseline_impact=risk_item.get("cost_impact", 0.0)
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.warning(f"Failed to create risk from {risk_item.get('id')}: {str(e)}")
        
        # If no risks found, create a default uncertainty risk
        if not risks:
            risks.append(self._create_default_budget_risk(project_data))
        
        return risks
    
    async def _create_schedule_risks(self, project_data: Dict[str, Any]) -> List[Risk]:
        """
        Create Risk objects for schedule-related uncertainties.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            List of Risk objects for schedule analysis
        """
        risks = []
        risk_data = project_data.get("risks", [])
        
        for risk_item in risk_data:
            # Only include schedule-related risks
            if risk_item.get("impact_type") in ["schedule", "both"]:
                try:
                    distribution = self._create_distribution_from_risk(risk_item)
                    
                    risk = Risk(
                        id=risk_item.get("id", f"risk_{len(risks)}"),
                        name=risk_item.get("name", "Unnamed Risk"),
                        category=self._map_risk_category(risk_item.get("category", "schedule")),
                        impact_type=ImpactType.SCHEDULE,
                        probability_distribution=distribution,
                        baseline_impact=risk_item.get("schedule_impact", 0.0)
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.warning(f"Failed to create risk from {risk_item.get('id')}: {str(e)}")
        
        # If no risks found, create a default uncertainty risk
        if not risks:
            risks.append(self._create_default_schedule_risk(project_data))
        
        return risks

    async def _create_resource_risks(self, project_data: Dict[str, Any]) -> List[Risk]:
        """
        Create Risk objects for resource-related uncertainties.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            List of Risk objects for resource analysis
        """
        risks = []
        risk_data = project_data.get("risks", [])
        
        for risk_item in risk_data:
            # Include resource-related risks
            if risk_item.get("category") == "resource":
                try:
                    distribution = self._create_distribution_from_risk(risk_item)
                    
                    risk = Risk(
                        id=risk_item.get("id", f"risk_{len(risks)}"),
                        name=risk_item.get("name", "Unnamed Risk"),
                        category=RiskCategory.RESOURCE,
                        impact_type=self._map_impact_type(risk_item.get("impact_type", "both")),
                        probability_distribution=distribution,
                        baseline_impact=risk_item.get("resource_impact", 0.0)
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.warning(f"Failed to create risk from {risk_item.get('id')}: {str(e)}")
        
        # If no risks found, create a default resource risk
        if not risks:
            risks.append(self._create_default_resource_risk(project_data))
        
        return risks
    
    def _create_distribution_from_risk(self, risk_item: Dict[str, Any]) -> ProbabilityDistribution:
        """
        Create a ProbabilityDistribution from risk data.
        
        Args:
            risk_item: Risk data dictionary
            
        Returns:
            ProbabilityDistribution object
        """
        # Check if distribution parameters are provided
        dist_type = risk_item.get("distribution_type", "triangular")
        
        if dist_type == "triangular":
            # Use three-point estimate if available
            min_val = risk_item.get("min_impact", 0.0)
            mode_val = risk_item.get("most_likely_impact", risk_item.get("baseline_impact", 0.0))
            max_val = risk_item.get("max_impact", mode_val * 2)
            
            return ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": min_val, "mode": mode_val, "max": max_val}
            )
        elif dist_type == "normal":
            mean = risk_item.get("mean_impact", risk_item.get("baseline_impact", 0.0))
            std = risk_item.get("std_impact", mean * 0.2)  # Default to 20% std dev
            
            return ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": mean, "std": std}
            )
        else:
            # Default to triangular distribution
            baseline = risk_item.get("baseline_impact", 0.0)
            return ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": baseline * 0.5, "mode": baseline, "max": baseline * 1.5}
            )

    def _create_default_budget_risk(self, project_data: Dict[str, Any]) -> Risk:
        """Create a default budget uncertainty risk."""
        remaining_budget = project_data.get("baseline_budget", 0.0) - project_data.get("current_spend", 0.0)
        uncertainty = remaining_budget * 0.1  # 10% uncertainty
        
        return Risk(
            id="default_budget_risk",
            name="Budget Uncertainty",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={
                    "min": -uncertainty,
                    "mode": 0.0,
                    "max": uncertainty * 2
                }
            ),
            baseline_impact=uncertainty
        )
    
    def _create_default_schedule_risk(self, project_data: Dict[str, Any]) -> Risk:
        """Create a default schedule uncertainty risk."""
        remaining_duration = project_data.get("baseline_duration", 0.0) - project_data.get("elapsed_time", 0.0)
        uncertainty = remaining_duration * 0.1  # 10% uncertainty
        
        return Risk(
            id="default_schedule_risk",
            name="Schedule Uncertainty",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={
                    "min": -uncertainty,
                    "mode": 0.0,
                    "max": uncertainty * 2
                }
            ),
            baseline_impact=uncertainty
        )
    
    def _create_default_resource_risk(self, project_data: Dict[str, Any]) -> Risk:
        """Create a default resource uncertainty risk."""
        return Risk(
            id="default_resource_risk",
            name="Resource Availability Uncertainty",
            category=RiskCategory.RESOURCE,
            impact_type=ImpactType.BOTH,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 0.0, "mode": 5.0, "max": 15.0}
            ),
            baseline_impact=5.0
        )

    async def _create_schedule_data(self, project_data: Dict[str, Any]) -> Optional[ScheduleData]:
        """
        Create ScheduleData structure from project data.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            ScheduleData object or None if insufficient data
        """
        milestones_data = project_data.get("milestones", [])
        
        if not milestones_data:
            return None
        
        milestones = []
        for milestone_item in milestones_data:
            try:
                milestone = Milestone(
                    id=milestone_item.get("id", f"milestone_{len(milestones)}"),
                    name=milestone_item.get("name", "Unnamed Milestone"),
                    planned_date=datetime.fromisoformat(milestone_item.get("planned_date", datetime.now().isoformat())),
                    baseline_duration=milestone_item.get("baseline_duration", 0.0),
                    critical_path=milestone_item.get("critical_path", False),
                    dependencies=milestone_item.get("dependencies", [])
                )
                milestones.append(milestone)
            except Exception as e:
                logger.warning(f"Failed to create milestone: {str(e)}")
        
        return ScheduleData(
            milestones=milestones,
            project_baseline_duration=project_data.get("baseline_duration", 0.0)
        )
    
    # Statistical calculation methods
    
    def _calculate_percentiles(
        self, 
        outcomes: np.ndarray, 
        confidence_level: float
    ) -> Dict[str, float]:
        """
        Calculate key percentiles from simulation outcomes.
        
        Args:
            outcomes: Array of simulation outcomes
            confidence_level: Confidence level for calculations
            
        Returns:
            Dictionary of percentile values
        """
        return {
            "p10": float(np.percentile(outcomes, 10)),
            "p25": float(np.percentile(outcomes, 25)),
            "p50": float(np.percentile(outcomes, 50)),
            "p75": float(np.percentile(outcomes, 75)),
            "p90": float(np.percentile(outcomes, 90)),
            "p95": float(np.percentile(outcomes, 95)),
            "mean": float(np.mean(outcomes)),
            "std": float(np.std(outcomes))
        }
    
    def _calculate_confidence_intervals(
        self, 
        outcomes: np.ndarray, 
        confidence_level: float
    ) -> Dict[str, Any]:
        """
        Calculate confidence intervals for simulation outcomes.
        
        Args:
            outcomes: Array of simulation outcomes
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Dictionary containing confidence interval information
        """
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        return {
            "confidence_level": confidence_level,
            "lower_bound": float(np.percentile(outcomes, lower_percentile)),
            "upper_bound": float(np.percentile(outcomes, upper_percentile)),
            "mean": float(np.mean(outcomes))
        }

    def _calculate_risk_contributions(
        self, 
        simulation_results: SimulationResults, 
        risks: List[Risk]
    ) -> List[Dict[str, Any]]:
        """
        Calculate individual risk contributions to overall uncertainty.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            risks: List of risks that were simulated
            
        Returns:
            List of risk contribution dictionaries
        """
        contributions = []
        
        for risk in risks:
            if risk.id in simulation_results.risk_contributions:
                risk_outcomes = simulation_results.risk_contributions[risk.id]
                variance = np.var(risk_outcomes)
                mean_impact = np.mean(risk_outcomes)
                
                contributions.append({
                    "risk_id": risk.id,
                    "risk_name": risk.name,
                    "mean_impact": float(mean_impact),
                    "variance": float(variance),
                    "std_dev": float(np.std(risk_outcomes)),
                    "max_impact": float(np.max(risk_outcomes)),
                    "min_impact": float(np.min(risk_outcomes))
                })
        
        # Sort by variance (highest contributors first)
        contributions.sort(key=lambda x: x["variance"], reverse=True)
        
        return contributions
    
    # Analysis helper methods
    
    async def _analyze_resource_impacts(
        self, 
        resource_allocations: List[Dict[str, Any]], 
        simulation_results: SimulationResults
    ) -> Dict[str, Any]:
        """
        Analyze resource utilization impacts from simulation.
        
        Args:
            resource_allocations: List of resource allocation data
            simulation_results: Monte Carlo simulation results
            
        Returns:
            Dictionary containing resource impact analysis
        """
        if not resource_allocations:
            return {"total_resources": 0, "utilization_rate": 0.0, "over_allocation_risk": 0.0}
        
        total_capacity = sum(r.get("capacity", 0.0) for r in resource_allocations)
        total_allocated = sum(r.get("allocated", 0.0) for r in resource_allocations)
        
        utilization_rate = (total_allocated / total_capacity) if total_capacity > 0 else 0.0
        
        # Estimate over-allocation risk based on simulation variance
        schedule_variance = np.var(simulation_results.schedule_outcomes)
        over_allocation_risk = min(1.0, schedule_variance / 100.0)  # Normalize to 0-1
        
        return {
            "total_resources": len(resource_allocations),
            "total_capacity": total_capacity,
            "total_allocated": total_allocated,
            "utilization_rate": utilization_rate,
            "over_allocation_risk": over_allocation_risk
        }

    async def _analyze_resource_conflicts(
        self, 
        project_data: Dict[str, Any], 
        simulation_results: SimulationResults
    ) -> Dict[str, Any]:
        """
        Analyze probability of resource conflicts.
        
        Args:
            project_data: Project data dictionary
            simulation_results: Monte Carlo simulation results
            
        Returns:
            Dictionary containing conflict analysis
        """
        resource_allocations = project_data.get("resource_allocations", [])
        
        if not resource_allocations:
            return {"conflict_probability": 0.0, "high_risk_resources": []}
        
        # Identify resources with high utilization
        high_risk_resources = []
        for resource in resource_allocations:
            capacity = resource.get("capacity", 0.0)
            allocated = resource.get("allocated", 0.0)
            
            if capacity > 0 and (allocated / capacity) > 0.85:  # 85% threshold
                high_risk_resources.append({
                    "resource_id": resource.get("id"),
                    "resource_name": resource.get("name", "Unknown"),
                    "utilization": allocated / capacity,
                    "capacity": capacity,
                    "allocated": allocated
                })
        
        # Calculate overall conflict probability
        conflict_probability = len(high_risk_resources) / len(resource_allocations) if resource_allocations else 0.0
        
        return {
            "conflict_probability": conflict_probability,
            "high_risk_resources": high_risk_resources,
            "total_resources_analyzed": len(resource_allocations)
        }
    
    async def _analyze_critical_path(
        self, 
        project_data: Dict[str, Any], 
        schedule_outcomes: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze critical path impacts from schedule simulation.
        
        Args:
            project_data: Project data dictionary
            schedule_outcomes: Array of schedule simulation outcomes
            
        Returns:
            Dictionary containing critical path analysis
        """
        milestones = project_data.get("milestones", [])
        critical_milestones = [m for m in milestones if m.get("critical_path", False)]
        
        if not critical_milestones:
            return {
                "critical_path_identified": False,
                "critical_milestones": 0,
                "delay_risk": 0.0
            }
        
        # Calculate delay risk based on schedule variance
        baseline_duration = project_data.get("baseline_duration", 0.0)
        mean_duration = np.mean(schedule_outcomes)
        delay_risk = max(0.0, (mean_duration - baseline_duration) / baseline_duration) if baseline_duration > 0 else 0.0
        
        return {
            "critical_path_identified": True,
            "critical_milestones": len(critical_milestones),
            "delay_risk": delay_risk,
            "milestone_details": [
                {
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "baseline_duration": m.get("baseline_duration", 0.0)
                }
                for m in critical_milestones
            ]
        }

    def _generate_resource_recommendations(
        self, 
        resource_impact_analysis: Dict[str, Any], 
        conflict_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on resource analysis.
        
        Args:
            resource_impact_analysis: Resource impact analysis results
            conflict_analysis: Resource conflict analysis results
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        utilization_rate = resource_impact_analysis.get("utilization_rate", 0.0)
        conflict_probability = conflict_analysis.get("conflict_probability", 0.0)
        high_risk_resources = conflict_analysis.get("high_risk_resources", [])
        
        if utilization_rate > 0.9:
            recommendations.append(
                "High resource utilization detected (>90%). Consider adding buffer capacity or adjusting timeline."
            )
        
        if conflict_probability > 0.3:
            recommendations.append(
                f"Resource conflict risk is elevated ({conflict_probability:.1%}). Review resource allocation for {len(high_risk_resources)} high-risk resources."
            )
        
        if high_risk_resources:
            resource_names = [r.get("resource_name", "Unknown") for r in high_risk_resources[:3]]
            recommendations.append(
                f"Critical resources requiring attention: {', '.join(resource_names)}"
            )
        
        if not recommendations:
            recommendations.append("Resource allocation appears balanced. Continue monitoring utilization trends.")
        
        return recommendations
    
    def _generate_analysis_summary(
        self, 
        budget_analysis: Dict[str, Any], 
        schedule_analysis: Dict[str, Any], 
        resource_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary of Monte Carlo analysis.
        
        Args:
            budget_analysis: Budget variance analysis results
            schedule_analysis: Schedule variance analysis results
            resource_analysis: Resource risk analysis results
            
        Returns:
            Dictionary containing analysis summary
        """
        # Determine overall risk level
        budget_risk = "low" if budget_analysis.get("probability_within_budget", 0) > 0.7 else \
                     "medium" if budget_analysis.get("probability_within_budget", 0) > 0.5 else "high"
        
        schedule_risk = "low" if schedule_analysis.get("probability_on_time", 0) > 0.7 else \
                       "medium" if schedule_analysis.get("probability_on_time", 0) > 0.5 else "high"
        
        resource_risk = "low" if resource_analysis.get("conflict_probability", {}).get("conflict_probability", 0) < 0.3 else \
                       "medium" if resource_analysis.get("conflict_probability", {}).get("conflict_probability", 0) < 0.6 else "high"
        
        # Generate key insights
        insights = []
        
        if budget_analysis.get("variance_percentage", 0) > 10:
            insights.append(f"Budget variance of {budget_analysis.get('variance_percentage', 0):.1f}% exceeds threshold")
        
        if schedule_analysis.get("variance_percentage", 0) > 10:
            insights.append(f"Schedule variance of {schedule_analysis.get('variance_percentage', 0):.1f}% exceeds threshold")
        
        if resource_analysis.get("conflict_probability", {}).get("conflict_probability", 0) > 0.5:
            insights.append("High probability of resource conflicts detected")
        
        return {
            "overall_risk_level": max([budget_risk, schedule_risk, resource_risk], key=lambda x: ["low", "medium", "high"].index(x)),
            "budget_risk_level": budget_risk,
            "schedule_risk_level": schedule_risk,
            "resource_risk_level": resource_risk,
            "key_insights": insights,
            "probability_of_success": min(
                budget_analysis.get("probability_within_budget", 0),
                schedule_analysis.get("probability_on_time", 0)
            )
        }

    # Empty analysis creators for cases with no data
    
    def _create_empty_budget_analysis(
        self, 
        baseline_budget: float, 
        current_spend: float
    ) -> Dict[str, Any]:
        """Create empty budget analysis when no risks are available."""
        return {
            "baseline_budget": baseline_budget,
            "current_spend": current_spend,
            "remaining_budget": baseline_budget - current_spend,
            "expected_final_cost": baseline_budget,
            "variance_from_baseline": 0.0,
            "variance_percentage": 0.0,
            "probability_within_budget": 1.0,
            "probability_within_10_percent": 1.0,
            "percentiles": {},
            "confidence_intervals": {},
            "risk_contributions": [],
            "simulation_id": None,
            "note": "No budget risks identified for analysis"
        }
    
    def _create_empty_schedule_analysis(
        self, 
        baseline_duration: float, 
        elapsed_time: float
    ) -> Dict[str, Any]:
        """Create empty schedule analysis when no risks are available."""
        return {
            "baseline_duration": baseline_duration,
            "elapsed_time": elapsed_time,
            "remaining_duration": baseline_duration - elapsed_time,
            "expected_final_duration": baseline_duration,
            "variance_from_baseline": 0.0,
            "variance_percentage": 0.0,
            "probability_on_time": 1.0,
            "probability_within_1_week": 1.0,
            "probability_within_1_month": 1.0,
            "percentiles": {},
            "confidence_intervals": {},
            "risk_contributions": [],
            "critical_path_analysis": {},
            "simulation_id": None,
            "note": "No schedule risks identified for analysis"
        }
    
    def _create_empty_resource_analysis(self) -> Dict[str, Any]:
        """Create empty resource analysis when no risks are available."""
        return {
            "total_resources": 0,
            "resource_utilization": {},
            "conflict_probability": {},
            "risk_contributions": [],
            "recommendations": ["Insufficient resource data for analysis"],
            "simulation_id": None,
            "note": "No resource risks identified for analysis"
        }
    
    # Utility mapping methods
    
    def _map_risk_category(self, category_str: str) -> RiskCategory:
        """Map string category to RiskCategory enum."""
        category_map = {
            "technical": RiskCategory.TECHNICAL,
            "schedule": RiskCategory.SCHEDULE,
            "cost": RiskCategory.COST,
            "resource": RiskCategory.RESOURCE,
            "external": RiskCategory.EXTERNAL,
            "quality": RiskCategory.QUALITY,
            "regulatory": RiskCategory.REGULATORY
        }
        return category_map.get(category_str.lower(), RiskCategory.COST)
    
    def _map_impact_type(self, impact_str: str) -> ImpactType:
        """Map string impact type to ImpactType enum."""
        impact_map = {
            "cost": ImpactType.COST,
            "schedule": ImpactType.SCHEDULE,
            "both": ImpactType.BOTH
        }
        return impact_map.get(impact_str.lower(), ImpactType.BOTH)
