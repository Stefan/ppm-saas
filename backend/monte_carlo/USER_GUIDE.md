# Monte Carlo Risk Simulation - User Guide

**Version:** 1.0  
**Target Audience:** Project Managers, Risk Analysts, Construction Professionals  

## Table of Contents
1. [Getting Started](#getting-started)
2. [Understanding Monte Carlo Simulation](#understanding-monte-carlo-simulation)
3. [Defining Risks](#defining-risks)
4. [Running Simulations](#running-simulations)
5. [Interpreting Results](#interpreting-results)
6. [Scenario Analysis](#scenario-analysis)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### What is Monte Carlo Risk Simulation?

Monte Carlo simulation is a statistical technique that uses random sampling to analyze the impact of risk and uncertainty in project outcomes. Instead of using single-point estimates, it runs thousands of scenarios to provide a range of possible outcomes with associated probabilities.

### Key Benefits
- **Realistic Risk Assessment**: Understand the full range of possible project outcomes
- **Informed Decision Making**: Make decisions based on probability distributions, not single estimates
- **Contingency Planning**: Determine appropriate contingency reserves based on confidence levels
- **Scenario Comparison**: Evaluate the effectiveness of different risk mitigation strategies

### System Requirements
- Web browser with JavaScript enabled
- Valid user account with risk analysis permissions
- Project data including risk register and baseline estimates

## Understanding Monte Carlo Simulation

### How It Works
1. **Risk Definition**: Each risk is modeled as a probability distribution
2. **Random Sampling**: The system randomly samples from each risk distribution
3. **Impact Calculation**: Sampled values are combined to calculate total project impact
4. **Iteration**: This process is repeated thousands of times (typically 10,000+)
5. **Statistical Analysis**: Results are analyzed to provide percentiles, confidence intervals, and risk contributions

### Key Concepts

#### Probability Distributions
Different types of uncertainty require different distribution types:

- **Triangular**: When you have optimistic, most likely, and pessimistic estimates
- **Normal**: For risks with symmetric uncertainty around a mean value
- **Lognormal**: For risks that cannot be negative and have right-skewed distributions
- **Uniform**: When all values within a range are equally likely
- **Beta**: For bounded risks with flexible shape parameters

#### Correlation
Risks often affect each other. The system models these relationships:
- **Positive Correlation**: When one risk increases, the other tends to increase
- **Negative Correlation**: When one risk increases, the other tends to decrease
- **No Correlation**: Risks are independent of each other

#### Percentiles
Results are expressed as percentiles:
- **P50 (Median)**: 50% chance the outcome will be below this value
- **P90**: 90% chance the outcome will be below this value (commonly used for contingency planning)
- **P95**: 95% chance the outcome will be below this value (conservative planning)

## Defining Risks

### Risk Categories
Organize risks by category for better analysis:
- **Cost**: Risks affecting project budget
- **Schedule**: Risks affecting project timeline
- **Technical**: Engineering and design risks
- **Resource**: Labor and equipment availability risks
- **External**: Market, regulatory, and environmental risks
- **Quality**: Risks affecting deliverable quality
- **Regulatory**: Permit and compliance risks

### Distribution Selection Guide

#### Use Triangular Distribution When:
- You have expert estimates for optimistic, most likely, and pessimistic scenarios
- The risk has a clear mode (most likely value)
- Examples: Material cost variations, weather delays

**Parameters:**
- **Min**: Best-case scenario (optimistic)
- **Mode**: Most likely scenario
- **Max**: Worst-case scenario (pessimistic)

#### Use Normal Distribution When:
- The risk follows a bell curve pattern
- You have historical data showing symmetric distribution
- Examples: Labor productivity variations, measurement errors

**Parameters:**
- **Mean**: Average expected value
- **Standard Deviation**: Measure of variability

#### Use Lognormal Distribution When:
- The risk cannot be negative
- The distribution is right-skewed (long tail on the right)
- Examples: Equipment failure costs, project duration overruns

**Parameters:**
- **Mu**: Mean of the underlying normal distribution
- **Sigma**: Standard deviation of the underlying normal distribution

### Correlation Guidelines

#### When to Use Correlations:
- Risks share common root causes
- One risk directly influences another
- Risks are affected by the same external factors

#### Correlation Coefficients:
- **0.8 to 1.0**: Very strong positive correlation
- **0.5 to 0.8**: Strong positive correlation
- **0.2 to 0.5**: Moderate positive correlation
- **-0.2 to 0.2**: Weak or no correlation
- **-0.5 to -0.2**: Moderate negative correlation
- **-0.8 to -0.5**: Strong negative correlation
- **-1.0 to -0.8**: Very strong negative correlation

## Running Simulations

### Step 1: Prepare Risk Data
1. Identify all significant project risks
2. Categorize risks by type and impact
3. Determine appropriate probability distributions
4. Estimate distribution parameters
5. Identify risk correlations

### Step 2: Configure Simulation
1. **Iterations**: Use 10,000 iterations (minimum) for statistical significance
2. **Random Seed**: Set a seed for reproducible results during analysis
3. **Baseline Data**: Include project baseline costs and schedule
4. **Correlations**: Define correlation matrix for dependent risks

### Step 3: Execute Simulation
1. Submit simulation request via API or web interface
2. Monitor progress (simulations typically complete in under 30 seconds)
3. Review convergence status to ensure statistical validity

### Step 4: Validate Results
1. Check that results are reasonable given input parameters
2. Verify convergence was achieved
3. Review risk contributions to ensure they make sense
4. Compare results with deterministic estimates for sanity check

## Interpreting Results

### Statistical Summary
- **Mean**: Average expected outcome across all iterations
- **Median (P50)**: Middle value when all outcomes are sorted
- **Standard Deviation**: Measure of variability in outcomes
- **Coefficient of Variation**: Relative measure of uncertainty (std dev / mean)

### Percentile Analysis
Use percentiles for decision making:
- **P10**: Optimistic scenario (10% chance of better outcome)
- **P50**: Most likely scenario (median outcome)
- **P90**: Conservative scenario (90% confidence level)
- **P95**: Very conservative scenario (95% confidence level)

### Confidence Intervals
Confidence intervals show the range of outcomes at different confidence levels:
- **80% CI**: Range containing 80% of possible outcomes
- **90% CI**: Range containing 90% of possible outcomes
- **95% CI**: Range containing 95% of possible outcomes

### Risk Contributions
Understand which risks drive the most uncertainty:
- **Contribution Percentage**: How much each risk contributes to total variance
- **Variance Contribution**: Absolute contribution to outcome variability
- **Correlation Effects**: How risk interactions affect contributions

### Example Interpretation

```
Cost Simulation Results:
- Mean: $1,250,000
- P50 (Median): $1,200,000
- P90: $1,450,000
- P95: $1,520,000
- Standard Deviation: $180,000

Interpretation:
- Expected project cost is $1.25M
- 50% chance of staying under $1.2M
- 90% chance of staying under $1.45M
- Recommended contingency: $250K (P90 - baseline)
```

## Scenario Analysis

### Creating Scenarios
Scenarios allow you to compare different risk profiles:

1. **Baseline Scenario**: Current risk assessment without mitigation
2. **Mitigation Scenario**: With risk response strategies applied
3. **Optimistic Scenario**: Assuming favorable conditions
4. **Pessimistic Scenario**: Assuming unfavorable conditions

### Mitigation Modeling
Model risk mitigation strategies:
- **Cost**: Investment required for mitigation
- **Effectiveness**: Percentage reduction in risk impact (0-100%)
- **Implementation Time**: Time required to implement mitigation

### Scenario Comparison
Compare scenarios using:
- **Cost Difference**: Change in expected costs
- **Schedule Difference**: Change in expected duration
- **Statistical Significance**: Whether differences are meaningful
- **Effect Size**: Magnitude of the difference

### ROI Analysis
Evaluate mitigation investments:
```
Mitigation ROI = (Risk Reduction - Mitigation Cost) / Mitigation Cost

Example:
- Baseline P90 Cost: $1,450,000
- Mitigated P90 Cost: $1,350,000
- Risk Reduction: $100,000
- Mitigation Cost: $25,000
- ROI = ($100,000 - $25,000) / $25,000 = 300%
```

## Best Practices

### Risk Definition
1. **Be Realistic**: Use realistic parameter estimates based on historical data
2. **Include All Significant Risks**: Don't ignore risks because they're hard to quantify
3. **Use Appropriate Distributions**: Match distribution type to risk characteristics
4. **Validate Parameters**: Ensure distribution parameters make sense
5. **Document Assumptions**: Record the basis for all parameter estimates

### Correlation Modeling
1. **Start Simple**: Begin with obvious correlations, add complexity gradually
2. **Validate Correlations**: Ensure correlation coefficients are realistic
3. **Avoid Over-Correlation**: Too many high correlations can inflate results
4. **Test Sensitivity**: Check how correlation changes affect results

### Simulation Configuration
1. **Use Sufficient Iterations**: Minimum 10,000 for statistical significance
2. **Check Convergence**: Ensure simulation has converged to stable results
3. **Set Random Seeds**: Use seeds for reproducible results during analysis
4. **Monitor Performance**: Keep risk count reasonable for good performance

### Results Analysis
1. **Focus on Percentiles**: Use P90 or P95 for conservative planning
2. **Understand Distributions**: Look at the shape, not just summary statistics
3. **Validate Results**: Check that results make intuitive sense
4. **Consider Risk Contributions**: Focus mitigation on high-contribution risks

### Communication
1. **Use Visual Aids**: Charts and graphs communicate uncertainty better than tables
2. **Explain Methodology**: Help stakeholders understand Monte Carlo concepts
3. **Focus on Decisions**: Translate results into actionable recommendations
4. **Provide Context**: Compare results to deterministic estimates

## Troubleshooting

### Common Issues

#### Unrealistic Results
**Symptoms**: Extremely high or low outcomes, results don't match expectations
**Causes**: 
- Incorrect distribution parameters
- Inappropriate distribution types
- Excessive correlations
- Data entry errors

**Solutions**:
- Review and validate all input parameters
- Check distribution parameter units and scales
- Reduce correlation coefficients if too high
- Compare individual risk impacts to total results

#### Poor Convergence
**Symptoms**: Convergence metrics show instability, results vary between runs
**Causes**:
- Insufficient iterations
- Extreme distribution parameters
- Numerical instability

**Solutions**:
- Increase iteration count
- Review extreme parameter values
- Check for very high correlations (>0.95)

#### Performance Issues
**Symptoms**: Simulations take too long, timeouts occur
**Causes**:
- Too many risks (>100)
- Very high iteration counts
- Complex correlation matrices

**Solutions**:
- Reduce number of risks by combining similar ones
- Use standard iteration count (10,000)
- Simplify correlation structure

#### Validation Errors
**Symptoms**: API returns validation errors, simulation won't start
**Causes**:
- Invalid distribution parameters
- Correlation coefficients outside [-1, 1] range
- Missing required fields

**Solutions**:
- Check all distribution parameters for validity
- Ensure correlation coefficients are between -1 and 1
- Verify all required fields are provided

### Getting Help

If you encounter issues not covered in this guide:

1. **Check System Status**: Verify the system is operational
2. **Review Error Messages**: Error messages often indicate the specific problem
3. **Consult API Documentation**: For technical integration issues
4. **Contact Support**: Reach out to the development team for assistance

### Support Contacts
- **Technical Issues**: monte-carlo-dev@company.com
- **User Training**: risk-analysis-team@company.com
- **Feature Requests**: product-management@company.com

---

**Document Version:** 1.0  
**Last Updated:** January 9, 2026  
**Next Review:** March 2026