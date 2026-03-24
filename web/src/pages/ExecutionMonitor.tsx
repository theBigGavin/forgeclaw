import { useEffect, useState } from 'react'
import {
  Play,
  Pause,
  Square,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Terminal,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { executionsApi } from '../api/client'
import type { Execution } from '../types'
import toast from 'react-hot-toast'

const statusConfig: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  pending: { 
    icon: <Clock className="w-5 h-5" />, 
    color: 'text-gray-500', 
    bg: 'bg-gray-50 border-gray-200' 
  },
  running: { 
    icon: <Loader2 className="w-5 h-5 animate-spin" />, 
    color: 'text-blue-500', 
    bg: 'bg-blue-50 border-blue-200' 
  },
  paused: { 
    icon: <Pause className="w-5 h-5" />, 
    color: 'text-yellow-600', 
    bg: 'bg-yellow-50 border-yellow-200' 
  },
  completed: { 
    icon: <CheckCircle className="w-5 h-5" />, 
    color: 'text-green-600', 
    bg: 'bg-green-50 border-green-200' 
  },
  failed: { 
    icon: <XCircle className="w-5 h-5" />, 
    color: 'text-red-600', 
    bg: 'bg-red-50 border-red-200' 
  },
  terminated: { 
    icon: <Square className="w-5 h-5" />, 
    color: 'text-gray-600', 
    bg: 'bg-gray-100 border-gray-300' 
  },
}

