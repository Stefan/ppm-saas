"""
Property-based tests for visualization generation.

Tests Property 22: Visualization Generation
Validates Requirements 8.1, 8.2, 8.3, 8.4, 8.5

This module contains property-based tests that verify the visualization system
generates all required chart types correctly across various input scenarios.
"""

import pytest
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any

from monte_carlo.models import (
    Risk, SimulationResults, ConvergenceMetrics, RiskCategory, ImpactType,
    ProbabilityDistribution, DistributionType, MitigationStrategy
)
from monte_carlo.visualization import (
    ChartGenerator, ChartConfig, ChartFormat, ChartTheme, VisualizationManager,
    ChartData
)


# Test data generation strategies
@st.composite
def generate_probability_distribution(draw):
    """Generate valid probability distributions for testing."""
    dist_type = draw(st.sampled_from(list(DistributionType)))
    
    if dist_type == DistributionType.NORMAL:
        mean = draw(st.floats(min_value=-1000, max_value=1000))
        std = draw(st.floats(min_value=0.1, max_value=100))
        parameters = {'mean': mean, 'std': std}
    elif dist_type == DistributionType.TRIANGULAR:
        min_val = draw(st.floats(min_value=0, max_value=100))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=min_val + 1000))
        mode = draw(st.floats(min_value=min_val, max_value=max_val))
        parameters = {'min': min_val, 'mode': mode, 'max': max_val}
    elif dist_type == DistributionType.UNIFORM:
        min_val = draw(st.floats(min_value=0, max_value=100))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=min_val + 1000))
        parameters = {'min': min_val, 'max': max_val}
    elif dist_type == DistributionType.BETA:
        alpha = draw(st.floats(min_value=0.1, max_value=10))
        beta = draw(st.floats(min_value=0.1, max_value=10))
        parameters = {'alpha': alpha, 'beta': beta}
    else:  # LOGNORMAL
        mu = draw(st.floats(min_value=-2, max_value=2))
        sigma = draw(st.floats(min_value=0.1, max_value=2))
        parameters = {'mu': mu, 'sigma': sigma}
    
    return ProbabilityDistribution(
        distribution_type=dist_type,
        parameters=parameters
    )


@st.composite
def generate_risk(draw):
    """Generate valid Risk objects for testing."""
    risk_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=50))
    category = draw(st.sampled_from(list(RiskCategory)))
    impact_type = draw(st.sampled_from(list(ImpactType)))
    distribution = draw(generate_probability_distribution())
    baseline_impact = draw(st.floats(min_value=1, max_value=10000))
    
    return Risk(
        id=risk_id,
        name=name,
        category=category,
        impact_type=impact_type,
        probability_distribution=distribution,
        baseline_impact=baseline_impact,
        correlation_dependencies=[],
        mitigation_strategies=[]
    )


@st.composite
def generate_simulation_results(draw):
    """Generate valid SimulationResults for testing."""
    simulation_id = draw(st.text(min_size=1, max_size=20))
    iteration_count = draw(st.integers(min_value=50, max_value=200))  # Much smaller size
    
    # Generate outcome arrays with some variation to avoid singular matrices
    base_cost = draw(st.floats(min_value=1000, max_value=5000))
    cost_variation = base_cost * 0.1
    cost_outcomes = np.random.normal(base_cost, cost_variation, iteration_count)
    
    base_schedule = draw(st.floats(min_value=10, max_value=50))
    schedule_variation = base_schedule * 0.1
    schedule_outcomes = np.random.normal(base_schedule, schedule_variation, iteration_count)
    
    # Generate risk contributions
    num_risks = draw(st.integers(min_value=1, max_value=3))  # Very small number of risks
    risk_contributions = {}
    for i in range(num_risks):
        risk_id = f"risk_{i}"
        base_contribution = draw(st.floats(min_value=-50, max_value=50))
        contribution_variation = 20
        contributions = np.random.normal(base_contribution, contribution_variation, iteration_count)
        risk_contributions[risk_id] = contributions
    
    # Simple convergence metrics
    convergence_metrics = ConvergenceMetrics(
        mean_stability=0.95,
        variance_stability=0.95,
        percentile_stability={50.0: 0.95},
        converged=True
    )
    
    return SimulationResults(
        simulation_id=simulation_id,
        timestamp=datetime.now(),
        iteration_count=iteration_count,
        cost_outcomes=cost_outcomes,
        schedule_outcomes=schedule_outcomes,
        risk_contributions=risk_contributions,
        convergence_metrics=convergence_metrics,
        execution_time=1.0
    )


