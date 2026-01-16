/**
 * Initialize CLS Prevention on App Load
 * 
 * This script should be imported in the root layout to set up
 * CLS prevention measures as early as possible.
 */

'use client'

import { useEffect } from 'react'
import { initializeCLSPrevention } from './cls-fixes'

export function useCLSPrevention() {
  useEffect(() => {
    // Initialize CLS prevention
    const observer = initializeCLSPrevention()
    
    // Log CLS improvements
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'layout-shift' && !(entry as any).hadRecentInput) {
              console.log('Layout shift detected:', {
                value: (entry as any).value,
                sources: (entry as any).sources,
                timestamp: entry.startTime
              })
            }
          }
        })
        
        clsObserver.observe({ entryTypes: ['layout-shift'] })
        
        return () => {
          clsObserver.disconnect()
          observer?.disconnect()
        }
      } catch (error) {
        console.warn('CLS monitoring not supported:', error)
      }
    }
  }, [])
}

/**
 * Component to initialize CLS prevention
 * Add this to your root layout
 */
export function CLSPreventionInit() {
  useCLSPrevention()
  return null
}
