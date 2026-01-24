'use client'

import React, { useState, useEffect, useMemo, forwardRef, useImperativeHandle } from 'react'
import { 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Download, 
  ChevronLeft, 
  ChevronRight,
  FileText,
  Filter
} from 'lucide-react'
import { getApiUrl } from '../../../../lib/api'

interface Commitment {
  id: string
  po_number: string
  po_date: string
  vendor: string
  vendor_description?: string
  project_nr: string
  wbs_element?: string
  po_net_amount: number
  total_amount: number
  currency: string
  po_status?: string
  po_line_nr: number
  delivery_date?: string
  created_at: string
  updated_at: string
  [key: string]: any // For additional columns
}

interface CommitmentsTableProps {
  accessToken: string | undefined
  onProjectClick?: (projectNr: string) => void
}

type SortDirection = 'asc' | 'desc' | null
type SortField = keyof Commitment | null

const CommitmentsTable = forwardRef<{ refresh: () => void }, CommitmentsTableProps>(({ accessToken, onProjectClick }, ref) => {
  const [commitments, setCommitments] = useState<Commitment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  
  // Sorting state
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  
  // Filtering state
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [showFilters, setShowFilters] = useState(false)

  // Fetch commitments data
  const fetchCommitments = async () => {
    if (!accessToken) return
    
    setLoading(true)
    setError(null)
    
    try {
      const offset = (currentPage - 1) * pageSize
      const response = await fetch(
        getApiUrl(`/csv-import/commitments?limit=${pageSize}&offset=${offset}`),
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setCommitments(data.commitments || [])
        setTotal(data.total || 0)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to fetch commitments')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch commitments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCommitments()
  }, [accessToken, currentPage, pageSize])

  // Expose refresh method to parent
  useImperativeHandle(ref, () => ({
    refresh: fetchCommitments
  }))

  // Apply client-side filtering and sorting
  const filteredAndSortedCommitments = useMemo(() => {
    let result = [...commitments]
    
    // Apply filters
    Object.entries(filters).forEach(([field, value]) => {
      if (value) {
        result = result.filter(commitment => {
          const fieldValue = commitment[field]
          if (fieldValue === null || fieldValue === undefined) return false
          return String(fieldValue).toLowerCase().includes(value.toLowerCase())
        })
      }
    })
    
    // Apply sorting
    if (sortField && sortDirection) {
      result.sort((a, b) => {
        const aValue = a[sortField]
        const bValue = b[sortField]
        
        if (aValue === null || aValue === undefined) return 1
        if (bValue === null || bValue === undefined) return -1
        
        let comparison = 0
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          comparison = aValue - bValue
        } else {
          comparison = String(aValue).localeCompare(String(bValue))
        }
        
        return sortDirection === 'asc' ? comparison : -comparison
      })
    }
    
    return result
  }, [commitments, filters, sortField, sortDirection])

  // Handle sort
  const handleSort = (field: keyof Commitment) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : sortDirection === 'desc' ? null : 'asc')
      if (sortDirection === 'desc') {
        setSortField(null)
      }
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Handle filter change
  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // Export to CSV
  const exportToCSV = () => {
    const headers = [
      'PO Number',
      'PO Date',
      'Vendor',
      'Vendor Description',
      'Project Nr',
      'WBS Element',
      'PO Net Amount',
      'Total Amount',
      'Currency',
      'PO Status',
      'PO Line Nr',
      'Delivery Date'
    ]
    
    const rows = filteredAndSortedCommitments.map(c => [
      c.po_number,
      c.po_date,
      c.vendor,
      c.vendor_description || '',
      c.project_nr,
      c.wbs_element || '',
      c.po_net_amount,
      c.total_amount,
      c.currency,
      c.po_status || '',
      c.po_line_nr,
      c.delivery_date || ''
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `commitments_export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  // Pagination helpers
  const totalPages = Math.ceil(total / pageSize)
  const startRecord = (currentPage - 1) * pageSize + 1
  const endRecord = Math.min(currentPage * pageSize, total)

  // Column definitions
  const columns: Array<{
    key: keyof Commitment
    label: string
    width?: string
    format?: (value: any) => string
  }> = [
    { key: 'po_number', label: 'PO Number', width: 'w-32' },
    { key: 'po_line_nr', label: 'Line', width: 'w-16' },
    { key: 'po_date', label: 'PO Date', width: 'w-28', format: (v) => v ? new Date(v).toLocaleDateString() : '' },
    { key: 'vendor', label: 'Vendor', width: 'w-32' },
    { key: 'vendor_description', label: 'Vendor Description', width: 'w-48' },
    { key: 'project_nr', label: 'Project Nr', width: 'w-28' },
    { key: 'wbs_element', label: 'WBS Element', width: 'w-32' },
    { key: 'po_net_amount', label: 'Net Amount', width: 'w-28', format: (v) => v?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' },
    { key: 'total_amount', label: 'Total Amount', width: 'w-28', format: (v) => v?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' },
    { key: 'currency', label: 'Currency', width: 'w-20' },
    { key: 'po_status', label: 'Status', width: 'w-24' },
    { key: 'delivery_date', label: 'Delivery Date', width: 'w-28', format: (v) => v ? new Date(v).toLocaleDateString() : '' },
  ]

  // Render sort icon
  const renderSortIcon = (field: keyof Commitment) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 text-gray-400" />
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="h-3 w-3 text-blue-600" />
    }
    if (sortDirection === 'desc') {
      return <ArrowDown className="h-3 w-3 text-blue-600" />
    }
    return <ArrowUpDown className="h-3 w-3 text-gray-400" />
  }

  if (loading && commitments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading commitments...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center text-red-600">
          <p className="font-medium">Error loading commitments</p>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={fetchCommitments}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (total === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Commitments Data</h3>
          <p className="text-gray-600 mb-4">
            No commitment records have been imported yet.
          </p>
          <a
            href="#csv-import"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to CSV Import
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Commitments Data</h3>
            <p className="text-sm text-gray-600 mt-1">
              Showing {startRecord}-{endRecord} of {total} records
              {Object.keys(filters).some(k => filters[k]) && (
                <span className="ml-2 text-blue-600">
                  ({filteredAndSortedCommitments.length} filtered)
                </span>
              )}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                showFilters 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="h-4 w-4 mr-1" />
              Filters
            </button>
            
            <button
              onClick={exportToCSV}
              className="flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={String(column.key)}
                    className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.width || ''}`}
                  >
                    <button
                      onClick={() => handleSort(column.key)}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>{column.label}</span>
                      {renderSortIcon(column.key)}
                    </button>
                  </th>
                ))}
              </tr>
              
              {/* Filter row */}
              {showFilters && (
                <tr className="bg-gray-100">
                  {columns.map((column) => (
                    <th key={`filter-${String(column.key)}`} className="px-4 py-2">
                      <input
                        type="text"
                        placeholder={`Filter ${column.label}...`}
                        value={filters[String(column.key)] || ''}
                        onChange={(e) => handleFilterChange(String(column.key), e.target.value)}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </th>
                  ))}
                </tr>
              )}
            </thead>
            
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedCommitments.map((commitment) => (
                <tr key={commitment.id} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td
                      key={`${commitment.id}-${String(column.key)}`}
                      className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                    >
                      {column.key === 'project_nr' && onProjectClick ? (
                        <button
                          onClick={() => onProjectClick(commitment.project_nr)}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {commitment[column.key] || '-'}
                        </button>
                      ) : (
                        <span>
                          {column.format 
                            ? column.format(commitment[column.key])
                            : commitment[column.key] || '-'
                          }
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setCurrentPage(1)
              }}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (currentPage <= 3) {
                  pageNum = i + 1
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = currentPage - 2 + i
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

CommitmentsTable.displayName = 'CommitmentsTable'

export default CommitmentsTable
