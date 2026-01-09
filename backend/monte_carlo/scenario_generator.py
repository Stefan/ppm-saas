"""
Scenario Generator - Creates and manages different risk scenarios for comparative analysis.

This module provides functionality for:
- Creating scenarios with modified risk parameters
- Comparing multiple scenarios
- Evaluating mitigation strategies
- Performing sensitivity analysis
"""

import copy
from typing import Dict, List, Optional, Tuple, Any
import uuid
from datetime import datetime

from .models import (
    Risk, Scenario, RiskModification, MitigationStrategy, MitigationAnalysis,
    ProbabilityDistribution, DistributionType, ScenarioComparison,
    SimulationResults, ValidationResult
)


class ScenarioGenerator:
    """
    Creates and manages different risk scenarios for comparative analysis.
    
    This class provides capabilities for:
    - Creating scenarios with individual risk parameter modifications
    - Ensuring scenario isolation to prevent cross-contamination
    - Evaluating mitigation strategies with cost-effectiveness analysis
    - Performing sensitivity analysis for external factors
    """
    
    def __init__(self):
        """Initialize the scenario generator."""
        self._scenarios: Dict[str, Scenario] = {}
    
    def create_scenario(self, 
                       base_risks: List[Risk], 
                       modifications: Dict[str, RiskModification],
                       name: str,
                       description: str = "") -> Scenario:
        """
        Create a new scenario with modified risk parameters.
        
        Args:
            base_risks: List of base risks to use as foundation
            modifications: Dictionary mapping risk IDs to their modifications
            name: Name for the scenario
            description: Optional description of the scenario
            
        Returns:
            Scenario: New scenario with applied modifications
            
        Raises:
            ValueError: If modifications reference non-existent risks
        """
        # Validate that all modifications reference existing risks
        risk_ids = {risk.id for risk in base_risks}
        for risk_id in modifications.keys():
            if risk_id not in risk_ids:
                raise ValueError(f"Modification references non-existent risk: {risk_id}")
        
        # Create deep copies of risks to ensure isolation
        scenario_risks = []
        for risk in base_risks:
            # Deep copy the risk to prevent cross-contamination
            risk_copy = copy.deepcopy(risk)
            
            # Apply modifications if they exist for this risk
            if risk.id in modifications:
                modification = modifications[risk.id]
                risk_copy = self._apply_risk_modification(risk_copy, modification)
            
            scenario_risks.append(risk_copy)
        
        # Create the scenario
        scenario_id = str(uuid.uuid4())
        scenario = Scenario(
            id=scenario_id,
            name=name,
            description=description,
            risks=scenario_risks,
            modifications=copy.deepcopy(modifications)
        )
        
        # Store the scenario
        self._scenarios[scenario_id] = scenario
        
        return scenario
    
    def _apply_risk_modification(self, risk: Risk, modification: RiskModification) -> Risk:
        """
        Apply a modification to a risk.
        
        Args:
            risk: Risk to modify
            modification: Modification to apply
            
        Returns:
            Risk: Modified risk
        """
        # Apply distribution parameter changes
        if modification.parameter_changes:
            new_parameters = risk.probability_distribution.parameters.copy()
            
            # Handle distribution-specific parameter constraints
            if risk.probability_distribution.distribution_type == DistributionType.TRIANGULAR:
                # Apply changes while maintaining min <= mode <= max constraint
                for param_name, new_value in modification.parameter_changes.items():
                    if param_name == 'min':
                        # Ensure min doesn't exceed mode
                        mode_val = new_parameters.get('mode', new_value + 1)
                        new_parameters[param_name] = min(new_value, mode_val - 0.1)
                    elif param_name == 'max':
                        # Ensure max is at least mode
                        mode_val = new_parameters.get('mode', new_value - 1)
                        new_parameters[param_name] = max(new_value, mode_val + 0.1)
                    elif param_name == 'mode':
                        # Ensure mode is between min and max
                        min_val = new_parameters.get('min', 0)
                        max_val = new_parameters.get('max', new_value + 10)
                        new_parameters[param_name] = max(min_val, min(new_value, max_val))
                    else:
                        new_parameters[param_name] = new_value
                        
            elif risk.probability_distribution.distribution_type == DistributionType.UNIFORM:
                # Apply changes while maintaining min < max constraint
                for param_name, new_value in modification.parameter_changes.items():
                    if param_name == 'min':
                        # Ensure min is less than max
                        max_val = new_parameters.get('max', new_value + 10)
                        new_parameters[param_name] = min(new_value, max_val - 0.1)
                    elif param_name == 'max':
                        # Ensure max is greater than min
                        min_val = new_parameters.get('min', new_value - 10)
                        new_parameters[param_name] = max(new_value, min_val + 0.1)
                    else:
                        new_parameters[param_name] = new_value
                        
            else:
                # For other distributions (normal, beta, lognormal), apply changes directly
                new_parameters.update(modification.parameter_changes)
            
            # Create new distribution with updated parameters
            distribution_type = (modification.distribution_type_change 
                               if modification.distribution_type_change 
                               else risk.probability_distribution.distribution_type)
            
            risk.probability_distribution = ProbabilityDistribution(
                distribution_type=distribution_type,
                parameters=new_parameters,
                bounds=risk.probability_distribution.bounds
            )
        
        # Apply distribution type change if specified
        elif modification.distribution_type_change:
            # Keep existing parameters but change type (may need parameter mapping)
            risk.probability_distribution = ProbabilityDistribution(
                distribution_type=modification.distribution_type_change,
                parameters=risk.probability_distribution.parameters,
                bounds=risk.probability_distribution.bounds
            )
        
        # Apply mitigation strategy if specified
        if modification.mitigation_applied:
            # Find the mitigation strategy
            mitigation = None
            for strategy in risk.mitigation_strategies:
                if strategy.id == modification.mitigation_applied:
                    mitigation = strategy
                    break
            
            if mitigation:
                # Apply mitigation effectiveness to reduce risk impact
                risk.baseline_impact *= (1.0 - mitigation.effectiveness)
                
                # Optionally modify distribution parameters to reflect mitigation
                if risk.probability_distribution.distribution_type == DistributionType.TRIANGULAR:
                    params = risk.probability_distribution.parameters
                    reduction_factor = (1.0 - mitigation.effectiveness)
                    params['max'] *= reduction_factor
                    params['mode'] *= reduction_factor
                    # Keep min the same or reduce it less
                    params['min'] *= max(0.5, reduction_factor)
        
        return risk
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        Retrieve a scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to retrieve
            
        Returns:
            Scenario or None if not found
        """
        return self._scenarios.get(scenario_id)
    
    def list_scenarios(self) -> List[Scenario]:
        """
        Get all created scenarios.
        
        Returns:
            List of all scenarios
        """
        return list(self._scenarios.values())
    
    def validate_scenario_isolation(self, scenario_a: Scenario, scenario_b: Scenario) -> ValidationResult:
        """
        Validate that two scenarios are properly isolated (no cross-contamination).
        
        Args:
            scenario_a: First scenario
            scenario_b: Second scenario
            
        Returns:
            ValidationResult: Validation results
        """
        errors = []
        warnings = []
        
        # Check that risks are independent objects (not shared references)
        for risk_a in scenario_a.risks:
            for risk_b in scenario_b.risks:
                if risk_a.id == risk_b.id:
                    # Same risk ID - check if they're the same object (bad)
                    if risk_a is risk_b:
                        errors.append(f"Risk {risk_a.id} is shared between scenarios (not isolated)")
                    
                    # Check if probability distributions are shared objects
                    if risk_a.probability_distribution is risk_b.probability_distribution:
                        errors.append(f"Risk {risk_a.id} shares probability distribution object between scenarios")
                    
                    # Check if mitigation strategies are shared objects
                    for strat_a in risk_a.mitigation_strategies:
                        for strat_b in risk_b.mitigation_strategies:
                            if strat_a.id == strat_b.id and strat_a is strat_b:
                                warnings.append(f"Mitigation strategy {strat_a.id} is shared between scenarios")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def create_baseline_scenario(self, risks: List[Risk], name: str = "Baseline") -> Scenario:
        """
        Create a baseline scenario with no modifications.
        
        Args:
            risks: List of risks for the baseline
            name: Name for the baseline scenario
            
        Returns:
            Scenario: Baseline scenario
        """
        return self.create_scenario(
            base_risks=risks,
            modifications={},
            name=name,
            description="Baseline scenario with no risk modifications"
        )
    
    def evaluate_mitigation_strategy(self, 
                                   base_scenario: Scenario, 
                                   mitigation: MitigationStrategy,
                                   target_risk_id: str) -> MitigationAnalysis:
        """
        Evaluate the cost-effectiveness of a mitigation strategy.
        
        Args:
            base_scenario: Baseline scenario to compare against
            mitigation: Mitigation strategy to evaluate
            target_risk_id: ID of the risk to apply mitigation to
            
        Returns:
            MitigationAnalysis: Analysis of mitigation effectiveness
            
        Raises:
            ValueError: If target risk not found or mitigation not applicable
        """
        # Find the target risk
        target_risk = None
        for risk in base_scenario.risks:
            if risk.id == target_risk_id:
                target_risk = risk
                break
        
        if not target_risk:
            raise ValueError(f"Risk {target_risk_id} not found in scenario")
        
        # Check if mitigation is applicable to this risk
        if mitigation.id not in [s.id for s in target_risk.mitigation_strategies]:
            raise ValueError(f"Mitigation {mitigation.id} not applicable to risk {target_risk_id}")
        
        # Calculate baseline risk exposure
        baseline_risk = target_risk.baseline_impact
        
        # Calculate mitigated risk exposure
        mitigated_risk = baseline_risk * (1.0 - mitigation.effectiveness)
        
        # Calculate risk reduction
        risk_reduction = baseline_risk - mitigated_risk
        
        # Calculate cost-benefit ratio
        cost_benefit_ratio = mitigation.cost / risk_reduction if risk_reduction > 0 else float('inf')
        
        # Calculate net present value (simplified - assumes immediate benefit)
        net_present_value = risk_reduction - mitigation.cost
        
        # Calculate return on investment
        return_on_investment = (risk_reduction - mitigation.cost) / mitigation.cost if mitigation.cost > 0 else float('inf')
        
        return MitigationAnalysis(
            strategy_id=mitigation.id,
            baseline_risk=baseline_risk,
            mitigated_risk=mitigated_risk,
            risk_reduction=risk_reduction,
            cost_benefit_ratio=cost_benefit_ratio,
            net_present_value=net_present_value,
            return_on_investment=return_on_investment
        )
    
    def compare_mitigation_strategies(self, 
                                    base_scenario: Scenario,
                                    target_risk_id: str) -> List[MitigationAnalysis]:
        """
        Compare all available mitigation strategies for a specific risk.
        
        Args:
            base_scenario: Baseline scenario to compare against
            target_risk_id: ID of the risk to analyze mitigations for
            
        Returns:
            List[MitigationAnalysis]: Analysis for each available mitigation strategy,
                                    sorted by return on investment (descending)
        """
        # Find the target risk
        target_risk = None
        for risk in base_scenario.risks:
            if risk.id == target_risk_id:
                target_risk = risk
                break
        
        if not target_risk:
            raise ValueError(f"Risk {target_risk_id} not found in scenario")
        
        # Evaluate each mitigation strategy
        analyses = []
        for mitigation in target_risk.mitigation_strategies:
            analysis = self.evaluate_mitigation_strategy(base_scenario, mitigation, target_risk_id)
            analyses.append(analysis)
        
        # Sort by return on investment (descending)
        analyses.sort(key=lambda x: x.return_on_investment, reverse=True)
        
        return analyses
    
    def calculate_expected_value_of_mitigation(self, 
                                             base_scenario: Scenario,
                                             mitigation: MitigationStrategy,
                                             target_risk_id: str,
                                             risk_probability: float = 1.0) -> float:
        """
        Calculate the expected value of a mitigation investment.
        
        Args:
            base_scenario: Baseline scenario
            mitigation: Mitigation strategy to evaluate
            target_risk_id: ID of the risk to mitigate
            risk_probability: Probability that the risk will occur (0.0 to 1.0)
            
        Returns:
            float: Expected value of the mitigation investment
        """
        if not 0.0 <= risk_probability <= 1.0:
            raise ValueError("Risk probability must be between 0.0 and 1.0")
        
        analysis = self.evaluate_mitigation_strategy(base_scenario, mitigation, target_risk_id)
        
        # Expected value = (probability of risk * risk reduction) - mitigation cost
        expected_value = (risk_probability * analysis.risk_reduction) - mitigation.cost
        
        return expected_value
    
    def create_mitigated_scenario(self, 
                                base_scenario: Scenario,
                                mitigation_plan: Dict[str, str],
                                name: str,
                                description: str = "") -> Scenario:
        """
        Create a scenario with multiple mitigation strategies applied.
        
        Args:
            base_scenario: Base scenario to apply mitigations to
            mitigation_plan: Dictionary mapping risk IDs to mitigation strategy IDs
            name: Name for the mitigated scenario
            description: Description of the scenario
            
        Returns:
            Scenario: New scenario with mitigations applied
        """
        modifications = {}
        
        for risk_id, mitigation_id in mitigation_plan.items():
            modifications[risk_id] = RiskModification(
                parameter_changes={},
                mitigation_applied=mitigation_id
            )
        
        return self.create_scenario(
            base_risks=base_scenario.risks,
            modifications=modifications,
            name=name,
            description=description
        )
    
    def calculate_portfolio_mitigation_value(self, 
                                           base_scenario: Scenario,
                                           mitigation_plan: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate the total value of a portfolio of mitigation strategies.
        
        Args:
            base_scenario: Base scenario
            mitigation_plan: Dictionary mapping risk IDs to mitigation strategy IDs
            
        Returns:
            Dict containing total costs, benefits, and portfolio metrics
        """
        total_cost = 0.0
        total_risk_reduction = 0.0
        individual_analyses = {}
        
        for risk_id, mitigation_id in mitigation_plan.items():
            # Find the risk and mitigation
            target_risk = next((r for r in base_scenario.risks if r.id == risk_id), None)
            if not target_risk:
                continue
                
            mitigation = next((m for m in target_risk.mitigation_strategies if m.id == mitigation_id), None)
            if not mitigation:
                continue
            
            # Analyze this mitigation
            analysis = self.evaluate_mitigation_strategy(base_scenario, mitigation, risk_id)
            individual_analyses[risk_id] = analysis
            
            total_cost += mitigation.cost
            total_risk_reduction += analysis.risk_reduction
        
        # Calculate portfolio metrics
        portfolio_cost_benefit_ratio = total_cost / total_risk_reduction if total_risk_reduction > 0 else float('inf')
        portfolio_net_present_value = total_risk_reduction - total_cost
        portfolio_roi = (total_risk_reduction - total_cost) / total_cost if total_cost > 0 else float('inf')
        
        return {
            'total_cost': total_cost,
            'total_risk_reduction': total_risk_reduction,
            'portfolio_cost_benefit_ratio': portfolio_cost_benefit_ratio,
            'portfolio_net_present_value': portfolio_net_present_value,
            'portfolio_roi': portfolio_roi,
            'individual_analyses': individual_analyses
        }
    
    def perform_sensitivity_analysis(self, 
                                    base_scenario: Scenario,
                                    target_variables: List[str],
                                    variation_range: float = 0.2) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on key variables to assess their impact.
        
        Args:
            base_scenario: Base scenario to analyze
            target_variables: List of variable names to analyze (risk IDs or parameter names)
            variation_range: Percentage variation to apply (e.g., 0.2 for ±20%)
            
        Returns:
            Dict containing sensitivity analysis results
        """
        if not 0.0 < variation_range <= 1.0:
            raise ValueError("Variation range must be between 0.0 and 1.0")
        
        sensitivity_results = {}
        
        for variable in target_variables:
            # Find the risk that matches this variable
            target_risk = None
            for risk in base_scenario.risks:
                if risk.id == variable:
                    target_risk = risk
                    break
            
            if not target_risk:
                # Skip variables that don't match any risk
                continue
            
            # Perform sensitivity analysis on this risk's baseline impact
            baseline_impact = target_risk.baseline_impact
            
            # Create scenarios with varied impact values
            low_value = baseline_impact * (1.0 - variation_range)
            high_value = baseline_impact * (1.0 + variation_range)
            
            # Create modified scenarios
            low_scenario = self._create_impact_modified_scenario(
                base_scenario, variable, low_value, f"{variable}_low"
            )
            high_scenario = self._create_impact_modified_scenario(
                base_scenario, variable, high_value, f"{variable}_high"
            )
            
            # Calculate sensitivity metrics
            impact_change = high_value - low_value
            sensitivity_ratio = impact_change / baseline_impact if baseline_impact != 0 else 0
            
            sensitivity_results[variable] = {
                'baseline_value': baseline_impact,
                'low_value': low_value,
                'high_value': high_value,
                'variation_range': variation_range,
                'absolute_change': impact_change,
                'sensitivity_ratio': sensitivity_ratio,
                'low_scenario': low_scenario,
                'high_scenario': high_scenario
            }
        
        return sensitivity_results
    
    def _create_impact_modified_scenario(self, 
                                       base_scenario: Scenario,
                                       risk_id: str,
                                       new_impact: float,
                                       scenario_name: str) -> Scenario:
        """
        Create a scenario with modified baseline impact for a specific risk.
        
        Args:
            base_scenario: Base scenario
            risk_id: ID of risk to modify
            new_impact: New baseline impact value
            scenario_name: Name for the new scenario
            
        Returns:
            Scenario: New scenario with modified impact
        """
        # Create deep copy of risks
        modified_risks = copy.deepcopy(base_scenario.risks)
        
        # Find and modify the target risk
        for risk in modified_risks:
            if risk.id == risk_id:
                risk.baseline_impact = new_impact
                break
        
        # Create new scenario
        scenario_id = str(uuid.uuid4())
        return Scenario(
            id=scenario_id,
            name=scenario_name,
            description=f"Sensitivity analysis scenario with {risk_id} impact = {new_impact}",
            risks=modified_risks
        )
    
    def calculate_parameter_impact_assessment(self, 
                                            base_scenario: Scenario,
                                            parameter_variations: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Assess the impact of parameter changes on scenario outcomes.
        
        Args:
            base_scenario: Base scenario
            parameter_variations: Dict mapping risk_id -> {param_name: new_value}
            
        Returns:
            Dict containing impact assessment results
        """
        impact_assessment = {}
        
        for risk_id, param_changes in parameter_variations.items():
            # Find the target risk
            target_risk = None
            for risk in base_scenario.risks:
                if risk.id == risk_id:
                    target_risk = risk
                    break
            
            if not target_risk:
                continue
            
            # Create scenario with parameter modifications
            modifications = {
                risk_id: RiskModification(parameter_changes=param_changes)
            }
            
            modified_scenario = self.create_scenario(
                base_risks=base_scenario.risks,
                modifications=modifications,
                name=f"Parameter_Impact_{risk_id}",
                description=f"Parameter impact assessment for {risk_id}"
            )
            
            # Calculate impact metrics
            original_params = target_risk.probability_distribution.parameters
            modified_risk = next(r for r in modified_scenario.risks if r.id == risk_id)
            modified_params = modified_risk.probability_distribution.parameters
            
            # Calculate parameter change magnitudes
            param_changes_magnitude = {}
            for param_name, new_value in param_changes.items():
                if param_name in original_params:
                    original_value = original_params[param_name]
                    if original_value != 0:
                        relative_change = (new_value - original_value) / original_value
                    else:
                        relative_change = float('inf') if new_value != 0 else 0
                    
                    param_changes_magnitude[param_name] = {
                        'original_value': original_value,
                        'new_value': new_value,
                        'absolute_change': new_value - original_value,
                        'relative_change': relative_change
                    }
            
            impact_assessment[risk_id] = {
                'modified_scenario': modified_scenario,
                'parameter_changes': param_changes_magnitude,
                'baseline_impact': target_risk.baseline_impact,
                'modified_baseline_impact': modified_risk.baseline_impact
            }
        
        return impact_assessment
    
    def identify_high_impact_parameters(self, 
                                      sensitivity_results: Dict[str, Any],
                                      threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Identify parameters with high impact on scenario outcomes.
        
        Args:
            sensitivity_results: Results from perform_sensitivity_analysis
            threshold: Minimum sensitivity ratio to be considered high impact
            
        Returns:
            List of high-impact parameters sorted by sensitivity ratio
        """
        high_impact_params = []
        
        for variable, results in sensitivity_results.items():
            sensitivity_ratio = results.get('sensitivity_ratio', 0)
            
            if abs(sensitivity_ratio) >= threshold:
                high_impact_params.append({
                    'variable': variable,
                    'sensitivity_ratio': sensitivity_ratio,
                    'baseline_value': results.get('baseline_value', 0),
                    'absolute_change': results.get('absolute_change', 0),
                    'impact_level': 'high' if abs(sensitivity_ratio) >= 0.5 else 'medium'
                })
        
        # Sort by absolute sensitivity ratio (descending)
        high_impact_params.sort(key=lambda x: abs(x['sensitivity_ratio']), reverse=True)
        
        return high_impact_params
    
    def generate_tornado_diagram_data(self, 
                                    sensitivity_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for tornado diagram visualization of sensitivity analysis.
        
        Args:
            sensitivity_results: Results from perform_sensitivity_analysis
            
        Returns:
            Dict containing tornado diagram data
        """
        tornado_data = {
            'variables': [],
            'low_impacts': [],
            'high_impacts': [],
            'ranges': [],
            'baseline_values': []
        }
        
        # Sort variables by sensitivity (absolute value)
        sorted_variables = sorted(
            sensitivity_results.items(),
            key=lambda x: abs(x[1].get('sensitivity_ratio', 0)),
            reverse=True
        )
        
        for variable, results in sorted_variables:
            tornado_data['variables'].append(variable)
            tornado_data['low_impacts'].append(results.get('low_value', 0))
            tornado_data['high_impacts'].append(results.get('high_value', 0))
            tornado_data['ranges'].append(results.get('absolute_change', 0))
            tornado_data['baseline_values'].append(results.get('baseline_value', 0))
        
        return tornado_data
    
    def perform_multi_variable_sensitivity(self, 
                                         base_scenario: Scenario,
                                         variable_combinations: List[Dict[str, float]],
                                         scenario_name_prefix: str = "MultiVar") -> Dict[str, Any]:
        """
        Perform sensitivity analysis on multiple variables simultaneously.
        
        Args:
            base_scenario: Base scenario
            variable_combinations: List of dicts mapping risk_id -> impact_multiplier
            scenario_name_prefix: Prefix for generated scenario names
            
        Returns:
            Dict containing multi-variable sensitivity results
        """
        multi_var_results = {}
        
        for i, combination in enumerate(variable_combinations):
            scenario_name = f"{scenario_name_prefix}_{i}"
            
            # Create modified risks with combined changes
            modified_risks = copy.deepcopy(base_scenario.risks)
            
            applied_changes = {}
            for risk_id, multiplier in combination.items():
                for risk in modified_risks:
                    if risk.id == risk_id:
                        original_impact = risk.baseline_impact
                        new_impact = original_impact * multiplier
                        risk.baseline_impact = new_impact
                        
                        applied_changes[risk_id] = {
                            'original_impact': original_impact,
                            'multiplier': multiplier,
                            'new_impact': new_impact
                        }
                        break
            
            # Create scenario with combined modifications
            scenario_id = str(uuid.uuid4())
            combined_scenario = Scenario(
                id=scenario_id,
                name=scenario_name,
                description=f"Multi-variable sensitivity scenario {i}",
                risks=modified_risks
            )
            
            # Calculate combined impact metrics
            total_baseline_impact = sum(r.baseline_impact for r in base_scenario.risks)
            total_modified_impact = sum(r.baseline_impact for r in modified_risks)
            
            multi_var_results[scenario_name] = {
                'scenario': combined_scenario,
                'applied_changes': applied_changes,
                'total_baseline_impact': total_baseline_impact,
                'total_modified_impact': total_modified_impact,
                'total_impact_change': total_modified_impact - total_baseline_impact,
                'relative_change': ((total_modified_impact - total_baseline_impact) / total_baseline_impact 
                                  if total_baseline_impact != 0 else 0)
            }
        
        return multi_var_results