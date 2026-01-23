/**
 * Alert Component
 * 
 * A professional alert component for notifications and messages.
 */

import React from 'react'
import { cn } from '@/lib/design-system'
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react'

type AlertVariant = 'info' | 'success' | 'warning' | 'error' | 'default' | 'destructive'

export interface AlertProps {
  variant?: AlertVariant
  title?: string
  children: React.ReactNode
  className?: string
  dismissible?: boolean
  onDismiss?: () => void
}

const alertVariants: Record<AlertVariant, { bg: string; border: string; icon: string; title: string }> = {
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: 'text-blue-500',
    title: 'text-blue-800',
  },
  success: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: 'text-green-500',
    title: 'text-green-800',
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: 'text-yellow-500',
    title: 'text-yellow-800',
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'text-red-500',
    title: 'text-red-800',
  },
  default: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    icon: 'text-gray-500',
    title: 'text-gray-800',
  },
  destructive: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'text-red-500',
    title: 'text-red-800',
  },
}

const alertIcons: Record<AlertVariant, React.ElementType> = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  default: Info,
  destructive: XCircle,
}

export function Alert({
  variant = 'info',
  title,
  children,
  className,
  dismissible = false,
  onDismiss,
}: AlertProps) {
  const styles = alertVariants[variant]
  const Icon = alertIcons[variant]

  return (
    <div
      role="alert"
      className={cn(
        'relative rounded-lg border p-4',
        styles.bg,
        styles.border,
        className
      )}
    >
      <div className="flex gap-3">
        <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', styles.icon)} />
        <div className="flex-1 min-w-0">
          {title && (
            <h5 className={cn('font-medium mb-1', styles.title)}>
              {title}
            </h5>
          )}
          <div className="text-sm text-gray-700">
            {children}
          </div>
        </div>
        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors"
          >
            <X className="h-4 w-4 text-gray-500" />
          </button>
        )}
      </div>
    </div>
  )
}

export const AlertTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <h5 className={cn('font-medium mb-1', className)}>{children}</h5>
)

export const AlertDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={cn('text-sm', className)}>{children}</div>
)

export default Alert
