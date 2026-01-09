"""
Model Validation Capabilities for Monte Carlo Risk Simulations.

This module provides comprehensive model validation including goodness-of-fit tests
for probability distributions and correlation matrix validation and consistency checking.
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from scipy import stats
from scipy.linalg import LinAlgError
import warnings

from .models import (
    Risk, ProbabilityDistribution, CorrelationMatrix, ValidationResult,
    DistributionType, RiskData, ImpactType
)


class DistributionValidator:
    """
    Validator for probability distributions with goodness-of-fit testing.
    
    Provides comprehensive validation of probability distributions including
    parameter validation, goodness-of-fit tests, and distribution fitting quality assessment.
    """
    
    def __init__(self):
        """Initialize the distribution validator."""
        self._supported_tests = {
            DistributionType.NORMAL: ['kolmogorov_smirnov', 'shapiro_wilk', 'anderson_darling'],
            DistributionType.TRIANGULAR: ['kolmogorov_smirnov', 'chi_square'],
            DistributionType.UNIFORM: ['kolmogorov_smirnov', 'chi_square'],
            DistributionType.BETA: ['kolmogorov_smirnov', 'chi_square'],
            DistributionType.LOGNORMAL: ['kolmogorov_smirnov', 'anderson_darling']
        }
    
    def validate_distribution(
        self,
        distribution: ProbabilityDistribution,
        historical_data: Optional[List[float]] = None,
        significance_level: float = 0.05
    ) -> ValidationResult:
        """
        Validate a probability distribution with optional goodness-of-fit testing.
        
        Args:
            distribution: ProbabilityDistribution to validate
            historical_data: Optional historical data for goodness-of-fit testing
            significance_level: Significance level for statistical tests (default 0.05)
            
        Returns:
            ValidationResult with validation status and detailed test results
        """
        errors = []
        warnings_list = []
        recommendations = []
        
        # Basic parameter validation (already done in ProbabilityDistribution.__post_init__)
        try:
            # Test sampling from distribution
            test_samples = distribution.sample(1000)
            if not np.all(np.isfinite(test_samples)):
                errors.append("Distribution produces non-finite samples")
            
            # Check for reasonable sample range
            sample_range = np.ptp(test_samples)
            if sample_range == 0:
                errors.append("Distribution produces constant values (zero variance)")
            elif sample_range < 1e-10:
                warnings_list.append("Distribution has very small variance, may indicate numerical issues")
            
        except Exception as e:
            errors.append(f"Failed to sample from distribution: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings_list, recommendations=recommendations)
        
        # Perform goodness-of-fit tests if historical data is provided
        if historical_data and len(historical_data) > 0:
            fit_results = self._perform_goodness_of_fit_tests(
                distribution, historical_data, significance_level
            )
            
            # Add fit test results to validation
            if fit_results['failed_tests']:
                warnings_list.extend([f"Failed goodness-of-fit test: {test}" for test in fit_results['failed_tests']])
            
            if fit_results['passed_tests']:
                recommendations.append(f"Passed goodness-of-fit tests: {', '.join(fit_results['passed_tests'])}")
            
            # Overall fit quality assessment
            if fit_results['overall_fit_quality'] < 0.3:
                errors.append(f"Poor overall fit quality: {fit_results['overall_fit_quality']:.3f}")
            elif fit_results['overall_fit_quality'] < 0.7:
                warnings_list.append(f"Moderate fit quality: {fit_results['overall_fit_quality']:.3f}")
            else:
                recommendations.append(f"Good fit quality: {fit_results['overall_fit_quality']:.3f}")
        
        # Distribution-specific validation
        dist_validation = self._validate_distribution_specific(distribution)
        errors.extend(dist_validation['errors'])
        warnings_list.extend(dist_validation['warnings'])
        recommendations.extend(dist_validation['recommendations'])
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings_list,
            recommendations=recommendations
        )
    
    def _perform_goodness_of_fit_tests(
        self,
        distribution: ProbabilityDistribution,
        historical_data: List[float],
        significance_level: float
    ) -> Dict[str, Any]:
        """
        Perform goodness-of-fit tests for a distribution against historical data.
        
        Args:
            distribution: Distribution to test
            historical_data: Historical data for comparison
            significance_level: Significance level for tests
            
        Returns:
            Dictionary containing test results and overall fit quality
        """
        data = np.array(historical_data)
        if len(data) < 10:
            return {
                'passed_tests': [],
                'failed_tests': [],
                'test_statistics': {},
                'p_values': {},
                'overall_fit_quality': 0.0,
                'error': 'Insufficient data for goodness-of-fit testing (minimum 10 samples required)'
            }
        
        available_tests = self._supported_tests.get(distribution.distribution_type, ['kolmogorov_smirnov'])
        passed_tests = []
        failed_tests = []
        test_statistics = {}
        p_values = {}
        
        for test_name in available_tests:
            try:
                if test_name == 'kolmogorov_smirnov':
                    result = self._kolmogorov_smirnov_test(distribution, data)
                elif test_name == 'shapiro_wilk':
                    result = self._shapiro_wilk_test(data)
                elif test_name == 'anderson_darling':
                    result = self._anderson_darling_test(distribution, data)
                elif test_name == 'chi_square':
                    result = self._chi_square_test(distribution, data)
                else:
                    continue
                
                test_statistics[test_name] = result['statistic']
                p_values[test_name] = result['p_value']
                
                if result['p_value'] > significance_level:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
                    
            except Exception as e:
                failed_tests.append(f"{test_name} (error: {str(e)})")
        
        # Calculate overall fit quality
        overall_fit_quality = self._calculate_overall_fit_quality(
            distribution, data, test_statistics, p_values
        )
        
        return {
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'test_statistics': test_statistics,
            'p_values': p_values,
            'overall_fit_quality': overall_fit_quality
        }
    
    def _kolmogorov_smirnov_test(
        self,
        distribution: ProbabilityDistribution,
        data: np.ndarray
    ) -> Dict[str, float]:
        """Perform Kolmogorov-Smirnov test."""
        # Generate theoretical CDF values
        sorted_data = np.sort(data)
        
        if distribution.distribution_type == DistributionType.NORMAL:
            theoretical_cdf = stats.norm.cdf(
                sorted_data,
                loc=distribution.parameters['mean'],
                scale=distribution.parameters['std']
            )
        elif distribution.distribution_type == DistributionType.UNIFORM:
            theoretical_cdf = stats.uniform.cdf(
                sorted_data,
                loc=distribution.parameters['min'],
                scale=distribution.parameters['max'] - distribution.parameters['min']
            )
        elif distribution.distribution_type == DistributionType.BETA:
            theoretical_cdf = stats.beta.cdf(
                sorted_data,
                a=distribution.parameters['alpha'],
                b=distribution.parameters['beta']
            )
        elif distribution.distribution_type == DistributionType.LOGNORMAL:
            theoretical_cdf = stats.lognorm.cdf(
                sorted_data,
                s=distribution.parameters['sigma'],
                scale=np.exp(distribution.parameters['mu'])
            )
        elif distribution.distribution_type == DistributionType.TRIANGULAR:
            # Triangular distribution CDF calculation
            a, b, c = distribution.parameters['min'], distribution.parameters['max'], distribution.parameters['mode']
            theoretical_cdf = np.zeros_like(sorted_data)
            
            mask1 = (sorted_data >= a) & (sorted_data <= c)
            mask2 = (sorted_data > c) & (sorted_data <= b)
            
            theoretical_cdf[mask1] = (sorted_data[mask1] - a)**2 / ((b - a) * (c - a))
            theoretical_cdf[mask2] = 1 - (b - sorted_data[mask2])**2 / ((b - a) * (b - c))
            theoretical_cdf[sorted_data > b] = 1.0
        else:
            raise ValueError(f"KS test not implemented for {distribution.distribution_type}")
        
        # Calculate empirical CDF
        n = len(data)
        empirical_cdf = np.arange(1, n + 1) / n
        
        # Calculate KS statistic
        ks_statistic = np.max(np.abs(empirical_cdf - theoretical_cdf))
        
        # Calculate p-value (approximation for large n)
        if n >= 35:
            p_value = 2 * np.exp(-2 * n * ks_statistic**2)
        else:
            # Use exact calculation for small samples (simplified)
            p_value = 1.0 - stats.ksone.cdf(ks_statistic * np.sqrt(n))
        
        return {'statistic': ks_statistic, 'p_value': max(0.0, min(1.0, p_value))}
    
    def _shapiro_wilk_test(self, data: np.ndarray) -> Dict[str, float]:
        """Perform Shapiro-Wilk test for normality."""
        if len(data) < 3 or len(data) > 5000:
            raise ValueError("Shapiro-Wilk test requires 3-5000 samples")
        
        statistic, p_value = stats.shapiro(data)
        return {'statistic': statistic, 'p_value': p_value}
    
    def _anderson_darling_test(
        self,
        distribution: ProbabilityDistribution,
        data: np.ndarray
    ) -> Dict[str, float]:
        """Perform Anderson-Darling test."""
        if distribution.distribution_type == DistributionType.NORMAL:
            result = stats.anderson(data, dist='norm')
            # Convert critical values to approximate p-value
            critical_values = result.critical_values
            significance_levels = result.significance_levels
            
            # Find approximate p-value
            statistic = result.statistic
            if statistic < critical_values[0]:
                p_value = 1 - significance_levels[0] / 100
            elif statistic > critical_values[-1]:
                p_value = significance_levels[-1] / 100
            else:
                # Interpolate
                for i in range(len(critical_values) - 1):
                    if critical_values[i] <= statistic <= critical_values[i + 1]:
                        # Linear interpolation
                        ratio = (statistic - critical_values[i]) / (critical_values[i + 1] - critical_values[i])
                        p_value = (significance_levels[i] + ratio * (significance_levels[i + 1] - significance_levels[i])) / 100
                        break
                else:
                    p_value = 0.05  # Default
            
            return {'statistic': statistic, 'p_value': p_value}
        else:
            raise ValueError(f"Anderson-Darling test not implemented for {distribution.distribution_type}")
    
    def _chi_square_test(
        self,
        distribution: ProbabilityDistribution,
        data: np.ndarray,
        num_bins: Optional[int] = None
    ) -> Dict[str, float]:
        """Perform Chi-square goodness-of-fit test."""
        if len(data) < 50:
            raise ValueError("Chi-square test requires at least 50 samples")
        
        # Determine number of bins
        if num_bins is None:
            num_bins = min(20, max(5, int(np.sqrt(len(data)))))
        
        # Create histogram
        observed_freq, bin_edges = np.histogram(data, bins=num_bins)
        
        # Calculate expected frequencies
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_width = bin_edges[1] - bin_edges[0]
        
        # Generate expected frequencies based on distribution
        expected_freq = np.zeros(num_bins)
        for i in range(num_bins):
            # Calculate probability for each bin
            if distribution.distribution_type == DistributionType.UNIFORM:
                a, b = distribution.parameters['min'], distribution.parameters['max']
                if bin_edges[i] >= a and bin_edges[i + 1] <= b:
                    prob = bin_width / (b - a)
                else:
                    # Handle partial overlap
                    overlap_start = max(bin_edges[i], a)
                    overlap_end = min(bin_edges[i + 1], b)
                    prob = max(0, overlap_end - overlap_start) / (b - a)
            else:
                # Use sampling approximation for other distributions
                samples = distribution.sample(10000)
                bin_prob = np.sum((samples >= bin_edges[i]) & (samples < bin_edges[i + 1])) / 10000
                prob = bin_prob
            
            expected_freq[i] = prob * len(data)
        
        # Ensure minimum expected frequency
        expected_freq = np.maximum(expected_freq, 1.0)
        
        # Calculate chi-square statistic
        chi_square_stat = np.sum((observed_freq - expected_freq)**2 / expected_freq)
        
        # Degrees of freedom (bins - 1 - number of estimated parameters)
        num_params = len(distribution.parameters)
        df = max(1, num_bins - 1 - num_params)
        
        # Calculate p-value
        p_value = 1 - stats.chi2.cdf(chi_square_stat, df)
        
        return {'statistic': chi_square_stat, 'p_value': p_value}
    
    def _calculate_overall_fit_quality(
        self,
        distribution: ProbabilityDistribution,
        data: np.ndarray,
        test_statistics: Dict[str, float],
        p_values: Dict[str, float]
    ) -> float:
        """
        Calculate overall fit quality score based on multiple test results.
        
        Returns a score between 0 and 1, where 1 indicates perfect fit.
        """
        if not p_values:
            return 0.0
        
        # Weight different tests
        test_weights = {
            'kolmogorov_smirnov': 0.4,
            'shapiro_wilk': 0.3,
            'anderson_darling': 0.3,
            'chi_square': 0.2
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for test_name, p_value in p_values.items():
            weight = test_weights.get(test_name, 0.1)
            # Convert p-value to quality score (higher p-value = better fit)
            score = min(1.0, p_value * 2)  # Scale p-values to 0-1 range
            weighted_score += weight * score
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        base_quality = weighted_score / total_weight
        
        # Additional quality factors
        # Check if distribution parameters are reasonable for the data
        data_mean = np.mean(data)
        data_std = np.std(data)
        
        parameter_reasonableness = 1.0
        if distribution.distribution_type == DistributionType.NORMAL:
            mean_diff = abs(distribution.parameters['mean'] - data_mean) / max(data_std, 1e-6)
            std_ratio = distribution.parameters['std'] / max(data_std, 1e-6)
            parameter_reasonableness = max(0.0, 1.0 - mean_diff * 0.1) * max(0.0, 1.0 - abs(1 - std_ratio) * 0.2)
        
        # Combine base quality with parameter reasonableness
        overall_quality = base_quality * 0.8 + parameter_reasonableness * 0.2
        
        return max(0.0, min(1.0, overall_quality))
    
    def _validate_distribution_specific(
        self,
        distribution: ProbabilityDistribution
    ) -> Dict[str, List[str]]:
        """Perform distribution-specific validation checks."""
        errors = []
        warnings_list = []
        recommendations = []
        
        if distribution.distribution_type == DistributionType.TRIANGULAR:
            min_val = distribution.parameters['min']
            mode_val = distribution.parameters['mode']
            max_val = distribution.parameters['max']
            
            # Check for degenerate cases
            if min_val == max_val:
                errors.append("Triangular distribution has zero range (min = max)")
            elif mode_val == min_val or mode_val == max_val:
                warnings_list.append("Triangular distribution mode is at boundary (may behave like uniform)")
            
            # Check for reasonable spread
            range_val = max_val - min_val
            mode_offset = abs(mode_val - (min_val + max_val) / 2)
            if mode_offset / range_val > 0.4:
                warnings_list.append("Triangular distribution is highly skewed")
        
        elif distribution.distribution_type == DistributionType.NORMAL:
            std_val = distribution.parameters['std']
            if std_val > 1000:
                warnings_list.append("Normal distribution has very large standard deviation")
            elif std_val < 1e-6:
                warnings_list.append("Normal distribution has very small standard deviation")
        
        elif distribution.distribution_type == DistributionType.BETA:
            alpha = distribution.parameters['alpha']
            beta = distribution.parameters['beta']
            
            if alpha < 1 or beta < 1:
                warnings_list.append("Beta distribution parameters < 1 may produce U-shaped distributions")
            elif alpha > 100 or beta > 100:
                warnings_list.append("Beta distribution parameters > 100 may cause numerical issues")
        
        return {
            'errors': errors,
            'warnings': warnings_list,
            'recommendations': recommendations
        }


class CorrelationValidator:
    """
    Validator for correlation matrices with consistency checking.
    
    Provides comprehensive validation of correlation matrices including
    positive definiteness checking, bounds validation, and mathematical consistency.
    """
    
    def __init__(self):
        """Initialize the correlation validator."""
        pass
    
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
        errors = []
        warnings_list = []
        recommendations = []
        
        # Basic validation (already done in CorrelationMatrix.__post_init__)
        risk_ids = correlation_matrix.risk_ids
        correlations = correlation_matrix.correlations
        
        if len(risk_ids) == 0:
            errors.append("Correlation matrix has no risk IDs")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings_list, recommendations=recommendations)
        
        # Build numpy matrix for advanced validation
        try:
            numpy_matrix = self._build_numpy_matrix(correlation_matrix)
        except Exception as e:
            errors.append(f"Failed to build correlation matrix: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings_list, recommendations=recommendations)
        
        # Check matrix properties
        matrix_validation = self._validate_matrix_properties(numpy_matrix, tolerance)
        errors.extend(matrix_validation['errors'])
        warnings_list.extend(matrix_validation['warnings'])
        recommendations.extend(matrix_validation['recommendations'])
        
        # Check for problematic correlation patterns
        pattern_validation = self._validate_correlation_patterns(correlation_matrix)
        warnings_list.extend(pattern_validation['warnings'])
        recommendations.extend(pattern_validation['recommendations'])
        
        # Validate correlation strength distribution
        strength_validation = self._validate_correlation_strengths(correlations)
        warnings_list.extend(strength_validation['warnings'])
        recommendations.extend(strength_validation['recommendations'])
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings_list,
            recommendations=recommendations
        )
    
    def _build_numpy_matrix(self, correlation_matrix: CorrelationMatrix) -> np.ndarray:
        """Build numpy correlation matrix from CorrelationMatrix object."""
        n = len(correlation_matrix.risk_ids)
        matrix = np.eye(n)  # Start with identity matrix
        
        # Fill in correlations
        for i, risk1 in enumerate(correlation_matrix.risk_ids):
            for j, risk2 in enumerate(correlation_matrix.risk_ids):
                if i != j:
                    correlation = correlation_matrix.get_correlation(risk1, risk2)
                    matrix[i, j] = correlation
        
        return matrix
    
    def _validate_matrix_properties(
        self,
        matrix: np.ndarray,
        tolerance: float
    ) -> Dict[str, List[str]]:
        """Validate mathematical properties of the correlation matrix."""
        errors = []
        warnings_list = []
        recommendations = []
        
        n = matrix.shape[0]
        
        # Check symmetry
        if not np.allclose(matrix, matrix.T, atol=tolerance):
            errors.append("Correlation matrix is not symmetric")
        
        # Check diagonal elements
        diagonal = np.diag(matrix)
        if not np.allclose(diagonal, 1.0, atol=tolerance):
            errors.append("Correlation matrix diagonal elements are not 1.0")
        
        # Check bounds
        off_diagonal = matrix[np.triu_indices(n, k=1)]
        if np.any(off_diagonal < -1 - tolerance) or np.any(off_diagonal > 1 + tolerance):
            errors.append("Correlation coefficients outside [-1, 1] bounds")
        
        # Check positive definiteness
        try:
            eigenvalues = np.linalg.eigvals(matrix)
            min_eigenvalue = np.min(eigenvalues)
            
            if min_eigenvalue < -tolerance:
                errors.append(f"Correlation matrix is not positive definite (min eigenvalue: {min_eigenvalue:.6f})")
            elif min_eigenvalue < tolerance:
                warnings_list.append(f"Correlation matrix is barely positive definite (min eigenvalue: {min_eigenvalue:.6f})")
            
            # Check condition number
            max_eigenvalue = np.max(eigenvalues)
            if min_eigenvalue > 0:
                condition_number = max_eigenvalue / min_eigenvalue
                if condition_number > 1e12:
                    errors.append(f"Correlation matrix is ill-conditioned (condition number: {condition_number:.2e})")
                elif condition_number > 1e6:
                    warnings_list.append(f"Correlation matrix has high condition number: {condition_number:.2e}")
            
        except LinAlgError as e:
            errors.append(f"Failed to compute eigenvalues: {str(e)}")
        
        # Check for near-singular matrix
        try:
            det = np.linalg.det(matrix)
            if abs(det) < tolerance:
                errors.append(f"Correlation matrix is nearly singular (determinant: {det:.2e})")
            elif abs(det) < 1e-6:
                warnings_list.append(f"Correlation matrix has small determinant: {det:.2e}")
        except LinAlgError:
            warnings_list.append("Could not compute matrix determinant")
        
        # Recommendations for improvement
        if len(errors) == 0 and len(warnings_list) > 0:
            recommendations.append("Consider reviewing correlation coefficients for numerical stability")
        
        if n > 10 and len(off_diagonal[np.abs(off_diagonal) > 0.8]) > n // 2:
            recommendations.append("Many high correlations detected - consider risk grouping or dimensionality reduction")
        
        return {
            'errors': errors,
            'warnings': warnings_list,
            'recommendations': recommendations
        }
    
    def _validate_correlation_patterns(
        self,
        correlation_matrix: CorrelationMatrix
    ) -> Dict[str, List[str]]:
        """Validate correlation patterns for logical consistency."""
        warnings_list = []
        recommendations = []
        
        correlations = correlation_matrix.correlations
        risk_ids = correlation_matrix.risk_ids
        
        # Check for perfect correlations
        perfect_correlations = [(r1, r2) for (r1, r2), corr in correlations.items() if abs(corr) >= 0.99]
        if perfect_correlations:
            warnings_list.append(f"Perfect or near-perfect correlations detected: {perfect_correlations}")
            recommendations.append("Consider combining perfectly correlated risks or reviewing correlation estimates")
        
        # Check for inconsistent triangular relationships
        # For risks A, B, C: if corr(A,B) and corr(B,C) are both high, corr(A,C) should also be reasonably high
        triangular_inconsistencies = []
        for i, risk_a in enumerate(risk_ids):
            for j, risk_b in enumerate(risk_ids[i+1:], i+1):
                for k, risk_c in enumerate(risk_ids[j+1:], j+1):
                    corr_ab = correlation_matrix.get_correlation(risk_a, risk_b)
                    corr_bc = correlation_matrix.get_correlation(risk_b, risk_c)
                    corr_ac = correlation_matrix.get_correlation(risk_a, risk_c)
                    
                    # Check triangular inequality-like relationship
                    if abs(corr_ab) > 0.7 and abs(corr_bc) > 0.7:
                        expected_min_corr = max(-1, corr_ab * corr_bc - np.sqrt((1 - corr_ab**2) * (1 - corr_bc**2)))
                        expected_max_corr = min(1, corr_ab * corr_bc + np.sqrt((1 - corr_ab**2) * (1 - corr_bc**2)))
                        
                        if not (expected_min_corr <= corr_ac <= expected_max_corr):
                            triangular_inconsistencies.append((risk_a, risk_b, risk_c))
        
        if triangular_inconsistencies:
            warnings_list.append(f"Triangular correlation inconsistencies detected for risk triplets: {triangular_inconsistencies[:3]}")
            recommendations.append("Review correlation estimates for mathematical consistency")
        
        return {
            'warnings': warnings_list,
            'recommendations': recommendations
        }
    
    def _validate_correlation_strengths(
        self,
        correlations: Dict[Tuple[str, str], float]
    ) -> Dict[str, List[str]]:
        """Validate the distribution of correlation strengths."""
        warnings_list = []
        recommendations = []
        
        if not correlations:
            return {'warnings': warnings_list, 'recommendations': recommendations}
        
        correlation_values = list(correlations.values())
        abs_correlations = [abs(c) for c in correlation_values]
        
        # Check correlation strength distribution
        high_correlations = [c for c in abs_correlations if c > 0.8]
        moderate_correlations = [c for c in abs_correlations if 0.3 <= c <= 0.8]
        low_correlations = [c for c in abs_correlations if c < 0.3]
        
        total_correlations = len(correlation_values)
        high_ratio = len(high_correlations) / total_correlations
        low_ratio = len(low_correlations) / total_correlations
        
        if high_ratio > 0.5:
            warnings_list.append(f"High proportion of strong correlations ({high_ratio:.1%})")
            recommendations.append("Consider if all strong correlations are justified by domain knowledge")
        
        if low_ratio > 0.8:
            warnings_list.append(f"High proportion of weak correlations ({low_ratio:.1%})")
            recommendations.append("Consider removing very weak correlations to simplify the model")
        
        # Check for correlation clustering
        if len(correlation_values) > 10:
            mean_abs_corr = np.mean(abs_correlations)
            std_abs_corr = np.std(abs_correlations)
            
            if std_abs_corr < 0.1:
                warnings_list.append("Correlations show little variation - consider if this reflects reality")
            
            if mean_abs_corr < 0.1:
                recommendations.append("Most correlations are very weak - consider simplifying correlation structure")
            elif mean_abs_corr > 0.6:
                recommendations.append("Most correlations are strong - verify this reflects actual risk relationships")
        
        return {
            'warnings': warnings_list,
            'recommendations': recommendations
        }
    
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
        suggestions = []
        
        try:
            numpy_matrix = self._build_numpy_matrix(correlation_matrix)
        except Exception as e:
            return {'suggestions': [f"Cannot build matrix: {str(e)}"], 'corrected_matrix': None}
        
        # Check if matrix needs fixing
        eigenvalues = np.linalg.eigvals(numpy_matrix)
        min_eigenvalue = np.min(eigenvalues)
        
        if min_eigenvalue >= tolerance:
            return {'suggestions': ['Matrix is already valid'], 'corrected_matrix': correlation_matrix}
        
        # Suggest fixes for non-positive definite matrix
        if min_eigenvalue < -tolerance:
            suggestions.append("Matrix is not positive definite")
            
            # Method 1: Eigenvalue adjustment
            corrected_matrix = self._fix_matrix_eigenvalue_adjustment(numpy_matrix, tolerance)
            suggestions.append("Applied eigenvalue adjustment to ensure positive definiteness")
            
            # Convert back to CorrelationMatrix format
            corrected_correlation_matrix = self._numpy_to_correlation_matrix(
                corrected_matrix, correlation_matrix.risk_ids
            )
            
            return {
                'suggestions': suggestions,
                'corrected_matrix': corrected_correlation_matrix,
                'correction_method': 'eigenvalue_adjustment'
            }
        
        return {'suggestions': ['No automatic fixes available'], 'corrected_matrix': None}
    
    def _fix_matrix_eigenvalue_adjustment(
        self,
        matrix: np.ndarray,
        tolerance: float
    ) -> np.ndarray:
        """Fix correlation matrix using eigenvalue adjustment."""
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        
        # Adjust negative eigenvalues
        adjusted_eigenvalues = np.maximum(eigenvalues, tolerance)
        
        # Reconstruct matrix
        corrected_matrix = eigenvectors @ np.diag(adjusted_eigenvalues) @ eigenvectors.T
        
        # Ensure diagonal is 1.0
        np.fill_diagonal(corrected_matrix, 1.0)
        
        # Ensure symmetry
        corrected_matrix = (corrected_matrix + corrected_matrix.T) / 2
        
        # Clip to [-1, 1] bounds
        corrected_matrix = np.clip(corrected_matrix, -1, 1)
        np.fill_diagonal(corrected_matrix, 1.0)
        
        return corrected_matrix
    
    def _numpy_to_correlation_matrix(
        self,
        numpy_matrix: np.ndarray,
        risk_ids: List[str]
    ) -> CorrelationMatrix:
        """Convert numpy matrix back to CorrelationMatrix format."""
        correlations = {}
        n = len(risk_ids)
        
        for i in range(n):
            for j in range(i + 1, n):
                risk1, risk2 = risk_ids[i], risk_ids[j]
                correlation = numpy_matrix[i, j]
                if abs(correlation) > 1e-10:  # Only store non-zero correlations
                    correlations[(risk1, risk2)] = correlation
        
        return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)


class ModelValidator:
    """
    Comprehensive model validator combining distribution and correlation validation.
    
    Provides unified interface for validating all aspects of Monte Carlo risk simulation models
    including probability distributions, correlation matrices, and overall model consistency.
    """
    
    def __init__(self):
        """Initialize the model validator."""
        self.distribution_validator = DistributionValidator()
        self.correlation_validator = CorrelationValidator()
    
    def validate_complete_model(
        self,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix] = None,
        historical_data: Optional[Dict[str, List[float]]] = None,
        significance_level: float = 0.05
    ) -> ValidationResult:
        """
        Validate a complete Monte Carlo risk simulation model.
        
        Args:
            risks: List of Risk objects to validate
            correlations: Optional correlation matrix
            historical_data: Optional historical data for goodness-of-fit testing
            significance_level: Significance level for statistical tests
            
        Returns:
            ValidationResult with comprehensive validation results
        """
        all_errors = []
        all_warnings = []
        all_recommendations = []
        
        # Check for empty risk list
        if not risks:
            all_errors.append("Risk list cannot be empty - at least one risk is required for simulation")
            return ValidationResult(
                is_valid=False,
                errors=all_errors,
                warnings=all_warnings,
                recommendations=all_recommendations
            )
        
        # Validate individual risk distributions
        for risk in risks:
            risk_historical_data = historical_data.get(risk.id) if historical_data else None
            
            dist_validation = self.distribution_validator.validate_distribution(
                risk.probability_distribution,
                risk_historical_data,
                significance_level
            )
            
            if not dist_validation.is_valid:
                all_errors.extend([f"Risk {risk.id}: {error}" for error in dist_validation.errors])
            
            all_warnings.extend([f"Risk {risk.id}: {warning}" for warning in dist_validation.warnings])
            all_recommendations.extend([f"Risk {risk.id}: {rec}" for rec in dist_validation.recommendations])
        
        # Validate correlation matrix if provided
        if correlations:
            corr_validation = self.correlation_validator.validate_correlation_matrix(correlations)
            
            if not corr_validation.is_valid:
                all_errors.extend([f"Correlation matrix: {error}" for error in corr_validation.errors])
            
            all_warnings.extend([f"Correlation matrix: {warning}" for warning in corr_validation.warnings])
            all_recommendations.extend([f"Correlation matrix: {rec}" for rec in corr_validation.recommendations])
            
            # Validate that correlation matrix includes all risks
            risk_ids = {risk.id for risk in risks}
            correlation_risk_ids = set(correlations.risk_ids)
            
            missing_risks = risk_ids - correlation_risk_ids
            extra_risks = correlation_risk_ids - risk_ids
            
            if missing_risks:
                all_warnings.append(f"Risks not in correlation matrix: {missing_risks}")
            
            if extra_risks:
                all_warnings.append(f"Correlation matrix includes unknown risks: {extra_risks}")
        
        # Overall model consistency checks
        model_consistency = self._validate_model_consistency(risks, correlations)
        all_warnings.extend(model_consistency['warnings'])
        all_recommendations.extend(model_consistency['recommendations'])
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            recommendations=all_recommendations
        )
    
    def _validate_model_consistency(
        self,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix]
    ) -> Dict[str, List[str]]:
        """Validate overall model consistency."""
        warnings_list = []
        recommendations = []
        
        # Check risk impact types for correlation consistency
        if correlations:
            cost_risks = [r for r in risks if r.impact_type in [ImpactType.COST, ImpactType.BOTH]]
            schedule_risks = [r for r in risks if r.impact_type in [ImpactType.SCHEDULE, ImpactType.BOTH]]
            
            # Check for correlations between different impact types
            mixed_correlations = []
            for (risk1_id, risk2_id), corr in correlations.correlations.items():
                risk1 = next((r for r in risks if r.id == risk1_id), None)
                risk2 = next((r for r in risks if r.id == risk2_id), None)
                
                if risk1 and risk2:
                    if (risk1.impact_type == ImpactType.COST and risk2.impact_type == ImpactType.SCHEDULE) or \
                       (risk1.impact_type == ImpactType.SCHEDULE and risk2.impact_type == ImpactType.COST):
                        if abs(corr) > 0.5:
                            mixed_correlations.append((risk1_id, risk2_id, corr))
            
            if mixed_correlations:
                recommendations.append(f"High correlations between cost and schedule risks detected: {mixed_correlations[:3]}")
                recommendations.append("Consider using cross-impact modeling for cost-schedule relationships")
        
        # Check for risk category clustering
        risk_categories = {}
        for risk in risks:
            category = risk.category
            if category not in risk_categories:
                risk_categories[category] = []
            risk_categories[category].append(risk.id)
        
        if len(risk_categories) == 1:
            warnings_list.append("All risks belong to the same category - consider risk diversification")
        elif len(risks) > 20 and len(risk_categories) > 10:
            recommendations.append("Many risk categories detected - consider grouping similar risks")
        
        return {
            'warnings': warnings_list,
            'recommendations': recommendations
        }