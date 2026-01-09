"""
Risk Correlation Analyzer - Models dependencies and correlations between risks.

This module provides functionality for:
- Creating and validating correlation matrices
- Generating correlated random samples
- Handling cross-impact relationships between cost and schedule risks
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.linalg import cholesky, LinAlgError
from .models import CorrelationMatrix, ValidationResult, ProbabilityDistribution, CrossImpactModel


class RiskCorrelationAnalyzer:
    """
    Models dependencies and correlations between different risks.
    
    This class handles correlation matrix validation, correlated sampling,
    and cross-impact relationship modeling for Monte Carlo simulations.
    """
    
    def create_correlation_matrix(self, correlations: Dict[Tuple[str, str], float], 
                                risk_ids: List[str]) -> CorrelationMatrix:
        """
        Create a correlation matrix from correlation coefficients.
        
        Args:
            correlations: Dictionary mapping risk ID pairs to correlation coefficients
            risk_ids: List of all risk IDs in the matrix
            
        Returns:
            CorrelationMatrix: Validated correlation matrix
            
        Raises:
            ValueError: If correlation coefficients are invalid
        """
        # Validate correlation coefficients are within bounds
        for (risk1, risk2), correlation in correlations.items():
            if not -1.0 <= correlation <= 1.0:
                raise ValueError(f"Correlation between {risk1} and {risk2} must be between -1 and 1, got {correlation}")
        
        # Create the correlation matrix object
        correlation_matrix = CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
        
        # Validate the matrix is positive definite
        validation_result = self.validate_correlation_matrix(correlation_matrix)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid correlation matrix: {'; '.join(validation_result.errors)}")
        
        return correlation_matrix
    
    def validate_correlation_matrix(self, matrix: CorrelationMatrix) -> ValidationResult:
        """
        Validate correlation matrix for positive definiteness and mathematical consistency.
        
        Args:
            matrix: CorrelationMatrix to validate
            
        Returns:
            ValidationResult: Validation results with errors and warnings
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Check correlation coefficient bounds
        for (risk1, risk2), correlation in matrix.correlations.items():
            if not -1.0 <= correlation <= 1.0:
                errors.append(f"Correlation between {risk1} and {risk2} is {correlation}, must be between -1 and 1")
        
        # Build full correlation matrix for positive definiteness check
        n = len(matrix.risk_ids)
        if n == 0:
            errors.append("Correlation matrix cannot be empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings, recommendations=recommendations)
        
        # Create numpy correlation matrix
        corr_matrix = np.eye(n)  # Start with identity matrix
        risk_id_to_index = {risk_id: i for i, risk_id in enumerate(matrix.risk_ids)}
        
        for (risk1, risk2), correlation in matrix.correlations.items():
            if risk1 in risk_id_to_index and risk2 in risk_id_to_index:
                i, j = risk_id_to_index[risk1], risk_id_to_index[risk2]
                corr_matrix[i, j] = correlation
                corr_matrix[j, i] = correlation  # Ensure symmetry
        
        # Check for positive definiteness using Cholesky decomposition
        try:
            cholesky(corr_matrix, lower=True)
        except LinAlgError:
            errors.append("Correlation matrix is not positive definite")
            recommendations.append("Consider reducing correlation magnitudes or removing conflicting correlations")
        
        # Check for perfect correlations (potential multicollinearity)
        for i in range(n):
            for j in range(i + 1, n):
                if abs(corr_matrix[i, j]) > 0.95:
                    risk1, risk2 = matrix.risk_ids[i], matrix.risk_ids[j]
                    warnings.append(f"Very high correlation ({corr_matrix[i, j]:.3f}) between {risk1} and {risk2}")
                    recommendations.append(f"Consider if {risk1} and {risk2} represent the same underlying risk")
        
        # Check matrix symmetry
        if not np.allclose(corr_matrix, corr_matrix.T):
            errors.append("Correlation matrix is not symmetric")
        
        # Check diagonal elements are 1
        if not np.allclose(np.diag(corr_matrix), 1.0):
            errors.append("Correlation matrix diagonal elements must be 1.0")
        
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def generate_correlated_samples(self, distributions: List[ProbabilityDistribution],
                                  correlations: CorrelationMatrix,
                                  sample_count: int,
                                  random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        """
        Generate correlated random samples using Cholesky decomposition.
        
        Args:
            distributions: List of probability distributions for each risk
            correlations: Correlation matrix defining dependencies
            sample_count: Number of samples to generate
            random_state: Random state for reproducibility
            
        Returns:
            np.ndarray: Array of shape (sample_count, n_risks) with correlated samples
            
        Raises:
            ValueError: If inputs are invalid or correlation matrix is not positive definite
        """
        if random_state is None:
            random_state = np.random.RandomState()
        
        n_risks = len(distributions)
        if n_risks != len(correlations.risk_ids):
            raise ValueError("Number of distributions must match number of risks in correlation matrix")
        
        if sample_count <= 0:
            raise ValueError("Sample count must be positive")
        
        # Validate correlation matrix
        validation_result = self.validate_correlation_matrix(correlations)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid correlation matrix: {'; '.join(validation_result.errors)}")
        
        # Build correlation matrix
        corr_matrix = np.eye(n_risks)
        risk_id_to_index = {risk_id: i for i, risk_id in enumerate(correlations.risk_ids)}
        
        for (risk1, risk2), correlation in correlations.correlations.items():
            if risk1 in risk_id_to_index and risk2 in risk_id_to_index:
                i, j = risk_id_to_index[risk1], risk_id_to_index[risk2]
                corr_matrix[i, j] = correlation
                corr_matrix[j, i] = correlation
        
        # Generate independent standard normal samples
        independent_samples = random_state.standard_normal((sample_count, n_risks))
        
        # Apply Cholesky decomposition to introduce correlations
        try:
            L = cholesky(corr_matrix, lower=True)
            correlated_normal = independent_samples @ L.T
        except LinAlgError as e:
            raise ValueError(f"Failed to decompose correlation matrix: {e}")
        
        # Transform to uniform using normal CDF, then to target distributions
        from scipy.stats import norm
        uniform_samples = norm.cdf(correlated_normal)
        
        # Transform uniform samples to target distributions using inverse CDF
        result_samples = np.zeros((sample_count, n_risks))
        
        for i, distribution in enumerate(distributions):
            # Use the inverse transform method via quantile function
            result_samples[:, i] = self._transform_uniform_to_distribution(
                uniform_samples[:, i], distribution, random_state
            )
        
        return result_samples
    
    def _transform_uniform_to_distribution(self, uniform_samples: np.ndarray,
                                         distribution: ProbabilityDistribution,
                                         random_state: np.random.RandomState) -> np.ndarray:
        """
        Transform uniform samples to target distribution using inverse CDF.
        
        Args:
            uniform_samples: Uniform samples in [0, 1]
            distribution: Target probability distribution
            random_state: Random state for reproducibility
            
        Returns:
            np.ndarray: Samples from target distribution
        """
        from scipy.stats import norm, triang, uniform, beta, lognorm
        
        if distribution.distribution_type.value == "normal":
            return norm.ppf(uniform_samples, 
                          loc=distribution.parameters['mean'],
                          scale=distribution.parameters['std'])
        
        elif distribution.distribution_type.value == "triangular":
            # Scipy triangular uses different parameterization
            a = distribution.parameters['min']
            b = distribution.parameters['max']
            c = distribution.parameters['mode']
            # Convert to scipy's parameterization
            loc = a
            scale = b - a
            c_norm = (c - a) / (b - a) if b != a else 0.5
            return triang.ppf(uniform_samples, c_norm, loc=loc, scale=scale)
        
        elif distribution.distribution_type.value == "uniform":
            return uniform.ppf(uniform_samples,
                             loc=distribution.parameters['min'],
                             scale=distribution.parameters['max'] - distribution.parameters['min'])
        
        elif distribution.distribution_type.value == "beta":
            samples = beta.ppf(uniform_samples,
                             distribution.parameters['alpha'],
                             distribution.parameters['beta'])
            # Apply bounds if specified
            if distribution.bounds:
                a, b = distribution.bounds
                samples = a + samples * (b - a)
            return samples
        
        elif distribution.distribution_type.value == "lognormal":
            return lognorm.ppf(uniform_samples,
                             s=distribution.parameters['sigma'],
                             scale=np.exp(distribution.parameters['mu']))
        
        else:
            raise ValueError(f"Unsupported distribution type: {distribution.distribution_type}")
    
    def model_cross_impacts(self, cost_risk_id: str, schedule_risk_id: str,
                          correlation: float, impact_multiplier: float = 1.0) -> CrossImpactModel:
        """
        Model cross-impact relationships between cost and schedule risks.
        
        Args:
            cost_risk_id: ID of the cost risk
            schedule_risk_id: ID of the schedule risk
            correlation: Correlation coefficient between the risks
            impact_multiplier: How much the primary risk affects the secondary risk
            
        Returns:
            CrossImpactModel: Model representing the cross-impact relationship
        """
        if not -1.0 <= correlation <= 1.0:
            raise ValueError(f"Correlation must be between -1 and 1, got {correlation}")
        
        if impact_multiplier < 0:
            raise ValueError(f"Impact multiplier must be non-negative, got {impact_multiplier}")
        
        return CrossImpactModel(
            primary_risk_id=cost_risk_id,
            secondary_risk_id=schedule_risk_id,
            correlation_coefficient=correlation,
            impact_multiplier=impact_multiplier
        )