/**
 * Mock Data Generators for UI Structure Tests
 * 
 * Provides generators for session, project, and financial data
 * that satisfy component prop types and can be used for testing.
 */

import type { Project, User, Resource, Risk } from '@/types'
import type { 
  FinancialMetrics, 
  BudgetVariance, 
  FinancialAlert,
  Project as FinancialProject 
} from '@/app/financials/types'

// ============================================================================
// Session Mock Generators
// ============================================================================

export interface MockSession {
  access_token: string
  refresh_token: string
  expires_at: number
  expires_in: number
  token_type: string
  user: {
    id: string
    email: string
    role: string
    aud: string
    created_at: string
  }
}

/**
 * Generates a mock session object for testing
 */
export function generateMockSession(overrides?: Partial<MockSession>): MockSession {
  const now = Date.now()
  const userId = overrides?.user?.id || `user-${Math.random().toString(36).substring(7)}`
  
  const baseSession: MockSession = {
    access_token: `mock-access-token-${Math.random().toString(36).substring(7)}`,
    refresh_token: `mock-refresh-token-${Math.random().toString(36).substring(7)}`,
    expires_at: now + 3600000, // 1 hour from now
    expires_in: 3600,
    token_type: 'bearer',
    user: {
      id: userId,
      email: overrides?.user?.email || `user-${userId}@example.com`,
      role: overrides?.user?.role || 'user',
      aud: overrides?.user?.aud || 'authenticated',
      created_at: overrides?.user?.created_at || new Date(now - 86400000).toISOString(), // 1 day ago
    },
  }
  
  // Apply overrides at top level only (not user level to avoid undefined values)
  if (overrides) {
    if (overrides.access_token) baseSession.access_token = overrides.access_token
    if (overrides.refresh_token) baseSession.refresh_token = overrides.refresh_token
    if (overrides.expires_at) baseSession.expires_at = overrides.expires_at
    if (overrides.expires_in) baseSession.expires_in = overrides.expires_in
    if (overrides.token_type) baseSession.token_type = overrides.token_type
  }
  
  return baseSession
}

/**
 * Generates a mock admin session
 */
export function generateMockAdminSession(overrides?: Partial<MockSession>): MockSession {
  return generateMockSession({
    ...overrides,
    user: {
      ...overrides?.user,
      role: 'admin',
    },
  })
}

// ============================================================================
// Project Mock Generators
// ============================================================================

/**
 * Generates a mock project for testing
 */
export function generateMockProject(overrides?: Partial<Project>): Project {
  const id = overrides?.id || `project-${Math.random().toString(36).substring(7)}`
  const now = new Date()
  const startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000) // 30 days ago
  const endDate = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000) // 60 days from now
  
  return {
    id,
    name: overrides?.name || `Project ${id.substring(8)}`,
    description: overrides?.description || `Description for ${id}`,
    status: overrides?.status || 'active',
    priority: overrides?.priority || 'medium',
    start_date: overrides?.start_date || startDate.toISOString(),
    end_date: overrides?.end_date || endDate.toISOString(),
    budget: overrides?.budget ?? 100000,
    manager_id: overrides?.manager_id || `manager-${Math.random().toString(36).substring(7)}`,
    team_members: overrides?.team_members || [],
    progress: overrides?.progress ?? Math.floor(Math.random() * 100),
    health: overrides?.health || 'green',
    created_at: overrides?.created_at || startDate.toISOString(),
    updated_at: overrides?.updated_at || now.toISOString(),
  }
}

/**
 * Generates multiple mock projects
 */
export function generateMockProjects(count: number, overrides?: Partial<Project>): Project[] {
  return Array.from({ length: count }, (_, i) => 
    generateMockProject({
      ...overrides,
      name: overrides?.name || `Project ${i + 1}`,
    })
  )
}

/**
 * Generates a mock financial project
 */
export function generateMockFinancialProject(overrides?: Partial<FinancialProject>): FinancialProject {
  const id = overrides?.id || `project-${Math.random().toString(36).substring(7)}`
  
  return {
    id,
    name: overrides?.name || `Project ${id.substring(8)}`,
    budget: overrides?.budget ?? Math.floor(Math.random() * 500000) + 50000,
    actual_cost: overrides?.actual_cost ?? Math.floor(Math.random() * 400000) + 30000,
    status: overrides?.status || 'active',
    health: overrides?.health || 'green',
  }
}

// ============================================================================
// Financial Data Mock Generators
// ============================================================================

/**
 * Generates mock financial metrics
 */
