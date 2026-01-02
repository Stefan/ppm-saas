'use client'

import { useAuth } from '../providers/SupabaseAuthProvider'
import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts'

export default function Dashboards() {
  const { session } = useAuth()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
const [newProject, setNewProject] = useState({ name: '', description: '', budget: 0, portfolio_id: 'your-default-portfolio-id' }) 


  useEffect(() => {
    if (session) {
      fetchProjects()
    }
  }, [session])

async function fetchProjects() {
  setLoading(true)
  setError(null)
  try {
    if (!session) throw new Error('Not authenticated')
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/projects/`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    })
    if (!response.ok) throw new Error('Fetch failed')
    const data = await response.json()
    setProjects(data)
  } catch (err) {
    if (err instanceof Error) {
      setError(err.message)
    } else {
      setError('Unknown error')
    }
  } finally {
    setLoading(false)
  }
}

async function addProject() {
  if (!session) {
    alert('Not authenticated – please login')
    return
  }
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/projects/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify(newProject)
    })
    if (!response.ok) throw new Error('Add failed')
    fetchProjects()  // Refresh list
    setNewProject({ name: '', description: '', budget: 0, portfolio_id: '' })  // Reset form
  } catch (err) {
    if (err instanceof Error) {
      alert(err.message)
    } else {
      alert('Unknown error')
    }
  }
}

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <div>
      <h1>Portfolio Dashboards</h1>
      <BarChart width={600} height={300} data={projects}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="budget" fill="#8884d8" />
      </BarChart>
      <table className="table-auto mt-4">
        <thead>
          <tr>
            <th>Name</th>
            <th>Budget</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project: any) => (
            <tr key={project.id}>
              <td>{project.name}</td>
              <td>{project.budget}</td>
              <td>{project.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-8">
  <h2>Add Project</h2>
  <input type="text" value={newProject.name} onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} placeholder="Name" className="mb-2 p-2 border" />
  <input type="text" value={newProject.description} onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} placeholder="Description" className="mb-2 p-2 border" />
  <input type="number" value={newProject.budget} onChange={(e) => setNewProject({ ...newProject, budget: parseFloat(e.target.value) })} placeholder="Budget" className="mb-2 p-2 border" />
  <button onClick={addProject} className="p-2 bg-green-500 text-white">Add</button>
</div>
    </div>
  )
}