'use client'

import { useEffect, useState, useMemo, Suspense, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { useAuth } from '../providers/SupabaseAuthProvider'
import AppLayout from '../../components/shared/AppLayout'
import PageContainer from '../../components/shared/PageContainer'
import { getApiUrl, apiRequest } from '../../lib/api/client'
import { 
  loadDashboardData, 
  clearDashboardCache,
  type QuickStats,
  type KPIs,
  type Project
} from '../../lib/api/dashboard-loader'
import ProjectCard from './components/ProjectCard'
import { useCrossDeviceSync } from '../../hooks/useCrossDeviceSync'
import { useAutoPrefetch } from '../../hooks/useRoutePrefetch'
import { TrendingUp, AlertTriangle, CheckCircle, Clock, DollarSign, RefreshCw, Eye, Users, BarChart3, GitBranch, Zap } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { ComponentErrorBoundary } from '../../components/error-boundaries/ComponentErrorBoundary'
import { SkeletonCard, SkeletonChart } from '../../components/ui/skeletons'
import type { DashboardWidget } from '../../components/ui/organisms/AdaptiveDashboard'
import { useLanguage } from '../../hooks/useLanguage'
import { useTranslations } from '../../lib/i18n/context'

// Dynamic imports for heavy components (code splitting)
const VarianceKPIs = dynamic(() => import('./components/VarianceKPIs'), {
  loading: () => (
    <div className="grid grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <SkeletonCard key={i} variant="stat" />
      ))}
    </div>
  ),
  ssr: false
})

const VarianceTrends = dynamic(() => import('./components/VarianceTrends'), {
  loading: () => <SkeletonChart variant="line" height="h-80" />,
  ssr: false
})

const VarianceAlerts = dynamic(() => import('./components/VarianceAlerts'), {
  loading: () => <SkeletonCard variant="stat" />,
  ssr: false
})

const VirtualizedProjectList = dynamic(() => import('../../components/ui/VirtualizedProjectList'), {
  loading: () => (
    <div className="divide-y divide-gray-200">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="px-6 py-4">
          <div className="animate-pulse flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <div className="w-3 h-3 bg-gray-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-1/6"></div>
          </div>
        </div>
      ))}
    </div>
  ),
  ssr: false
})

const AdaptiveDashboard = dynamic(() => import('../../components/ui/organisms/AdaptiveDashboard').then(mod => ({ default: mod.default })), {
  loading: () => (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="animate-pulse space-y-4">
        <div className="h-5 bg-gray-200 rounded w-1/3"></div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    </div>
  ),
  ssr: false
})