export default function ExecutionMonitor() {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    loadExecutions()
    let interval: ReturnType<typeof setInterval>
    if (autoRefresh) {
      interval = setInterval(loadExecutions, 3000)
    }
    return () => clearInterval(interval)
  }, [autoRefresh])

  const loadExecutions = async () => {
    try {
      const response = await executionsApi.list()
      setExecutions(response.data)
      
      // Update selected execution if it's still in the list
      if (selectedExecution) {
        const updated = response.data.find((e: Execution) => e.id === selectedExecution.id)
        if (updated) {
          setSelectedExecution(updated)
        }
      }
    } catch (error) {
      console.error('Failed to load executions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleControl = async (executionId: string, action: 'pause' | 'resume' | 'terminate') => {
    try {
      await executionsApi.control(executionId, action)
      toast.success(`Execution ${action}d`)
      loadExecutions()
    } catch (error) {
      toast.error(`Failed to ${action} execution`)
    }
  }

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start).getTime()
    const endTime = end ? new Date(end).getTime() : Date.now()
    const seconds = Math.floor((endTime - startTime) / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ${minutes % 60}m`
  }

  const getProgressPercent = (execution: Execution) => {
    const total = execution.node_results?.length || 1
    const completed = execution.node_results?.filter(
      (r: any) => r.status === 'success' || r.status === 'failed'
    ).length || 0
    return Math.round((completed / total) * 100)
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
          <h2 className="text-2xl font-bold text-gray-900">Execution Monitor</h2>
          <p className="text-gray-500">Monitor and control running workflows</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300"
            />
            Auto-refresh
          </label>
          <button
            onClick={loadExecutions}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Executions List */}
        <div className="col-span-1 space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto">
          {executions.length === 0 ? (
            <div className="card p-8 text-center">
              <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">No executions yet</p>
            </div>
          ) : (
            executions.map((exec) => {
              const status = statusConfig[exec.status]
              return (
                <button
                  key={exec.id}
                  onClick={() => setSelectedExecution(exec)}
                  className={`w-full card p-4 text-left transition-all ${
                    selectedExecution?.id === exec.id
                      ? 'ring-2 ring-primary-500 shadow-md'
                      : 'hover:shadow-md'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className={`flex items-center gap-2 ${status.color}`}>
                      {status.icon}
                      <span className="font-medium capitalize">{exec.status}</span>
                    </div>
                    <span className="text-xs text-gray-400 font-mono">
                      {exec.id.slice(0, 8)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2 truncate">{exec.workflow_id}</p>
                  
                  {/* Progress bar */}
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                    <div 
                      className={`h-1.5 rounded-full ${
                        exec.status === 'completed' ? 'bg-green-500' :
                        exec.status === 'failed' ? 'bg-red-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${getProgressPercent(exec)}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>{formatDuration(exec.started_at, exec.completed_at)}</span>
                    <span>•</span>
                    <span>{new Date(exec.started_at).toLocaleTimeString()}</span>
                  </div>
                </button>
              )
            })
          )}
        </div>

        {/* Execution Details */}
        <div className="col-span-2 space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          {selectedExecution ? (
            <>
              {/* Header Card */}
              <div className={`card p-5 border-2 ${statusConfig[selectedExecution.status].bg}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={statusConfig[selectedExecution.status].color}>
                      {statusConfig[selectedExecution.status].icon}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold">
                        Execution <span className="font-mono">{selectedExecution.id.slice(0, 12)}...</span>
                      </h3>
                      <p className="text-sm text-gray-500">
                        Workflow: <span className="font-mono">{selectedExecution.workflow_id}</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedExecution.status === 'running' && (
                      <>
                        <button
                          onClick={() => handleControl(selectedExecution.id, 'pause')}
                          className="btn-secondary flex items-center gap-2"
                        >
                          <Pause className="w-4 h-4" />
                          Pause
                        </button>
                        <button
                          onClick={() => handleControl(selectedExecution.id, 'terminate')}
                          className="btn-secondary text-red-600 hover:bg-red-50 flex items-center gap-2"
                        >
                          <Square className="w-4 h-4" />
                          Stop
                        </button>
                      </>
                    )}
                    {selectedExecution.status === 'paused' && (
                      <button
                        onClick={() => handleControl(selectedExecution.id, 'resume')}
                        className="btn-primary flex items-center gap-2"
                      >
                        <Play className="w-4 h-4" />
                        Resume
                      </button>
                    )}
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Status</span>
                    <p className="font-semibold capitalize mt-0.5">{selectedExecution.status}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Duration</span>
                    <p className="font-semibold mt-0.5">
                      {formatDuration(selectedExecution.started_at, selectedExecution.completed_at)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Progress</span>
                    <p className="font-semibold mt-0.5">
                      {selectedExecution.node_results?.filter((r: any) => r.status === 'success').length || 0} / {selectedExecution.node_results?.length || 0} nodes
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Started</span>
                    <p className="font-semibold mt-0.5">
                      {new Date(selectedExecution.started_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Node Results */}
              <div className="card p-5">
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-primary-500" />
                  Node Results
                </h4>
                <div className="space-y-2">
                  {selectedExecution.node_results?.map((result: any, index: number) => (
                    <div key={index} className="border rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleNode(result.node_id)}
                        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {expandedNodes.has(result.node_id) ? (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          )}
                          <span className="font-medium font-mono text-sm">{result.node_id}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            result.status === 'success'
                              ? 'bg-green-100 text-green-700'
                              : result.status === 'failed'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            {result.status}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500 font-mono">
                          {result.duration_ms}ms
                        </span>
                      </button>
                      {expandedNodes.has(result.node_id) && (
                        <div className="p-4 bg-white">
                          {result.output !== undefined && (
                            <div className="mb-4">
                              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Output</span>
                              <pre className="mt-2 p-3 bg-gray-50 rounded-lg text-xs overflow-auto max-h-48 border">
                                {typeof result.output === 'string'
                                  ? result.output
                                  : JSON.stringify(result.output, null, 2)}
                              </pre>
                            </div>
                          )}
                          {result.error && (
                            <div>
                              <span className="text-xs font-medium text-red-500 uppercase tracking-wide">Error</span>
                              <pre className="mt-2 p-3 bg-red-50 rounded-lg text-xs text-red-700 overflow-auto max-h-48 border border-red-200">
                                {result.error}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Logs */}
              {selectedExecution.logs && selectedExecution.logs.length > 0 && (
                <div className="card p-5">
                  <h4 className="font-semibold mb-4">Execution Logs</h4>
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-xl font-mono text-xs max-h-64 overflow-auto">
                    {selectedExecution.logs.map((log: any, index: number) => (
                      <div key={index} className="mb-1.5 leading-relaxed">
                        <span className="text-gray-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        {' '}
                        <span className={`font-semibold ${
                          log.level === 'error' ? 'text-red-400' :
                          log.level === 'warn' ? 'text-yellow-400' :
                          log.level === 'debug' ? 'text-gray-500' :
                          'text-cyan-400'
                        }`}>
                          [{log.level.toUpperCase()}]
                        </span>
                        {' '}
                        <span className="text-gray-300">{log.message}</span>
                        {log.node_id && (
                          <span className="text-gray-500 ml-2">({log.node_id})</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty state if no node results */}
              {(!selectedExecution.node_results || selectedExecution.node_results.length === 0) && (
                <div className="card p-8 text-center text-gray-400">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3" />
                  <p>No node results yet</p>
                  <p className="text-sm mt-1">Execution is still initializing...</p>
                </div>
              )}
            </>
          ) : (
            <div className="card p-12 text-center text-gray-400">
              <Terminal className="w-16 h-16 mx-auto mb-4" />
              <p className="text-lg">Select an execution to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