export function generateMockFinancialMetrics(overrides?: Partial<FinancialMetrics>): FinancialMetrics {
  const totalBudget = overrides?.total_budget ?? 1000000
  const totalActual = overrides?.total_actual ?? 850000
  const totalVariance = totalActual - totalBudget
  const variancePercentage = (totalVariance / totalBudget) * 100
  
  return {
    total_budget: totalBudget,
    total_actual: totalActual,
    total_variance: overrides?.total_variance ?? totalVariance,
    variance_percentage: overrides?.variance_percentage ?? variancePercentage,
    projects_over_budget: overrides?.projects_over_budget ?? 3,
    projects_under_budget: overrides?.projects_under_budget ?? 7,
    average_budget_utilization: overrides?.average_budget_utilization ?? 85,
    currency_distribution: overrides?.currency_distribution ?? { USD: 1000000 },
  }
}

/**
 * Generates mock budget variance data
 */
export function generateMockBudgetVariance(overrides?: Partial<BudgetVariance>): BudgetVariance {
  const projectId = overrides?.project_id || `project-${Math.random().toString(36).substring(7)}`
  const totalPlanned = overrides?.total_planned ?? 100000
  const totalActual = overrides?.total_actual ?? 95000
  const varianceAmount = totalActual - totalPlanned
  const variancePercentage = (varianceAmount / totalPlanned) * 100
  
  return {
    project_id: projectId,
    total_planned: totalPlanned,
    total_actual: totalActual,
    variance_amount: overrides?.variance_amount ?? varianceAmount,
    variance_percentage: overrides?.variance_percentage ?? variancePercentage,
    currency: overrides?.currency || 'USD',
    categories: overrides?.categories || [
      {
        category: 'Labor',
        planned: 50000,
        actual: 48000,
        variance: -2000,
        variance_percentage: -4,
      },
      {
        category: 'Materials',
        planned: 30000,
        actual: 32000,
        variance: 2000,
        variance_percentage: 6.67,
      },
      {
        category: 'Equipment',
        planned: 20000,
        actual: 15000,
        variance: -5000,
        variance_percentage: -25,
      },
    ],
    status: overrides?.status || 'under',
  }
}

/**
 * Generates mock financial alert
 */
export function generateMockFinancialAlert(overrides?: Partial<FinancialAlert>): FinancialAlert {
  const projectId = overrides?.project_id || `project-${Math.random().toString(36).substring(7)}`
  const budget = overrides?.budget ?? 100000
  const actualCost = overrides?.actual_cost ?? 95000
  const utilizationPercentage = (actualCost / budget) * 100
  const varianceAmount = actualCost - budget
  
  return {
    project_id: projectId,
    project_name: overrides?.project_name || `Project ${projectId.substring(8)}`,
    budget,
    actual_cost: actualCost,
    utilization_percentage: overrides?.utilization_percentage ?? utilizationPercentage,
    variance_amount: overrides?.variance_amount ?? varianceAmount,
    alert_level: overrides?.alert_level || (utilizationPercentage > 90 ? 'critical' : 'warning'),
    message: overrides?.message || `Budget utilization at ${utilizationPercentage.toFixed(1)}%`,
  }
}

// ============================================================================
// User Mock Generators
// ============================================================================

/**
 * Generates a mock user
 */
export function generateMockUser(overrides?: Partial<User>): User {
  const id = overrides?.id || `user-${Math.random().toString(36).substring(7)}`
  const now = new Date().toISOString()
  
  return {
    id,
    email: overrides?.email || `user-${id.substring(5)}@example.com`,
    name: overrides?.name || `User ${id.substring(5)}`,
    avatar_url: overrides?.avatar_url,
    role: overrides?.role || 'user',
    preferences: overrides?.preferences || {
      theme: 'light',
      language: 'en',
      timezone: 'UTC',
      notifications: {
        email: true,
        push: false,
        inApp: true,
        frequency: 'daily',
      },
      dashboard: {
        layout: 'grid',
        widgets: [],
        refreshInterval: 60000,
      },
      accessibility: {
        highContrast: false,
        reducedMotion: false,
        fontSize: 'medium',
        screenReader: false,
        keyboardNavigation: false,
      },
    },
    created_at: overrides?.created_at || now,
    updated_at: overrides?.updated_at || now,
  }
}

// ============================================================================
// Resource Mock Generators
// ============================================================================

/**
 * Generates a mock resource
 */
export function generateMockResource(overrides?: Partial<Resource>): Resource {
  const id = overrides?.id || `resource-${Math.random().toString(36).substring(7)}`
  const now = new Date().toISOString()
  const capacity = overrides?.capacity ?? 40
  const allocated = Math.floor(Math.random() * capacity)
  const available = capacity - allocated
  const utilization = (allocated / capacity) * 100
  
  return {
    id,
    name: overrides?.name || `Resource ${id.substring(9)}`,
    email: overrides?.email || `resource-${id.substring(9)}@example.com`,
    role: overrides?.role || 'Developer',
    capacity,
    availability: overrides?.availability ?? available,
    hourly_rate: overrides?.hourly_rate ?? 100,
    skills: overrides?.skills || ['JavaScript', 'React', 'Node.js'],
    location: overrides?.location || 'Remote',
    current_projects: overrides?.current_projects || [],
    utilization_percentage: overrides?.utilization_percentage ?? utilization,
    available_hours: overrides?.available_hours ?? available,
    allocated_hours: overrides?.allocated_hours ?? allocated,
    capacity_hours: overrides?.capacity_hours ?? capacity,
    availability_status: overrides?.availability_status || (
      utilization >= 90 ? 'fully_allocated' :
      utilization >= 70 ? 'mostly_allocated' :
      utilization >= 40 ? 'partially_allocated' :
      'available'
    ),
    can_take_more_work: overrides?.can_take_more_work ?? utilization < 90,
    created_at: overrides?.created_at || now,
    updated_at: overrides?.updated_at || now,
  }
}

