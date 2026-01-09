"""
Cost Escalation Module - Time-based cost escalation modeling.

This module implements inflation and currency risk factors for Monte Carlo simulations,
providing time-based cost escalation calculations as required by Requirements 4.5.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .models import ProbabilityDistribution, DistributionType


class EscalationFactorType(Enum):
    """Types of cost escalation factors."""
    INFLATION = "inflation"
    CURRENCY = "currency"
    MATERIAL = "material"
    LABOR = "labor"
    FUEL = "fuel"


@dataclass
class EscalationFactor:
    """
    Represents a time-based cost escalation factor.
    
    Attributes:
        factor_type: Type of escalation factor
        annual_rate: Annual escalation rate (as decimal, e.g., 0.03 for 3%)
        distribution: Probability distribution for the escalation rate
        start_date: Start date for escalation calculations
        compound_frequency: How often escalation compounds (monthly, quarterly, annually)
        category_weights: Weights for different cost categories affected by this factor
    """
    factor_type: EscalationFactorType
    annual_rate: float
    distribution: Optional[ProbabilityDistribution] = None
    start_date: Optional[datetime] = None
    compound_frequency: str = "annually"  # monthly, quarterly, annually
    category_weights: Optional[Dict[str, float]] = None


@dataclass
class CostEscalationResult:
    """
    Result of cost escalation calculation.
    
    Attributes:
        base_cost: Original cost before escalation
        escalated_cost: Cost after applying escalation factors
        escalation_amount: Total escalation amount
        escalation_by_factor: Breakdown of escalation by factor type
        time_period_months: Time period over which escalation was applied
    """
    base_cost: float
    escalated_cost: float
    escalation_amount: float
    escalation_by_factor: Dict[EscalationFactorType, float]
    time_period_months: float


class CostEscalationModeler:
    """
    Models time-based cost escalation including inflation and currency risk factors.
    
    Implements Requirements 4.5: When inflation or currency risks exist, 
    the Monte Carlo Engine shall incorporate time-based cost escalation factors into simulations.
    """
    
    def __init__(self):
        """Initialize the cost escalation modeler."""
        self.escalation_factors: List[EscalationFactor] = []
        self.default_factors = self._create_default_factors()
        self._removed_default_factors: set = set()  # Track removed default factors
    
    def _create_default_factors(self) -> Dict[EscalationFactorType, EscalationFactor]:
        """Create default escalation factors for common scenarios."""
        return {
            EscalationFactorType.INFLATION: EscalationFactor(
                factor_type=EscalationFactorType.INFLATION,
                annual_rate=0.025,  # 2.5% default inflation
                distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': 0.025, 'std': 0.01},
                    bounds=(0.0, 0.10)
                ),
                compound_frequency="annually"
            ),
            EscalationFactorType.CURRENCY: EscalationFactor(
                factor_type=EscalationFactorType.CURRENCY,
                annual_rate=0.0,  # Neutral default
                distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': 0.0, 'std': 0.05},
                    bounds=(-0.20, 0.20)
                ),
                compound_frequency="monthly"
            ),
            EscalationFactorType.MATERIAL: EscalationFactor(
                factor_type=EscalationFactorType.MATERIAL,
                annual_rate=0.035,  # 3.5% material escalation
                distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.TRIANGULAR,
                    parameters={'min': 0.01, 'mode': 0.035, 'max': 0.08},
                    bounds=(0.0, 0.15)
                ),
                compound_frequency="quarterly"
            ),
            EscalationFactorType.LABOR: EscalationFactor(
                factor_type=EscalationFactorType.LABOR,
                annual_rate=0.03,  # 3% labor escalation
                distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.TRIANGULAR,
                    parameters={'min': 0.015, 'mode': 0.03, 'max': 0.06},
                    bounds=(0.0, 0.10)
                ),
                compound_frequency="annually"
            )
        }
    
    def add_escalation_factor(self, factor: EscalationFactor):
        """
        Add a custom escalation factor.
        
        Args:
            factor: EscalationFactor to add
        """
        self.escalation_factors.append(factor)
    
    def remove_escalation_factor(self, factor_type: EscalationFactorType):
        """
        Remove escalation factors of a specific type.
        
        Args:
            factor_type: Type of escalation factor to remove
        """
        # Remove custom factors
        self.escalation_factors = [
            f for f in self.escalation_factors 
            if f.factor_type != factor_type
        ]
        
        # Mark default factor as removed
        self._removed_default_factors.add(factor_type)
    
    def get_active_factors(self) -> List[EscalationFactor]:
        """
        Get all active escalation factors (custom + defaults not overridden).
        
        Returns:
            List of active EscalationFactor objects
        """
        active_factors = []
        custom_types = {f.factor_type for f in self.escalation_factors}
        
        # Add custom factors
        active_factors.extend(self.escalation_factors)
        
        # Add default factors not overridden by custom ones and not explicitly removed
        for factor_type, default_factor in self.default_factors.items():
            if factor_type not in custom_types and factor_type not in self._removed_default_factors:
                active_factors.append(default_factor)
        
        return active_factors
    
    def calculate_escalation(
        self,
        base_cost: float,
        start_date: datetime,
        end_date: datetime,
        cost_categories: Optional[Dict[str, float]] = None,
        random_state: Optional[np.random.RandomState] = None
    ) -> CostEscalationResult:
        """
        Calculate time-based cost escalation for a given period.
        
        Args:
            base_cost: Base cost before escalation
            start_date: Start date for escalation calculation
            end_date: End date for escalation calculation
            cost_categories: Optional breakdown of costs by category
            random_state: Optional random state for sampling
            
        Returns:
            CostEscalationResult with escalated costs and breakdown
        """
        if random_state is None:
            random_state = np.random.RandomState()
        
        # Calculate time period
        time_delta = end_date - start_date
        time_period_months = time_delta.days / 30.44  # Average days per month
        time_period_years = time_period_months / 12.0
        
        if time_period_years <= 0:
            # No escalation for zero or negative time periods
            return CostEscalationResult(
                base_cost=base_cost,
                escalated_cost=base_cost,
                escalation_amount=0.0,
                escalation_by_factor={},
                time_period_months=time_period_months
            )
        
        # Get active escalation factors
        active_factors = self.get_active_factors()
        
        # Initialize escalation tracking
        escalation_by_factor = {}
        total_escalated_cost = base_cost
        
        # Apply each escalation factor
        for factor in active_factors:
            factor_escalation = self._apply_single_factor(
                cost=base_cost,  # Apply to base cost, not escalated cost
                factor=factor,
                time_period_years=time_period_years,
                cost_categories=cost_categories,
                random_state=random_state
            )
            
            escalation_by_factor[factor.factor_type] = factor_escalation
            total_escalated_cost += factor_escalation
        
        # Calculate total escalation amount
        total_escalation = total_escalated_cost - base_cost
        
        return CostEscalationResult(
            base_cost=base_cost,
            escalated_cost=total_escalated_cost,
            escalation_amount=total_escalation,
            escalation_by_factor=escalation_by_factor,
            time_period_months=time_period_months
        )
    
    def _apply_single_factor(
        self,
        cost: float,
        factor: EscalationFactor,
        time_period_years: float,
        cost_categories: Optional[Dict[str, float]] = None,
        random_state: np.random.RandomState = None
    ) -> float:
        """
        Apply a single escalation factor to a cost.
        
        Args:
            cost: Cost to escalate
            factor: EscalationFactor to apply
            time_period_years: Time period in years
            cost_categories: Optional cost category breakdown
            random_state: Random state for sampling
            
        Returns:
            Escalation amount for this factor
        """
        # Sample escalation rate from distribution if available
        if factor.distribution:
            sampled_rate = factor.distribution.sample(1, random_state)[0]
        else:
            sampled_rate = factor.annual_rate
        
        # Ensure rate is within reasonable bounds
        sampled_rate = max(-0.50, min(sampled_rate, 1.0))  # -50% to 100% annual rate
        
        # Calculate effective cost based on category weights
        effective_cost = cost
        if factor.category_weights and cost_categories:
            # Apply factor only to relevant cost categories
            weighted_cost = 0.0
            for category, category_cost in cost_categories.items():
                weight = factor.category_weights.get(category, 0.0)
                weighted_cost += category_cost * weight
            effective_cost = weighted_cost
        
        # Calculate compound escalation based on frequency
        if factor.compound_frequency == "monthly":
            periods_per_year = 12
        elif factor.compound_frequency == "quarterly":
            periods_per_year = 4
        else:  # annually
            periods_per_year = 1
        
        # Convert annual rate to period rate
        period_rate = sampled_rate / periods_per_year
        total_periods = time_period_years * periods_per_year
        
        # Calculate compound escalation
        if abs(period_rate) < 1e-10:  # Avoid division by zero for very small rates
            escalation_multiplier = total_periods * period_rate
        else:
            escalation_multiplier = (1 + period_rate) ** total_periods - 1
        
        # Calculate escalation amount
        escalation_amount = effective_cost * escalation_multiplier
        
        return escalation_amount
    
    def simulate_escalation_scenarios(
        self,
        base_cost: float,
        start_date: datetime,
        end_date: datetime,
        num_scenarios: int = 1000,
        cost_categories: Optional[Dict[str, float]] = None,
        random_seed: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Simulate multiple escalation scenarios for Monte Carlo analysis.
        
        Args:
            base_cost: Base cost before escalation
            start_date: Start date for escalation
            end_date: End date for escalation
            num_scenarios: Number of scenarios to simulate
            cost_categories: Optional cost category breakdown
            random_seed: Optional random seed for reproducibility
            
        Returns:
            Dictionary containing arrays of escalated costs and factor contributions
        """
        random_state = np.random.RandomState(random_seed)
        
        # Initialize result arrays
        escalated_costs = np.zeros(num_scenarios)
        escalation_amounts = np.zeros(num_scenarios)
        
        # Initialize factor contribution arrays
        active_factors = self.get_active_factors()
        factor_contributions = {
            factor.factor_type: np.zeros(num_scenarios) 
            for factor in active_factors
        }
        
        # Run scenarios
        for i in range(num_scenarios):
            result = self.calculate_escalation(
                base_cost=base_cost,
                start_date=start_date,
                end_date=end_date,
                cost_categories=cost_categories,
                random_state=random_state
            )
            
            escalated_costs[i] = result.escalated_cost
            escalation_amounts[i] = result.escalation_amount
            
            for factor_type, contribution in result.escalation_by_factor.items():
                factor_contributions[factor_type][i] = contribution
        
        return {
            'escalated_costs': escalated_costs,
            'escalation_amounts': escalation_amounts,
            'base_cost': base_cost,
            'factor_contributions': factor_contributions,
            'time_period_months': (end_date - start_date).days / 30.44
        }
    
    def get_escalation_summary(
        self,
        base_cost: float,
        start_date: datetime,
        end_date: datetime,
        confidence_levels: List[float] = [0.80, 0.90, 0.95]
    ) -> Dict[str, any]:
        """
        Get a statistical summary of escalation impacts.
        
        Args:
            base_cost: Base cost before escalation
            start_date: Start date for escalation
            end_date: End date for escalation
            confidence_levels: Confidence levels for interval calculations
            
        Returns:
            Dictionary containing escalation summary statistics
        """
        # Run simulation scenarios
        scenarios = self.simulate_escalation_scenarios(
            base_cost=base_cost,
            start_date=start_date,
            end_date=end_date,
            num_scenarios=10000
        )
        
        escalated_costs = scenarios['escalated_costs']
        escalation_amounts = scenarios['escalation_amounts']
        
        # Calculate summary statistics
        summary = {
            'base_cost': base_cost,
            'time_period_months': scenarios['time_period_months'],
            'escalation_statistics': {
                'mean': float(np.mean(escalation_amounts)),
                'std': float(np.std(escalation_amounts)),
                'min': float(np.min(escalation_amounts)),
                'max': float(np.max(escalation_amounts)),
                'median': float(np.median(escalation_amounts))
            },
            'escalated_cost_statistics': {
                'mean': float(np.mean(escalated_costs)),
                'std': float(np.std(escalated_costs)),
                'min': float(np.min(escalated_costs)),
                'max': float(np.max(escalated_costs)),
                'median': float(np.median(escalated_costs))
            },
            'percentiles': {},
            'confidence_intervals': {},
            'factor_contributions': {}
        }
        
        # Calculate percentiles
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            summary['percentiles'][f'P{p}'] = float(np.percentile(escalated_costs, p))
        
        # Calculate confidence intervals
        for confidence in confidence_levels:
            alpha = 1 - confidence
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_bound = np.percentile(escalated_costs, lower_percentile)
            upper_bound = np.percentile(escalated_costs, upper_percentile)
            
            summary['confidence_intervals'][f'{int(confidence*100)}%'] = {
                'lower': float(lower_bound),
                'upper': float(upper_bound),
                'range': float(upper_bound - lower_bound)
            }
        
        # Calculate factor contribution statistics
        for factor_type, contributions in scenarios['factor_contributions'].items():
            summary['factor_contributions'][factor_type.value] = {
                'mean': float(np.mean(contributions)),
                'std': float(np.std(contributions)),
                'contribution_percentage': float(np.mean(contributions) / np.mean(escalation_amounts) * 100) if np.mean(escalation_amounts) != 0 else 0.0
            }
        
        return summary
    
    def validate_escalation_factors(self) -> List[str]:
        """
        Validate all escalation factors for consistency and reasonableness.
        
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        active_factors = self.get_active_factors()
        
        for factor in active_factors:
            # Check for reasonable annual rates
            if abs(factor.annual_rate) > 0.50:  # More than 50% annual rate
                warnings.append(
                    f"{factor.factor_type.value} has extreme annual rate: {factor.annual_rate:.1%}"
                )
            
            # Check distribution parameters if present
            if factor.distribution:
                try:
                    # Test sampling from distribution
                    test_samples = factor.distribution.sample(100)
                    if not np.all(np.isfinite(test_samples)):
                        warnings.append(
                            f"{factor.factor_type.value} distribution produces non-finite samples"
                        )
                    
                    # Check for extreme values
                    if np.any(test_samples < -1.0) or np.any(test_samples > 2.0):
                        warnings.append(
                            f"{factor.factor_type.value} distribution produces extreme values"
                        )
                        
                except Exception as e:
                    warnings.append(
                        f"{factor.factor_type.value} distribution error: {str(e)}"
                    )
            
            # Check category weights if present
            if factor.category_weights:
                total_weight = sum(factor.category_weights.values())
                if total_weight > 1.1:  # Allow small tolerance
                    warnings.append(
                        f"{factor.factor_type.value} category weights sum to {total_weight:.2f} (>1.0)"
                    )
                
                for category, weight in factor.category_weights.items():
                    if weight < 0 or weight > 1:
                        warnings.append(
                            f"{factor.factor_type.value} has invalid weight for {category}: {weight}"
                        )
        
        return warnings