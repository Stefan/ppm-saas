/**
 * Table Component
 * 
 * A professional table component with clean styling.
 */

import React from 'react'
import { cn } from '@/lib/design-system'

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  children: React.ReactNode
  className?: string
}

export function Table({ children, className, ...props }: TableProps) {
  return (
    <div className="w-full overflow-auto rounded-lg border border-gray-200">
      <table
        className={cn('w-full text-sm', className)}
        {...props}
      >
        {children}
      </table>
    </div>
  )
}

export function TableHeader({ children, className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={cn('bg-gray-50 border-b border-gray-200', className)} {...props}>
      {children}
    </thead>
  )
}

export function TableBody({ children, className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={cn('divide-y divide-gray-100', className)} {...props}>
      {children}
    </tbody>
  )
}

export function TableRow({ children, className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        'transition-colors hover:bg-gray-50',
        className
      )}
      {...props}
    >
      {children}
    </tr>
  )
}

export function TableHead({ children, className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        'px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider',
        className
      )}
      {...props}
    >
      {children}
    </th>
  )
}

export function TableCell({ children, className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn(
        'px-4 py-3 text-gray-900',
        className
      )}
      {...props}
    >
      {children}
    </td>
  )
}

export default Table
