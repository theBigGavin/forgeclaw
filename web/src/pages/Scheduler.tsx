import { useEffect, useState } from 'react'
import {
  Plus,
  Clock,
  Calendar,
  Zap,
  Play,
  Pause,
  Trash2,
  AlertCircle,
} from 'lucide-react'
import { schedulerApi } from '../api/client'
import type { ScheduledTask } from '../types'
import toast from 'react-hot-toast'

type TriggerType = 'cron' | 'interval' | 'event' | 'once'
type ContextPolicy = 'none' | 'recent' | 'filtered' | 'full'

const triggerIcons: Record<string, React.ReactNode> = {
  cron: <Calendar className="w-5 h-5" />,
  interval: <Clock className="w-5 h-5" />,
  event: <Zap className="w-5 h-5" />,
  once: <Play className="w-5 h-5" />,
}

export default function Scheduler() {
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    workflow_id: '',
    trigger_type: 'interval' as TriggerType,
    trigger_config: '',
    context_policy: 'recent' as ContextPolicy,
  })

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    try {
      const response = await schedulerApi.list()
      setTasks(response.data)
    } catch (error) {
      toast.error('Failed to load scheduled tasks')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      let triggerConfig = {}
      if (formData.trigger_type === 'interval') {
        triggerConfig = { minutes: parseInt(formData.trigger_config) || 60 }
      } else if (formData.trigger_type === 'cron') {
        triggerConfig = { expression: formData.trigger_config || '0 9 * * *' }
      } else if (formData.trigger_type === 'event') {
        triggerConfig = { event_type: formData.trigger_config || 'workflow.completed' }
      } else {
        triggerConfig = { execute_at: formData.trigger_config || new Date().toISOString() }
      }

      await schedulerApi.create({
        name: formData.name,
        workflow_id: formData.workflow_id,
        trigger: {
          type: formData.trigger_type,
          config: triggerConfig,
        },
        context_policy: formData.context_policy,
      })

      toast.success('Task scheduled!')
      setShowForm(false)
      setFormData({
        name: '',
        workflow_id: '',
        trigger_type: 'interval',
        trigger_config: '',
        context_policy: 'recent',
      })
      loadTasks()
    } catch (error) {
      toast.error('Failed to schedule task')
    }
  }

  const handleToggle = async (taskId: string, enabled: boolean) => {
    try {
      await schedulerApi.update(taskId, { enabled: !enabled })
      toast.success(enabled ? 'Task paused' : 'Task enabled')
      loadTasks()
    } catch (error) {
      toast.error('Failed to update task')
    }
  }

  const handleDelete = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this scheduled task?')) return

    try {
      await schedulerApi.delete(taskId)
      setTasks(tasks.filter((t) => t.id !== taskId))
      toast.success('Task deleted')
    } catch (error) {
      toast.error('Failed to delete task')
    }
  }

  const getTriggerDisplay = (task: ScheduledTask) => {
    const { type, config } = task.trigger
    if (!config) return type || 'Unknown'
    
    if (type === 'interval') {
      const minutes = config.minutes || config.minutes_5 || config.minutes_1 || 5
      return `Every ${minutes} minutes`
    } else if (type === 'cron') {
      return `Cron: ${config.expression || config.minute + ' ' + config.hour + ' * * *'}`
    } else if (type === 'event') {
      return `On: ${config.event_type || 'workflow.completed'}`
    } else if (type === 'once' || config.execute_at) {
      return `Once at: ${new Date(config.execute_at || Date.now()).toLocaleString()}`
    }
    return type || 'Unknown'
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
          <h2 className="text-2xl font-bold text-gray-900">Scheduler</h2>
          <p className="text-gray-500">Automate workflows with scheduled tasks</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Task
        </button>
      </div>

      {/* New Task Form */}
      {showForm && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Schedule New Task</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Task Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="Daily Report"
                  required
                />
              </div>
              <div>
                <label className="label">Workflow ID</label>
                <input
                  type="text"
                  value={formData.workflow_id}
                  onChange={(e) => setFormData({ ...formData, workflow_id: e.target.value })}
                  className="input w-full"
                  placeholder="wf_xxx"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="label">Trigger Type</label>
                <select
                  value={formData.trigger_type}
                  onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value as TriggerType })}
                  className="input w-full"
                >
                  <option value="interval">Interval</option>
                  <option value="cron">Cron</option>
                  <option value="event">Event</option>
                  <option value="once">Once</option>
                </select>
              </div>
              <div>
                <label className="label">
                  {formData.trigger_type === 'interval' && 'Minutes'}
                  {formData.trigger_type === 'cron' && 'Cron Expression'}
                  {formData.trigger_type === 'event' && 'Event Type'}
                  {formData.trigger_type === 'once' && 'Execute At'}
                </label>
                <input
                  type="text"
                  value={formData.trigger_config}
                  onChange={(e) => setFormData({ ...formData, trigger_config: e.target.value })}
                  className="input w-full"
                  placeholder={
                    formData.trigger_type === 'interval' ? '60' :
                    formData.trigger_type === 'cron' ? '0 9 * * *' :
                    formData.trigger_type === 'event' ? 'workflow.completed' :
                    new Date().toISOString()
                  }
                />
              </div>
              <div>
                <label className="label">Context Policy</label>
                <select
                  value={formData.context_policy}
                  onChange={(e) => setFormData({ ...formData, context_policy: e.target.value as ContextPolicy })}
                  className="input w-full"
                >
                  <option value="none">None (Fresh start)</option>
                  <option value="recent">Recent (Last 5)</option>
                  <option value="filtered">Filtered (Relevant)</option>
                  <option value="full">Full (All history)</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary">
                Schedule
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tasks List */}
      <div className="space-y-4">
        {tasks.length === 0 ? (
          <div className="card p-12 text-center">
            <Clock className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No scheduled tasks</h3>
            <p className="text-gray-500">Create your first scheduled task to automate workflows</p>
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className="card p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 bg-gray-100 rounded-lg">
                  {triggerIcons[task.trigger.type]}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{task.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Workflow: {task.workflow_id}</span>
                    <span>•</span>
                    <span>{getTriggerDisplay(task)}</span>
                    <span>•</span>
                    <span className="capitalize">{task.context_policy} context</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggle(task.id, task.enabled)}
                  className={`p-2 rounded-lg ${
                    task.enabled
                      ? 'text-green-600 hover:bg-green-50'
                      : 'text-gray-400 hover:bg-gray-100'
                  }`}
                  title={task.enabled ? 'Pause' : 'Enable'}
                >
                  {task.enabled ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => handleDelete(task.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Delete"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Box */}
      <div className="card p-4 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Context Policy Guide:</p>
            <ul className="space-y-1 list-disc list-inside">
              <li><strong>None:</strong> Fresh start, no previous context</li>
              <li><strong>Recent:</strong> Include last 5 execution results</li>
              <li><strong>Filtered:</strong> Include semantically relevant context</li>
              <li><strong>Full:</strong> Include all project history (use with caution)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
