/**
 * AI Performance Monitoring Utilities
 * Tracks AI service performance and provides optimization insights
 */

interface AIPerformanceMetrics {
  requestCount: number
  averageResponseTime: number
  errorRate: number
  successRate: number
  lastRequestTime: string | null
  totalProcessingTime: number
}

interface AIServiceStats {
  helpChat: AIPerformanceMetrics
  proactiveTips: AIPerformanceMetrics
  riskAnalysis: AIPerformanceMetrics
  monteCarloSimulation: AIPerformanceMetrics
}

class AIPerformanceMonitor {
  private stats: AIServiceStats = {
    helpChat: this.createEmptyMetrics(),
    proactiveTips: this.createEmptyMetrics(),
    riskAnalysis: this.createEmptyMetrics(),
    monteCarloSimulation: this.createEmptyMetrics()
  }

  private createEmptyMetrics(): AIPerformanceMetrics {
    return {
      requestCount: 0,
      averageResponseTime: 0,
      errorRate: 0,
      successRate: 100,
      lastRequestTime: null,
      totalProcessingTime: 0
    }
  }

  recordRequest(service: keyof AIServiceStats, responseTime: number, success: boolean = true): void {
    const metrics = this.stats[service]
    
    metrics.requestCount++
    metrics.totalProcessingTime += responseTime
    metrics.averageResponseTime = metrics.totalProcessingTime / metrics.requestCount
    metrics.lastRequestTime = new Date().toISOString()
    
    if (!success) {
      const errorCount = Math.round(metrics.requestCount * (metrics.errorRate / 100)) + 1
      metrics.errorRate = (errorCount / metrics.requestCount) * 100
    }
    
    metrics.successRate = 100 - metrics.errorRate
  }

  getPerformanceStats(): AIServiceStats {
    return { ...this.stats }
  }

  getServiceStats(service: keyof AIServiceStats): AIPerformanceMetrics {
    return { ...this.stats[service] }
  }

  resetStats(service?: keyof AIServiceStats): void {
    if (service) {
      this.stats[service] = this.createEmptyMetrics()
    } else {
      this.stats = {
        helpChat: this.createEmptyMetrics(),
        proactiveTips: this.createEmptyMetrics(),
        riskAnalysis: this.createEmptyMetrics(),
        monteCarloSimulation: this.createEmptyMetrics()
      }
    }
  }

  getOverallPerformance(): {
    totalRequests: number
    averageResponseTime: number
    overallSuccessRate: number
    overallErrorRate: number
  } {
    const services = Object.values(this.stats)
    const totalRequests = services.reduce((sum, service) => sum + service.requestCount, 0)
    const totalProcessingTime = services.reduce((sum, service) => sum + service.totalProcessingTime, 0)
    const totalErrors = services.reduce((sum, service) => 
      sum + Math.round(service.requestCount * (service.errorRate / 100)), 0)

    return {
      totalRequests,
      averageResponseTime: totalRequests > 0 ? totalProcessingTime / totalRequests : 0,
      overallSuccessRate: totalRequests > 0 ? ((totalRequests - totalErrors) / totalRequests) * 100 : 100,
      overallErrorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0
    }
  }

  isPerformanceHealthy(): boolean {
    const overall = this.getOverallPerformance()
    return overall.overallSuccessRate >= 95 && overall.averageResponseTime <= 2000
  }

  getPerformanceRecommendations(): string[] {
    const recommendations: string[] = []
    const overall = this.getOverallPerformance()

    if (overall.overallErrorRate > 5) {
      recommendations.push('High error rate detected. Consider implementing retry logic or checking AI service connectivity.')
    }

    if (overall.averageResponseTime > 2000) {
      recommendations.push('Slow response times detected. Consider implementing request caching or optimizing AI prompts.')
    }

    if (overall.totalRequests > 1000) {
      recommendations.push('High request volume. Consider implementing rate limiting or request batching.')
    }

    Object.entries(this.stats).forEach(([service, metrics]) => {
      if (metrics.errorRate > 10) {
        recommendations.push(`${service} service has high error rate (${metrics.errorRate.toFixed(1)}%). Investigate service-specific issues.`)
      }
    })

    return recommendations
  }
}

// Export singleton instance
export const aiPerformanceMonitor = new AIPerformanceMonitor()

// Utility functions
export const recordAIRequest = (service: keyof AIServiceStats, responseTime: number, success: boolean = true) => {
  aiPerformanceMonitor.recordRequest(service, responseTime, success)
}

export const getAIPerformanceStats = () => {
  return aiPerformanceMonitor.getPerformanceStats()
}

export const isAIPerformanceHealthy = () => {
  return aiPerformanceMonitor.isPerformanceHealthy()
}

export default aiPerformanceMonitor