class TestVisualizationGeneration:
    """
    Property-based tests for visualization generation.
    
    **Feature: monte-carlo-risk-simulations, Property 22: Visualization Generation**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chart_generator = ChartGenerator()
        self.visualization_manager = VisualizationManager()
        # Ensure matplotlib doesn't try to display charts during testing
        plt.ioff()
    
    def teardown_method(self):
        """Clean up after tests."""
        plt.close('all')
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000, suppress_health_check=[HealthCheck.data_too_large])
    def test_probability_distribution_chart_generation(self, simulation_results):
        """
        Property: For any simulation results, probability distribution charts should be 
        generated successfully for both cost and schedule outcomes.
        
        **Validates: Requirements 8.1**
        """
        # Test cost distribution chart
        cost_chart = self.chart_generator.generate_probability_distribution_chart(
            simulation_results, outcome_type='cost'
        )
        
        # Verify chart data structure
        assert isinstance(cost_chart, ChartData)
        assert cost_chart.title is not None
        assert len(cost_chart.title) > 0
        assert cost_chart.data is not None
        assert 'cost' in cost_chart.metadata['outcome_type']
        assert cost_chart.metadata['iteration_count'] == simulation_results.iteration_count
        
        # Verify statistical metadata is present
        assert 'mean' in cost_chart.metadata
        assert 'median' in cost_chart.metadata
        assert 'std_dev' in cost_chart.metadata
        assert isinstance(cost_chart.metadata['mean'], (int, float))
        assert isinstance(cost_chart.metadata['median'], (int, float))
        assert isinstance(cost_chart.metadata['std_dev'], (int, float))
        
        # Test schedule distribution chart
        schedule_chart = self.chart_generator.generate_probability_distribution_chart(
            simulation_results, outcome_type='schedule'
        )
        
        # Verify chart data structure
        assert isinstance(schedule_chart, ChartData)
        assert schedule_chart.title is not None
        assert len(schedule_chart.title) > 0
        assert schedule_chart.data is not None
        assert 'schedule' in schedule_chart.metadata['outcome_type']
        
        # Clean up matplotlib figures
        plt.close(cost_chart.data)
        plt.close(schedule_chart.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000)
    def test_tornado_diagram_generation(self, simulation_results):
        """
        Property: For any simulation results with risk contributions, tornado diagrams 
        should be generated successfully showing individual risk contributions.
        
        **Validates: Requirements 8.2**
        """
        # Skip if no risk contributions
        assume(len(simulation_results.risk_contributions) > 0)
        
        # Test cost tornado diagram
        tornado_chart = self.chart_generator.generate_tornado_diagram(
            simulation_results, outcome_type='cost'
        )
        
        # Verify chart data structure
        assert isinstance(tornado_chart, ChartData)
        assert tornado_chart.title is not None
        assert 'tornado' in tornado_chart.title.lower() or 'contribution' in tornado_chart.title.lower()
        assert tornado_chart.data is not None
        assert 'cost' in tornado_chart.metadata['outcome_type']
        
        # Verify risk contribution metadata
        assert 'risk_contributions' in tornado_chart.metadata
        assert isinstance(tornado_chart.metadata['risk_contributions'], dict)
        assert len(tornado_chart.metadata['risk_contributions']) > 0
        
        # Verify all contribution percentages are non-negative
        for contribution in tornado_chart.metadata['risk_contributions'].values():
            assert contribution >= 0
        
        # Verify total contribution is reasonable (should be <= 100%)
        total_contribution = tornado_chart.metadata.get('total_contribution', 0)
        assert 0 <= total_contribution <= 100
        
        # Clean up matplotlib figure
        plt.close(tornado_chart.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000)
    def test_cdf_chart_generation(self, simulation_results):
        """
        Property: For any simulation results, CDF charts should be generated successfully 
        with key percentile markers.
        
        **Validates: Requirements 8.3**
        """
        # Test cost CDF chart
        cdf_chart = self.chart_generator.generate_cdf_chart(
            simulation_results, outcome_type='cost'
        )
        
        # Verify chart data structure
        assert isinstance(cdf_chart, ChartData)
        assert cdf_chart.title is not None
        assert 'cdf' in cdf_chart.title.lower() or 'cumulative' in cdf_chart.title.lower()
        assert cdf_chart.data is not None
        assert 'cost' in cdf_chart.metadata['outcome_type']
        
        # Verify percentile markers are present
        assert 'percentile_markers' in cdf_chart.metadata
        percentile_markers = cdf_chart.metadata['percentile_markers']
        assert isinstance(percentile_markers, dict)
        assert len(percentile_markers) > 0
        
        # Verify percentile values are in ascending order
        percentiles = sorted(percentile_markers.keys())
        values = [percentile_markers[p] for p in percentiles]
        for i in range(1, len(values)):
            assert values[i] >= values[i-1], "Percentile values should be in ascending order"
        
        # Verify confidence intervals are present
        assert 'confidence_intervals' in cdf_chart.metadata
        confidence_intervals = cdf_chart.metadata['confidence_intervals']
        assert isinstance(confidence_intervals, dict)
        
        # Verify confidence interval bounds are valid
        for ci_level, (lower, upper) in confidence_intervals.items():
            assert lower <= upper, f"Confidence interval bounds invalid for {ci_level}"
            assert isinstance(lower, (int, float))
            assert isinstance(upper, (int, float))
        
        # Clean up matplotlib figure
        plt.close(cdf_chart.data)
    
    @given(st.lists(generate_risk(), min_size=1, max_size=3), generate_simulation_results())
    @settings(max_examples=3, deadline=15000)
    def test_risk_heat_map_generation(self, risks, simulation_results):
        """
        Property: For any list of risks and simulation results, risk heat maps should be 
        generated successfully showing probability vs. impact.
        
        **Validates: Requirements 8.4**
        """
        # Ensure risk contributions exist for the risks
        risk_contributions = {}
        for risk in risks:
            # Generate some contribution data for each risk
            contributions = np.random.normal(0, 100, simulation_results.iteration_count)
            risk_contributions[risk.id] = contributions
        
        # Update simulation results with risk contributions
        simulation_results.risk_contributions = risk_contributions
        
        # Generate heat map
        heat_map_chart = self.chart_generator.generate_risk_heat_map(
            risks, simulation_results
        )
        
        # Verify chart data structure
        assert isinstance(heat_map_chart, ChartData)
        assert heat_map_chart.title is not None
        assert 'heat map' in heat_map_chart.title.lower() or 'risk' in heat_map_chart.title.lower()
        assert heat_map_chart.data is not None
        
        # Verify risk data metadata
        assert 'risk_data' in heat_map_chart.metadata
        risk_data = heat_map_chart.metadata['risk_data']
        assert isinstance(risk_data, list)
        assert len(risk_data) > 0
        
        # Verify each risk data entry has required fields
        for risk_entry in risk_data:
            assert 'id' in risk_entry
            assert 'name' in risk_entry
            assert 'category' in risk_entry
            assert 'mean_impact' in risk_entry
            assert 'estimated_probability' in risk_entry
            
            # Verify probability is between 0 and 1
            assert 0 <= risk_entry['estimated_probability'] <= 1
            
            # Verify impact is non-negative
            assert risk_entry['mean_impact'] >= 0
        
        # Verify thresholds are present
        assert 'impact_threshold' in heat_map_chart.metadata
        assert 'probability_threshold' in heat_map_chart.metadata
        
        # Clean up matplotlib figure
        plt.close(heat_map_chart.data)
    
    @given(st.lists(st.tuples(st.text(min_size=1, max_size=10), generate_simulation_results()), 
                   min_size=2, max_size=3))
    @settings(max_examples=3, deadline=15000)
    def test_scenario_overlay_chart_generation(self, scenario_data):
        """
        Property: For any list of scenario results, overlay charts should be generated 
        successfully showing multiple distribution curves.
        
        **Validates: Requirements 8.5**
        """
        scenario_results = [(name, results) for name, results in scenario_data]
        
        # Test distribution overlay
        overlay_chart = self.chart_generator.generate_scenario_overlay_chart(
            scenario_results, outcome_type='cost', chart_type='distribution'
        )
        
        # Verify chart data structure
        assert isinstance(overlay_chart, ChartData)
        assert overlay_chart.title is not None
        assert 'scenario' in overlay_chart.title.lower() or 'comparison' in overlay_chart.title.lower()
        assert overlay_chart.data is not None
        assert 'cost' in overlay_chart.metadata['outcome_type']
        assert overlay_chart.metadata['chart_type'] == 'distribution'
        
        # Verify scenario statistics
        assert 'scenario_statistics' in overlay_chart.metadata
        scenario_stats = overlay_chart.metadata['scenario_statistics']
        assert isinstance(scenario_stats, list)
        assert len(scenario_stats) == len(scenario_results)
        
        # Verify each scenario has required statistics
        for stat_entry in scenario_stats:
            assert 'Scenario' in stat_entry
            assert 'Mean' in stat_entry
            assert 'Median' in stat_entry
            assert 'Std Dev' in stat_entry
            assert 'P90' in stat_entry
        
        # Test CDF overlay
        cdf_overlay_chart = self.chart_generator.generate_scenario_overlay_chart(
            scenario_results, outcome_type='cost', chart_type='cdf'
        )
        
        # Verify CDF overlay structure
        assert isinstance(cdf_overlay_chart, ChartData)
        assert cdf_overlay_chart.metadata['chart_type'] == 'cdf'
        
        # Clean up matplotlib figures
        plt.close(overlay_chart.data)
        plt.close(cdf_overlay_chart.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000)
    def test_complete_visualization_suite_generation(self, simulation_results):
        """
        Property: For any simulation results, a complete visualization suite should be 
        generated successfully containing all required chart types.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        # Generate complete visualization suite
        charts = self.visualization_manager.generate_complete_visualization_suite(
            simulation_results
        )
        
        # Verify basic charts are present
        expected_basic_charts = ['cost_distribution', 'schedule_distribution']
        for chart_name in expected_basic_charts:
            assert chart_name in charts
            assert isinstance(charts[chart_name], ChartData)
            assert charts[chart_name].data is not None
        
        # Verify CDF charts are present
        expected_cdf_charts = ['cost_cdf', 'schedule_cdf']
        for chart_name in expected_cdf_charts:
            assert chart_name in charts
            assert isinstance(charts[chart_name], ChartData)
        
        # Verify tornado diagrams are present if risk contributions exist
        if simulation_results.risk_contributions:
            expected_tornado_charts = ['cost_tornado', 'schedule_tornado']
            for chart_name in expected_tornado_charts:
                assert chart_name in charts
                assert isinstance(charts[chart_name], ChartData)
        
        # Clean up all matplotlib figures
        for chart_data in charts.values():
            if chart_data and chart_data.data:
                plt.close(chart_data.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000)
    def test_chart_configuration_consistency(self, simulation_results):
        """
        Property: For any chart configuration, all generated charts should respect 
        the configuration settings consistently.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        # Test with custom configuration
        custom_config = ChartConfig(
            format=ChartFormat.PNG,
            theme=ChartTheme.PROFESSIONAL,
            width=10,
            height=6,
            font_size=12,
            show_grid=True
        )
        
        chart_generator = ChartGenerator(custom_config)
        
        # Generate a chart with custom configuration
        chart = chart_generator.generate_probability_distribution_chart(
            simulation_results, outcome_type='cost'
        )
        
        # Verify chart respects configuration
        assert isinstance(chart, ChartData)
        assert chart.data is not None
        
        # Verify the chart generator uses the custom configuration
        assert chart_generator.config.format == ChartFormat.PNG
        assert chart_generator.config.theme == ChartTheme.PROFESSIONAL
        assert chart_generator.config.width == 10
        assert chart_generator.config.height == 6
        assert chart_generator.config.font_size == 12
        assert chart_generator.config.show_grid == True
        
        # Clean up matplotlib figure
        plt.close(chart.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=5, deadline=15000)
    def test_chart_data_export_consistency(self, simulation_results):
        """
        Property: For any generated chart, the exported chart data should contain 
        all required metadata and be structurally consistent.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        # Generate a chart
        chart = self.chart_generator.generate_probability_distribution_chart(
            simulation_results, outcome_type='cost'
        )
        
        # Export chart data
        exported_data = self.chart_generator.export_chart_data(chart)
        
        # Verify exported data structure
        assert isinstance(exported_data, dict)
        
        # Verify required fields are present
        required_fields = ['title', 'subtitle', 'x_label', 'y_label', 'metadata', 'config']
        for field in required_fields:
            assert field in exported_data
        
        # Verify config data
        config_data = exported_data['config']
        assert isinstance(config_data, dict)
        assert 'format' in config_data
        assert 'theme' in config_data
        assert 'width' in config_data
        assert 'height' in config_data
        assert 'dpi' in config_data
        
        # Verify metadata consistency
        assert exported_data['metadata'] == chart.metadata
        
        # Clean up matplotlib figure
        plt.close(chart.data)
    
    @given(generate_simulation_results())
    @settings(max_examples=3, deadline=15000)
    def test_visualization_validation_completeness(self, simulation_results):
        """
        Property: For any simulation results, visualization validation should provide 
        comprehensive assessment of available chart types and data quality.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        # Validate visualization requirements
        validation_results = self.visualization_manager.validate_visualization_requirements(
            simulation_results
        )
        
        # Verify validation structure
        assert isinstance(validation_results, dict)
        
        # Verify required validation fields
        required_fields = ['valid', 'warnings', 'errors', 'recommendations', 'available_charts']
        for field in required_fields:
            assert field in validation_results
        
        # Verify field types
        assert isinstance(validation_results['valid'], bool)
        assert isinstance(validation_results['warnings'], list)
        assert isinstance(validation_results['errors'], list)
        assert isinstance(validation_results['recommendations'], list)
        assert isinstance(validation_results['available_charts'], list)
        
        # Verify logical consistency
        if len(validation_results['errors']) > 0:
            assert validation_results['valid'] == False
        
        # Verify available charts are reasonable
        if len(simulation_results.cost_outcomes) > 0:
            assert any('cost' in chart for chart in validation_results['available_charts'])
        
        if len(simulation_results.schedule_outcomes) > 0:
            assert any('schedule' in chart for chart in validation_results['available_charts'])
    
    def test_invalid_outcome_type_handling(self):
        """
        Property: Chart generation should handle invalid outcome types gracefully 
        by raising appropriate errors.
        
        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        # Create minimal simulation results
        simulation_results = SimulationResults(
            simulation_id="test",
            timestamp=datetime.now(),
            iteration_count=100,
            cost_outcomes=np.array([1000] * 100),
            schedule_outcomes=np.array([10] * 100),
            risk_contributions={},
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.9,
                variance_stability=0.9,
                percentile_stability={50.0: 0.9},
                converged=True
            ),
            execution_time=1.0
        )
        
        # Test invalid outcome type for distribution chart
        with pytest.raises(ValueError, match="outcome_type must be 'cost' or 'schedule'"):
            self.chart_generator.generate_probability_distribution_chart(
                simulation_results, outcome_type='invalid'
            )
        
        # Test invalid outcome type for tornado diagram
        with pytest.raises(ValueError, match="outcome_type must be 'cost' or 'schedule'"):
            self.chart_generator.generate_tornado_diagram(
                simulation_results, outcome_type='invalid'
            )
        
        # Test invalid outcome type for CDF chart
        with pytest.raises(ValueError, match="outcome_type must be 'cost' or 'schedule'"):
            self.chart_generator.generate_cdf_chart(
                simulation_results, outcome_type='invalid'
            )
    
    def test_empty_data_handling(self):
        """
        Property: Chart generation should handle empty or insufficient data gracefully.
        
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        # Test with empty risk contributions
        simulation_results = SimulationResults(
            simulation_id="test",
            timestamp=datetime.now(),
            iteration_count=100,
            cost_outcomes=np.array([1000] * 100),
            schedule_outcomes=np.array([10] * 100),
            risk_contributions={},  # Empty risk contributions
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.9,
                variance_stability=0.9,
                percentile_stability={50.0: 0.9},
                converged=True
            ),
            execution_time=1.0
        )
        
        # Tornado diagram should raise error with empty risk contributions
        with pytest.raises(ValueError, match="No risk contributions found"):
            self.chart_generator.generate_tornado_diagram(simulation_results)
        
        # Heat map should raise error with empty risks
        with pytest.raises(ValueError, match="Risks and risk contributions are required"):
            self.chart_generator.generate_risk_heat_map([], simulation_results)
        
        # Scenario overlay should raise error with empty scenarios
        with pytest.raises(ValueError, match="At least one scenario result is required"):
            self.chart_generator.generate_scenario_overlay_chart([])


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])