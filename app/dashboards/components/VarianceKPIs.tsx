'use client'

import { useState, useEffect, memo } from 'react'
import { TrendingUp, TrendingDown, AlertTriangle, Target } from 'lucide-react'
import { getApiUrl } from '../../../lib/api'
import { useTranslations } from '../../../lib/i18n/context'
import { resilientFetch } from '@/lib/api/resilient-fetch'
import { usePermissions } from '@/app/providers/EnhancedAuthProvider'

interface VarianceKPIs {
  total_variance: number
  variance_percentage: number
  projects_over_budget: number
  projects_under_budget: number
  total_commitments: number
  total_actuals: number
  currency: string
}

interface VarianceKPIsProps {
  session: any
  selectedCurrency?: string
  showDetailedMetrics?: boolean
  allowEdit?: boolean
}

function VarianceKPIs({ session, selectedCurrency = 'USD', showDetailedMetrics, allowEdit }: VarianceKPIsProps) {
  const { t } = useTranslations()
  const { hasPermission, loading: permissionsLoading } = usePermissions()
  const [varianceData, setVarianceData] = useState<VarianceKPIs | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Determine permissions - use props if provided, otherwise check permissions
  const canViewFinancials = showDetailedMetrics !== undefined 
    ? showDetailedMetrics 
    : hasPermission('financial_read')
  
  const canEditFinancials = allowEdit !== undefined 
    ? allowEdit 
    : hasPermission('financial_update')

  useEffect(() => {
    console.log('VarianceKPIs useEffect - session:', session?.access_token ? 'present' : 'missing')
    if (session) {
      // Defer to avoid blocking main thread during initial render
      const timeoutId = setTimeout(() => {
        fetchVarianceKPIs()
      }, 50)
      
      return () => clearTimeout(timeoutId)
    }
  }, [session, selectedCurrency])

  const fetchVarianceKPIs = async () => {
    if (!session?.access_token) {
      console.log('No session token, skipping variance fetch')
      return
    }
    
    setLoading(true)
    setError(null)
    
    const result = await resilientFetch<{ variances: any[] }>(
      getApiUrl('/csv-import/variances'),
      {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        timeout: 5000,
        retries: 1,
        fallbackData: { variances: [] },
        silentFail: true,
      }
    )
    
    if (!result.data || result.data.variances.length === 0) {
      setVarianceData(null)
      setLoading(false)
      return
    }
    
    const variances = result.data.variances
    
    // Calculate KPIs from variance data
    const totalCommitments = variances?.reduce((sum: number, v: any) => sum + (v?.total_commitment || 0), 0) || 0
    const totalActuals = variances?.reduce((sum: number, v: any) => sum + (v?.total_actual || 0), 0) || 0
    const totalVariance = totalActuals - totalCommitments
    const variancePercentage = totalCommitments > 0 ? (totalVariance / totalCommitments * 100) : 0
    
    const projectsOverBudget = variances?.filter((v: any) => v?.status === 'over')?.length || 0
    const projectsUnderBudget = variances?.filter((v: any) => v?.status === 'under')?.length || 0
    
    setVarianceData({
      total_variance: totalVariance,
      variance_percentage: variancePercentage,
      projects_over_budget: projectsOverBudget,
      projects_under_budget: projectsUnderBudget,
      total_commitments: totalCommitments,
      total_actuals: totalActuals,
      currency: selectedCurrency
    })
    
    setLoading(false)
  }

  if (loading || permissionsLoading) {
    return (
      <div data-testid="variance-kpis-skeleton" className="bg-white rounded-lg border border-gray-200 p-4 h-full flex flex-col" style={{ minHeight: '240px' }}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-3 flex-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-100 p-3 rounded-lg">
                <div className="h-3 bg-gray-200 rounded w-3/4 mb-3"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !varianceData) {
    return (
      <div data-testid="variance-kpis-error" className="bg-white rounded-lg border border-gray-200 p-4 h-full flex flex-col" style={{ minHeight: '240px' }}>
        <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wide">{t('variance.kpis')}</h3>
        <div className="flex-1 flex items-center justify-center">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center">
            <Target className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
            <span className="text-sm text-blue-800">
              {error ? `Variance data unavailable: ${error}` : 'No variance data available. Import CSV files to see variance analysis.'}
            </span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-testid="variance-kpis" className="bg-white rounded-lg border border-gray-200 p-4 h-full flex flex-col" style={{ minHeight: '240px' }}>
      {/* Header */}
      <div data-testid="variance-kpis-header" className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">{t('variance.kpis')}</h3>
        {varianceData.projects_over_budget > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-50 border border-red-200 rounded-full">
            <AlertTriangle className="h-3.5 w-3.5 text-red-600" />
            <span className="text-xs font-medium text-red-800">
              {varianceData.projects_over_budget} {t('financials.overBudget')}
            </span>
          </div>
        )}
      </div>

      {/* KPI Grid - 2x2 layout */}
      <div data-testid="variance-kpis-grid" className="grid grid-cols-2 gap-2 flex-1">
        {canViewFinancials ? (
          <>
            <div data-testid="variance-kpis-net-variance" className="bg-gray-50 p-2 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-600">{t('variance.netVariance')}</p>
                {varianceData.total_variance >= 0 ? 
                  <TrendingUp className="h-3.5 w-3.5 text-red-600" /> : 
                  <TrendingDown className="h-3.5 w-3.5 text-green-600" />
                }
              </div>
              <p className={`text-lg font-bold ${
                varianceData.total_variance >= 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {varianceData.total_variance >= 0 ? '+' : ''}
                {(varianceData.total_variance / 1000).toFixed(0)}k
              </p>
            </div>
            
            <div data-testid="variance-kpis-variance-percent" className="bg-gray-50 p-2 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-600">{t('financials.variance')} %</p>
                <Target className="h-3.5 w-3.5 text-gray-500" />
              </div>
              <p className={`text-lg font-bold ${
                varianceData.variance_percentage >= 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {varianceData.variance_percentage >= 0 ? '+' : ''}
                {varianceData.variance_percentage.toFixed(1)}%
              </p>
            </div>
            
            <div data-testid="variance-kpis-over-budget" className="bg-gray-50 p-2 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-600">{t('financials.overBudget')}</p>
                <AlertTriangle className="h-3.5 w-3.5 text-red-600" />
              </div>
              <p className="text-lg font-bold text-red-600">
                {varianceData.projects_over_budget}
              </p>
            </div>
            
            <div data-testid="variance-kpis-under-budget" className="bg-gray-50 p-2 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-600">{t('financials.underBudget')}</p>
                <TrendingDown className="h-3.5 w-3.5 text-green-600" />
              </div>
              <p className="text-lg font-bold text-green-600">
                {varianceData.projects_under_budget}
              </p>
            </div>
          </>
        ) : (
          <div className="col-span-2 bg-gray-50 p-4 rounded-lg flex items-center justify-center">
            <p className="text-sm text-gray-500">Financial details restricted</p>
          </div>
        )}
      </div>

      {/* Commitments vs Actuals - Compact */}
      {canViewFinancials && (
        <div data-testid="variance-kpis-commitments-actuals" className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex justify-between text-xs mb-2">
            <span className="text-gray-600">{t('variance.totalCommitments')}: <span className="font-semibold text-blue-600">{(varianceData.total_commitments / 1000).toFixed(0)}k</span></span>
            <span className="text-gray-600">{t('variance.totalActuals')}: <span className="font-semibold text-purple-600">{(varianceData.total_actuals / 1000).toFixed(0)}k</span></span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className={`h-1.5 rounded-full ${
                varianceData.total_actuals > varianceData.total_commitments ? 'bg-red-500' : 'bg-blue-500'
              }`}
              style={{ 
                width: `${Math.min(100, (varianceData.total_actuals / Math.max(varianceData.total_commitments, 1)) * 100)}%`
              }}
            />
          </div>
          <div className="text-right mt-1">
            <span className="text-xs text-gray-500">
              {((varianceData.total_actuals / Math.max(varianceData.total_commitments, 1)) * 100).toFixed(0)}% spent
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// Custom comparison function to prevent unnecessary re-renders
// Only re-render if session token or currency changes
const arePropsEqual = (prevProps: VarianceKPIsProps, nextProps: VarianceKPIsProps) => {
  return (
    prevProps.session?.access_token === nextProps.session?.access_token &&
    prevProps.selectedCurrency === nextProps.selectedCurrency
  )
}

export default memo(VarianceKPIs, arePropsEqual)