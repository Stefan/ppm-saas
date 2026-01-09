"""
Monte Carlo Engine - Core simulation orchestrator.

This module contains the main Monte Carlo simulation engine
that coordinates between risk modeling, correlation analysis, and results processing.
"""

import time
import uuid
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

from .models import (
    Risk, SimulationResults, CorrelationMatrix, ValidationResult, 
    ProgressStatus, ConvergenceMetrics, ImpactType, DistributionType,
    ScheduleData, Milestone, Activity, ResourceConstraint, ProbabilityDistribution
)
from .simulation_config import SimulationConfig, ConfigurationManager
from .model_validator import ModelValidator
from .change_detector import ModelChangeDetector, ChangeDetectionReport, ChangeSeverity
from .cost_escalation import CostEscalationModeler, EscalationFactor, EscalationFactorType
from .distribution_outputs import DistributionOutputGenerator, BudgetComplianceResult, ScheduleComplianceResult


class MonteCarloEngine:
    """
    Central simulation orchestrator that performs statistical simulations using random sampling.
    
    The engine coordinates between risk modeling, correlation analysis, and results processing
    to execute Monte Carlo simulations with configurable parameters and performance monitoring.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize the Monte Carlo Engine with optional configuration.
        
        Args:
            config: Optional SimulationConfig. If None, uses default configuration.
        """
        self._active_simulations: Dict[str, ProgressStatus] = {}
        self._simulation_cache: Dict[str, SimulationResults] = {}
        self._parameter_cache: Dict[str, str] = {}  # simulation_id -> parameter_hash
        self._lock = threading.Lock()
        
        # Initialize configuration management
        self._config_manager = ConfigurationManager()
        self._config = config or self._config_manager.get_default_config()
        
        # Initialize model validator
        self._model_validator = ModelValidator()
        
        # Initialize change detector
        self._change_detector = ModelChangeDetector(
            sensitivity_threshold=self._config.parameter_change_sensitivity
        )
        
        # Initialize cost escalation modeler
        self._cost_escalation_modeler = CostEscalationModeler()
        
        # Initialize distribution output generator
        self._distribution_output_generator = DistributionOutputGenerator()
    
    def _generate_parameter_hash(
        self, 
        risks: List[Risk], 
        iterations: int, 
        correlations: Optional[CorrelationMatrix] = None,
        random_seed: Optional[int] = None,
        baseline_costs: Optional[Dict[str, float]] = None,
        schedule_data: Optional[ScheduleData] = None
    ) -> str:
        """
        Generate a hash of simulation parameters for caching and change detection.
        
        Args:
            risks: List of Risk objects
            iterations: Number of iterations
            correlations: Optional correlation matrix
            random_seed: Optional random seed
            baseline_costs: Optional baseline cost data
            schedule_data: Optional schedule data
            
        Returns:
            SHA-256 hash of parameters
        """
        # Create a serializable representation of parameters
        param_dict = {
            'iterations': iterations,
            'random_seed': random_seed,
            'baseline_costs': baseline_costs or {},
            'risks': []
        }
        
        # Add schedule data if present
        if schedule_data:
            param_dict['schedule_data'] = {
                'project_baseline_duration': schedule_data.project_baseline_duration,
                'milestones': [
                    {
                        'id': m.id,
                        'name': m.name,
                        'baseline_duration': m.baseline_duration,
                        'critical_path': m.critical_path,
                        'dependencies': sorted(m.dependencies)
                    } for m in schedule_data.milestones
                ],
                'activities': [
                    {
                        'id': a.id,
                        'name': a.name,
                        'baseline_duration': a.baseline_duration,
                        'earliest_start': a.earliest_start,
                        'latest_start': a.latest_start,
                        'float_time': a.float_time,
                        'critical_path': a.critical_path,
                        'resource_requirements': a.resource_requirements
                    } for a in schedule_data.activities
                ],
                'resource_constraints': [
                    {
                        'resource_id': rc.resource_id,
                        'resource_name': rc.resource_name,
                        'total_availability': rc.total_availability,
                        'utilization_limit': rc.utilization_limit,
                        'availability_periods': rc.availability_periods
                    } for rc in schedule_data.resource_constraints
                ]
            }
        
        # Serialize risks
        for risk in risks:
            risk_dict = {
                'id': risk.id,
                'name': risk.name,
                'category': risk.category.value,
                'impact_type': risk.impact_type.value,
                'baseline_impact': risk.baseline_impact,
                'distribution': {
                    'type': risk.probability_distribution.distribution_type.value,
                    'parameters': risk.probability_distribution.parameters,
                    'bounds': risk.probability_distribution.bounds
                },
                'correlation_dependencies': sorted(risk.correlation_dependencies),
                'mitigation_strategies': [
                    {
                        'id': ms.id,
                        'cost': ms.cost,
                        'effectiveness': ms.effectiveness,
                        'implementation_time': ms.implementation_time
                    } for ms in risk.mitigation_strategies
                ]
            }
            param_dict['risks'].append(risk_dict)
        
        # Sort risks by ID for consistent hashing
        param_dict['risks'].sort(key=lambda x: x['id'])
        
        # Add correlations if present
        if correlations:
            correlation_dict = {}
            for (risk1, risk2), corr in correlations.correlations.items():
                # Use sorted tuple as key for consistent ordering
                key = tuple(sorted([risk1, risk2]))
                correlation_dict[f"{key[0]}_{key[1]}"] = corr
            param_dict['correlations'] = correlation_dict
        
        # Generate hash
        param_json = json.dumps(param_dict, sort_keys=True)
        return hashlib.sha256(param_json.encode()).hexdigest()
    
    def _detect_parameter_changes(
        self, 
        current_hash: str, 
        previous_simulation_id: Optional[str] = None
    ) -> bool:
        """
        Detect if parameters have changed since last simulation.
        
        Args:
            current_hash: Hash of current parameters
            previous_simulation_id: ID of previous simulation to compare against
            
        Returns:
            True if parameters have changed, False otherwise
        """
        if previous_simulation_id is None:
            return True  # No previous simulation to compare
        
        with self._lock:
            previous_hash = self._parameter_cache.get(previous_simulation_id)
            if previous_hash is None:
                return True  # No cached hash found
            return previous_hash != current_hash
    
    def run_simulation_with_caching(
        self,
        risks: List[Risk],
        iterations: int = 10000,
        correlations: Optional[CorrelationMatrix] = None,
        random_seed: Optional[int] = None,
        progress_callback: Optional[callable] = None,
        previous_simulation_id: Optional[str] = None,
        force_rerun: bool = False,
        baseline_costs: Optional[Dict[str, float]] = None,
        schedule_data: Optional[ScheduleData] = None
    ) -> SimulationResults:
        """
        Execute Monte Carlo simulation with parameter change detection and caching.
        
        Args:
            risks: List of Risk objects to simulate
            iterations: Number of simulation iterations (minimum 10,000)
            correlations: Optional correlation matrix for dependent risks
            random_seed: Optional random seed for reproducibility
            progress_callback: Optional callback for progress updates
            previous_simulation_id: ID of previous simulation for change detection
            force_rerun: Force re-execution even if parameters haven't changed
            baseline_costs: Optional baseline cost data for integration
            schedule_data: Optional schedule data for timeline and milestone integration
            
        Returns:
            SimulationResults containing all simulation outcomes and metrics
        """
        # Generate parameter hash for change detection
        current_hash = self._generate_parameter_hash(risks, iterations, correlations, random_seed, baseline_costs, schedule_data)
        
        # Check if parameters have changed
        parameters_changed = self._detect_parameter_changes(current_hash, previous_simulation_id)
        
        # If parameters haven't changed and we have cached results, return them
        if not force_rerun and not parameters_changed and previous_simulation_id:
            cached_results = self.get_cached_results(previous_simulation_id)
            if cached_results:
                # Return the cached results with the same simulation ID
                return cached_results
        
        # Run new simulation
        results = self.run_simulation(risks, iterations, correlations, random_seed, progress_callback, baseline_costs, schedule_data)
        
        # Cache parameter hash
        with self._lock:
            self._parameter_cache[results.simulation_id] = current_hash
        
        return results
    
    def invalidate_cache_for_risk(self, risk_id: str):
        """
        Invalidate cached simulations that include a specific risk.
        
        Args:
            risk_id: ID of the risk that has been modified
        """
        with self._lock:
            # Find simulations that need to be invalidated
            simulations_to_remove = []
            
            for simulation_id, results in self._simulation_cache.items():
                if risk_id in results.risk_contributions:
                    simulations_to_remove.append(simulation_id)
            
            # Remove invalidated simulations
            for simulation_id in simulations_to_remove:
                if simulation_id in self._simulation_cache:
                    del self._simulation_cache[simulation_id]
                if simulation_id in self._parameter_cache:
                    del self._parameter_cache[simulation_id]
    
    def get_parameter_change_summary(
        self,
        current_risks: List[Risk],
        previous_simulation_id: str,
        iterations: int = 10000,
        correlations: Optional[CorrelationMatrix] = None,
        random_seed: Optional[int] = None,
        baseline_costs: Optional[Dict[str, float]] = None,
        schedule_data: Optional[ScheduleData] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of what parameters have changed since the last simulation.
        
        Args:
            current_risks: Current list of risks
            previous_simulation_id: ID of previous simulation to compare against
            iterations: Current iteration count
            correlations: Current correlation matrix
            random_seed: Current random seed
            baseline_costs: Optional baseline cost data
            schedule_data: Optional schedule data
            
        Returns:
            Dictionary summarizing parameter changes
        """
        current_hash = self._generate_parameter_hash(current_risks, iterations, correlations, random_seed, baseline_costs, schedule_data)
        
        with self._lock:
            previous_hash = self._parameter_cache.get(previous_simulation_id)
            
            if previous_hash == current_hash:
                return {'changed': False, 'changes': []}
            
            # Get previous results for detailed comparison
            previous_results = self._simulation_cache.get(previous_simulation_id)
            if not previous_results:
                return {'changed': True, 'changes': ['Previous simulation not found in cache']}
        
        changes = []
        
        # Compare basic parameters
        if previous_results.iteration_count != iterations:
            changes.append(f"Iteration count changed: {previous_results.iteration_count} -> {iterations}")
        
        # Compare risks (simplified comparison)
        current_risk_ids = {risk.id for risk in current_risks}
        previous_risk_ids = set(previous_results.risk_contributions.keys())
        
        added_risks = current_risk_ids - previous_risk_ids
        removed_risks = previous_risk_ids - current_risk_ids
        
        if added_risks:
            changes.append(f"Added risks: {', '.join(added_risks)}")
        if removed_risks:
            changes.append(f"Removed risks: {', '.join(removed_risks)}")
        
        # For common risks, we'd need more detailed comparison
        # This is a simplified version
        common_risks = current_risk_ids & previous_risk_ids
        if common_risks and len(changes) == 0:
            changes.append("Risk parameters or distributions may have changed")
        
        return {
            'changed': True,
            'changes': changes,
            'current_hash': current_hash,
            'previous_hash': previous_hash
        }
    
    def run_simulation(
        self, 
        risks: List[Risk], 
        iterations: int = 10000,
        correlations: Optional[CorrelationMatrix] = None,
        random_seed: Optional[int] = None,
        progress_callback: Optional[callable] = None,
        baseline_costs: Optional[Dict[str, float]] = None,
        schedule_data: Optional[ScheduleData] = None
    ) -> SimulationResults:
        """
        Execute Monte Carlo simulation with configurable iterations.
        
        Args:
            risks: List of Risk objects to simulate
            iterations: Number of simulation iterations (minimum 10,000)
            correlations: Optional correlation matrix for dependent risks
            random_seed: Optional random seed for reproducibility
            progress_callback: Optional callback for progress updates
            baseline_costs: Optional baseline cost data for integration
            schedule_data: Optional schedule data for timeline and milestone integration
            
        Returns:
            SimulationResults containing all simulation outcomes and metrics
            
        Raises:
            ValueError: If iterations < 10000 or risks list is empty
            RuntimeError: If simulation fails to complete
        """
        # Validate inputs
        validation_result = self.validate_simulation_parameters(risks, iterations, schedule_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid simulation parameters: {validation_result.errors}")
        
        # Initialize simulation
        simulation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Set up random state
        random_state = np.random.RandomState(random_seed)
        
        # Initialize progress tracking
        progress_status = ProgressStatus(
            simulation_id=simulation_id,
            current_iteration=0,
            total_iterations=iterations,
            elapsed_time=0.0,
            estimated_remaining_time=0.0,
            status="running"
        )
        
        with self._lock:
            self._active_simulations[simulation_id] = progress_status
        
        try:
            # Initialize result arrays
            cost_outcomes = np.zeros(iterations)
            schedule_outcomes = np.zeros(iterations)
            risk_contributions = {risk.id: np.zeros(iterations) for risk in risks}
            
            # Prepare baseline costs integration
            baseline_cost_total = 0.0
            if baseline_costs:
                baseline_cost_total = sum(baseline_costs.values())
            
            # Prepare correlation handling
            correlated_sampling = correlations is not None
            if correlated_sampling:
                # Validate that all risks in correlation matrix exist
                risk_ids = [risk.id for risk in risks]
                for risk_id in correlations.risk_ids:
                    if risk_id not in risk_ids:
                        raise ValueError(f"Correlation matrix references unknown risk: {risk_id}")
                
                # Create correlation-aware sampling
                correlated_risk_indices = {risk_id: i for i, risk_id in enumerate(correlations.risk_ids)}
                correlation_matrix = self._build_numpy_correlation_matrix(correlations)
                
                # Use Cholesky decomposition for correlated sampling
                try:
                    cholesky_matrix = np.linalg.cholesky(correlation_matrix)
                except np.linalg.LinAlgError:
                    # Fallback to uncorrelated sampling if matrix is not positive definite
                    correlated_sampling = False
                    cholesky_matrix = None
            else:
                cholesky_matrix = None
                correlated_risk_indices = {}
            
            # Track convergence metrics
            convergence_tracker = ConvergenceTracker()
            
            # Track risk interactions to prevent double-counting
            risk_interaction_tracker = RiskInteractionTracker(risks, correlations)
            
            # Run simulation iterations
            for i in range(iterations):
                iteration_start = time.time()
                
                # Generate correlated or independent samples
                if correlated_sampling and cholesky_matrix is not None:
                    # Generate correlated samples
                    independent_samples = random_state.standard_normal(len(correlations.risk_ids))
                    correlated_samples = cholesky_matrix @ independent_samples
                    
                    # Map correlated samples to risks
                    risk_samples = {}
                    for risk in risks:
                        if risk.id in correlated_risk_indices:
                            # Use correlated sample
                            corr_idx = correlated_risk_indices[risk.id]
                            # Transform standard normal to risk distribution
                            risk_samples[risk.id] = self._transform_sample_to_distribution(
                                correlated_samples[corr_idx], risk.probability_distribution, random_state
                            )
                        else:
                            # Use independent sample
                            risk_samples[risk.id] = risk.probability_distribution.sample(1, random_state)[0]
                else:
                    # Generate independent samples
                    risk_samples = {}
                    for risk in risks:
                        risk_samples[risk.id] = risk.probability_distribution.sample(1, random_state)[0]
                
                # Calculate risk impacts with correlation adjustments
                total_cost_impact = 0.0
                total_schedule_impact = 0.0
                iteration_risk_impacts = {}
                
                for risk in risks:
                    # Get base sample for this risk
                    sample = risk_samples[risk.id]
                    
                    # Apply baseline impact
                    base_impact = sample * risk.baseline_impact
                    
                    # Apply correlation adjustments to prevent double-counting
                    adjusted_impact = risk_interaction_tracker.adjust_for_correlations(
                        risk.id, base_impact, iteration_risk_impacts, correlations
                    )
                    
                    iteration_risk_impacts[risk.id] = adjusted_impact
                    risk_contributions[risk.id][i] = adjusted_impact
                    
                    # Add to appropriate outcome type
                    if risk.impact_type in [ImpactType.COST, ImpactType.BOTH]:
                        total_cost_impact += adjusted_impact
                    if risk.impact_type in [ImpactType.SCHEDULE, ImpactType.BOTH]:
                        total_schedule_impact += adjusted_impact
                
                # Apply schedule simulation logic if schedule data is provided
                if schedule_data:
                    total_schedule_impact = self._simulate_schedule_impact(
                        total_schedule_impact, iteration_risk_impacts, schedule_data, random_state
                    )
                
                # Integrate with baseline costs (bidirectional impacts)
                final_cost_outcome = baseline_cost_total + total_cost_impact
                
                # Handle negative cost impacts (cost savings) properly
                if total_cost_impact < 0:
                    # Cost savings - ensure we don't go below reasonable minimum
                    min_cost = baseline_cost_total * 0.1  # Minimum 10% of baseline
                    final_cost_outcome = max(final_cost_outcome, min_cost)
                
                # Store iteration results
                cost_outcomes[i] = final_cost_outcome
                schedule_outcomes[i] = total_schedule_impact
                
                # Update convergence tracking
                if i > 0 and i % 1000 == 0:  # Check convergence every 1000 iterations
                    convergence_tracker.update(cost_outcomes[:i+1], schedule_outcomes[:i+1])
                
                # Update progress
                current_time = time.time()
                elapsed = current_time - start_time
                
                with self._lock:
                    progress_status.current_iteration = i + 1
                    progress_status.elapsed_time = elapsed
                    if i > 0:
                        avg_time_per_iteration = elapsed / (i + 1)
                        remaining_iterations = iterations - (i + 1)
                        progress_status.estimated_remaining_time = avg_time_per_iteration * remaining_iterations
                
                # Call progress callback if provided
                if progress_callback and (i + 1) % 1000 == 0:
                    progress_callback(progress_status)
            
            # Finalize convergence metrics
            final_convergence = convergence_tracker.finalize(cost_outcomes, schedule_outcomes, iterations)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update final progress status
            with self._lock:
                progress_status.status = "completed"
                progress_status.elapsed_time = execution_time
                progress_status.estimated_remaining_time = 0.0
            
            # Create simulation results
            results = SimulationResults(
                simulation_id=simulation_id,
                timestamp=datetime.now(),
                iteration_count=iterations,
                cost_outcomes=cost_outcomes,
                schedule_outcomes=schedule_outcomes,
                risk_contributions=risk_contributions,
                convergence_metrics=final_convergence,
                execution_time=execution_time
            )
            
            # Cache results
            with self._lock:
                self._simulation_cache[simulation_id] = results
                # Also cache the parameter hash for change detection
                param_hash = self._generate_parameter_hash(risks, iterations, correlations, random_seed, baseline_costs, schedule_data)
                self._parameter_cache[simulation_id] = param_hash
            
            return results
            
        except Exception as e:
            # Update progress status on failure
            with self._lock:
                progress_status.status = "failed"
            raise RuntimeError(f"Simulation failed: {str(e)}") from e
        
        finally:
            # Clean up active simulation tracking
            with self._lock:
                if simulation_id in self._active_simulations:
                    del self._active_simulations[simulation_id]
    
    def validate_simulation_parameters(self, risks: List[Risk], iterations: int = 10000, schedule_data: Optional[ScheduleData] = None) -> ValidationResult:
        """
        Validate simulation parameters before execution.
        
        Args:
            risks: List of Risk objects to validate
            iterations: Number of simulation iterations
            schedule_data: Optional schedule data to validate
            
        Returns:
            ValidationResult indicating if parameters are valid
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Check minimum iterations
        if iterations < 10000:
            errors.append(f"Minimum 10,000 iterations required, got {iterations}")
        
        # Check risks list
        if not risks:
            errors.append("At least one risk must be provided")
        
        # Validate individual risks
        risk_ids = set()
        for risk in risks:
            if risk.id in risk_ids:
                errors.append(f"Duplicate risk ID: {risk.id}")
            risk_ids.add(risk.id)
            
            # Check for valid probability distribution
            try:
                # Test sampling from distribution
                test_sample = risk.probability_distribution.sample(1)
                if not np.isfinite(test_sample[0]):
                    errors.append(f"Risk {risk.id} produces non-finite samples")
            except Exception as e:
                errors.append(f"Risk {risk.id} distribution error: {str(e)}")
        
        # Performance warnings
        if iterations > 100000:
            warnings.append("Large iteration count may impact performance")
        
        if len(risks) > 100:
            warnings.append("Large number of risks may impact performance")
        
        # Recommendations
        if iterations < 50000:
            recommendations.append("Consider using 50,000+ iterations for better statistical accuracy")
        
        # Validate schedule data if provided
        if schedule_data:
            schedule_validation = self.validate_resource_constraints(schedule_data)
            errors.extend(schedule_validation.errors)
            warnings.extend(schedule_validation.warnings)
            recommendations.extend(schedule_validation.recommendations)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def get_simulation_progress(self, simulation_id: str) -> Optional[ProgressStatus]:
        """
        Get current progress status for a running simulation.
        
        Args:
            simulation_id: ID of the simulation to check
            
        Returns:
            ProgressStatus if simulation is active, None otherwise
        """
        with self._lock:
            return self._active_simulations.get(simulation_id)
    
    def get_cached_results(self, simulation_id: str) -> Optional[SimulationResults]:
        """
        Retrieve cached simulation results.
        
        Args:
            simulation_id: ID of the simulation results to retrieve
            
        Returns:
            SimulationResults if cached, None otherwise
        """
        with self._lock:
            return self._simulation_cache.get(simulation_id)
    
    def _build_numpy_correlation_matrix(self, correlations: CorrelationMatrix) -> np.ndarray:
        """
        Build a NumPy correlation matrix from the CorrelationMatrix object.
        
        Args:
            correlations: CorrelationMatrix object
            
        Returns:
            NumPy array representing the correlation matrix
        """
        n = len(correlations.risk_ids)
        matrix = np.eye(n)  # Start with identity matrix
        
        # Fill in correlations
        for i, risk1 in enumerate(correlations.risk_ids):
            for j, risk2 in enumerate(correlations.risk_ids):
                if i != j:
                    correlation = correlations.get_correlation(risk1, risk2)
                    matrix[i, j] = correlation
        
        return matrix
    
    def _transform_sample_to_distribution(
        self, 
        standard_normal_sample: float, 
        distribution: ProbabilityDistribution,
        random_state: np.random.RandomState
    ) -> float:
        """
        Transform a standard normal sample to match the target distribution.
        
        This is a simplified transformation - in practice, you'd use inverse CDF methods.
        For now, we'll use a basic approach that maintains correlation structure.
        
        Args:
            standard_normal_sample: Sample from standard normal distribution
            distribution: Target probability distribution
            random_state: Random state for additional sampling if needed
            
        Returns:
            Transformed sample matching the target distribution
        """
        # For simplicity, we'll use a basic linear transformation
        # In a full implementation, you'd use inverse CDF methods
        
        if distribution.distribution_type == DistributionType.NORMAL:
            mean = distribution.parameters['mean']
            std = distribution.parameters['std']
            return mean + std * standard_normal_sample
        
        elif distribution.distribution_type == DistributionType.TRIANGULAR:
            # For triangular, we'll use a simplified approach
            # Generate a new sample but maintain some correlation structure
            base_sample = distribution.sample(1, random_state)[0]
            # Apply some influence from the correlated sample
            correlation_influence = 0.3 * standard_normal_sample * (distribution.parameters['max'] - distribution.parameters['min']) / 6
            return base_sample + correlation_influence
        
        else:
            # For other distributions, fall back to independent sampling
            # This is a simplification - full implementation would use proper inverse CDF
            return distribution.sample(1, random_state)[0]
    
    def _simulate_schedule_impact(
        self,
        base_schedule_impact: float,
        risk_impacts: Dict[str, float],
        schedule_data: ScheduleData,
        random_state: np.random.RandomState
    ) -> float:
        """
        Simulate schedule impact considering milestone data, critical path analysis,
        and activity-specific vs project-wide risks.
        
        Args:
            base_schedule_impact: Base schedule impact from risk calculations
            risk_impacts: Dictionary of individual risk impacts
            schedule_data: Schedule data with milestones and activities
            random_state: Random state for additional sampling
            
        Returns:
            Adjusted schedule impact considering schedule constraints
        """
        if not schedule_data.milestones and not schedule_data.activities:
            # No schedule data available, return base impact
            return base_schedule_impact
        
        # Start with base schedule impact
        total_schedule_impact = base_schedule_impact
        
        # Apply critical path analysis considerations
        critical_path_multiplier = self._calculate_critical_path_multiplier(
            schedule_data, risk_impacts, random_state
        )
        
        # Apply milestone-based adjustments
        milestone_adjustment = self._calculate_milestone_adjustments(
            schedule_data, risk_impacts, random_state
        )
        
        # Apply activity-specific vs project-wide risk modeling
        activity_adjustment = self._calculate_activity_adjustments(
            schedule_data, risk_impacts, random_state
        )
        
        # Combine adjustments (multiplicative for critical path, additive for others)
        adjusted_impact = (total_schedule_impact * critical_path_multiplier) + milestone_adjustment + activity_adjustment
        
        # Apply resource constraint impacts if available
        if schedule_data.resource_constraints:
            resource_adjustment = self._calculate_resource_constraint_impact(
                schedule_data, adjusted_impact, random_state
            )
            adjusted_impact += resource_adjustment
        
        # Ensure schedule impact doesn't go negative (delays only, no negative time)
        return max(0.0, adjusted_impact)
    
    def _calculate_critical_path_multiplier(
        self,
        schedule_data: ScheduleData,
        risk_impacts: Dict[str, float],
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate critical path multiplier for schedule risks.
        
        Critical path activities have higher impact on overall schedule.
        """
        if not schedule_data.activities and not schedule_data.milestones:
            return 1.0
        
        # Count critical path items
        critical_activities = [a for a in schedule_data.activities if a.critical_path]
        critical_milestones = [m for m in schedule_data.milestones if m.critical_path]
        
        total_activities = len(schedule_data.activities)
        total_milestones = len(schedule_data.milestones)
        total_items = total_activities + total_milestones
        
        if total_items == 0:
            return 1.0
        
        # Calculate critical path ratio
        critical_items = len(critical_activities) + len(critical_milestones)
        critical_path_ratio = critical_items / total_items if total_items > 0 else 0.0
        
        # Critical path items have 1.5x to 2.5x impact multiplier
        base_multiplier = 1.0
        critical_multiplier = 1.5 + (critical_path_ratio * 1.0)  # 1.5 to 2.5 range
        
        # Apply some randomness to the multiplier
        randomness = random_state.normal(0, 0.1)  # Small random variation
        final_multiplier = critical_multiplier + randomness
        
        return max(1.0, final_multiplier)  # Ensure multiplier is at least 1.0
    
    def _calculate_milestone_adjustments(
        self,
        schedule_data: ScheduleData,
        risk_impacts: Dict[str, float],
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate milestone-based schedule adjustments.
        
        Considers milestone dependencies and their impact on overall schedule.
        """
        if not schedule_data.milestones:
            return 0.0
        
        total_adjustment = 0.0
        
        for milestone in schedule_data.milestones:
            # Calculate dependency impact
            dependency_factor = len(milestone.dependencies) * 0.1  # 10% per dependency
            
            # Milestone duration impact
            duration_factor = milestone.baseline_duration / max(schedule_data.project_baseline_duration, 1.0)
            
            # Random milestone-specific impact
            milestone_impact = random_state.normal(0, duration_factor * 0.5)
            
            # Combine factors
            milestone_adjustment = milestone_impact * (1.0 + dependency_factor)
            
            # Critical path milestones have higher impact
            if milestone.critical_path:
                milestone_adjustment *= 1.5
            
            total_adjustment += milestone_adjustment
        
        return total_adjustment
    
    def _calculate_activity_adjustments(
        self,
        schedule_data: ScheduleData,
        risk_impacts: Dict[str, float],
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate activity-specific vs project-wide risk adjustments.
        
        Models both activity-specific risks and project-wide risks.
        """
        if not schedule_data.activities:
            return 0.0
        
        total_adjustment = 0.0
        
        # Activity-specific risk modeling
        for activity in schedule_data.activities:
            # Float time provides buffer against schedule risks
            float_buffer = activity.float_time / max(activity.baseline_duration, 1.0)
            risk_absorption = min(0.8, float_buffer)  # Up to 80% risk absorption
            
            # Activity duration impact
            duration_weight = activity.baseline_duration / max(schedule_data.project_baseline_duration, 1.0)
            
            # Random activity-specific impact
            activity_impact = random_state.normal(0, duration_weight * 0.3)
            
            # Apply float buffer to reduce impact
            adjusted_impact = activity_impact * (1.0 - risk_absorption)
            
            # Critical path activities have no float buffer
            if activity.critical_path:
                adjusted_impact = activity_impact * 1.2  # 20% increase for critical path
            
            total_adjustment += adjusted_impact
        
        # Project-wide risk component (affects all activities)
        project_wide_factor = random_state.normal(0, 0.1)  # Small project-wide variation
        project_wide_adjustment = project_wide_factor * len(schedule_data.activities) * 0.1
        
        return total_adjustment + project_wide_adjustment
    
    def _calculate_resource_constraint_impact(
        self,
        schedule_data: ScheduleData,
        current_schedule_impact: float,
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate the impact of resource constraints on schedule.
        
        Resource availability affects schedule risk realization.
        Implements resource availability impact calculations and constraint validation.
        """
        if not schedule_data.resource_constraints or not schedule_data.activities:
            return 0.0
        
        total_resource_impact = 0.0
        
        # Calculate resource utilization pressure and availability impacts
        for resource in schedule_data.resource_constraints:
            # Calculate total resource demand from activities
            total_demand = 0.0
            peak_demand_periods = []
            
            for activity in schedule_data.activities:
                if resource.resource_id in activity.resource_requirements:
                    demand = activity.resource_requirements[resource.resource_id]
                    total_demand += demand
                    
                    # Track peak demand periods for scheduling validation
                    peak_demand_periods.append({
                        'activity_id': activity.id,
                        'start': activity.earliest_start,
                        'end': activity.earliest_start + activity.baseline_duration,
                        'demand': demand,
                        'critical_path': activity.critical_path
                    })
            
            # Calculate base utilization ratio
            available_capacity = resource.total_availability * resource.utilization_limit
            base_utilization_ratio = total_demand / max(available_capacity, 0.001)
            
            # Apply resource availability periods if defined
            availability_impact = self._calculate_availability_period_impact(
                resource, peak_demand_periods, random_state
            )
            
            # Calculate scheduling constraint impact
            scheduling_impact = self._calculate_scheduling_constraint_impact(
                resource, peak_demand_periods, schedule_data.project_baseline_duration, random_state
            )
            
            # High utilization increases schedule risk
            utilization_impact = 0.0
            if base_utilization_ratio > 0.8:  # Over 80% utilization
                over_utilization = base_utilization_ratio - 0.8
                resource_pressure = over_utilization * 2.0  # 2x multiplier for over-utilization
                
                # Random component for resource availability variation
                availability_variation = random_state.normal(0, 0.1)
                
                utilization_impact = (resource_pressure + availability_variation) * abs(current_schedule_impact) * 0.1
            
            # Combine all resource impacts
            resource_total_impact = utilization_impact + availability_impact + scheduling_impact
            
            # Critical path activities amplify resource constraint impacts
            critical_path_activities = [p for p in peak_demand_periods if p['critical_path']]
            if critical_path_activities:
                critical_path_multiplier = 1.0 + (len(critical_path_activities) / max(len(peak_demand_periods), 1)) * 0.5
                resource_total_impact *= critical_path_multiplier
            
            total_resource_impact += resource_total_impact
        
        return total_resource_impact
    
    def _calculate_availability_period_impact(
        self,
        resource: ResourceConstraint,
        demand_periods: List[Dict],
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate impact of resource availability periods on schedule.
        
        Models how varying resource availability affects schedule risk.
        """
        if not resource.availability_periods:
            return 0.0
        
        total_availability_impact = 0.0
        
        for start_day, end_day, availability_factor in resource.availability_periods:
            # Find activities that overlap with this availability period
            overlapping_demands = []
            for demand in demand_periods:
                if (demand['start'] < end_day and demand['end'] > start_day):
                    # Calculate overlap duration
                    overlap_start = max(demand['start'], start_day)
                    overlap_end = min(demand['end'], end_day)
                    overlap_duration = max(0, overlap_end - overlap_start)
                    
                    if overlap_duration > 0:
                        overlapping_demands.append({
                            'demand': demand['demand'],
                            'overlap_duration': overlap_duration,
                            'activity_duration': demand['end'] - demand['start'],
                            'critical_path': demand['critical_path']
                        })
            
            if overlapping_demands:
                # Calculate reduced availability impact
                period_duration = end_day - start_day
                reduced_capacity = resource.total_availability * (1.0 - availability_factor)
                
                # Calculate demand during reduced availability
                total_overlap_demand = sum(d['demand'] * (d['overlap_duration'] / d['activity_duration']) 
                                         for d in overlapping_demands)
                
                if total_overlap_demand > 0:
                    # Impact is proportional to demand during reduced availability
                    availability_shortage = reduced_capacity / max(resource.total_availability, 0.001)
                    
                    # Random variation in availability impact
                    availability_variation = random_state.normal(1.0, 0.2)  # 20% variation
                    
                    period_impact = (availability_shortage * total_overlap_demand * availability_variation) / 10.0
                    
                    # Critical path activities have higher impact
                    critical_demands = [d for d in overlapping_demands if d['critical_path']]
                    if critical_demands:
                        period_impact *= 1.5
                    
                    total_availability_impact += period_impact
        
        return total_availability_impact
    
    def _calculate_scheduling_constraint_impact(
        self,
        resource: ResourceConstraint,
        demand_periods: List[Dict],
        project_duration: float,
        random_state: np.random.RandomState
    ) -> float:
        """
        Calculate impact of resource scheduling constraints.
        
        Models how resource conflicts and scheduling constraints affect timeline.
        """
        if len(demand_periods) <= 1:
            return 0.0  # No scheduling conflicts with single or no activities
        
        # Sort demand periods by start time
        sorted_periods = sorted(demand_periods, key=lambda x: x['start'])
        
        total_scheduling_impact = 0.0
        available_capacity = resource.total_availability * resource.utilization_limit
        
        # Simulate resource scheduling conflicts
        for i in range(len(sorted_periods)):
            current_period = sorted_periods[i]
            
            # Check for overlapping resource demands
            overlapping_periods = []
            for j in range(len(sorted_periods)):
                if i != j:
                    other_period = sorted_periods[j]
                    # Check if periods overlap
                    if (current_period['start'] < other_period['end'] and 
                        current_period['end'] > other_period['start']):
                        overlapping_periods.append(other_period)
            
            if overlapping_periods:
                # Calculate total demand during overlap
                total_concurrent_demand = current_period['demand']
                for overlap in overlapping_periods:
                    total_concurrent_demand += overlap['demand']
                
                # Check if demand exceeds available capacity
                if total_concurrent_demand > available_capacity:
                    # Calculate resource conflict impact
                    excess_demand = total_concurrent_demand - available_capacity
                    conflict_ratio = excess_demand / max(available_capacity, 0.001)
                    
                    # Duration of the conflict
                    conflict_start = current_period['start']
                    conflict_end = current_period['end']
                    for overlap in overlapping_periods:
                        conflict_start = max(conflict_start, overlap['start'])
                        conflict_end = min(conflict_end, overlap['end'])
                    
                    conflict_duration = max(0, conflict_end - conflict_start)
                    
                    # Impact is proportional to conflict severity and duration
                    base_impact = conflict_ratio * conflict_duration * 0.1
                    
                    # Random variation in scheduling efficiency
                    scheduling_efficiency = random_state.uniform(0.7, 1.0)  # 70-100% efficiency
                    scheduling_impact = base_impact / scheduling_efficiency
                    
                    # Critical path conflicts have higher impact
                    if (current_period['critical_path'] or 
                        any(overlap['critical_path'] for overlap in overlapping_periods)):
                        scheduling_impact *= 2.0
                    
                    total_scheduling_impact += scheduling_impact
        
        return total_scheduling_impact
    
    def validate_resource_constraints(
        self,
        schedule_data: ScheduleData
    ) -> ValidationResult:
        """
        Validate resource constraints and scheduling feasibility.
        
        Args:
            schedule_data: Schedule data to validate
            
        Returns:
            ValidationResult indicating constraint validity and potential issues
        """
        errors = []
        warnings = []
        recommendations = []
        
        if not schedule_data.resource_constraints:
            return ValidationResult(is_valid=True, errors=errors, warnings=warnings, recommendations=recommendations)
        
        for resource in schedule_data.resource_constraints:
            # Validate resource constraint parameters
            if resource.total_availability <= 0:
                errors.append(f"Resource {resource.resource_id} has invalid total availability: {resource.total_availability}")
            
            if not 0.0 <= resource.utilization_limit <= 1.0:
                errors.append(f"Resource {resource.resource_id} has invalid utilization limit: {resource.utilization_limit}")
            
            # Check resource demand vs availability
            total_demand = 0.0
            peak_concurrent_demand = 0.0
            
            for activity in schedule_data.activities:
                if resource.resource_id in activity.resource_requirements:
                    demand = activity.resource_requirements[resource.resource_id]
                    total_demand += demand
                    
                    # Calculate peak concurrent demand (simplified)
                    peak_concurrent_demand = max(peak_concurrent_demand, demand)
            
            available_capacity = resource.total_availability * resource.utilization_limit
            
            # Check for over-utilization
            if peak_concurrent_demand > available_capacity:
                errors.append(
                    f"Resource {resource.resource_id} peak demand ({peak_concurrent_demand}) "
                    f"exceeds available capacity ({available_capacity})"
                )
            
            # Check for high utilization
            utilization_ratio = total_demand / max(available_capacity * len(schedule_data.activities), 0.001)
            if utilization_ratio > 0.9:
                warnings.append(
                    f"Resource {resource.resource_id} has high utilization ratio: {utilization_ratio:.2f}"
                )
            elif utilization_ratio > 0.8:
                recommendations.append(
                    f"Consider monitoring resource {resource.resource_id} utilization: {utilization_ratio:.2f}"
                )
            
            # Validate availability periods
            for start_day, end_day, availability_factor in resource.availability_periods:
                if start_day >= end_day:
                    errors.append(
                        f"Resource {resource.resource_id} has invalid availability period: "
                        f"start ({start_day}) >= end ({end_day})"
                    )
                
                if not 0.0 <= availability_factor <= 1.0:
                    errors.append(
                        f"Resource {resource.resource_id} has invalid availability factor: {availability_factor}"
                    )
                
                if start_day < 0 or end_day > schedule_data.project_baseline_duration:
                    warnings.append(
                        f"Resource {resource.resource_id} availability period ({start_day}-{end_day}) "
                        f"extends beyond project duration ({schedule_data.project_baseline_duration})"
                    )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def clear_cache(self, simulation_ids: Optional[List[str]] = None):
        """
        Clear cached simulation results.
        
        Args:
            simulation_ids: Optional list of specific simulation IDs to clear.
                          If None, clears all cached results.
        """
        with self._lock:
            if simulation_ids is None:
                self._simulation_cache.clear()
                self._parameter_cache.clear()
            else:
                for sim_id in simulation_ids:
                    if sim_id in self._simulation_cache:
                        del self._simulation_cache[sim_id]
                    if sim_id in self._parameter_cache:
                        del self._parameter_cache[sim_id]
    
    def get_configuration(self) -> SimulationConfig:
        """
        Get the current simulation configuration.
        
        Returns:
            Current SimulationConfig instance
        """
        return self._config.copy_with_overrides()
    
    def set_configuration(self, config: SimulationConfig):
        """
        Set a new simulation configuration.
        
        Args:
            config: New SimulationConfig to use
            
        Raises:
            ValueError: If configuration is invalid
        """
        validation_result = self._config_manager.validate_config(config)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")
        
        self._config = config
        
        # Clear cache if caching is disabled in new config
        if not config.enable_caching:
            self.clear_cache()
    
    def update_configuration(self, **overrides):
        """
        Update the current configuration with parameter overrides.
        
        Args:
            **overrides: Configuration parameter overrides
            
        Raises:
            ValueError: If resulting configuration is invalid
        """
        new_config = self._config.copy_with_overrides(**overrides)
        self.set_configuration(new_config)
    
    def get_configuration_manager(self) -> ConfigurationManager:
        """
        Get the configuration manager for accessing presets and validation.
        
        Returns:
            ConfigurationManager instance
        """
        return self._config_manager
    
    def run_simulation_with_config(
        self,
        risks: List[Risk],
        config: Optional[SimulationConfig] = None,
        correlations: Optional[CorrelationMatrix] = None,
        progress_callback: Optional[callable] = None,
        previous_simulation_id: Optional[str] = None,
        force_rerun: bool = False,
        baseline_costs: Optional[Dict[str, float]] = None,
        schedule_data: Optional[ScheduleData] = None
    ) -> SimulationResults:
        """
        Execute Monte Carlo simulation with specified configuration.
        
        Args:
            risks: List of Risk objects to simulate
            config: Optional SimulationConfig. If None, uses current engine configuration
            correlations: Optional correlation matrix for dependent risks
            progress_callback: Optional callback for progress updates
            previous_simulation_id: ID of previous simulation for change detection
            force_rerun: Force re-execution even if parameters haven't changed
            baseline_costs: Optional baseline cost data for integration
            schedule_data: Optional schedule data for timeline and milestone integration
            
        Returns:
            SimulationResults containing all simulation outcomes and metrics
        """
        # Use provided config or current engine config
        effective_config = config or self._config
        
        # Get effective iterations based on risk count
        effective_iterations = effective_config.get_effective_iterations(len(risks))
        
        # Set up random state from config
        random_state = effective_config.get_random_state()
        random_seed = effective_config.random_seed
        
        # Use caching if enabled
        if effective_config.enable_caching:
            return self.run_simulation_with_caching(
                risks=risks,
                iterations=effective_iterations,
                correlations=correlations,
                random_seed=random_seed,
                progress_callback=progress_callback if effective_config.enable_progress_tracking else None,
                previous_simulation_id=previous_simulation_id,
                force_rerun=force_rerun,
                baseline_costs=baseline_costs,
                schedule_data=schedule_data
            )
        else:
            return self.run_simulation(
                risks=risks,
                iterations=effective_iterations,
                correlations=correlations,
                random_seed=random_seed,
                progress_callback=progress_callback if effective_config.enable_progress_tracking else None,
                baseline_costs=baseline_costs,
                schedule_data=schedule_data
            )
    
    def validate_model(
        self,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix] = None,
        historical_data: Optional[Dict[str, List[float]]] = None,
        significance_level: float = 0.05
    ) -> ValidationResult:
        """
        Validate a complete Monte Carlo risk simulation model.
        
        Performs comprehensive validation including probability distributions,
        correlation matrices, and overall model consistency.
        
        Args:
            risks: List of Risk objects to validate
            correlations: Optional correlation matrix
            historical_data: Optional historical data for goodness-of-fit testing
            significance_level: Significance level for statistical tests
            
        Returns:
            ValidationResult with comprehensive validation results
        """
        return self._model_validator.validate_complete_model(
            risks=risks,
            correlations=correlations,
            historical_data=historical_data,
            significance_level=significance_level
        )
    
    def validate_distribution(
        self,
        distribution: ProbabilityDistribution,
        historical_data: Optional[List[float]] = None,
        significance_level: float = 0.05
    ) -> ValidationResult:
        """
        Validate a single probability distribution with optional goodness-of-fit testing.
        
        Args:
            distribution: ProbabilityDistribution to validate
            historical_data: Optional historical data for goodness-of-fit testing
            significance_level: Significance level for statistical tests
            
        Returns:
            ValidationResult with validation status and detailed test results
        """
        return self._model_validator.distribution_validator.validate_distribution(
            distribution=distribution,
            historical_data=historical_data,
            significance_level=significance_level
        )
    
    def validate_correlation_matrix(
        self,
        correlation_matrix: CorrelationMatrix,
        tolerance: float = 1e-8
    ) -> ValidationResult:
        """
        Validate a correlation matrix for mathematical consistency.
        
        Args:
            correlation_matrix: CorrelationMatrix to validate
            tolerance: Numerical tolerance for validation checks
            
        Returns:
            ValidationResult with validation status and detailed analysis
        """
        return self._model_validator.correlation_validator.validate_correlation_matrix(
            correlation_matrix=correlation_matrix,
            tolerance=tolerance
        )
    
    def suggest_correlation_matrix_fixes(
        self,
        correlation_matrix: CorrelationMatrix,
        tolerance: float = 1e-8
    ) -> Dict[str, Any]:
        """
        Suggest fixes for correlation matrix issues.
        
        Args:
            correlation_matrix: CorrelationMatrix with potential issues
            tolerance: Numerical tolerance for fixes
            
        Returns:
            Dictionary containing suggested fixes and corrected matrix
        """
        return self._model_validator.correlation_validator.suggest_correlation_matrix_fixes(
            correlation_matrix=correlation_matrix,
            tolerance=tolerance
        )
    
    def detect_model_changes(
        self,
        current_risks: List[Risk],
        previous_risks: Optional[List[Risk]] = None,
        current_correlations: Optional[CorrelationMatrix] = None,
        previous_correlations: Optional[CorrelationMatrix] = None,
        baseline_model_id: Optional[str] = None
    ) -> ChangeDetectionReport:
        """
        Detect changes in model assumptions and provide validation guidance.
        
        Args:
            current_risks: Current list of risks
            previous_risks: Previous list of risks for comparison
            current_correlations: Current correlation matrix
            previous_correlations: Previous correlation matrix
            baseline_model_id: Optional ID for baseline model comparison
            
        Returns:
            ChangeDetectionReport with detected changes and validation guidance
        """
        return self._change_detector.detect_changes(
            current_risks=current_risks,
            previous_risks=previous_risks,
            current_correlations=current_correlations,
            previous_correlations=previous_correlations,
            baseline_model_id=baseline_model_id
        )
    
    def store_baseline_model(
        self,
        model_id: str,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix] = None
    ):
        """
        Store a baseline model for future change detection.
        
        Args:
            model_id: Unique identifier for the baseline model
            risks: List of risks to store as baseline
            correlations: Optional correlation matrix to store
        """
        self._change_detector.store_baseline_model(
            model_id=model_id,
            risks=risks,
            correlations=correlations
        )
    
    def get_change_detection_history(self, days_back: int = 30) -> List[ChangeDetectionReport]:
        """
        Get change detection history for the specified number of days.
        
        Args:
            days_back: Number of days to look back in history
            
        Returns:
            List of ChangeDetectionReport objects
        """
        return self._change_detector.get_change_history(days_back=days_back)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of validation areas needing attention.
        
        Returns:
            Dictionary containing validation summary information
        """
        return self._change_detector.get_validation_summary()
    
    def highlight_validation_areas(
        self,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix] = None,
        baseline_model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Highlight areas requiring validation based on model analysis.
        
        Args:
            risks: Current list of risks to analyze
            correlations: Optional correlation matrix
            baseline_model_id: Optional baseline model for comparison
            
        Returns:
            Dictionary containing validation area highlights and recommendations
        """
        # Perform model validation
        validation_result = self.validate_model(risks, correlations)
        
        # Detect changes if baseline available
        change_report = None
        if baseline_model_id:
            change_report = self.detect_model_changes(
                current_risks=risks,
                current_correlations=correlations,
                baseline_model_id=baseline_model_id
            )
        
        # Combine validation and change detection results
        validation_areas = []
        
        # Add validation issues
        if not validation_result.is_valid:
            validation_areas.append({
                "area": "Model Validation",
                "priority": "high",
                "issues": validation_result.errors,
                "recommendations": validation_result.recommendations
            })
        
        if validation_result.warnings:
            validation_areas.append({
                "area": "Model Warnings",
                "priority": "medium",
                "issues": validation_result.warnings,
                "recommendations": ["Review and address warnings"]
            })
        
        # Add change detection results
        if change_report and change_report.detected_changes:
            for guidance in change_report.validation_guidance:
                validation_areas.append({
                    "area": guidance.area,
                    "priority": guidance.priority,
                    "description": guidance.description,
                    "recommendations": guidance.recommended_actions,
                    "validation_methods": guidance.validation_methods,
                    "expected_effort": guidance.expected_effort
                })
        
        # Generate overall recommendations
        overall_recommendations = []
        
        high_priority_areas = [area for area in validation_areas if area["priority"] == "high"]
        if high_priority_areas:
            overall_recommendations.append("Address high-priority validation areas immediately")
        
        if change_report and change_report.changes_by_severity.get(ChangeSeverity.CRITICAL, 0) > 0:
            overall_recommendations.append("Critical model changes detected - halt simulations until validated")
        
        if not validation_areas:
            overall_recommendations.append("Model appears valid - continue with routine monitoring")
        
        return {
            "validation_areas": validation_areas,
            "overall_recommendations": overall_recommendations,
            "validation_summary": {
                "total_areas": len(validation_areas),
                "high_priority": len(high_priority_areas),
                "model_valid": validation_result.is_valid,
                "changes_detected": change_report.total_changes if change_report else 0
            }
        }
    
    # Cost Escalation Methods
    
    def add_escalation_factor(self, factor: EscalationFactor):
        """
        Add a cost escalation factor to the simulation.
        
        Args:
            factor: EscalationFactor to add
        """
        self._cost_escalation_modeler.add_escalation_factor(factor)
    
    def remove_escalation_factor(self, factor_type: EscalationFactorType):
        """
        Remove escalation factors of a specific type.
        
        Args:
            factor_type: Type of escalation factor to remove
        """
        self._cost_escalation_modeler.remove_escalation_factor(factor_type)
    
    def get_escalation_summary(
        self,
        base_cost: float,
        start_date: datetime,
        end_date: datetime,
        confidence_levels: List[float] = [0.80, 0.90, 0.95]
    ) -> Dict[str, Any]:
        """
        Get a statistical summary of cost escalation impacts.
        
        Args:
            base_cost: Base cost before escalation
            start_date: Start date for escalation
            end_date: End date for escalation
            confidence_levels: Confidence levels for interval calculations
            
        Returns:
            Dictionary containing escalation summary statistics
        """
        return self._cost_escalation_modeler.get_escalation_summary(
            base_cost=base_cost,
            start_date=start_date,
            end_date=end_date,
            confidence_levels=confidence_levels
        )
    
    def simulate_cost_escalation(
        self,
        base_cost: float,
        start_date: datetime,
        end_date: datetime,
        num_scenarios: int = 1000,
        cost_categories: Optional[Dict[str, float]] = None,
        random_seed: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Simulate multiple cost escalation scenarios.
        
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
        return self._cost_escalation_modeler.simulate_escalation_scenarios(
            base_cost=base_cost,
            start_date=start_date,
            end_date=end_date,
            num_scenarios=num_scenarios,
            cost_categories=cost_categories,
            random_seed=random_seed
        )
    
    # Distribution Output Methods
    
    def calculate_budget_compliance(
        self,
        simulation_results: SimulationResults,
        target_budget: float,
        confidence_levels: Optional[List[float]] = None
    ) -> BudgetComplianceResult:
        """
        Calculate budget compliance probability and risk analysis.
        
        Implements Requirement 4.4: Output cost distributions showing probability 
        of staying within budget at different confidence levels.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            target_budget: Target budget amount to analyze compliance against
            confidence_levels: Confidence levels for interval calculations
            
        Returns:
            BudgetComplianceResult with comprehensive budget analysis
        """
        return self._distribution_output_generator.calculate_budget_compliance(
            simulation_results=simulation_results,
            target_budget=target_budget,
            confidence_levels=confidence_levels
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
        
        Implements Requirement 5.4: Output schedule distributions showing probability 
        of completion by target dates.
        
        Args:
            simulation_results: Results from Monte Carlo simulation
            target_date: Target completion date to analyze compliance against
            project_start_date: Project start date for duration calculations
            confidence_levels: Confidence levels for interval calculations
            milestone_dates: Optional milestone dates for intermediate analysis
            
        Returns:
            ScheduleComplianceResult with comprehensive schedule analysis
        """
        return self._distribution_output_generator.calculate_schedule_compliance(
            simulation_results=simulation_results,
            target_date=target_date,
            project_start_date=project_start_date,
            confidence_levels=confidence_levels,
            milestone_dates=milestone_dates
        )
    
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
        return self._distribution_output_generator.generate_compliance_report(
            simulation_results=simulation_results,
            target_budget=target_budget,
            target_date=target_date,
            project_start_date=project_start_date,
            milestone_dates=milestone_dates
        )
    
    def run_simulation_with_escalation(
        self,
        risks: List[Risk],
        base_costs: Dict[str, float],
        project_start_date: datetime,
        project_end_date: datetime,
        iterations: int = 10000,
        correlations: Optional[CorrelationMatrix] = None,
        random_seed: Optional[int] = None,
        progress_callback: Optional[callable] = None,
        schedule_data: Optional[ScheduleData] = None,
        cost_categories: Optional[Dict[str, float]] = None
    ) -> SimulationResults:
        """
        Execute Monte Carlo simulation with integrated cost escalation modeling.
        
        Implements Requirement 4.5: Incorporate time-based cost escalation factors 
        when inflation or currency risks exist.
        
        Args:
            risks: List of Risk objects to simulate
            base_costs: Base costs by category before escalation
            project_start_date: Project start date for escalation calculations
            project_end_date: Project end date for escalation calculations
            iterations: Number of simulation iterations
            correlations: Optional correlation matrix for dependent risks
            random_seed: Optional random seed for reproducibility
            progress_callback: Optional callback for progress updates
            schedule_data: Optional schedule data for timeline integration
            cost_categories: Optional cost category breakdown for escalation
            
        Returns:
            SimulationResults with escalation-adjusted cost outcomes
        """
        # Set up random state
        random_state = np.random.RandomState(random_seed)
        
        # Calculate base cost total
        total_base_cost = sum(base_costs.values())
        
        # Run base simulation
        base_results = self.run_simulation(
            risks=risks,
            iterations=iterations,
            correlations=correlations,
            random_seed=random_seed,
            progress_callback=progress_callback,
            baseline_costs=base_costs,
            schedule_data=schedule_data
        )
        
        # Apply cost escalation to each iteration
        escalated_cost_outcomes = np.zeros(iterations)
        
        for i in range(iterations):
            # Get base cost outcome from simulation
            base_cost_outcome = base_results.cost_outcomes[i]
            
            # Apply escalation to the base cost outcome
            escalation_result = self._cost_escalation_modeler.calculate_escalation(
                base_cost=base_cost_outcome,
                start_date=project_start_date,
                end_date=project_end_date,
                cost_categories=cost_categories,
                random_state=random_state
            )
            
            escalated_cost_outcomes[i] = escalation_result.escalated_cost
        
        # Create new simulation results with escalated costs
        escalated_results = SimulationResults(
            simulation_id=base_results.simulation_id + "_escalated",
            timestamp=base_results.timestamp,
            iteration_count=base_results.iteration_count,
            cost_outcomes=escalated_cost_outcomes,
            schedule_outcomes=base_results.schedule_outcomes,
            risk_contributions=base_results.risk_contributions,
            convergence_metrics=base_results.convergence_metrics,
            execution_time=base_results.execution_time
        )
        
        return escalated_results


class RiskInteractionTracker:
    """Helper class to track risk interactions and prevent double-counting."""
    
    def __init__(self, risks: List[Risk], correlations: Optional[CorrelationMatrix] = None):
        """
        Initialize the risk interaction tracker.
        
        Args:
            risks: List of risks to track
            correlations: Optional correlation matrix
        """
        self.risks = {risk.id: risk for risk in risks}
        self.correlations = correlations
        self.interaction_adjustments = {}
    
    def adjust_for_correlations(
        self, 
        risk_id: str, 
        base_impact: float, 
        current_impacts: Dict[str, float],
        correlations: Optional[CorrelationMatrix] = None
    ) -> float:
        """
        Adjust risk impact to prevent double-counting in correlated risks.
        
        Args:
            risk_id: ID of the current risk
            base_impact: Base impact before correlation adjustment
            current_impacts: Dictionary of impacts calculated so far in this iteration
            correlations: Optional correlation matrix
            
        Returns:
            Adjusted impact accounting for correlations
        """
        if not correlations or not current_impacts:
            return base_impact
        
        # Calculate correlation adjustment
        adjustment_factor = 1.0
        total_correlation_effect = 0.0
        
        for other_risk_id, other_impact in current_impacts.items():
            if other_risk_id != risk_id:
                correlation = correlations.get_correlation(risk_id, other_risk_id)
                if abs(correlation) > 0.1:  # Only adjust for meaningful correlations
                    # Reduce impact based on correlation to prevent double-counting
                    correlation_effect = abs(correlation) * 0.1  # 10% reduction per 100% correlation
                    total_correlation_effect += correlation_effect
        
        # Cap the total adjustment to prevent over-correction
        adjustment_factor = max(0.5, 1.0 - min(total_correlation_effect, 0.5))
        
        return base_impact * adjustment_factor


class ConvergenceTracker:
    """Helper class to track simulation convergence."""
    
    def __init__(self):
        """Initialize convergence tracker."""
        self.cost_means = []
        self.cost_variances = []
        self.schedule_means = []
        self.schedule_variances = []
        self.percentile_history = {p: [] for p in [10, 50, 90]}
    
    def update(self, cost_outcomes: np.ndarray, schedule_outcomes: np.ndarray):
        """Update convergence metrics with current outcomes."""
        # Calculate running statistics
        cost_mean = np.mean(cost_outcomes)
        cost_var = np.var(cost_outcomes)
        schedule_mean = np.mean(schedule_outcomes)
        schedule_var = np.var(schedule_outcomes)
        
        self.cost_means.append(cost_mean)
        self.cost_variances.append(cost_var)
        self.schedule_means.append(schedule_mean)
        self.schedule_variances.append(schedule_var)
        
        # Track key percentiles
        for p in self.percentile_history.keys():
            cost_percentile = np.percentile(cost_outcomes, p)
            self.percentile_history[p].append(cost_percentile)
    
    def finalize(self, cost_outcomes: np.ndarray, schedule_outcomes: np.ndarray, iterations: int) -> ConvergenceMetrics:
        """Calculate final convergence metrics."""
        # Calculate stability measures (coefficient of variation of running means)
        mean_stability = 0.0
        variance_stability = 0.0
        
        if len(self.cost_means) > 1:
            mean_cv = np.std(self.cost_means[-10:]) / np.mean(self.cost_means[-10:]) if len(self.cost_means) >= 10 else 1.0
            var_cv = np.std(self.cost_variances[-10:]) / np.mean(self.cost_variances[-10:]) if len(self.cost_variances) >= 10 else 1.0
            mean_stability = 1.0 - min(mean_cv, 1.0)  # Higher is more stable
            variance_stability = 1.0 - min(var_cv, 1.0)
        
        # Calculate percentile stability
        percentile_stability = {}
        for p, history in self.percentile_history.items():
            if len(history) > 1:
                p_cv = np.std(history[-10:]) / np.mean(history[-10:]) if len(history) >= 10 else 1.0
                percentile_stability[float(p)] = 1.0 - min(p_cv, 1.0)
            else:
                percentile_stability[float(p)] = 0.0
        
        # Determine if converged (stability > 0.95 for key metrics)
        converged = (
            mean_stability > 0.95 and 
            variance_stability > 0.95 and 
            all(s > 0.95 for s in percentile_stability.values())
        )
        
        # Estimate iterations to convergence
        iterations_to_convergence = None
        if converged and len(self.cost_means) > 0:
            # Find when stability first exceeded 0.95
            for i, (m_stab, v_stab) in enumerate(zip(
                self._calculate_running_stability(self.cost_means),
                self._calculate_running_stability(self.cost_variances)
            )):
                if m_stab > 0.95 and v_stab > 0.95:
                    iterations_to_convergence = (i + 1) * 1000  # Since we check every 1000 iterations
                    break
        
        return ConvergenceMetrics(
            mean_stability=mean_stability,
            variance_stability=variance_stability,
            percentile_stability=percentile_stability,
            converged=converged,
            iterations_to_convergence=iterations_to_convergence
        )
    
    def _calculate_running_stability(self, values: List[float]) -> List[float]:
        """Calculate running stability for a series of values."""
        stability = []
        for i in range(len(values)):
            if i < 2:
                stability.append(0.0)
            else:
                window = values[max(0, i-9):i+1]  # Last 10 values or less
                if len(window) > 1 and np.mean(window) != 0:
                    cv = np.std(window) / np.mean(window)
                    stability.append(1.0 - min(cv, 1.0))
                else:
                    stability.append(0.0)
        return stability