import { useState, useEffect, useCallback } from 'react'
import { Sparkles, Clock, DollarSign, CheckCircle, Loader2 } from 'lucide-react'
import { plannerApi, workflowsApi } from '../api/client'
import type { PlanningResult, WorkflowDefinition, PlanningTask } from '../types'
import toast from 'react-hot-toast'

export default function Planner() {
  const [goal, setGoal] = useState('')
  const [planning, setPlanning] = useState(false)
  const [result, setResult] = useState<PlanningResult | null>(null)
  const [confirming, setConfirming] = useState(false)
  
  // Async polling state
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<PlanningTask | null>(null)
  const [pollInterval, setPollInterval] = useState<number | null>(null)

  // Polling effect
  useEffect(() => {
    if (!taskId || !pollInterval) return

    const poll = async () => {
      try {
        const response = await plannerApi.getTaskStatus(taskId)
        const status = response.data
        setTaskStatus(status)
        
        console.log('Task status:', status.status, 'Progress:', status.progress, 'Step:', status.current_step)
        
        // Check if completed or failed
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          setPollInterval(null)
          setPlanning(false)
          
          if (status.draft) {
            setResult({ success: true, draft: status.draft, error: null })
            toast.success(`Plan generated in ${status.elapsed_seconds.toFixed(1)}s!`)
          }
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          setPollInterval(null)
          setPlanning(false)
          toast.error(`Planning failed: ${status.error}`)
        }
        // Otherwise continue polling (pending/running)
      } catch (error: any) {
        console.error('Polling error:', error)
        // Don't stop polling on transient errors
      }
    }

    // Poll immediately then every 2 seconds
    poll()
    const interval = setInterval(poll, 2000)
    setPollInterval(interval)

    return () => {
      clearInterval(interval)
    }
  }, [taskId])

  const handlePlan = async () => {
    if (planning) return
    
    if (!goal.trim()) {
      toast.error('Please enter your goal')
      return
    }

    setPlanning(true)
    setResult(null)
    setTaskId(null)
    setTaskStatus(null)

    try {
      // Start async planning
      const response = await plannerApi.planAsync({
        goal,
        context: {},
      })
      
      const newTaskId = response.data.task_id
      setTaskId(newTaskId)
      toast.success('Planning started! Monitoring progress...')
      
    } catch (error: any) {
      const message = error.response?.data?.error || error.message || 'Unknown error'
      toast.error(`Failed to start planning: ${message}`)
      console.error('Planning error:', error)
      setPlanning(false)
    }
  }

  const handleConfirm = async () => {
    if (confirming) return
    if (!result) return

    setConfirming(true)
    try {
      console.log('Confirming draft:', result.draft.id)
      const response = await plannerApi.confirm(result.draft.id)
      console.log('Confirm response:', response.data)
      
      // LockedWorkflow contains the draft, extract it
      const workflowDef: WorkflowDefinition = response.data.draft || response.data
      
      console.log('Creating workflow:', workflowDef)
      await workflowsApi.create(workflowDef)
      toast.success('Workflow created and locked!')
      setResult(null)
      setGoal('')
    } catch (error: any) {
      console.error('Confirm failed:', error)
      const message = error.response?.data?.detail || error.message || 'Unknown error'
      toast.error(`Failed to confirm plan: ${message}`)
    } finally {
      setConfirming(false)
    }
  }

  // Progress bar color based on status
  const getProgressColor = () => {
    if (!taskStatus) return 'bg-blue-600'
    switch (taskStatus.status) {
      case 'completed': return 'bg-green-600'
      case 'failed': return 'bg-red-600'
      case 'running': return 'bg-blue-600 animate-pulse'
      default: return 'bg-gray-400'
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">AI Workflow Planner</h2>
        <p className="text-gray-500">
          Describe your task in natural language, and our AI will design the optimal workflow
        </p>
      </div>

      {/* Input Section */}
      <div className="card p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          What would you like to accomplish?
        </label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Example: Create a workflow that fetches the latest news about AI, summarizes them, and sends a daily email report..."
          className="input w-full h-32 resize-none"
          disabled={planning}
        />
        <div className="flex justify-between items-center mt-4">
          <p className="text-sm text-gray-500">
            The AI will analyze your goal, select appropriate skills, and estimate costs.
          </p>
          <button
            onClick={handlePlan}
            disabled={planning || !goal.trim()}
            className="btn-primary flex items-center gap-2"
          >
            {planning ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Planning...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Plan
              </>
            )}
          </button>
        </div>
        
        {/* Async Progress Display */}
        {planning && taskStatus && (
          <div className="mt-6 space-y-3">
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getProgressColor()}`}
                style={{ width: `${taskStatus.progress}%` }}
              />
            </div>
            
            {/* Status Info */}
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {taskStatus.status === 'running' && (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                )}
                {taskStatus.status === 'completed' && (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                )}
                <span className="font-medium text-gray-700">
                  {taskStatus.current_step || 'Initializing'}
                </span>
              </div>
              <div className="text-gray-500">
                <span className="font-medium">{taskStatus.progress}%</span>
                <span className="mx-2">•</span>
                <span>{taskStatus.elapsed_seconds.toFixed(1)}s</span>
              </div>
            </div>
            
            {/* Task ID for MCP monitoring */}
            <div className="text-xs text-gray-400 font-mono bg-gray-50 p-2 rounded">
              Task: {taskId}
            </div>
          </div>
        )}
        
        {/* Simple loading state (before first poll) */}
        {planning && !taskStatus && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              <div>
                <p className="font-medium text-blue-800">Starting planning task...</p>
                <p className="text-sm text-blue-600">This may take 10-60 seconds depending on complexity.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Planning Result */}
      {result && (
        <div className="space-y-6">
          {/* Error Display */}
          {(result as any).error && (
            <div className="card p-6 bg-red-50 border-red-200">
              <h3 className="text-lg font-semibold text-red-700 mb-2">Planning Failed</h3>
              <p className="text-red-600">{(result as any).error}</p>
              <p className="text-sm text-gray-500 mt-2">
                Please check your API configuration in .env file and try again.
              </p>
            </div>
          )}
          
          {/* Success Message */}
          {result.success && (
            <div className="card p-6 bg-green-50 border-green-200">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <div>
                  <h3 className="text-lg font-semibold text-green-800">Planning Complete!</h3>
                  <p className="text-green-700">
                    Generated workflow with {result.draft?.nodes.length || 0} nodes
                    {taskStatus && ` in ${taskStatus.elapsed_seconds.toFixed(1)}s`}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {/* Analysis */}
          {result.draft && result.draft.analysis && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">4W1H Analysis</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium text-blue-700">What</span>
                  <p className="text-gray-800 mt-1">{result.draft.analysis.what}</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <span className="text-sm font-medium text-green-700">Why</span>
                  <p className="text-gray-800 mt-1">{result.draft.analysis.why}</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <span className="text-sm font-medium text-purple-700">Who</span>
                  <p className="text-gray-800 mt-1">{result.draft.analysis.who}</p>
                </div>
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <span className="text-sm font-medium text-yellow-700">When</span>
                  <p className="text-gray-800 mt-1">{result.draft.analysis.when}</p>
                </div>
                <div className="col-span-2 p-4 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">How</span>
                  <p className="text-gray-800 mt-1">{result.draft.analysis.how}</p>
                </div>
              </div>
            </div>
          )}

          {/* Draft Preview */}
          {result.draft && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Proposed Workflow</h3>
              <div className="space-y-3">
                {result.draft.nodes.map((node, index) => (
                  <div
                    key={node.id}
                    className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="w-8 h-8 flex items-center justify-center bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <span className="font-medium">{node.name}</span>
                      <span className="text-sm text-gray-500 ml-2">
                        ({node.type})
                      </span>
                      {node.skill_id && (
                        <p className="text-xs text-gray-400">Skill: {node.skill_id}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cost Estimate */}
          {result.cost_estimate && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Cost Estimate</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <Clock className="w-6 h-6 mx-auto mb-2 text-primary-500" />
                  <span className="text-2xl font-bold text-gray-900">
                    {result.cost_estimate.estimated_time_minutes}
                  </span>
                  <p className="text-sm text-gray-500">minutes</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <DollarSign className="w-6 h-6 mx-auto mb-2 text-green-500" />
                  <span className="text-2xl font-bold text-gray-900">
                    ${result.cost_estimate.estimated_cost_usd.toFixed(3)}
                  </span>
                  <p className="text-sm text-gray-500">estimated cost</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <Sparkles className="w-6 h-6 mx-auto mb-2 text-purple-500" />
                  <span className="text-2xl font-bold text-gray-900">
                    {result.cost_estimate.estimated_tokens.toLocaleString()}
                  </span>
                  <p className="text-sm text-gray-500">tokens</p>
                </div>
              </div>
            </div>
          )}

          {/* Confirm Button */}
          <div className="card p-6 bg-primary-50 border-primary-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-primary-900">Ready to create?</h3>
                <p className="text-primary-700">
                  This will create a locked workflow that can be executed.
                </p>
              </div>
              <button
                onClick={handleConfirm}
                disabled={confirming}
                className="btn-primary flex items-center gap-2"
              >
                {confirming ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Create Workflow
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
