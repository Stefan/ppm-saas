import React from 'react'
import { cn } from '@/lib/design-system'

interface AlertProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'destructive' | 'warning'
}

interface AlertDescriptionProps {
  children: React.ReactNode
  className?: string
}

export const Alert: React.FC<AlertProps> = ({ 
  children, 
  className, 
  variant = 'default' 
}) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800'
  }

  return (
    <div className={cn(
      'border rounded-lg p-4 flex items-start gap-3',
      variantClasses[variant],
      className
    )}>
      {children}
    </div>
  )
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  children, 
  className 
}) => (
  <div className={cn('text-sm', className)}>
    {children}
  </div>
)