import { useState, useEffect, useCallback } from 'react'
import { 
  Project, 
  BudgetVariance, 
  FinancialAlert, 
  FinancialMetrics,
  ComprehensiveFinancialReport,
  CostAnalysis,
  BudgetPerformanceMetrics
} from '../types'
import { 
  fetchProjects, 
  fetchBudgetVariance, 
  fetchFinancialAlerts, 
  fetchComprehensiveReport 
} from '../utils/api'
import { 
  calculateFinancialMetrics, 
  calculateBudgetPerformance 
} from '../utils/calculations'
import { getApiUrl } from '../../../lib/api'

interface UseFinancialDataProps {
  accessToken: string | undefined
  selectedCurrency: string
}

export function useFinancialData({ accessToken, selectedCurrency }: UseFinancialDataProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [budgetVariances, setBudgetVariances] = useState<BudgetVariance[]>([])
  const [financialAlerts, setFinancialAlerts] = useState<FinancialAlert[]>([])
  const [metrics, setMetrics] = useState<FinancialMetrics | null>(null)
  const [comprehensiveReport, setComprehensiveReport] = useState<ComprehensiveFinancialReport | null>(null)
  const [costAnalysis, setCostAnalysis] = useState<CostAnalysis[]>([])
  const [budgetPerformance, setBudgetPerformance] = useState<BudgetPerformanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAllProjects = useCallback(async () => {
    if (!accessToken) return
    
    try {
      const projectsData = await fetchProjects(accessToken)
      setProjects(projectsData)
      return projectsData
    } catch (error: unknown) {
      console.error('Error fetching projects:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch projects')
      return []
    }
  }, [accessToken])

  const fetchAllBudgetVariances = useCallback(async (projectsList: Project[]) => {
    if (!accessToken || !projectsList.length) return
    
    const variances: BudgetVariance[] = []
    
    for (const project of projectsList) {
      const variance = await fetchBudgetVariance(project.id, selectedCurrency, accessToken)
      if (variance) {
        variances.push(variance)
      }
    }
    
    setBudgetVariances(variances)
    return variances
  }, [accessToken, selectedCurrency])

  const fetchAllFinancialAlerts = useCallback(async () => {
    if (!accessToken) return
    
    try {
      const alerts = await fetchFinancialAlerts(accessToken)
      setFinancialAlerts(alerts)
    } catch (error) {
      console.error('Failed to fetch financial alerts:', error)
    }
  }, [accessToken])

  const fetchAllComprehensiveReport = useCallback(async () => {
    if (!accessToken) return
    
    try {
      const report = await fetchComprehensiveReport(selectedCurrency, accessToken)
      setComprehensiveReport(report)
    } catch (error) {
      console.error('Failed to fetch comprehensive financial report:', error)
    }
  }, [accessToken, selectedCurrency])

  const fetchCostAnalysisData = useCallback(async () => {
    if (!accessToken) return
    
    try {
      // Fetch commitments and actuals to calculate real cost analysis
      const [commitmentsRes, actualsRes] = await Promise.all([
        fetch(getApiUrl('/csv-import/commitments?limit=10000'), {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          }
        }),
        fetch(getApiUrl('/csv-import/actuals?limit=10000'), {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          }
        })
      ])

      if (!commitmentsRes.ok || !actualsRes.ok) {
        console.error('Failed to fetch cost analysis data')
        setCostAnalysis([])
        return
      }

      const commitmentsData = await commitmentsRes.json()
      const actualsData = await actualsRes.json()

      const commitments = commitmentsData.commitments || []
      const actuals = actualsData.actuals || []

      // Group by category (WBS) and calculate monthly trends
      const categoryMap = new Map<string, { 
        currentMonth: number
        previousMonth: number
        category: string
      }>()

      const now = new Date()
      const currentMonth = now.getMonth()
      const currentYear = now.getFullYear()
      const previousMonth = currentMonth === 0 ? 11 : currentMonth - 1
      const previousYear = currentMonth === 0 ? currentYear - 1 : currentYear

      // Process actuals (real spending)
      actuals.forEach((a: any) => {
        const category = a.wbs_element || a.wbs || a.cost_center || 'Uncategorized'
        const postingDate = a.posting_date ? new Date(a.posting_date) : null
        const amount = a.invoice_amount || a.amount || 0

        if (!postingDate) return

        const month = postingDate.getMonth()
        const year = postingDate.getFullYear()

        if (!categoryMap.has(category)) {
          categoryMap.set(category, {
            currentMonth: 0,
            previousMonth: 0,
            category
          })
        }

        const data = categoryMap.get(category)!

        if (year === currentYear && month === currentMonth) {
          data.currentMonth += amount
        } else if (year === previousYear && month === previousMonth) {
          data.previousMonth += amount
        }
      })

      // Convert to CostAnalysis format
      const costAnalysisData: CostAnalysis[] = Array.from(categoryMap.entries())
        .map(([category, data]) => {
          const percentageChange = data.previousMonth > 0
            ? ((data.currentMonth - data.previousMonth) / data.previousMonth) * 100
            : 0

          let trend: 'up' | 'down' | 'stable' = 'stable'
          if (Math.abs(percentageChange) > 5) {
            trend = percentageChange > 0 ? 'up' : 'down'
          }

          return {
            category: category.length > 20 ? category.substring(0, 20) + '...' : category,
            current_month: data.currentMonth,
            previous_month: data.previousMonth,
            trend,
            percentage_change: percentageChange
          }
        })
        .filter(item => item.current_month > 0 || item.previous_month > 0) // Only show categories with data
        .sort((a, b) => b.current_month - a.current_month) // Sort by current month spending
        .slice(0, 8) // Top 8 categories

      setCostAnalysis(costAnalysisData)
    } catch (error) {
      console.error('Error calculating cost analysis:', error)
      setCostAnalysis([])
    }
  }, [accessToken])

  const calculateMetrics = useCallback((variances: BudgetVariance[]) => {
    if (!variances.length) return
    
    const metricsData = calculateFinancialMetrics(variances, selectedCurrency)
    setMetrics(metricsData)
  }, [selectedCurrency])

  const calculatePerformance = useCallback((variances: BudgetVariance[]) => {
    const performance = calculateBudgetPerformance(variances)
    setBudgetPerformance(performance)
  }, [])

  const fetchAllData = useCallback(async () => {
    if (!accessToken) return
    
    setLoading(true)
    setError(null)
    
    try {
      // Fetch projects first
      const projectsData = await fetchAllProjects()
      
      // Then fetch budget variances
      const variancesData = await fetchAllBudgetVariances(projectsData || [])
      
      // Calculate metrics and performance
      if (variancesData) {
        calculateMetrics(variancesData)
        calculatePerformance(variancesData)
      }
      
      // Fetch other data in parallel
      await Promise.all([
        fetchAllFinancialAlerts(),
        fetchAllComprehensiveReport(),
        fetchCostAnalysisData()
      ])
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [
    accessToken, 
    fetchAllProjects, 
    fetchAllBudgetVariances, 
    fetchAllFinancialAlerts, 
    fetchAllComprehensiveReport, 
    fetchCostAnalysisData,
    calculateMetrics,
    calculatePerformance
  ])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  return {
    projects,
    budgetVariances,
    financialAlerts,
    metrics,
    comprehensiveReport,
    costAnalysis,
    budgetPerformance,
    loading,
    error,
    refetch: fetchAllData
  }
}