/**
 * SlowQueriesTable Component
 * 
 * Displays recent slow queries in a table format.
 * Wrapped in React.memo() to prevent unnecessary re-renders.
 * 
 * Requirements: 3.4, 8.2
 */

import { memo } from 'react'

interface SlowQueryData {
  endpoint: string
  duration: number
  time: string
}

interface SlowQueriesTableProps {
  slowQueriesData: SlowQueryData[]
  translations: {
    recentSlowQueries: string
    endpoint: string
    duration: string
    time: string
  }
}

function SlowQueriesTable({ slowQueriesData, translations }: SlowQueriesTableProps) {
  if (slowQueriesData.length === 0) {
    return null
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {translations.recentSlowQueries}
      </h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/2">
                {translations.endpoint}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">
                {translations.duration}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">
                {translations.time}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {slowQueriesData.map((query, index) => (
              <tr key={index}>
                <td className="px-6 py-4 text-sm text-gray-900 break-words max-w-0">
                  <div 
                    className="font-mono text-xs bg-gray-100 px-2 py-1 rounded cursor-help" 
                    title={query.endpoint}
                  >
                    {query.endpoint}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                  {query.duration}ms
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {query.time}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Wrap in React.memo() to prevent unnecessary re-renders
export default memo(SlowQueriesTable)
