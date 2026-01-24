# Efficiency Score Fix

## Problem
The efficiency score was showing huge negative percentages (e.g., -500%, -1000%) because it was using the wrong formula for Commitments vs Actuals comparison.

**Old Formula (WRONG):**
```typescript
efficiency_score = 100 - Math.abs(variance_percentage)
```

This formula works for Budget vs Actual (where you want to minimize variance), but NOT for Commitments vs Actuals.

**Example of the problem:**
- Commitments: $100,000
- Actuals: $20,000
- Variance: -$80,000
- Variance %: -80%
- Old Efficiency: 100 - 80 = 20% ❌ (seems low, but actually good!)

- Commitments: $100,000
- Actuals: $600,000
- Variance: +$500,000
- Variance %: +500%
- Old Efficiency: 100 - 500 = **-400%** ❌ (NEGATIVE!)

## Solution

### New Efficiency Logic for Commitments vs Actuals

The efficiency should be based on **Spend Rate** (Actuals / Commitments), not variance percentage.

**Ideal Spend Rate:** 80-100%
- This means you're spending most of your commitments efficiently
- Not over-spending (>100%)
- Not under-utilizing (<80%)

### New Formula

```typescript
const spendRate = (actuals / commitments) * 100

if (spendRate >= 80 && spendRate <= 100) {
  efficiency = 100  // Perfect efficiency
} else if (spendRate > 100) {
  // Over-spending: reduce efficiency based on how much over
  efficiency = Math.max(0, 100 - (spendRate - 100))
} else {
  // Under-spending: efficiency based on utilization
  efficiency = (spendRate / 80) * 100
}

// Clamp between 0-100
efficiency = Math.min(100, Math.max(0, efficiency))
```

### Examples with New Formula

**Example 1: Perfect Efficiency**
- Commitments: $100,000
- Actuals: $90,000
- Spend Rate: 90%
- **Efficiency: 100%** ✅ (spending commitments efficiently)

**Example 2: Under-Utilized**
- Commitments: $100,000
- Actuals: $20,000
- Spend Rate: 20%
- **Efficiency: 25%** ✅ (20/80 * 100 = 25%)

**Example 3: Over-Spending**
- Commitments: $100,000
- Actuals: $150,000
- Spend Rate: 150%
- **Efficiency: 50%** ✅ (100 - (150-100) = 50%)

**Example 4: Severely Over-Spending**
- Commitments: $100,000
- Actuals: $600,000
- Spend Rate: 600%
- **Efficiency: 0%** ✅ (100 - (600-100) = -500, clamped to 0)

## Efficiency Score Interpretation

| Spend Rate | Efficiency | Meaning | Color |
|------------|-----------|---------|-------|
| 80-100% | 100% | Perfect - spending commitments efficiently | 🟢 Green |
| 60-80% | 75-100% | Good - decent utilization | 🟡 Yellow |
| 40-60% | 50-75% | Fair - under-utilized | 🟡 Yellow |
| 0-40% | 0-50% | Poor - very under-utilized | 🔴 Red |
| 100-120% | 80-100% | Acceptable - slightly over | 🟡 Yellow |
| 120-150% | 50-80% | Concerning - over-spending | 🔴 Red |
| >150% | 0-50% | Critical - severely over-spending | 🔴 Red |

## Visual Representation

```
Efficiency Score Chart:

100% |     ████████████
     |    █            █
 80% |   █              █
     |  █                █
 60% | █                  █
     |█                    █
 40% |                      █
     |                       █
 20% |                        █
     |                         █
  0% |__________________________█___
     0%  40%  80% 100% 120% 160% 200%
              Spend Rate
```

## Implementation

### Files Modified

1. **app/financials/components/views/OverviewView.tsx**
   - Updated `displayProjectData` calculation
   - Updated `displayCategoryData` calculation
   - New efficiency formula based on spend rate

### Code Changes

**Project Performance Data:**
```typescript
const displayProjectData = analytics?.projectPerformanceData.length
  ? analytics.projectPerformanceData.map(p => {
      let efficiency_score = 0
      if (p.spend_percentage >= 80 && p.spend_percentage <= 100) {
        efficiency_score = 100
      } else if (p.spend_percentage > 100) {
        efficiency_score = Math.max(0, 100 - (p.spend_percentage - 100))
      } else {
        efficiency_score = (p.spend_percentage / 80) * 100
      }
      
      return {
        ...p,
        efficiency_score: Math.min(100, Math.max(0, efficiency_score))
      }
    })
  : analyticsData.projectPerformanceData
```

**Category Data:**
```typescript
const displayCategoryData = analytics?.categoryData.length 
  ? analytics.categoryData.map(c => {
      const spendRate = c.commitments > 0 ? (c.actuals / c.commitments * 100) : 0
      let efficiency = 0
      if (spendRate >= 80 && spendRate <= 100) {
        efficiency = 100
      } else if (spendRate > 100) {
        efficiency = Math.max(0, 100 - (spendRate - 100))
      } else {
        efficiency = (spendRate / 80) * 100
      }
      
      return {
        ...c,
        efficiency: Math.min(100, Math.max(0, efficiency))
      }
    })
  : analyticsData.categoryData
```

## Benefits

✅ **No More Negative Values**: Efficiency always between 0-100%
✅ **Meaningful Metric**: Based on spend rate, not variance
✅ **Intuitive**: Higher efficiency = better utilization
✅ **Consistent**: Same logic for projects and categories
✅ **Visual Clarity**: Works well with progress bars and charts

## Testing

- [x] No negative efficiency scores
- [x] Values between 0-100%
- [x] Perfect efficiency (100%) for 80-100% spend rate
- [x] Lower efficiency for under-utilization
- [x] Lower efficiency for over-spending
- [x] Charts display correctly
- [x] No TypeScript errors

## Real Data Impact

With your data (31.2% overall spend rate):
- **Old Formula**: Would show negative or very low efficiency
- **New Formula**: Shows ~39% efficiency (31.2/80 * 100)
- **Interpretation**: Projects are under-utilized (only spending 31% of commitments)

This makes sense! Your projects have committed $46M but only spent $14M, indicating:
- Projects are in early stages
- Conservative spending
- Good budget control
- Room for acceleration

The efficiency score now correctly reflects this situation.
