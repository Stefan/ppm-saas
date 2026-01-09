"""
Simulation Results Analyzer - Processes simulation outputs and generates statistical insights.

This module provides comprehensive statistical analysis of Monte Carlo simulation results,
including percentile calculations, confidence intervals, risk contribution analysis,
and scenario comparison capabilities.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy import stats
from .models import (
    SimulationResults, PercentileAnalysis, ConfidenceIntervals, 
    RiskContribution, ScenarioComparison
)


class SimulationResultsAnalyzer:
    """
    Processes simulation outputs and generates statistical insights.
    
    This class provides methods for calculating percentiles, confidence intervals,
    identifying risk contributors, and comparing scenarios.
    """
    
    def __init__(self):
        """Initialize the results analyzer."""
        self.standard_percentiles = [10, 25, 50, 75, 90, 95, 99]
        self.standard_confidence_levels = [0.80, 0.90, 0.95]
    
    def calculate_percentiles(self, results: SimulationResults, 
                            outcome_type: str = 'cost') -> PercentileAnalysis:
        """
        Calculate key percentiles and statistical measures for simulation results.
        
        Args:
            results: SimulationResults object containing simulation data
            outcome_type: 'cost' or 'schedule' to specify which outcomes to analyze
            
        Returns:
            PercentileAnalysis object with percentiles and statistical measures
            
        Raises:
            ValueError: If outcome_type is not 'cost' or 'schedule'
        """
        if outcome_type == 'cost':
            data = results.cost_outcomes
        elif outcome_type == 'schedule':
            data = results.schedule_outcomes
        else:
            raise ValueError("outcome_type must be 'cost' or 'schedule'")
        
        # Calculate percentiles
        percentiles = {}
        for p in self.standard_percentiles:
            percentiles[p] = np.percentile(data, p)
        
        # Calculate statistical measures
        mean = np.mean(data)
        median = np.median(data)
        
        # Handle single-value case for standard deviation
        if len(data) <= 1:
            std_dev = 0.0
        else:
            std_dev = np.std(data, ddof=1)  # Sample standard deviation
        
        coefficient_of_variation = std_dev / mean if mean != 0 else 0
        
        return PercentileAnalysis(
            percentiles=percentiles,
            mean=mean,
            median=median,
            std_dev=std_dev,
            coefficient_of_variation=coefficient_of_variation
        )
    
    def generate_confidence_intervals(self, results: SimulationResults,
                                    outcome_type: str = 'cost',
                                    confidence_levels: Optional[List[float]] = None) -> ConfidenceIntervals:
        """
        Generate confidence intervals for simulation results.
        
        Args:
            results: SimulationResults object containing simulation data
            outcome_type: 'cost' or 'schedule' to specify which outcomes to analyze
            confidence_levels: List of confidence levels (0.0 to 1.0). 
                             Defaults to [0.80, 0.90, 0.95]
            
        Returns:
            ConfidenceIntervals object with intervals for each confidence level
            
        Raises:
            ValueError: If outcome_type is not 'cost' or 'schedule'
        """
        if outcome_type == 'cost':
            data = results.cost_outcomes
        elif outcome_type == 'schedule':
            data = results.schedule_outcomes
        else:
            raise ValueError("outcome_type must be 'cost' or 'schedule'")
        
        if confidence_levels is None:
            confidence_levels = self.standard_confidence_levels
        
        intervals = {}
        for confidence_level in confidence_levels:
            # Calculate confidence interval using percentiles
            alpha = 1 - confidence_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_bound = np.percentile(data, lower_percentile)
            upper_bound = np.percentile(data, upper_percentile)
            
            intervals[confidence_level] = (lower_bound, upper_bound)
        
        return ConfidenceIntervals(
            intervals=intervals,
            sample_size=len(data)
        )
    
    def calculate_expected_values_and_variation(self, results: SimulationResults) -> Dict[str, Dict[str, float]]:
        """
        Calculate expected values, standard deviations, and coefficient of variation
        for both cost and schedule outcomes.
        
        Args:
            results: SimulationResults object containing simulation data
            
        Returns:
            Dictionary with statistical measures for cost and schedule outcomes
        """
        statistics = {}
        
        for outcome_type, data in [('cost', results.cost_outcomes), 
                                  ('schedule', results.schedule_outcomes)]:
            mean = np.mean(data)
            
            # Handle single-value case for standard deviation and variance
            if len(data) <= 1:
                std_dev = 0.0
                variance = 0.0
            else:
                std_dev = np.std(data, ddof=1)
                variance = np.var(data, ddof=1)
            
            coefficient_of_variation = std_dev / mean if mean != 0 else 0
            
            statistics[outcome_type] = {
                'expected_value': mean,
                'standard_deviation': std_dev,
                'coefficient_of_variation': coefficient_of_variation,
                'variance': variance,
                'skewness': stats.skew(data) if len(data) > 1 else 0.0,
                'kurtosis': stats.kurtosis(data) if len(data) > 1 else 0.0
            }
        
        return statistics
    
    def identify_top_risk_contributors(self, results: SimulationResults, 
                                     top_n: int = 10) -> List[RiskContribution]:
        """
        Identify the top N risks contributing to overall project uncertainty.
        
        Args:
            results: SimulationResults object containing simulation data
            top_n: Number of top contributors to return (default: 10)
            
        Returns:
            List of RiskContribution objects sorted by contribution percentage
            
        Raises:
            ValueError: If top_n is not positive or results have no risk contributions
        """
        if top_n <= 0:
            raise ValueError("top_n must be positive")
        
        if not results.risk_contributions:
            raise ValueError("No risk contributions found in simulation results")
        
        # Calculate variance contribution for each risk
        total_variance = np.var(results.cost_outcomes, ddof=1)
        risk_contributions = []
        
        for risk_id, contributions in results.risk_contributions.items():
            # Calculate variance contribution of this risk
            risk_variance = np.var(contributions, ddof=1)
            
            # Calculate percentage contribution to total variance
            if total_variance > 0:
                contribution_percentage = (risk_variance / total_variance) * 100
            else:
                contribution_percentage = 0.0
            
            # Calculate correlation effects with other risks
            correlation_effects = {}
            for other_risk_id, other_contributions in results.risk_contributions.items():
                if other_risk_id != risk_id:
                    # Calculate correlation coefficient
                    correlation = np.corrcoef(contributions, other_contributions)[0, 1]
                    if not np.isnan(correlation):
                        correlation_effects[other_risk_id] = correlation
            
            risk_contributions.append(RiskContribution(
                risk_id=risk_id,
                risk_name=risk_id,  # Using ID as name for now
                contribution_percentage=contribution_percentage,
                variance_contribution=risk_variance,
                correlation_effects=correlation_effects
            ))
        
        # Sort by contribution percentage (descending) and return top N
        risk_contributions.sort(key=lambda x: x.contribution_percentage, reverse=True)
        return risk_contributions[:top_n]
    
    def calculate_risk_contribution_ranking(self, results: SimulationResults) -> Dict[str, Dict[str, float]]:
        """
        Calculate comprehensive risk contribution ranking and uncertainty attribution.
        
        Args:
            results: SimulationResults object containing simulation data
            
        Returns:
            Dictionary with detailed contribution analysis for each risk
        """
        if not results.risk_contributions:
            return {}
        
        total_cost_variance = np.var(results.cost_outcomes, ddof=1)
        total_schedule_variance = np.var(results.schedule_outcomes, ddof=1)
        
        ranking = {}
        
        for risk_id, contributions in results.risk_contributions.items():
            risk_variance = np.var(contributions, ddof=1)
            risk_mean = np.mean(contributions)
            risk_std = np.std(contributions, ddof=1)
            
            # Calculate contribution to total cost variance
            cost_contribution_pct = (risk_variance / total_cost_variance * 100) if total_cost_variance > 0 else 0
            
            # Calculate correlation with total cost outcomes
            cost_correlation = np.corrcoef(contributions, results.cost_outcomes)[0, 1]
            if np.isnan(cost_correlation):
                cost_correlation = 0.0
            
            # Calculate correlation with schedule outcomes
            schedule_correlation = np.corrcoef(contributions, results.schedule_outcomes)[0, 1]
            if np.isnan(schedule_correlation):
                schedule_correlation = 0.0
            
            # Calculate uncertainty metrics
            coefficient_of_variation = (risk_std / risk_mean) if risk_mean != 0 else 0
            
            ranking[risk_id] = {
                'variance_contribution': risk_variance,
                'contribution_percentage': cost_contribution_pct,
                'mean_impact': risk_mean,
                'standard_deviation': risk_std,
                'coefficient_of_variation': coefficient_of_variation,
                'cost_correlation': cost_correlation,
                'schedule_correlation': schedule_correlation,
                'uncertainty_index': cost_contribution_pct * abs(cost_correlation)
            }
        
        return ranking
    
    def compare_scenarios(self, scenario_a: SimulationResults, 
                         scenario_b: SimulationResults) -> ScenarioComparison:
        """
        Compare two simulation scenarios and provide statistical significance tests.
        
        Args:
            scenario_a: First simulation results to compare
            scenario_b: Second simulation results to compare
            
        Returns:
            ScenarioComparison object with statistical comparison results
            
        Raises:
            ValueError: If scenarios have different iteration counts or invalid data
        """
        if scenario_a.iteration_count != scenario_b.iteration_count:
            raise ValueError("Scenarios must have the same number of iterations for valid comparison")
        
        # Perform statistical tests for cost differences
        cost_difference = self._calculate_outcome_differences(
            scenario_a.cost_outcomes, scenario_b.cost_outcomes, "cost"
        )
        
        # Perform statistical tests for schedule differences
        schedule_difference = self._calculate_outcome_differences(
            scenario_a.schedule_outcomes, scenario_b.schedule_outcomes, "schedule"
        )
        
        return ScenarioComparison(
            scenario_a_id=scenario_a.simulation_id,
            scenario_b_id=scenario_b.simulation_id,
            cost_difference=cost_difference,
            schedule_difference=schedule_difference,
            statistical_significance=cost_difference.get('statistical_significance', {}),
            effect_size=cost_difference.get('effect_size', {})
        )
    
    def _calculate_outcome_differences(self, outcomes_a: np.ndarray, 
                                     outcomes_b: np.ndarray, 
                                     outcome_type: str) -> Dict[str, float]:
        """
        Calculate statistical differences between two outcome arrays.
        
        Args:
            outcomes_a: First set of outcomes
            outcomes_b: Second set of outcomes
            outcome_type: Type of outcome ('cost' or 'schedule')
            
        Returns:
            Dictionary with statistical measures and test results
        """
        # Basic descriptive statistics
        mean_a = np.mean(outcomes_a)
        mean_b = np.mean(outcomes_b)
        std_a = np.std(outcomes_a, ddof=1)
        std_b = np.std(outcomes_b, ddof=1)
        
        # Calculate differences
        mean_difference = mean_b - mean_a
        relative_difference = (mean_difference / mean_a * 100) if mean_a != 0 else 0
        
        # Perform two-sample t-test
        t_statistic, t_p_value = stats.ttest_ind(outcomes_a, outcomes_b, equal_var=False)
        
        # Perform Mann-Whitney U test (non-parametric alternative)
        u_statistic, u_p_value = stats.mannwhitneyu(outcomes_a, outcomes_b, alternative='two-sided')
        
        # Perform Kolmogorov-Smirnov test for distribution differences
        ks_statistic, ks_p_value = stats.ks_2samp(outcomes_a, outcomes_b)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(outcomes_a) - 1) * std_a**2 + (len(outcomes_b) - 1) * std_b**2) / 
                           (len(outcomes_a) + len(outcomes_b) - 2))
        cohens_d = mean_difference / pooled_std if pooled_std != 0 else 0
        
        # Calculate confidence interval for mean difference
        se_diff = np.sqrt(std_a**2 / len(outcomes_a) + std_b**2 / len(outcomes_b))
        df = len(outcomes_a) + len(outcomes_b) - 2
        t_critical = stats.t.ppf(0.975, df)  # 95% confidence interval
        ci_lower = mean_difference - t_critical * se_diff
        ci_upper = mean_difference + t_critical * se_diff
        
        return {
            'mean_a': mean_a,
            'mean_b': mean_b,
            'std_a': std_a,
            'std_b': std_b,
            'mean_difference': mean_difference,
            'relative_difference_percent': relative_difference,
            't_statistic': t_statistic,
            't_p_value': t_p_value,
            'mannwhitney_u_statistic': u_statistic,
            'mannwhitney_p_value': u_p_value,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'cohens_d': cohens_d,
            'confidence_interval_95': (ci_lower, ci_upper),
            'statistical_significance': {
                't_test': t_p_value,
                'mann_whitney': u_p_value,
                'kolmogorov_smirnov': ks_p_value
            },
            'effect_size': {
                'cohens_d': cohens_d,
                'mean_difference': mean_difference,
                'relative_difference': relative_difference
            }
        }
    
    def perform_scenario_difference_analysis(self, scenario_a: SimulationResults,
                                           scenario_b: SimulationResults,
                                           significance_level: float = 0.05) -> Dict[str, any]:
        """
        Perform comprehensive scenario difference analysis with interpretation.
        
        Args:
            scenario_a: First simulation results to compare
            scenario_b: Second simulation results to compare
            significance_level: Significance level for statistical tests (default: 0.05)
            
        Returns:
            Dictionary with comprehensive analysis results and interpretations
        """
        comparison = self.compare_scenarios(scenario_a, scenario_b)
        
        # Interpret statistical significance
        cost_significant = any(p_value < significance_level 
                             for p_value in comparison.cost_difference['statistical_significance'].values())
        schedule_significant = any(p_value < significance_level 
                                 for p_value in comparison.schedule_difference['statistical_significance'].values())
        
        # Interpret effect sizes (Cohen's d interpretation)
        def interpret_effect_size(cohens_d):
            abs_d = abs(cohens_d)
            if abs_d < 0.2:
                return "negligible"
            elif abs_d < 0.5:
                return "small"
            elif abs_d < 0.8:
                return "medium"
            else:
                return "large"
        
        cost_effect_interpretation = interpret_effect_size(comparison.cost_difference['cohens_d'])
        schedule_effect_interpretation = interpret_effect_size(comparison.schedule_difference['cohens_d'])
        
        return {
            'comparison_results': comparison,
            'cost_analysis': {
                'statistically_significant': bool(cost_significant),
                'effect_size_interpretation': cost_effect_interpretation,
                'practical_significance': bool(abs(comparison.cost_difference['relative_difference_percent']) > 5),
                'recommendation': self._generate_recommendation(
                    cost_significant, cost_effect_interpretation, 
                    comparison.cost_difference['relative_difference_percent']
                )
            },
            'schedule_analysis': {
                'statistically_significant': bool(schedule_significant),
                'effect_size_interpretation': schedule_effect_interpretation,
                'practical_significance': bool(abs(comparison.schedule_difference['relative_difference_percent']) > 5),
                'recommendation': self._generate_recommendation(
                    schedule_significant, schedule_effect_interpretation,
                    comparison.schedule_difference['relative_difference_percent']
                )
            },
            'overall_assessment': {
                'scenarios_differ_significantly': bool(cost_significant or schedule_significant),
                'primary_difference_type': 'cost' if cost_significant else 'schedule' if schedule_significant else 'none',
                'confidence_level': (1 - significance_level) * 100
            }
        }
    
    def _generate_recommendation(self, is_significant: bool, effect_size: str, 
                               relative_difference: float) -> str:
        """
        Generate recommendation based on statistical analysis results.
        
        Args:
            is_significant: Whether the difference is statistically significant
            effect_size: Effect size interpretation ('negligible', 'small', 'medium', 'large')
            relative_difference: Relative difference as percentage
            
        Returns:
            String recommendation for decision making
        """
        if not is_significant:
            return "No statistically significant difference detected. Scenarios are likely equivalent."
        
        direction = "higher" if relative_difference > 0 else "lower"
        
        if effect_size == "large":
            return f"Strong evidence of {direction} outcomes. Consider this scenario carefully."
        elif effect_size == "medium":
            return f"Moderate evidence of {direction} outcomes. Further analysis may be warranted."
        elif effect_size == "small":
            return f"Weak evidence of {direction} outcomes. Difference may not be practically significant."
        else:
            return f"Statistically significant but negligible practical difference."