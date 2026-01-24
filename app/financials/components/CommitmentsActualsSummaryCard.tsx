'use client'

import { TrendingUp, TrendingDown, DollarSign, AlertCircle, CheckCircle } from 'lucide-react'
import { CommitmentsActualsSummary } from '../hooks/useCommitmentsActualsData'

interface CommitmentsActualsSummaryCardProps {
  summary: CommitmentsActualsSummary | null
  projectBudget?: number
  loading?: boolean
}

export default function CommitmentsActualsSummaryCard({ 
  summary, 
  projectBudget,
  loading 
}: CommitmentsActualsSummaryCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-500">No commitments & actuals data available</p>
      </div>
    )
  }

  // Calculate variance if project budget is provided
  const variance = projectBudget ? projectBudget - summary.totalSpend : null
  const variancePercentage = projectBudget && projectBudget > 0 
    ? ((variance! / projectBudget) * 100) 
    : null

  // Determine status color
  const getStatusColor = () => {
    if (!variancePercentage) return 'text-gray-600'
    if (variancePercentage < -5) return 'text-red-600' // Over budget
    if (variancePercentage > 5) return 'text-green-600' // Under budget
    return 'text-yellow-600' // Near budget
  }

  const getStatusBg = () => {
    if (!variancePercentage) return 'bg-gray-50'
    if (variancePercentage < -5) return 'bg-red-50'
    if (variancePercentage > 5) return 'bg-green-50'
    return 'bg-yellow-50'
  }

  const getStatusIcon = () => {
    if (!variancePercentage) return null
    if (variancePercentage < -5) return <AlertCircle className="h-5 w-5 text-red-600" />
    if (variancePercentage > 5) return <CheckCircle className="h-5 w-5 text-green-600" />
    return <AlertCircle className="h-5 w-5 text-yellow-600" />
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: summary.currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Commitments & Actuals</h3>
        <DollarSign className="h-6 w-6 text-blue-600" />
      </div>

      <div className="space-y-4">
        {/* Total Commitments */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total Commitments</span>
          <span className="text-lg font-semibold text-gray-900">
            {formatCurrency(summary.totalCommitments)}
          </span>
        </div>

        {/* Total Actuals */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total Actuals</span>
          <span className="text-lg font-semibold text-gray-900">
            {formatCurrency(summary.totalActuals)}
          </span>
        </div>

        <div className="border-t border-gray-200 pt-3">
          {/* Combined Total Spend */}
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-medium text-gray-700">Total Spend</span>
            <span className="text-xl font-bold text-gray-900">
              {formatCurrency(summary.totalSpend)}
            </span>
          </div>

          {/* Variance (if budget provided) */}
          {variance !== null && (
            <div className={`${getStatusBg()} rounded-lg p-3 mt-3`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon()}
                  <span className="text-sm font-medium text-gray-700">Net Variance</span>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${getStatusColor()}`}>
                    {formatCurrency(Math.abs(variance))}
                  </div>
                  <div className={`text-xs ${getStatusColor()}`}>
                    {variance >= 0 ? 'Under Budget' : 'Over Budget'} ({Math.abs(variancePercentage!).toFixed(1)}%)
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Project Counts */}
        <div className="border-t border-gray-200 pt-3 mt-3">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-green-50 rounded p-2">
              <div className="text-lg font-bold text-green-600">
                {summary.underBudgetCount}
              </div>
              <div className="text-xs text-green-700">Under</div>
            </div>
            <div className="bg-yellow-50 rounded p-2">
              <div className="text-lg font-bold text-yellow-600">
                {summary.onBudgetCount}
              </div>
              <div className="text-xs text-yellow-700">On Track</div>
            </div>
            <div className="bg-red-50 rounded p-2">
              <div className="text-lg font-bold text-red-600">
                {summary.overBudgetCount}
              </div>
              <div className="text-xs text-red-700">Over</div>
            </div>
          </div>
          <div className="text-xs text-gray-500 text-center mt-2">
            {summary.projectCount} projects tracked
          </div>
        </div>
      </div>
    </div>
  )
}
