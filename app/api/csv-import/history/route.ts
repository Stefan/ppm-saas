/**
 * CSV Import History API Endpoint
 * Handles retrieval of CSV import history records
 */

import { NextRequest, NextResponse } from 'next/server'

interface CSVImportRecord {
  id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  recordsProcessed: number
  totalRecords: number
  errors: string[]
  createdAt: string
  completedAt?: string
  userId: string
  importType: 'projects' | 'risks' | 'resources' | 'users'
}

// Mock data for development (replace with database in production)
const mockImportHistory: CSVImportRecord[] = [
  {
    id: 'import-001',
    filename: 'projects_2024_01.csv',
    status: 'completed',
    recordsProcessed: 150,
    totalRecords: 150,
    errors: [],
    createdAt: '2024-01-15T10:30:00Z',
    completedAt: '2024-01-15T10:32:15Z',
    userId: 'user-123',
    importType: 'projects'
  },
  {
    id: 'import-002',
    filename: 'risks_assessment.csv',
    status: 'completed',
    recordsProcessed: 89,
    totalRecords: 92,
    errors: [
      'Row 45: Invalid risk level value',
      'Row 67: Missing required field: impact',
      'Row 78: Invalid date format'
    ],
    createdAt: '2024-01-14T14:20:00Z',
    completedAt: '2024-01-14T14:25:30Z',
    userId: 'user-123',
    importType: 'risks'
  },
  {
    id: 'import-003',
    filename: 'resources_q1.csv',
    status: 'failed',
    recordsProcessed: 0,
    totalRecords: 200,
    errors: [
      'File format not supported',
      'Invalid CSV structure'
    ],
    createdAt: '2024-01-13T09:15:00Z',
    userId: 'user-123',
    importType: 'resources'
  },
  {
    id: 'import-004',
    filename: 'team_members.csv',
    status: 'processing',
    recordsProcessed: 45,
    totalRecords: 120,
    errors: [],
    createdAt: '2024-01-16T11:00:00Z',
    userId: 'user-123',
    importType: 'users'
  }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('userId')
    const status = searchParams.get('status')
    const importType = searchParams.get('importType')
    const limit = parseInt(searchParams.get('limit') || '50')
    const offset = parseInt(searchParams.get('offset') || '0')

    // Filter records based on query parameters
    let filteredHistory = [...mockImportHistory]

    if (userId) {
      filteredHistory = filteredHistory.filter(record => record.userId === userId)
    }

    if (status) {
      filteredHistory = filteredHistory.filter(record => record.status === status)
    }

    if (importType) {
      filteredHistory = filteredHistory.filter(record => record.importType === importType)
    }

    // Sort by creation date (newest first)
    filteredHistory.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

    // Apply pagination
    const paginatedHistory = filteredHistory.slice(offset, offset + limit)

    const response = {
      data: paginatedHistory,
      pagination: {
        total: filteredHistory.length,
        limit,
        offset,
        hasMore: offset + limit < filteredHistory.length
      },
      summary: {
        totalImports: filteredHistory.length,
        completed: filteredHistory.filter(r => r.status === 'completed').length,
        failed: filteredHistory.filter(r => r.status === 'failed').length,
        processing: filteredHistory.filter(r => r.status === 'processing').length,
        pending: filteredHistory.filter(r => r.status === 'pending').length
      }
    }

    return NextResponse.json(response, { status: 200 })

  } catch (error) {
    console.error('CSV import history error:', error)
    return NextResponse.json({
      error: 'Failed to retrieve CSV import history',
      message: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const importId = searchParams.get('importId')

    if (!importId) {
      return NextResponse.json({
        error: 'Missing required parameter: importId'
      }, { status: 400 })
    }

    // In a real implementation, this would delete from database
    const recordIndex = mockImportHistory.findIndex(record => record.id === importId)
    
    if (recordIndex === -1) {
      return NextResponse.json({
        error: 'Import record not found'
      }, { status: 404 })
    }

    // Remove the record
    mockImportHistory.splice(recordIndex, 1)

    return NextResponse.json({
      message: 'Import record deleted successfully',
      deletedId: importId
    }, { status: 200 })

  } catch (error) {
    console.error('CSV import history deletion error:', error)
    return NextResponse.json({
      error: 'Failed to delete import record',
      message: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}