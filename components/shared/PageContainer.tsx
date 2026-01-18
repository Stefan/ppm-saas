'use client'

import React from 'react'
import { cn } from '../../lib/utils/design-system'

interface PageContainerProps {
  children: React.ReactNode
  maxWidth?: 'narrow' | 'default' | 'wide' | 'full'
  className?: string
  compact?: boolean
}

/**
 * PageContainer - Wrapper für Page Content mit optimaler Breite
 * 
 * @param maxWidth - Maximale Breite des Containers
 *   - narrow: 1200px (für Formulare, Text)
 *   - default: 1400px (Standard für die meisten Seiten)
 *   - wide: 1600px (für Dashboards mit vielen Daten)
 *   - full: 100% (keine Begrenzung)
 * @param compact - Reduziertes Padding für mehr Informationsdichte
 */
export function PageContainer({ 
  children, 
  maxWidth = 'default',
  compact = false,
  className 
}: PageContainerProps) {
  const maxWidthClasses = {
    narrow: 'max-w-[1200px]',
    default: 'max-w-[1400px]',
    wide: 'max-w-[1600px]',
    full: 'max-w-full'
  }

  const paddingClasses = compact 
    ? 'px-4 sm:px-6 lg:px-8 py-3 sm:py-4 lg:py-6'
    : 'px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8'

  return (
    <div className={cn(
      'w-full mx-auto',
      maxWidthClasses[maxWidth],
      paddingClasses,
      className
    )}>
      {children}
    </div>
  )
}

export default PageContainer