// ============================================================================
// Risk Mock Generators
// ============================================================================

/**
 * Generates a mock risk
 */
export function generateMockRisk(overrides?: Partial<Risk>): Risk {
  const id = overrides?.id || `risk-${Math.random().toString(36).substring(7)}`
  const now = new Date().toISOString()
  const probability = overrides?.probability ?? Math.floor(Math.random() * 10) + 1
  const impact = overrides?.impact ?? Math.floor(Math.random() * 10) + 1
  
  return {
    id,
    project_id: overrides?.project_id || `project-${Math.random().toString(36).substring(7)}`,
    project_name: overrides?.project_name || 'Sample Project',
    title: overrides?.title || `Risk ${id.substring(5)}`,
    description: overrides?.description || `Description for risk ${id}`,
    category: overrides?.category || 'technical',
    probability,
    impact,
    risk_score: overrides?.risk_score ?? probability * impact,
    status: overrides?.status || 'identified',
    mitigation: overrides?.mitigation || 'Mitigation plan to be developed',
    owner: overrides?.owner || 'Risk Manager',
    due_date: overrides?.due_date || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: overrides?.created_at || now,
    updated_at: overrides?.updated_at || now,
  }
}

// ============================================================================
// Batch Generators
// ============================================================================

/**
 * Generates multiple mock financial alerts
 */
export function generateMockFinancialAlerts(count: number, overrides?: Partial<FinancialAlert>): FinancialAlert[] {
  return Array.from({ length: count }, (_, i) => 
    generateMockFinancialAlert({
      ...overrides,
      project_name: overrides?.project_name || `Project ${i + 1}`,
    })
  )
}

/**
 * Generates multiple mock resources
 */
export function generateMockResources(count: number, overrides?: Partial<Resource>): Resource[] {
  return Array.from({ length: count }, (_, i) => 
    generateMockResource({
      ...overrides,
      name: overrides?.name || `Resource ${i + 1}`,
    })
  )
}

/**
 * Generates multiple mock risks
 */
export function generateMockRisks(count: number, overrides?: Partial<Risk>): Risk[] {
  return Array.from({ length: count }, (_, i) => 
    generateMockRisk({
      ...overrides,
      title: overrides?.title || `Risk ${i + 1}`,
    })
  )
}

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validates that a mock session has all required fields
 */
export function isValidMockSession(session: any): session is MockSession {
  return (
    typeof session === 'object' &&
    session !== null &&
    typeof session.access_token === 'string' &&
    session.access_token.length > 0 &&
    typeof session.refresh_token === 'string' &&
    session.refresh_token.length > 0 &&
    typeof session.expires_at === 'number' &&
    typeof session.expires_in === 'number' &&
    typeof session.token_type === 'string' &&
    typeof session.user === 'object' &&
    session.user !== null &&
    typeof session.user.id === 'string' &&
    session.user.id.length > 0 &&
    typeof session.user.email === 'string' &&
    session.user.email.length > 0 &&
    typeof session.user.role === 'string' &&
    session.user.role.length > 0 &&
    typeof session.user.aud === 'string' &&
    typeof session.user.created_at === 'string'
  )
}

/**
 * Validates that a mock project has all required fields
 */
export function isValidMockProject(project: any): project is Project {
  return (
    typeof project === 'object' &&
    project !== null &&
    typeof project.id === 'string' &&
    typeof project.name === 'string' &&
    typeof project.status === 'string' &&
    typeof project.priority === 'string' &&
    typeof project.start_date === 'string' &&
    typeof project.health === 'string' &&
    typeof project.progress === 'number' &&
    typeof project.created_at === 'string' &&
    typeof project.updated_at === 'string'
  )
}

/**
 * Validates that mock financial metrics have all required fields
 */
export function isValidMockFinancialMetrics(metrics: any): metrics is FinancialMetrics {
  return (
    typeof metrics === 'object' &&
    metrics !== null &&
    typeof metrics.total_budget === 'number' &&
    typeof metrics.total_actual === 'number' &&
    typeof metrics.total_variance === 'number' &&
    typeof metrics.variance_percentage === 'number' &&
    typeof metrics.projects_over_budget === 'number' &&
    typeof metrics.projects_under_budget === 'number' &&
    typeof metrics.average_budget_utilization === 'number' &&
    typeof metrics.currency_distribution === 'object'
  )
}
