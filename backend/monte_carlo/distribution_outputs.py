"""
Distribution Outputs Module - Cost and schedule distribution outputs.

This module implements budget compliance probability calculations and completion 
probability by target dates as required by Requirements 4.4 and 5.4.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from .models import SimulationResults


class ComplianceLevel(Enum):
    """Budget compliance confidence levels."""
    LOW = "low"          # 50-70% confidence
    MEDIUM = "medium"    # 70-90% confidence
    HIGH = "high"        # 90-95% confidence
    VERY_HIGH = "very_high"  # 95%+ confidence


@dataclass
class BudgetComplianceResult:
    """
    Result of budget compliance probability calculation.
    
    Attributes:
        target_budget: Target budget amount
        compliance_probability: Probability of staying within budget (0-1)
        expected_cost: Expected cost from simulation
        cost_at_risk: Amount at risk above target budget
        confidence_intervals: Confidence intervals for cost outcomes
        percentile_analysis: Percentile breakdown of costs
        compliance_level: Categorized compliance level
    """
    target_budget: float
    compliance_probability: float
    expected_cost: float
    cost_at_risk: float
    confidence_intervals: Dict[str, Tuple[float, float]]
    percentile_analysis: Dict[str, float]
    compliance_level: ComplianceLevel


@dataclass
class ScheduleComplianceResult:
    """
    Result of schedule completion probability calculation.
    
    Attributes:
        target_date: Target completion date
        completion_probability: Probability of completing by target date (0-1)
        expected_completion: Expected completion date from simulation
        schedule_at_risk: Days at risk beyond target date
        confidence_intervals: Confidence intervals for completion dates
        percentile_analysis: Percentile breakdown of completion times
        milestone_probabilities: Completion probabilities for intermediate milestones
    """
    target_date: datetime
    completion_probability: float
    expected_completion: datetime
    schedule_at_risk: float
    confidence_intervals: Dict[str, Tuple[datetime, datetime]]
    percentile_analysis: Dict[str, datetime]
    milestone_probabilities: Optional[Dict[str, float]] = None


@dataclass
class DistributionSummary:
    """
    Summary of distribution characteristics.
    
    Attributes:
        mean: Mean value
        median: Median value
        std_dev: Standard deviation
        coefficient_of_variation: Coefficient of variation (std/mean)
        skewness: Distribution skewness
        kurtosis: Distribution kurtosis
        percentiles: Key percentile values
        confidence_intervals: Confidence intervals at different levels
    """
    mean: float
    median: float
    std_dev: float
    coefficient_of_variation: float
    skewness: float
    kurtosis: float
    percentiles: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]


class DistributionOutputGenerator:
    """
    Generates cost and schedule distribution outputs for Monte Carlo simulation results.
    
    Implements Requirements 4.4 and 5.4:
    - Budget compliance probability calculations at different confidence levels
    - Completion probability by target dates
    """
    
    def __init__(self):
        """Initialize the distribution output generator."""
        self.default_confidence_levels = [0.80, 0.90, 0.95]
        self.default_percentiles = [10, 25, 50, 75, 90, 95, 99]
    
    def calculate_budget_compliance(
        self,
        simulation_results: SimulationResults,
        target_budget: float,
        confidence_levels: Optional[List[float]] = None
    ) -> BudgetComplianceResult:
        """
        Calculate budget compliance probability and risk analysis.
        
        Implements Requirement 4.4: The Monte Carlo Engine shall output cost distributions 
        showing probability of staying within budget at different confidence levels.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            target_budget: Target budget amount to analyze compliance against
            confidence_levels: Confidence levels for interval calculations
            
        Returns:
            BudgetComplianceResult with comprehensive budget analysis
        """
        if confidence_levels is None:
            confidence_levels = self.default_confidence_levels
        
        cost_outcomes = simulation_results.cost_outcomes
        
        # Calculate compliance probability
        within_budget_count = np.sum(cost_outcomes <= target_budget)
        compliance_probability = within_budget_count / len(cost_outcomes)
        
        # Calculate expected cost
        expected_cost = float(np.mean(cost_outcomes))
        
        # Calculate cost at risk (expected excess over budget)
        excess_costs = cost_outcomes - target_budget
        excess_costs = excess_costs[excess_costs > 0]  # Only positive excesses
        cost_at_risk = float(np.mean(excess_costs)) if len(excess_costs) > 0 else 0.0
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for confidence in confidence_levels:
            alpha = 1 - confidence
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_bound = float(np.percentile(cost_outcomes, lower_percentile))
            upper_bound = float(np.percentile(cost_outcomes, upper_percentile))
            
            confidence_intervals[f'{int(confidence*100)}%'] = (lower_bound, upper_bound)
        
        # Calculate percentile analysis
        percentile_analysis = {}
        for p in self.default_percentiles:
            percentile_analysis[f'P{p}'] = float(np.percentile(cost_outcomes, p))
        
        # Determine compliance level
        compliance_level = self._categorize_compliance_level(compliance_probability)
        
        return BudgetComplianceResult(
            target_budget=target_budget,
            compliance_probability=compliance_probability,
            expected_cost=expected_cost,
            cost_at_risk=cost_at_risk,
            confidence_intervals=confidence_intervals,
            percentile_analysis=percentile_analysis,
            compliance_level=compliance_level
        )
    
    def calculate_schedule_compliance(
        self,
        simulation_results: SimulationResults,
        target_date: datetime,
        project_start_date: datetime,
        confidence_levels: Optional[List[float]] = None,
        milestone_dates: Optional[Dict[str, datetime]] = None
    ) -> ScheduleComplianceResult:
        """
        Calculate schedule completion probability and risk analysis.
        
        Implements Requirement 5.4: The Monte Carlo Engine shall output schedule distributions 
        showing probability of completion by target dates.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            target_date: Target completion date to analyze compliance against
            project_start_date: Project start date for duration calculations
            confidence_levels: Confidence levels for interval calculations
            milestone_dates: Optional milestone dates for intermediate analysis
            
        Returns:
            ScheduleComplianceResult with comprehensive schedule analysis
        """
        if confidence_levels is None:
            confidence_levels = self.default_confidence_levels
        
        schedule_outcomes = simulation_results.schedule_outcomes
        
        # Convert schedule outcomes (days) to completion dates
        completion_dates = np.array([
            project_start_date + timedelta(days=float(duration))
            for duration in schedule_outcomes
        ])
        
        # Calculate completion probability
        on_time_count = np.sum(completion_dates <= target_date)
        completion_probability = on_time_count / len(completion_dates)
        
        # Calculate expected completion date
        expected_duration = float(np.mean(schedule_outcomes))
        expected_completion = project_start_date + timedelta(days=expected_duration)
        
        # Calculate schedule at risk (expected delay beyond target)
        target_duration = (target_date - project_start_date).days
        delays = schedule_outcomes - target_duration
        delays = delays[delays > 0]  # Only positive delays
        schedule_at_risk = float(np.mean(delays)) if len(delays) > 0 else 0.0
        
        # Calculate confidence intervals for completion dates
        confidence_intervals = {}
        for confidence in confidence_levels:
            alpha = 1 - confidence
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_duration = np.percentile(schedule_outcomes, lower_percentile)
            upper_duration = np.percentile(schedule_outcomes, upper_percentile)
            
            lower_date = project_start_date + timedelta(days=float(lower_duration))
            upper_date = project_start_date + timedelta(days=float(upper_duration))
            
            confidence_intervals[f'{int(confidence*100)}%'] = (lower_date, upper_date)
        
        # Calculate percentile analysis for completion dates
        percentile_analysis = {}
        for p in self.default_percentiles:
            duration = np.percentile(schedule_outcomes, p)
            completion_date = project_start_date + timedelta(days=float(duration))
            percentile_analysis[f'P{p}'] = completion_date
        
        # Calculate milestone probabilities if provided
        milestone_probabilities = None
        if milestone_dates:
            milestone_probabilities = {}
            for milestone_name, milestone_date in milestone_dates.items():
                milestone_duration = (milestone_date - project_start_date).days
                milestone_on_time = np.sum(schedule_outcomes <= milestone_duration)
                milestone_probabilities[milestone_name] = milestone_on_time / len(schedule_outcomes)
        
        return ScheduleComplianceResult(
            target_date=target_date,
            completion_probability=completion_probability,
            expected_completion=expected_completion,
            schedule_at_risk=schedule_at_risk,
            confidence_intervals=confidence_intervals,
            percentile_analysis=percentile_analysis,
            milestone_probabilities=milestone_probabilities
        )
    
    def generate_distribution_summary(
        self,
        data: np.ndarray,
        confidence_levels: Optional[List[float]] = None
    ) -> DistributionSummary:
        """
        Generate comprehensive distribution summary statistics.
        
        Args:
            data: Array of simulation outcomes
            confidence_levels: Confidence levels for interval calculations
            
        Returns:
            DistributionSummary with comprehensive statistics
        """
        if confidence_levels is None:
            confidence_levels = self.default_confidence_levels
        
        # Basic statistics
        mean = float(np.mean(data))
        median = float(np.median(data))
        std_dev = float(np.std(data))
        coefficient_of_variation = std_dev / mean if mean != 0 else float('inf')
        
        # Higher-order moments
        from scipy import stats
        skewness = float(stats.skew(data))
        kurtosis = float(stats.kurtosis(data))
        
        # Percentiles
        percentiles = {}
        for p in self.default_percentiles:
            percentiles[f'P{p}'] = float(np.percentile(data, p))
        
        # Confidence intervals
        confidence_intervals = {}
        for confidence in confidence_levels:
            alpha = 1 - confidence
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_bound = float(np.percentile(data, lower_percentile))
            upper_bound = float(np.percentile(data, upper_percentile))
            
            confidence_intervals[f'{int(confidence*100)}%'] = (lower_bound, upper_bound)
        
        return DistributionSummary(
            mean=mean,
            median=median,
            std_dev=std_dev,
            coefficient_of_variation=coefficient_of_variation,
            skewness=skewness,
            kurtosis=kurtosis,
            percentiles=percentiles,
            confidence_intervals=confidence_intervals
        )
    
    def calculate_value_at_risk(
        self,
        data: np.ndarray,
        confidence_levels: List[float] = [0.95, 0.99]
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) for cost or schedule outcomes.
        
        Args:
            data: Array of simulation outcomes
            confidence_levels: Confidence levels for VaR calculation
            
        Returns:
            Dictionary of VaR values at different confidence levels
        """
        var_results = {}
        
        for confidence in confidence_levels:
            # VaR is the percentile corresponding to the confidence level
            var_percentile = confidence * 100
            var_value = float(np.percentile(data, var_percentile))
            var_results[f'VaR_{int(confidence*100)}%'] = var_value
        
        return var_results
    
    def calculate_conditional_value_at_risk(
        self,
        data: np.ndarray,
        confidence_levels: List[float] = [0.95, 0.99]
    ) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) for cost or schedule outcomes.
        
        CVaR is the expected value of outcomes beyond the VaR threshold.
        
        Args:
            data: Array of simulation outcomes
            confidence_levels: Confidence levels for CVaR calculation
            
        Returns:
            Dictionary of CVaR values at different confidence levels
        """
        cvar_results = {}
        
        for confidence in confidence_levels:
            # Find VaR threshold
            var_percentile = confidence * 100
            var_threshold = np.percentile(data, var_percentile)
            
            # Calculate CVaR as mean of values beyond VaR
            tail_values = data[data >= var_threshold]
            cvar_value = float(np.mean(tail_values)) if len(tail_values) > 0 else var_threshold
            
            cvar_results[f'CVaR_{int(confidence*100)}%'] = cvar_value
        
        return cvar_results
    
    def generate_compliance_report(
        self,
        simulation_results: SimulationResults,
        target_budget: Optional[float] = None,
        target_date: Optional[datetime] = None,
        project_start_date: Optional[datetime] = None,
        milestone_dates: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for both cost and schedule.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            target_budget: Optional target budget for compliance analysis
            target_date: Optional target completion date
            project_start_date: Optional project start date for schedule analysis
            milestone_dates: Optional milestone dates for intermediate analysis
            
        Returns:
            Dictionary containing comprehensive compliance analysis
        """
        report = {
            'simulation_summary': {
                'simulation_id': simulation_results.simulation_id,
                'timestamp': simulation_results.timestamp.isoformat(),
                'iteration_count': simulation_results.iteration_count,
                'execution_time': simulation_results.execution_time
            },
            'cost_analysis': {},
            'schedule_analysis': {},
            'risk_analysis': {}
        }
        
        # Cost analysis
        cost_summary = self.generate_distribution_summary(simulation_results.cost_outcomes)
        report['cost_analysis']['distribution_summary'] = cost_summary
        
        cost_var = self.calculate_value_at_risk(simulation_results.cost_outcomes)
        cost_cvar = self.calculate_conditional_value_at_risk(simulation_results.cost_outcomes)
        report['cost_analysis']['value_at_risk'] = cost_var
        report['cost_analysis']['conditional_value_at_risk'] = cost_cvar
        
        if target_budget:
            budget_compliance = self.calculate_budget_compliance(
                simulation_results, target_budget
            )
            report['cost_analysis']['budget_compliance'] = budget_compliance
        
        # Schedule analysis
        schedule_summary = self.generate_distribution_summary(simulation_results.schedule_outcomes)
        report['schedule_analysis']['distribution_summary'] = schedule_summary
        
        schedule_var = self.calculate_value_at_risk(simulation_results.schedule_outcomes)
        schedule_cvar = self.calculate_conditional_value_at_risk(simulation_results.schedule_outcomes)
        report['schedule_analysis']['value_at_risk'] = schedule_var
        report['schedule_analysis']['conditional_value_at_risk'] = schedule_cvar
        
        if target_date and project_start_date:
            schedule_compliance = self.calculate_schedule_compliance(
                simulation_results, target_date, project_start_date, milestone_dates=milestone_dates
            )
            report['schedule_analysis']['schedule_compliance'] = schedule_compliance
        
        # Risk contribution analysis
        if simulation_results.risk_contributions:
            risk_analysis = self._analyze_risk_contributions(simulation_results)
            report['risk_analysis'] = risk_analysis
        
        return report
    
    def _categorize_compliance_level(self, probability: float) -> ComplianceLevel:
        """
        Categorize compliance probability into levels.
        
        Args:
            probability: Compliance probability (0-1)
            
        Returns:
            ComplianceLevel enum value
        """
        if probability >= 0.95:
            return ComplianceLevel.VERY_HIGH
        elif probability >= 0.90:
            return ComplianceLevel.HIGH
        elif probability >= 0.70:
            return ComplianceLevel.MEDIUM
        else:
            return ComplianceLevel.LOW
    
    def _analyze_risk_contributions(self, simulation_results: SimulationResults) -> Dict[str, Any]:
        """
        Analyze individual risk contributions to overall uncertainty.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            
        Returns:
            Dictionary containing risk contribution analysis
        """
        risk_contributions = simulation_results.risk_contributions
        
        # Calculate contribution statistics for each risk
        contribution_stats = {}
        for risk_id, contributions in risk_contributions.items():
            stats = self.generate_distribution_summary(contributions)
            contribution_stats[risk_id] = {
                'mean_contribution': stats.mean,
                'std_contribution': stats.std_dev,
                'max_contribution': float(np.max(contributions)),
                'min_contribution': float(np.min(contributions)),
                'contribution_percentiles': stats.percentiles
            }
        
        # Rank risks by mean absolute contribution
        risk_rankings = []
        for risk_id, stats in contribution_stats.items():
            risk_rankings.append({
                'risk_id': risk_id,
                'mean_absolute_contribution': abs(stats['mean_contribution']),
                'contribution_volatility': stats['std_contribution']
            })
        
        # Sort by mean absolute contribution (descending)
        risk_rankings.sort(key=lambda x: x['mean_absolute_contribution'], reverse=True)
        
        # Calculate total contribution variance
        total_cost_variance = float(np.var(simulation_results.cost_outcomes))
        total_schedule_variance = float(np.var(simulation_results.schedule_outcomes))
        
        return {
            'contribution_statistics': contribution_stats,
            'risk_rankings': risk_rankings[:10],  # Top 10 risks
            'total_cost_variance': total_cost_variance,
            'total_schedule_variance': total_schedule_variance,
            'top_risk_contributors': [r['risk_id'] for r in risk_rankings[:5]]
        }