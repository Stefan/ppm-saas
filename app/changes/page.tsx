'use client'


import AppLayout from '../../components/shared/AppLayout'
import ChangeRequestManager from './components/ChangeRequestManager'
import { ResponsiveContainer } from '../../components/ui/molecules/ResponsiveContainer'

export default function ChangesPage() {
  return (
    <AppLayout>
      <ResponsiveContainer padding="md">
        <div data-testid="changes-page">
          <div data-testid="changes-header" className="mb-6">
            <h1 data-testid="changes-title" className="text-2xl sm:text-3xl font-bold text-gray-900">Change Management</h1>
            <p className="text-gray-600 mt-2">
              Manage project change requests, approvals, and implementation tracking
            </p>
          </div>
          <div data-testid="changes-list">
            <ChangeRequestManager />
          </div>
        </div>
      </ResponsiveContainer>
    </AppLayout>
  )
}