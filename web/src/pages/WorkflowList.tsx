import { useEffect, useState } from 'react'
import { Plus, Play, Edit2, Trash2, GitBranch, Clock } from 'lucide-react'
import { workflowsApi, executionsApi } from '../api/client'
import type { Workflow } from '../types'

export default function WorkflowList() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      const response = await workflowsApi.list()
      setWorkflows(response.data)
    } catch (error) {
      console.error('Failed to load workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRun = async (workflowId: string) => {
    try {
      await executionsApi.start(workflowId, {})
      alert('Workflow started!')
    } catch (error) {
      console.error('Failed to start workflow:', error)
    }
  }

  const handleDelete = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return
    
    try {
      await workflowsApi.delete(workflowId)
      setWorkflows(workflows.filter(w => w.id !== workflowId))
    } catch (error) {
      console.error('Failed to delete workflow:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Workflows</h2>
          <p className="text-gray-500">Manage and execute your workflows</p>
        </div>
        <div className="flex gap-3">
          <a
            href="/planner"
            className="btn-secondary flex items-center gap-2"
          >
            AI Planner
          </a>
          <a
            href="/workflows/new"
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </a>
        </div>
      </div>

      {workflows.length === 0 ? (
        <div className="card p-12 text-center">
          <GitBranch className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No workflows yet</h3>
          <p className="text-gray-500 mb-6">Create your first workflow to get started</p>
          <div className="flex justify-center gap-4">
            <a href="/planner" className="btn-secondary">
              Use AI Planner
            </a>
            <a href="/workflows/new" className="btn-primary">
              Build Manually
            </a>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {workflow.name}
                    </h3>
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                      v{workflow.version}
                    </span>
                  </div>
                  <p className="text-gray-500 mb-4">{workflow.description}</p>
                  
                  <div className="flex items-center gap-6 text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4" />
                      {workflow.nodes?.length || 0} nodes
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Created recently
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRun(workflow.id)}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    title="Run workflow"
                  >
                    <Play className="w-5 h-5" />
                  </button>
                  <a
                    href={`/workflows/${workflow.id}/edit`}
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                    title="Edit workflow"
                  >
                    <Edit2 className="w-5 h-5" />
                  </a>
                  <button
                    onClick={() => handleDelete(workflow.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Delete workflow"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
