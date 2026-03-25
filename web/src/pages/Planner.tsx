import { useState } from 'react'
import { Sparkles, Clock, DollarSign, Shield, CheckCircle } from 'lucide-react'
import { plannerApi, workflowsApi } from '../api/client'
import type { PlanningResult, WorkflowDefinition } from '../types'
import toast from 'react-hot-toast'

export default function Planner() {
  const [goal, setGoal] = useState('')
  const [planning, setPlanning] = useState(false)
  const [result, setResult] = useState<PlanningResult | null>(null)
  const [confirming, setConfirming] = useState(false)

  const handlePlan = async () => {
    if (!goal.trim()) {
      toast.error('Please enter your goal')
      return
    }

    setPlanning(true)
    setResult(null)

    try {
      const response = await plannerApi.plan({
        goal,
        context: {},
      })
      const data = response.data
      
      // Check for error in response
      if ((data as any).error) {
        toast.error(`Planning failed: ${(data as any).error}`)
      } else if (!data.draft) {
        toast.error('Planning returned empty result')
      } else {
        setResult(data)
        toast.success('Plan generated!')
      }
    } catch (error: any) {
      const message = error.response?.data?.error || error.message || 'Unknown error'
      toast.error(`Failed to generate plan: ${message}`)
      console.error('Planning error:', error)
    } finally {
      setPlanning(false)
    }
  }

  const handleConfirm = async () => {
    if (!result) return

    setConfirming(true)
    try {
      const response = await plannerApi.confirm(result.draft.id)
      const workflowDef: WorkflowDefinition = response.data
      
      await workflowsApi.create(workflowDef)
      toast.success('Workflow created and locked!')
      setResult(null)
      setGoal('')
    } catch (error) {
      toast.error('Failed to confirm plan')
    } finally {
      setConfirming(false)
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
            <Sparkles className="w-5 h-5" />
            {planning ? 'Planning...' : 'Generate Plan'}
          </button>
        </div>
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

          {/* Risk Assessment */}
          {result.risk_assessment && result.risk_assessment.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Risk Assessment</h3>
              <div className="space-y-3">
                {result.risk_assessment.map((risk, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      risk.severity === 'high'
                        ? 'bg-red-50 border border-red-200'
                        : risk.severity === 'medium'
                        ? 'bg-yellow-50 border border-yellow-200'
                        : 'bg-blue-50 border border-blue-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Shield className={`w-4 h-4 ${
                        risk.severity === 'high'
                          ? 'text-red-500'
                          : risk.severity === 'medium'
                          ? 'text-yellow-500'
                          : 'text-blue-500'
                      }`} />
                      <span className="font-medium capitalize">{risk.type} Risk</span>
                      <span className="text-xs uppercase px-2 py-0.5 rounded bg-white">
                        {risk.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{risk.description}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Mitigation: {risk.mitigation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          {result.draft && (
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => setResult(null)}
                className="btn-secondary px-8"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={confirming}
                className="btn-primary px-8 flex items-center gap-2"
              >
                <CheckCircle className="w-5 h-5" />
                {confirming ? 'Creating...' : 'Confirm & Create Workflow'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