export default function UltraFastDashboard() {
  const { session } = useAuth()
  const router = useRouter()
  const { currentLanguage } = useLanguage()
  const { t } = useTranslations()
  
  const [quickStats, setQuickStats] = useState<QuickStats | null>(null)
  const [kpis, setKPIs] = useState<KPIs | null>(null)
  const [recentProjects, setRecentProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [varianceAlertCount, setVarianceAlertCount] = useState(0)
  const [dashboardWidgets, setDashboardWidgets] = useState<DashboardWidget[]>([])
  const [dashboardLayout, setDashboardLayout] = useState<'grid' | 'masonry' | 'list'>('grid')
  const [showAdaptiveDashboard, setShowAdaptiveDashboard] = useState(false)

  // Prefetch /resources route for instant navigation
  useAutoPrefetch(['/resources', '/scenarios', '/financials'], 1500)

  // Cross-device synchronization
  const {
    preferences,
    updatePreferences,
    initialize: initializeSync,
    isSyncing,
    lastSyncTime
  } = useCrossDeviceSync()

  // Loading component for Suspense fallbacks
  const LoadingFallback = ({ message = "Loading..." }: { message?: string }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
        <div className="h-32 bg-gray-200 rounded"></div>
      </div>
      <p className="text-sm text-gray-500 mt-2">{message}</p>
    </div>
  )

  // Error component for error boundaries
  const ErrorFallback = ({ error, onRetry }: { error: Error; onRetry: () => void }) => (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start">
        <AlertTriangle className="h-5 w-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800">Component Error</h3>
          <p className="text-sm text-red-700 mt-1">{error.message}</p>
          <button
            onClick={onRetry}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  )

  // Optimized data loading with parallel requests, caching, and progressive loading
  const loadOptimizedData = useCallback(async () => {
    if (!session?.access_token) return
    
    setLoading(true)
    setError(null)
    
    try {
      // Use progressive loading: show critical data first, then secondary data
      await loadDashboardData(
        session.access_token,
        // Callback for critical data (QuickStats + KPIs)
        (criticalData) => {
          setQuickStats(criticalData.quickStats)
          setKPIs(criticalData.kpis)
          setLoading(false) // Stop loading spinner once critical data is ready
          setLastUpdated(new Date())
        },
        // Callback for secondary data (Projects)
        (projects) => {
          setRecentProjects(projects)
        }
      )
    } catch (err) {
      console.error('Dashboard load error:', err)
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      
      // Show fallback data instead of error
      setQuickStats({
        total_projects: 0,
        active_projects: 0,
        health_distribution: { green: 0, yellow: 0, red: 0 },
        critical_alerts: 0,
        at_risk_projects: 0
      })
      setKPIs({
        project_success_rate: 0,
        budget_performance: 0,
        timeline_performance: 0,
        average_health_score: 0,
        resource_efficiency: 0,
        active_projects_ratio: 0
      })
      setLoading(false)
    }
  }, [session?.access_token])

  // Optimized loading with progressive data loading
  useEffect(() => {
    if (session?.access_token) {
      loadOptimizedData()
      // Initialize cross-device sync
      if (session.user?.id) {
        initializeSync(session.user.id)
      }
    }
  }, [session, initializeSync, loadOptimizedData])

  // Sync dashboard preferences when they change
  useEffect(() => {
    if (preferences?.dashboardLayout) {
      setDashboardLayout(preferences.dashboardLayout.layout)
      setDashboardWidgets(preferences.dashboardLayout.widgets || [])
      setShowAdaptiveDashboard((preferences.dashboardLayout.widgets?.length || 0) > 0)
    }
  }, [preferences])

  // Generate dashboard widgets from existing data
  useEffect(() => {
    if (quickStats && kpis && !showAdaptiveDashboard) {
      generateDashboardWidgets()
    }
  }, [quickStats, kpis, showAdaptiveDashboard])

  const generateDashboardWidgets = () => {
    const widgets: DashboardWidget[] = [
      {
        id: 'project-success-rate',
        type: 'metric',
        title: 'Project Success Rate',
        data: {
          value: `${kpis?.project_success_rate || 0}%`,
          label: 'Success Rate',
          change: 5.2
        },
        size: 'small',
        position: { x: 0, y: 0 },
        priority: 1
      },
      {
        id: 'budget-performance',
        type: 'metric',
        title: 'Budget Performance',
        data: {
          value: `${kpis?.budget_performance || 0}%`,
          label: 'Budget Efficiency',
          change: -2.1
        },
        size: 'small',
        position: { x: 1, y: 0 },
        priority: 2
      },
      {
        id: 'timeline-performance',
        type: 'metric',
        title: 'Timeline Performance',
        data: {
          value: `${kpis?.timeline_performance || 0}%`,
          label: 'On-Time Delivery',
          change: 3.7
        },
        size: 'small',
        position: { x: 2, y: 0 },
        priority: 3
      },
      {
        id: 'active-projects-ratio',
        type: 'metric',
        title: 'Active Projects',
        data: {
          value: `${kpis?.active_projects_ratio || 0}%`,
          label: 'Active Ratio',
          change: 1.2
        },
        size: 'small',
        position: { x: 3, y: 0 },
        priority: 4
      },
      {
        id: 'project-health-overview',
        type: 'chart',
        title: 'Project Health Overview',
        data: {
          healthy: quickStats?.health_distribution?.green || 0,
          atRisk: quickStats?.health_distribution?.yellow || 0,
          critical: quickStats?.health_distribution?.red || 0
        },
        size: 'medium',
        position: { x: 0, y: 1 },
        priority: 5
      },
      {
        id: 'recent-projects-list',
        type: 'list',
        title: 'Recent Projects',
        data: {
          items: recentProjects?.slice(0, 5)?.map(project => ({
            name: project?.name || 'Unknown Project',
            status: project?.health === 'green' ? 'success' : 
                   project?.health === 'yellow' ? 'warning' : 'error'
          })) || []
        },
        size: 'medium',
        position: { x: 2, y: 1 },
        priority: 6
      }
    ]

    // Add AI-powered insights if variance alerts exist
    if (varianceAlertCount > 0) {
      widgets.push({
        id: 'ai-budget-insight',
        type: 'ai-insight',
        title: 'Budget Optimization Insight',
        data: {
          insight: `Detected ${varianceAlertCount} budget variance${varianceAlertCount !== 1 ? 's' : ''}. Consider reallocating resources from over-performing projects to those at risk.`,
          confidence: 0.85,
          impact: 'high',
          actions: ['View Details', 'Apply Suggestions', 'Dismiss']
        },
        size: 'large',
        position: { x: 0, y: 2 },
        priority: 1,
        aiRecommended: true
      })
    }

    setDashboardWidgets(widgets)
  }

  // Quick refresh (optimized with cache clearing)
  const quickRefresh = useCallback(async () => {
    if (!session?.access_token) return
    
    try {
      // Clear cache to force fresh data
      clearDashboardCache()
      await loadOptimizedData()
    } catch (err) {
      console.error('Refresh failed:', err)
    }
  }, [session?.access_token, loadOptimizedData])

  // Handle dashboard widget updates and sync across devices
  const handleWidgetUpdate = useCallback(async (widgets: DashboardWidget[]) => {
    setDashboardWidgets(widgets)
    
    // Sync dashboard preferences across devices
    if (preferences) {
      await updatePreferences({
        ...preferences,
        dashboardLayout: {
          ...preferences.dashboardLayout,
          widgets
        }
      })
    }
  }, [preferences, updatePreferences])

  // Handle layout changes and sync across devices
  const handleLayoutChange = useCallback(async (layout: 'grid' | 'masonry' | 'list') => {
    setDashboardLayout(layout)
    
    // Sync layout preference across devices
    if (preferences) {
      await updatePreferences({
        ...preferences,
        dashboardLayout: {
          ...preferences.dashboardLayout,
          layout
        }
      })
    }
  }, [preferences, updatePreferences])

  // Toggle between adaptive and traditional dashboard
  const toggleDashboardMode = useCallback(() => {
    setShowAdaptiveDashboard(!showAdaptiveDashboard)
  }, [showAdaptiveDashboard])

  // Memoized calculations for performance
  const healthPercentages = useMemo(() => {
    if (!quickStats?.health_distribution) return { healthy: 0, atRisk: 0, critical: 0 }
    
    const total = quickStats?.total_projects || 1
    return {
      healthy: Math.round(((quickStats?.health_distribution?.green || 0) / total) * 100),
      atRisk: Math.round(((quickStats?.health_distribution?.yellow || 0) / total) * 100),
      critical: Math.round(((quickStats?.health_distribution?.red || 0) / total) * 100)
    }
  }, [quickStats])

  // Ultra-fast loading state
  if (loading) return (
    <AppLayout>
      <PageContainer maxWidth="wide">
        {/* Header Skeleton */}
        <div className="animate-pulse mb-6">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
        
        {/* KPI Cards Skeleton */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem',
            marginBottom: '1.5rem'
          }}
        >
          {[...Array(4)].map((_, i) => (
            <SkeletonCard key={i} variant="stat" />
          ))}
        </div>
        
        {/* Variance KPIs Skeleton */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem',
            marginBottom: '1.5rem'
          }}
        >
          {[...Array(4)].map((_, i) => (
            <SkeletonCard key={i} variant="stat" />
          ))}
        </div>
        
        {/* Health Overview Skeleton */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
            gap: '1.5rem',
            marginBottom: '1.5rem'
          }}
        >
          <SkeletonChart variant="pie" />
          <div className="card">
            <div className="card-body">
              <div className="animate-pulse space-y-4">
                <div className="h-5 bg-gray-200 rounded w-1/3"></div>
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex justify-between">
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Variance Trends Skeleton */}
        <div className="mb-6">
          <SkeletonChart variant="line" height="h-80" />
        </div>
        
        {/* Recent Projects Skeleton */}
        <div className="card">
          <div className="card-header">
            <div className="animate-pulse h-5 bg-gray-200 rounded w-1/4"></div>
          </div>
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="px-4 py-4 sm:px-6">
                <div className="animate-pulse flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="w-3 h-3 bg-gray-200 rounded-full"></div>
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                  <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </PageContainer>
    </AppLayout>
  )

  return (
    <AppLayout>
      <PageContainer maxWidth="wide" compact>
        {/* Ultra-fast Header */}
        <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-3 mb-4">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
              {quickStats && quickStats.critical_alerts > 0 && (
                <div className="flex items-center px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                  <AlertTriangle className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="whitespace-nowrap">{quickStats.critical_alerts} {t('dashboard.critical')}</span>
                </div>
              )}
              {varianceAlertCount > 0 && (
                <div className="flex items-center px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
                  <DollarSign className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="whitespace-nowrap">{varianceAlertCount} {varianceAlertCount !== 1 ? t('dashboard.budgetAlerts') : t('dashboard.budgetAlert')}</span>
                </div>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-600">
              {quickStats && <span className="whitespace-nowrap">{quickStats.total_projects} {t('dashboard.projects')}</span>}
              {lastUpdated && (
                <span className="whitespace-nowrap">{t('dashboard.updated')}: {lastUpdated.toLocaleTimeString()}</span>
              )}
              {lastSyncTime && (
                <span className="whitespace-nowrap flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-1 flex-shrink-0 ${isSyncing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
                  {isSyncing ? t('dashboard.syncing') : t('dashboard.synced')}
                </span>
              )}
              <span className="flex items-center text-green-600 whitespace-nowrap">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1 flex-shrink-0"></div>
                {t('dashboard.live')}
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={toggleDashboardMode}
              className="flex items-center justify-center px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
              title={showAdaptiveDashboard ? t('dashboard.traditionalView') : t('dashboard.aiView')}
            >
              <Zap className="h-4 w-4 mr-2 flex-shrink-0" />
              <span>{t('dashboard.aiEnhanced')}</span>
            </button>
            
            <button
              onClick={quickRefresh}
              className="flex items-center justify-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2 flex-shrink-0" />
              <span>{t('dashboard.refresh')}</span>
            </button>
          </div>
        </div>

        {/* Error Banner (if any) */}
        {error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-yellow-800 break-words">
                {t('dashboard.fallbackData')} - {error}
              </span>
            </div>
          </div>
        )}

        {/* Adaptive Dashboard or Traditional Dashboard */}
        {showAdaptiveDashboard && session?.user?.id ? (
          <ComponentErrorBoundary
            componentName="AdaptiveDashboard"
            fallbackComponent={({ error, resetError }) => (
              <ErrorFallback error={error} onRetry={resetError} />
            )}
          >
            <Suspense fallback={<LoadingFallback message="Loading AI-enhanced dashboard..." />}>
              <AdaptiveDashboard
                userId={session.user.id}
                userRole={session.user.user_metadata?.role || 'user'}
                widgets={dashboardWidgets}
                layout={dashboardLayout}
                enableAI={true}
                enableDragDrop={true}
                onWidgetUpdate={handleWidgetUpdate}
                onLayoutChange={handleLayoutChange}
                className="mt-6"
              />
            </Suspense>
          </ComponentErrorBoundary>
        ) : (
          <>
            {/* Traditional Dashboard Content */}
            {/* Ultra-fast KPI Cards */}
            {kpis && (
              <ComponentErrorBoundary
                componentName="KPICards"
                fallbackComponent={({ error, resetError }) => (
                  <ErrorFallback error={error} onRetry={resetError} />
                )}
              >
                <div 
                  className="mb-4"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '1rem'
                  }}
                >
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-600">{t('kpi.successRate')}</p>
                        <p className="text-2xl font-bold text-green-600 mt-1">{kpis?.project_success_rate || 0}%</p>
                      </div>
                      <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-600">{t('kpi.budgetPerformance')}</p>
                        <p className="text-2xl font-bold text-blue-600 mt-1">{kpis?.budget_performance || 0}%</p>
                      </div>
                      <DollarSign className="h-6 w-6 text-blue-600 flex-shrink-0" />
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-600">{t('kpi.timelinePerformance')}</p>
                        <p className="text-2xl font-bold text-purple-600 mt-1">{kpis?.timeline_performance || 0}%</p>
                      </div>
                      <Clock className="h-6 w-6 text-purple-600 flex-shrink-0" />
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-600">{t('kpi.activeProjects')}</p>
                        <p className="text-2xl font-bold text-indigo-600 mt-1">{kpis?.active_projects_ratio || 0}%</p>
                      </div>
                      <TrendingUp className="h-6 w-6 text-indigo-600 flex-shrink-0" />
                    </div>
                  </div>
                </div>
              </ComponentErrorBoundary>
            )}

            {/* Variance KPIs Integration */}
            <ComponentErrorBoundary
              componentName="VarianceKPIs"
              fallbackComponent={({ error, resetError }) => (
                <ErrorFallback error={error} onRetry={resetError} />
              )}
            >
              <Suspense fallback={<LoadingFallback message="Loading variance KPIs..." />}>
                <VarianceKPIs session={session} selectedCurrency="USD" />
              </Suspense>
            </ComponentErrorBoundary>

            {/* Quick Health Overview */}
            {quickStats && (
              <ComponentErrorBoundary
                componentName="HealthOverview"
                fallbackComponent={({ error, resetError }) => (
                  <ErrorFallback error={error} onRetry={resetError} />
                )}
              >
                <div 
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                    gap: '1rem'
                  }}
                  className="mb-4"
                >
                  {/* Health Distribution */}
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-base font-semibold text-gray-900 mb-3">{t('health.projectHealth')}</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center min-w-0">
                          <div className="w-2.5 h-2.5 bg-green-500 rounded-full mr-2 flex-shrink-0"></div>
                          <span className="text-sm font-medium text-gray-700">{t('health.healthy')}</span>
                        </div>
                        <div className="flex items-center space-x-2 flex-shrink-0">
                          <span className="text-sm font-bold text-gray-900">{quickStats?.health_distribution?.green || 0}</span>
                          <span className="text-xs text-gray-500">({healthPercentages?.healthy || 0}%)</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center min-w-0">
                          <div className="w-2.5 h-2.5 bg-yellow-500 rounded-full mr-2 flex-shrink-0"></div>
                          <span className="text-sm font-medium text-gray-700">{t('health.atRisk')}</span>
                        </div>
                        <div className="flex items-center space-x-2 flex-shrink-0">
                          <span className="text-sm font-bold text-gray-900">{quickStats?.health_distribution?.yellow || 0}</span>
                          <span className="text-xs text-gray-500">({healthPercentages?.atRisk || 0}%)</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center min-w-0">
                          <div className="w-2.5 h-2.5 bg-red-500 rounded-full mr-2 flex-shrink-0"></div>
                          <span className="text-sm font-medium text-gray-700">{t('health.critical')}</span>
                        </div>
                        <div className="flex items-center space-x-2 flex-shrink-0">
                          <span className="text-sm font-bold text-gray-900">{quickStats?.health_distribution?.red || 0}</span>
                          <span className="text-xs text-gray-500">({healthPercentages?.critical || 0}%)</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Simple Health Bar */}
                    <div className="mt-3">
                      <div className="flex h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="bg-green-500" 
                          style={{ width: `${healthPercentages?.healthy || 0}%` }}
                        >
                        </div>
                        <div 
                          className="bg-yellow-500" 
                          style={{ width: `${healthPercentages?.atRisk || 0}%` }}
                        >
                        </div>
                        <div 
                          className="bg-red-500" 
                          style={{ width: `${healthPercentages?.critical || 0}%` }}
                        >
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-base font-semibold text-gray-900 mb-3">{t('stats.quickStats')}</h3>
                    <div 
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '0.75rem'
                      }}
                    >
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{quickStats?.total_projects || 0}</div>
                        <div className="text-xs text-gray-600">{t('stats.totalProjects')}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{quickStats?.active_projects || 0}</div>
                        <div className="text-xs text-gray-600">{t('stats.activeProjects')}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">{quickStats?.critical_alerts || 0}</div>
                        <div className="text-xs text-gray-600">{t('stats.criticalAlerts')}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-600">{quickStats?.at_risk_projects || 0}</div>
                        <div className="text-xs text-gray-600">{t('stats.atRisk')}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </ComponentErrorBoundary>
            )}

            {/* Variance Trends and Alerts - Side by Side */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
                gap: '1rem'
              }}
              className="mb-4"
            >
              <ComponentErrorBoundary
                componentName="VarianceTrends"
                fallbackComponent={({ error, resetError }) => (
                  <ErrorFallback error={error} onRetry={resetError} />
                )}
              >
                <Suspense fallback={<LoadingFallback message="Loading variance trends..." />}>
                  <VarianceTrends session={session} selectedCurrency="USD" />
                </Suspense>
              </ComponentErrorBoundary>

              <ComponentErrorBoundary
                componentName="VarianceAlerts"
                fallbackComponent={({ error, resetError }) => (
                  <ErrorFallback error={error} onRetry={resetError} />
                )}
              >
                <Suspense fallback={<LoadingFallback message="Loading variance alerts..." />}>
                  <VarianceAlerts session={session} onAlertCount={setVarianceAlertCount} />
                </Suspense>
              </ComponentErrorBoundary>
            </div>

            {/* Recent Projects and Quick Actions - Side by Side */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
                gap: '1rem'
              }}
            >
              {/* Recent Projects (Loaded in background) */}
              {(recentProjects?.length || 0) > 0 && (
                <ComponentErrorBoundary
                  componentName="RecentProjects"
                  fallbackComponent={({ error, resetError }) => (
                    <ErrorFallback error={error} onRetry={resetError} />
                  )}
                >
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    <div className="px-4 py-3 border-b border-gray-200">
                      <h3 className="text-base font-semibold text-gray-900">{t('projects.recentProjects')}</h3>
                    </div>
                    <VirtualizedProjectList 
                      projects={recentProjects} 
                      height={400}
                      itemHeight={100}
                    />
                  </div>
                </ComponentErrorBoundary>
              )}

              {/* Quick Actions */}
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-base font-semibold text-gray-900 mb-3">{t('actions.quickActions')}</h3>
                <div 
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '0.75rem'
                  }}
                >
                  <button 
                    onClick={() => router.push('/scenarios')}
                    className="flex items-center justify-center p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="text-center">
                      <GitBranch className="h-6 w-6 text-gray-400 mx-auto mb-1" />
                      <span className="text-xs font-medium text-gray-700">{t('actions.scenarios')}</span>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => router.push('/dashboards')}
                    className="flex items-center justify-center p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="text-center">
                      <BarChart3 className="h-6 w-6 text-gray-400 mx-auto mb-1" />
                      <span className="text-xs font-medium text-gray-700">{t('actions.charts')}</span>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => router.push('/resources')}
                    className="flex items-center justify-center p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
                  >
                    <div className="text-center">
                      <Users className="h-6 w-6 text-gray-400 mx-auto mb-1" />
                      <span className="text-xs font-medium text-gray-700">{t('actions.resources')}</span>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => router.push('/financials')}
                    className="flex items-center justify-center p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors"
                  >
                    <div className="text-center">
                      <DollarSign className="h-6 w-6 text-gray-400 mx-auto mb-1" />
                      <span className="text-xs font-medium text-gray-700">{t('actions.financials')}</span>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => router.push('/reports')}
                    className="flex items-center justify-center p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors"
                  >
                    <div className="text-center">
                      <Eye className="h-6 w-6 text-gray-400 mx-auto mb-1" />
                      <span className="text-xs font-medium text-gray-700">{t('actions.reports')}</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </PageContainer>
    </AppLayout>
  )
}