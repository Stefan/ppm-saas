"""
Risk Distribution Modeler - Models individual risks as probability distributions.

This module contains functionality for:
- Creating probability distributions from risk data
- Fitting distributions to historical data
- Validating distribution parameters
- Modeling cross-impact relationships
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import scipy.stats as stats
from scipy.optimize import minimize

from .models import (
    ProbabilityDistribution, 
    DistributionType, 
    Risk, 
    RiskData, 
    CrossImpactModel,
    ValidationResult
)


class RiskDistributionModeler:
    """
    Models individual risks as probability distributions and handles distribution fitting.
    
    This class provides functionality for:
    - Creating probability distributions from risk data
    - Three-point estimation for triangular distributions
    - Maximum likelihood estimation for historical data fitting
    - Cross-impact relationship modeling
    - Distribution parameter validation
    """
    
    def __init__(self):
        """Initialize the Risk Distribution Modeler."""
        self.supported_distributions = {
            DistributionType.NORMAL: self._create_normal_distribution,
            DistributionType.TRIANGULAR: self._create_triangular_distribution,
            DistributionType.UNIFORM: self._create_uniform_distribution,
            DistributionType.BETA: self._create_beta_distribution,
            DistributionType.LOGNORMAL: self._create_lognormal_distribution
        }
    
    def create_distribution(self, risk_data: RiskData, 
                          distribution_type: DistributionType,
                          bounds: Optional[Tuple[float, float]] = None) -> ProbabilityDistribution:
        """
        Create a probability distribution from risk data.
        
        Args:
            risk_data: Risk data containing historical impacts or expert estimates
            distribution_type: Type of distribution to create
            bounds: Optional bounds for the distribution
            
        Returns:
            ProbabilityDistribution: Configured probability distribution
            
        Raises:
            ValueError: If distribution type is not supported or data is invalid
        """
        if distribution_type not in self.supported_distributions:
            raise ValueError(f"Unsupported distribution type: {distribution_type}")
        
        # Validate risk data
        if not risk_data.historical_impacts and not risk_data.three_point_estimate:
            raise ValueError("Risk data must contain either historical impacts or three-point estimate")
        
        # Create distribution using appropriate method
        distribution_creator = self.supported_distributions[distribution_type]
        parameters = distribution_creator(risk_data)
        
        # Create and validate the distribution
        distribution = ProbabilityDistribution(
            distribution_type=distribution_type,
            parameters=parameters,
            bounds=bounds
        )
        
        return distribution
    
    def _create_normal_distribution(self, risk_data: RiskData) -> Dict[str, float]:
        """Create normal distribution parameters from risk data."""
        if risk_data.historical_impacts:
            # Use historical data
            data = np.array(risk_data.historical_impacts)
            mean = np.mean(data)
            std = np.std(data, ddof=1)  # Sample standard deviation
            
            # Ensure positive standard deviation
            if std <= 0:
                std = abs(mean) * 0.1 if mean != 0 else 1.0
                
        elif risk_data.three_point_estimate:
            # Convert three-point estimate to normal parameters
            optimistic, most_likely, pessimistic = risk_data.three_point_estimate
            mean = (optimistic + 4 * most_likely + pessimistic) / 6  # PERT formula
            std = (pessimistic - optimistic) / 6  # Approximate standard deviation
            
            if std <= 0:
                raise ValueError("Invalid three-point estimate: pessimistic must be greater than optimistic")
        else:
            raise ValueError("No valid data for normal distribution creation")
        
        return {'mean': mean, 'std': std}
    
    def _create_triangular_distribution(self, risk_data: RiskData) -> Dict[str, float]:
        """Create triangular distribution parameters from risk data."""
        if risk_data.three_point_estimate:
            optimistic, most_likely, pessimistic = risk_data.three_point_estimate
            
            # Validate parameter ordering
            if not (optimistic <= most_likely <= pessimistic):
                raise ValueError("Three-point estimate must satisfy optimistic <= most_likely <= pessimistic")
            
            return {
                'min': optimistic,
                'mode': most_likely,
                'max': pessimistic
            }
        elif risk_data.historical_impacts:
            # Estimate triangular parameters from historical data
            data = np.array(risk_data.historical_impacts)
            min_val = np.min(data)
            max_val = np.max(data)
            mode = np.median(data)  # Use median as mode approximation
            
            return {
                'min': min_val,
                'mode': mode,
                'max': max_val
            }
        else:
            raise ValueError("No valid data for triangular distribution creation")
    
    def _create_uniform_distribution(self, risk_data: RiskData) -> Dict[str, float]:
        """Create uniform distribution parameters from risk data."""
        if risk_data.historical_impacts:
            data = np.array(risk_data.historical_impacts)
            min_val = np.min(data)
            max_val = np.max(data)
            
            # Add small buffer to ensure all data points are within bounds
            range_buffer = (max_val - min_val) * 0.05
            min_val -= range_buffer
            max_val += range_buffer
            
        elif risk_data.three_point_estimate:
            optimistic, _, pessimistic = risk_data.three_point_estimate
            min_val = optimistic
            max_val = pessimistic
        else:
            raise ValueError("No valid data for uniform distribution creation")
        
        if min_val >= max_val:
            raise ValueError("Invalid uniform distribution: min must be less than max")
        
        return {'min': min_val, 'max': max_val}
    
    def _create_beta_distribution(self, risk_data: RiskData) -> Dict[str, float]:
        """Create beta distribution parameters from risk data."""
        if risk_data.historical_impacts:
            # Fit beta distribution to historical data (assuming data is normalized to [0,1])
            data = np.array(risk_data.historical_impacts)
            
            # Normalize data to [0,1] range if needed
            if np.min(data) < 0 or np.max(data) > 1:
                data_min, data_max = np.min(data), np.max(data)
                data = (data - data_min) / (data_max - data_min)
            
            # Method of moments estimation
            mean = np.mean(data)
            var = np.var(data, ddof=1)
            
            # Ensure valid variance for beta distribution
            if var >= mean * (1 - mean):
                var = mean * (1 - mean) * 0.99
            
            # Calculate alpha and beta parameters
            alpha = mean * ((mean * (1 - mean)) / var - 1)
            beta = (1 - mean) * ((mean * (1 - mean)) / var - 1)
            
            # Ensure positive parameters
            alpha = max(alpha, 0.1)
            beta = max(beta, 0.1)
            
        elif risk_data.three_point_estimate:
            # Convert three-point estimate to beta parameters
            optimistic, most_likely, pessimistic = risk_data.three_point_estimate
            
            # Normalize to [0,1] range
            range_val = pessimistic - optimistic
            if range_val <= 0:
                raise ValueError("Invalid three-point estimate for beta distribution")
            
            mode_normalized = (most_likely - optimistic) / range_val
            
            # Use mode and spread to estimate alpha and beta
            # Assuming moderate spread
            alpha = mode_normalized * 6 + 1
            beta = (1 - mode_normalized) * 6 + 1
            
        else:
            raise ValueError("No valid data for beta distribution creation")
        
        return {'alpha': alpha, 'beta': beta}
    
    def _create_lognormal_distribution(self, risk_data: RiskData) -> Dict[str, float]:
        """Create lognormal distribution parameters from risk data."""
        if risk_data.historical_impacts:
            data = np.array(risk_data.historical_impacts)
            
            # Ensure all data is positive for lognormal
            if np.any(data <= 0):
                raise ValueError("Lognormal distribution requires positive data")
            
            # Calculate parameters from log-transformed data
            log_data = np.log(data)
            mu = np.mean(log_data)
            sigma = np.std(log_data, ddof=1)
            
            if sigma <= 0:
                sigma = 0.1  # Minimum sigma value
                
        elif risk_data.three_point_estimate:
            optimistic, most_likely, pessimistic = risk_data.three_point_estimate
            
            if optimistic <= 0 or most_likely <= 0 or pessimistic <= 0:
                raise ValueError("Lognormal distribution requires positive three-point estimates")
            
            # Use geometric mean and spread
            geometric_mean = (optimistic * most_likely * pessimistic) ** (1/3)
            mu = np.log(geometric_mean)
            
            # Estimate sigma from range
            sigma = (np.log(pessimistic) - np.log(optimistic)) / 6
            
            if sigma <= 0:
                sigma = 0.1
                
        else:
            raise ValueError("No valid data for lognormal distribution creation")
        
        return {'mu': mu, 'sigma': sigma}
    
    def validate_distribution_parameters(self, distribution: ProbabilityDistribution) -> ValidationResult:
        """
        Validate distribution parameters for mathematical validity.
        
        Args:
            distribution: Probability distribution to validate
            
        Returns:
            ValidationResult: Validation result with errors and warnings
        """
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # Test sampling to ensure distribution is valid
            test_samples = distribution.sample(100)
            
            # Check for NaN or infinite values
            if np.any(np.isnan(test_samples)) or np.any(np.isinf(test_samples)):
                errors.append("Distribution produces NaN or infinite values")
            
            # Check if samples are within bounds
            if distribution.bounds:
                lower, upper = distribution.bounds
                if np.any(test_samples < lower) or np.any(test_samples > upper):
                    warnings.append("Some samples fall outside specified bounds")
            
            # Distribution-specific validations
            if distribution.distribution_type == DistributionType.NORMAL:
                if distribution.parameters['std'] > abs(distribution.parameters['mean']) * 2:
                    warnings.append("High coefficient of variation may indicate inappropriate normal distribution")
            
            elif distribution.distribution_type == DistributionType.TRIANGULAR:
                min_val = distribution.parameters['min']
                mode = distribution.parameters['mode']
                max_val = distribution.parameters['max']
                
                if abs(mode - (min_val + max_val) / 2) > (max_val - min_val) * 0.4:
                    warnings.append("Mode is far from center, consider if triangular is appropriate")
            
            elif distribution.distribution_type == DistributionType.BETA:
                alpha = distribution.parameters['alpha']
                beta = distribution.parameters['beta']
                
                if alpha < 1 or beta < 1:
                    warnings.append("Beta parameters < 1 create U-shaped distribution")
                
                if alpha > 10 or beta > 10:
                    recommendations.append("High beta parameters create very peaked distribution")
            
        except Exception as e:
            errors.append(f"Distribution validation failed: {str(e)}")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
        
    def create_triangular_from_three_point(self, optimistic: float, most_likely: float, 
                                          pessimistic: float,
                                          bounds: Optional[Tuple[float, float]] = None) -> ProbabilityDistribution:
        """
        Create a triangular distribution from three-point estimation.
        
        Args:
            optimistic: Best-case scenario value
            most_likely: Most likely scenario value  
            pessimistic: Worst-case scenario value
            bounds: Optional bounds for the distribution
            
        Returns:
            ProbabilityDistribution: Triangular distribution
            
        Raises:
            ValueError: If parameter ordering is invalid
        """
        # Validate parameter ordering
        if not (optimistic <= most_likely <= pessimistic):
            raise ValueError(
                f"Three-point estimate must satisfy optimistic ({optimistic}) <= "
                f"most_likely ({most_likely}) <= pessimistic ({pessimistic})"
            )
        
        # Check for degenerate case
        if optimistic == pessimistic:
            raise ValueError("Optimistic and pessimistic values cannot be equal")
        
        # Additional mathematical validity checks
        if not all(np.isfinite([optimistic, most_likely, pessimistic])):
            raise ValueError("All three-point estimate values must be finite")
        
        parameters = {
            'min': optimistic,
            'mode': most_likely,
            'max': pessimistic
        }
        
        distribution = ProbabilityDistribution(
            distribution_type=DistributionType.TRIANGULAR,
            parameters=parameters,
            bounds=bounds
        )
        
        return distribution
    
    def validate_three_point_estimate(self, optimistic: float, most_likely: float, 
                                    pessimistic: float) -> ValidationResult:
        """
        Validate three-point estimation parameters.
        
        Args:
            optimistic: Best-case scenario value
            most_likely: Most likely scenario value
            pessimistic: Worst-case scenario value
            
        Returns:
            ValidationResult: Validation result with errors and warnings
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Check parameter ordering
        if not (optimistic <= most_likely <= pessimistic):
            errors.append(
                f"Parameter ordering violated: optimistic ({optimistic}) <= "
                f"most_likely ({most_likely}) <= pessimistic ({pessimistic})"
            )
        
        # Check for finite values
        if not all(np.isfinite([optimistic, most_likely, pessimistic])):
            errors.append("All three-point estimate values must be finite")
        
        # Check for degenerate cases
        if optimistic == pessimistic:
            errors.append("Optimistic and pessimistic values cannot be equal")
        
        # Warnings for potentially problematic distributions
        if len(errors) == 0:  # Only check if basic validation passes
            range_val = pessimistic - optimistic
            
            # Check if mode is too close to boundaries
            if abs(most_likely - optimistic) < range_val * 0.05:
                warnings.append("Mode is very close to optimistic value, creating highly skewed distribution")
            elif abs(pessimistic - most_likely) < range_val * 0.05:
                warnings.append("Mode is very close to pessimistic value, creating highly skewed distribution")
            
            # Check for very wide ranges
            if range_val > abs(most_likely) * 5:
                warnings.append("Very wide range relative to most likely value may indicate high uncertainty")
            
            # Recommendations for better estimates
            center = (optimistic + pessimistic) / 2
            if abs(most_likely - center) > range_val * 0.3:
                recommendations.append("Consider if the mode should be closer to the center of the range")
            
            if range_val < abs(most_likely) * 0.1:
                recommendations.append("Very narrow range may be better modeled as a normal distribution")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
        
    def fit_distribution_from_historical(self, historical_data: List[float], 
                                        distribution_types: Optional[List[DistributionType]] = None) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """
        Fit appropriate probability distributions to historical data using maximum likelihood estimation.
        
        Args:
            historical_data: List of historical impact values
            distribution_types: Optional list of distribution types to consider. If None, tests all supported types.
            
        Returns:
            Tuple of (best_distribution, fit_statistics) where fit_statistics contains
            goodness-of-fit metrics and model selection information
            
        Raises:
            ValueError: If historical data is invalid or no suitable distribution found
        """
        if not historical_data or len(historical_data) < 3:
            raise ValueError("Historical data must contain at least 3 data points")
        
        data = np.array(historical_data)
        
        # Check for invalid data
        if not np.all(np.isfinite(data)):
            raise ValueError("Historical data must contain only finite values")
        
        if distribution_types is None:
            distribution_types = list(DistributionType)
        
        best_distribution = None
        best_fit_stats = None
        best_score = float('inf')
        
        fit_results = {}
        
        for dist_type in distribution_types:
            try:
                distribution, fit_stats = self._fit_single_distribution(data, dist_type)
                fit_results[dist_type] = (distribution, fit_stats)
                
                # Use AIC (Akaike Information Criterion) for model selection
                if fit_stats['aic'] < best_score:
                    best_score = fit_stats['aic']
                    best_distribution = distribution
                    best_fit_stats = fit_stats
                    best_fit_stats['selected_distribution'] = dist_type
                    
            except (ValueError, RuntimeError) as e:
                # Distribution fitting failed, skip this distribution
                fit_results[dist_type] = (None, {'error': str(e)})
                continue
        
        if best_distribution is None:
            raise ValueError("No suitable distribution could be fitted to the historical data")
        
        # Add comparison information
        best_fit_stats['all_fits'] = fit_results
        best_fit_stats['data_summary'] = {
            'count': len(data),
            'mean': np.mean(data),
            'std': np.std(data, ddof=1),
            'min': np.min(data),
            'max': np.max(data),
            'skewness': self._calculate_skewness(data),
            'kurtosis': self._calculate_kurtosis(data)
        }
        
        return best_distribution, best_fit_stats
    
    def _fit_single_distribution(self, data: np.ndarray, dist_type: DistributionType) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """
        Fit a single distribution type to data using maximum likelihood estimation.
        
        Args:
            data: Historical data array
            dist_type: Distribution type to fit
            
        Returns:
            Tuple of (distribution, fit_statistics)
        """
        if dist_type == DistributionType.NORMAL:
            return self._fit_normal_mle(data)
        elif dist_type == DistributionType.TRIANGULAR:
            return self._fit_triangular_mle(data)
        elif dist_type == DistributionType.UNIFORM:
            return self._fit_uniform_mle(data)
        elif dist_type == DistributionType.BETA:
            return self._fit_beta_mle(data)
        elif dist_type == DistributionType.LOGNORMAL:
            return self._fit_lognormal_mle(data)
        else:
            raise ValueError(f"Unsupported distribution type for MLE fitting: {dist_type}")
    
    def _fit_normal_mle(self, data: np.ndarray) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """Fit normal distribution using maximum likelihood estimation."""
        mean = np.mean(data)
        std = np.std(data, ddof=1)  # Sample standard deviation
        
        if std <= 0:
            std = abs(mean) * 0.01 if mean != 0 else 0.01
        
        distribution = ProbabilityDistribution(
            DistributionType.NORMAL,
            {'mean': mean, 'std': std}
        )
        
        # Calculate goodness-of-fit statistics
        log_likelihood = np.sum(stats.norm.logpdf(data, mean, std))
        aic = 2 * 2 - 2 * log_likelihood  # 2 parameters
        bic = np.log(len(data)) * 2 - 2 * log_likelihood
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(data, lambda x: stats.norm.cdf(x, mean, std))
        
        fit_stats = {
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'parameters': {'mean': mean, 'std': std}
        }
        
        return distribution, fit_stats
    
    def _fit_triangular_mle(self, data: np.ndarray) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """Fit triangular distribution using method of moments and MLE refinement."""
        # Initial estimates using method of moments
        min_val = np.min(data)
        max_val = np.max(data)
        
        # Handle constant data case
        if max_val == min_val:
            # For constant data, create a very narrow triangular distribution
            epsilon = abs(min_val) * 1e-6 if min_val != 0 else 1e-6
            min_val -= epsilon
            max_val += epsilon
            mode = (min_val + max_val) / 2
        else:
            # Estimate mode using kernel density estimation peak
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(data)
            x_range = np.linspace(min_val, max_val, 1000)
            density = kde(x_range)
            mode = x_range[np.argmax(density)]
            
            # Ensure mode is within bounds
            mode = np.clip(mode, min_val, max_val)
        
        distribution = ProbabilityDistribution(
            DistributionType.TRIANGULAR,
            {'min': min_val, 'mode': mode, 'max': max_val}
        )
        
        # Calculate goodness-of-fit statistics
        scale = max_val - min_val
        c = (mode - min_val) / scale if scale > 0 else 0.5
        
        log_likelihood = np.sum(stats.triang.logpdf(
            data, 
            c=c,
            loc=min_val,
            scale=scale
        ))
        
        aic = 2 * 3 - 2 * log_likelihood  # 3 parameters
        bic = np.log(len(data)) * 3 - 2 * log_likelihood
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(
            data, 
            lambda x: stats.triang.cdf(
                x, 
                c=c,
                loc=min_val,
                scale=scale
            )
        )
        
        fit_stats = {
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'parameters': {'min': min_val, 'mode': mode, 'max': max_val}
        }
        
        return distribution, fit_stats
    
    def _fit_uniform_mle(self, data: np.ndarray) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """Fit uniform distribution using maximum likelihood estimation."""
        min_val = np.min(data)
        max_val = np.max(data)
        
        # Add small buffer to ensure all data points are within bounds
        range_buffer = (max_val - min_val) * 0.01
        min_val -= range_buffer
        max_val += range_buffer
        
        distribution = ProbabilityDistribution(
            DistributionType.UNIFORM,
            {'min': min_val, 'max': max_val}
        )
        
        # Calculate goodness-of-fit statistics
        log_likelihood = np.sum(stats.uniform.logpdf(data, min_val, max_val - min_val))
        aic = 2 * 2 - 2 * log_likelihood  # 2 parameters
        bic = np.log(len(data)) * 2 - 2 * log_likelihood
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(
            data, 
            lambda x: stats.uniform.cdf(x, min_val, max_val - min_val)
        )
        
        fit_stats = {
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'parameters': {'min': min_val, 'max': max_val}
        }
        
        return distribution, fit_stats
    
    def _fit_beta_mle(self, data: np.ndarray) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """Fit beta distribution using maximum likelihood estimation."""
        # Normalize data to [0,1] if needed
        data_min, data_max = np.min(data), np.max(data)
        
        if data_min < 0 or data_max > 1:
            # Handle constant data case
            if data_max == data_min:
                # For constant data, create a very narrow range
                epsilon = abs(data_min) * 1e-6 if data_min != 0 else 1e-6
                data_min -= epsilon
                data_max += epsilon
            
            normalized_data = (data - data_min) / (data_max - data_min)
        else:
            normalized_data = data
        
        # Ensure data is strictly within (0,1) for beta distribution
        epsilon = 1e-6
        normalized_data = np.clip(normalized_data, epsilon, 1 - epsilon)
        
        # Use scipy's MLE fitting
        alpha_mle, beta_mle, _, _ = stats.beta.fit(normalized_data, floc=0, fscale=1)
        
        distribution = ProbabilityDistribution(
            DistributionType.BETA,
            {'alpha': alpha_mle, 'beta': beta_mle}
        )
        
        # Calculate goodness-of-fit statistics
        log_likelihood = np.sum(stats.beta.logpdf(normalized_data, alpha_mle, beta_mle))
        aic = 2 * 2 - 2 * log_likelihood  # 2 parameters
        bic = np.log(len(data)) * 2 - 2 * log_likelihood
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(
            normalized_data, 
            lambda x: stats.beta.cdf(x, alpha_mle, beta_mle)
        )
        
        fit_stats = {
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'parameters': {'alpha': alpha_mle, 'beta': beta_mle},
            'data_transformation': {
                'original_min': data_min,
                'original_max': data_max,
                'normalized': data_min < 0 or data_max > 1
            }
        }
        
        return distribution, fit_stats
    
    def _fit_lognormal_mle(self, data: np.ndarray) -> Tuple[ProbabilityDistribution, Dict[str, Any]]:
        """Fit lognormal distribution using maximum likelihood estimation."""
        if np.any(data <= 0):
            raise ValueError("Lognormal distribution requires positive data")
        
        # Use scipy's MLE fitting
        sigma_mle, _, mu_mle = stats.lognorm.fit(data, floc=0)
        
        # Convert to our parameterization (mu, sigma)
        mu = np.log(mu_mle)
        sigma = sigma_mle
        
        distribution = ProbabilityDistribution(
            DistributionType.LOGNORMAL,
            {'mu': mu, 'sigma': sigma}
        )
        
        # Calculate goodness-of-fit statistics
        log_likelihood = np.sum(stats.lognorm.logpdf(data, sigma, scale=np.exp(mu)))
        aic = 2 * 2 - 2 * log_likelihood  # 2 parameters
        bic = np.log(len(data)) * 2 - 2 * log_likelihood
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(
            data, 
            lambda x: stats.lognorm.cdf(x, sigma, scale=np.exp(mu))
        )
        
        fit_stats = {
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'ks_statistic': ks_statistic,
            'ks_p_value': ks_p_value,
            'parameters': {'mu': mu, 'sigma': sigma}
        }
        
        return distribution, fit_stats
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate sample skewness."""
        n = len(data)
        if n < 3:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        skewness = (n / ((n - 1) * (n - 2))) * np.sum(((data - mean) / std) ** 3)
        return skewness
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate sample excess kurtosis."""
        n = len(data)
        if n < 4:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((data - mean) / std) ** 4) - \
                  (3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
        return kurtosis
    
    def perform_goodness_of_fit_test(self, data: List[float], 
                                   distribution: ProbabilityDistribution,
                                   significance_level: float = 0.05) -> Dict[str, Any]:
        """
        Perform comprehensive goodness-of-fit testing for a distribution.
        
        Args:
            data: Historical data to test against
            distribution: Probability distribution to test
            significance_level: Significance level for statistical tests
            
        Returns:
            Dictionary containing test results and recommendations
        """
        data_array = np.array(data)
        
        # Generate CDF function for the distribution
        if distribution.distribution_type == DistributionType.NORMAL:
            cdf_func = lambda x: stats.norm.cdf(x, distribution.parameters['mean'], distribution.parameters['std'])
        elif distribution.distribution_type == DistributionType.TRIANGULAR:
            params = distribution.parameters
            scale = params['max'] - params['min']
            if scale > 0:
                c = (params['mode'] - params['min']) / scale
            else:
                c = 0.5  # Default for degenerate case
            cdf_func = lambda x: stats.triang.cdf(x, c, loc=params['min'], scale=scale)
        elif distribution.distribution_type == DistributionType.UNIFORM:
            params = distribution.parameters
            cdf_func = lambda x: stats.uniform.cdf(x, params['min'], params['max'] - params['min'])
        elif distribution.distribution_type == DistributionType.BETA:
            params = distribution.parameters
            cdf_func = lambda x: stats.beta.cdf(x, params['alpha'], params['beta'])
        elif distribution.distribution_type == DistributionType.LOGNORMAL:
            params = distribution.parameters
            cdf_func = lambda x: stats.lognorm.cdf(x, params['sigma'], scale=np.exp(params['mu']))
        else:
            raise ValueError(f"Goodness-of-fit test not implemented for {distribution.distribution_type}")
        
        # Kolmogorov-Smirnov test
        ks_statistic, ks_p_value = stats.kstest(data_array, cdf_func)
        
        # Anderson-Darling test (if available for the distribution)
        ad_statistic = None
        ad_p_value = None
        
        if distribution.distribution_type == DistributionType.NORMAL:
            ad_result = stats.anderson(data_array, dist='norm')
            ad_statistic = ad_result.statistic
            # Approximate p-value calculation for Anderson-Darling
            ad_p_value = 1.0 if ad_statistic < ad_result.critical_values[0] else 0.01
        
        # Chi-square goodness-of-fit test
        # Create bins for the test
        n_bins = min(10, max(5, int(np.sqrt(len(data_array)))))
        observed_freq, bin_edges = np.histogram(data_array, bins=n_bins)
        
        # Calculate expected frequencies
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_widths = bin_edges[1:] - bin_edges[:-1]
        
        expected_freq = []
        for i in range(len(bin_edges) - 1):
            prob = cdf_func(bin_edges[i + 1]) - cdf_func(bin_edges[i])
            expected_freq.append(prob * len(data_array))
        
        expected_freq = np.array(expected_freq)
        
        # Combine bins with low expected frequencies
        min_expected = 5
        combined_observed = []
        combined_expected = []
        
        current_obs = 0
        current_exp = 0
        
        for obs, exp in zip(observed_freq, expected_freq):
            current_obs += obs
            current_exp += exp
            
            if current_exp >= min_expected:
                combined_observed.append(current_obs)
                combined_expected.append(current_exp)
                current_obs = 0
                current_exp = 0
        
        # Add remaining to last bin if any
        if current_obs > 0 or current_exp > 0:
            if combined_observed:
                combined_observed[-1] += current_obs
                combined_expected[-1] += current_exp
            else:
                combined_observed.append(current_obs)
                combined_expected.append(current_exp)
        
        # Perform chi-square test
        chi2_statistic = None
        chi2_p_value = None
        
        if len(combined_observed) > 1:
            try:
                chi2_statistic, chi2_p_value = stats.chisquare(combined_observed, combined_expected)
            except ValueError as e:
                # Handle numerical precision issues in chi-square test
                if "sum of the observed frequencies must agree" in str(e):
                    # Skip chi-square test if there are precision issues
                    chi2_statistic = None
                    chi2_p_value = None
                else:
                    raise
        
        # Compile results
        test_results = {
            'kolmogorov_smirnov': {
                'statistic': ks_statistic,
                'p_value': ks_p_value,
                'significant': bool(ks_p_value < significance_level)
            },
            'anderson_darling': {
                'statistic': ad_statistic,
                'p_value': ad_p_value,
                'significant': bool(ad_p_value is not None and ad_p_value < significance_level)
            } if ad_statistic is not None else None,
            'chi_square': {
                'statistic': chi2_statistic,
                'p_value': chi2_p_value,
                'significant': bool(chi2_p_value is not None and chi2_p_value < significance_level)
            } if chi2_statistic is not None else None,
            'overall_assessment': self._assess_goodness_of_fit(ks_p_value, ad_p_value, chi2_p_value, significance_level),
            'sample_size': len(data_array),
            'significance_level': significance_level
        }
        
        return test_results
    
    def _assess_goodness_of_fit(self, ks_p: float, ad_p: Optional[float], 
                              chi2_p: Optional[float], alpha: float) -> Dict[str, Any]:
        """Assess overall goodness-of-fit based on multiple tests."""
        significant_tests = []
        
        if ks_p < alpha:
            significant_tests.append('Kolmogorov-Smirnov')
        
        if ad_p is not None and ad_p < alpha:
            significant_tests.append('Anderson-Darling')
        
        if chi2_p is not None and chi2_p < alpha:
            significant_tests.append('Chi-square')
        
        if not significant_tests:
            assessment = "GOOD_FIT"
            recommendation = "Distribution provides a good fit to the data"
        elif len(significant_tests) == 1:
            assessment = "MARGINAL_FIT"
            recommendation = f"Distribution shows some deviation ({significant_tests[0]} test significant). Consider alternative distributions."
        else:
            assessment = "POOR_FIT"
            recommendation = f"Distribution shows poor fit ({', '.join(significant_tests)} tests significant). Consider alternative distributions."
        
        return {
            'assessment': assessment,
            'recommendation': recommendation,
            'significant_tests': significant_tests,
            'min_p_value': min(p for p in [ks_p, ad_p, chi2_p] if p is not None)
        }
    
    def model_cross_impacts(self, cost_risk: Risk, schedule_risk: Risk, 
                          correlation: float) -> CrossImpactModel:
        """
        Model cross-impact relationships between cost and schedule risks.
        
        Args:
            cost_risk: Primary cost risk
            schedule_risk: Secondary schedule risk affected by cost risk
            correlation: Correlation coefficient between the risks
            
        Returns:
            CrossImpactModel: Cross-impact relationship model
            
        Raises:
            ValueError: If correlation is outside [-1, 1] bounds
        """
        if not -1.0 <= correlation <= 1.0:
            raise ValueError(f"Correlation coefficient must be between -1 and 1, got {correlation}")
        
        # Calculate impact multiplier based on risk characteristics
        # This is a simplified model - in practice, this would be more sophisticated
        cost_baseline = cost_risk.baseline_impact
        schedule_baseline = schedule_risk.baseline_impact
        
        # Impact multiplier represents how much the primary risk affects the secondary
        # Higher correlation leads to higher impact multiplier
        base_multiplier = abs(correlation) * 0.5  # Base multiplier up to 50%
        
        # Adjust based on relative magnitudes of the risks
        if cost_baseline > 0 and schedule_baseline > 0:
            magnitude_ratio = min(cost_baseline / schedule_baseline, 2.0)  # Cap at 2x
            impact_multiplier = base_multiplier * magnitude_ratio
        else:
            impact_multiplier = base_multiplier
        
        return CrossImpactModel(
            primary_risk_id=cost_risk.id,
            secondary_risk_id=schedule_risk.id,
            correlation_coefficient=correlation,
            impact_multiplier=impact_multiplier
        )