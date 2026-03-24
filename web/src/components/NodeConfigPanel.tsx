import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'

interface NodeConfigPanelProps {
  node: any
  onChange: (data: any) => void
}

export default function NodeConfigPanel({ node, onChange }: NodeConfigPanelProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'inputs' | 'advanced'>('general')
  const data = node.data

  const handleChange = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  const addInput = () => {
    const inputs = data.inputs || {}
    const newKey = `input_${Object.keys(inputs).length + 1}`
    handleChange('inputs', { ...inputs, [newKey]: '' })
  }

  const updateInput = (oldKey: string, newKey: string, value: string) => {
    const inputs = { ...data.inputs }
    if (oldKey !== newKey) {
      delete inputs[oldKey]
    }
    inputs[newKey] = value
    handleChange('inputs', inputs)
  }

  const removeInput = (key: string) => {
    const inputs = { ...data.inputs }
    delete inputs[key]
    handleChange('inputs', inputs)
  }

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex border-b">
        {['general', 'inputs', 'advanced'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`px-3 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-4">
          <div>
            <label className="label">Node Name</label>
            <input
              type="text"
              value={data.name || ''}
              onChange={(e) => handleChange('name', e.target.value)}
              className="input w-full"
              placeholder="Enter node name"
            />
          </div>
          
          <div>
            <label className="label">Description</label>
            <textarea
              value={data.description || ''}
              onChange={(e) => handleChange('description', e.target.value)}
              className="input w-full h-20 resize-none"
              placeholder="Optional description"
            />
          </div>

          {data.type === 'skill' && (
            <>
              <div>
                <label className="label">Skill ID</label>
                <input
                  type="text"
                  value={data.skill_id || ''}
                  onChange={(e) => handleChange('skill_id', e.target.value)}
                  className="input w-full"
                  placeholder="e.g., http.request"
                />
              </div>
              <div>
                <label className="label">Skill Version</label>
                <input
                  type="text"
                  value={data.skill_version || 'latest'}
                  onChange={(e) => handleChange('skill_version', e.target.value)}
                  className="input w-full"
                  placeholder="latest"
                />
              </div>
            </>
          )}

          {data.type === 'code' && (
            <div>
              <label className="label">Python Code</label>
              <textarea
                value={data.code || ''}
                onChange={(e) => handleChange('code', e.target.value)}
                className="input w-full h-40 font-mono text-xs"
                placeholder={`# Write Python code here\ndef main(inputs):\n    return {"result": "Hello World"}`}
                spellCheck={false}
              />
            </div>
          )}

          {data.type === 'template' && (
            <div>
              <label className="label">Template</label>
              <textarea
                value={data.template || ''}
                onChange={(e) => handleChange('template', e.target.value)}
                className="input w-full h-40 font-mono text-xs"
                placeholder="Hello {{name}}! Result: {{input.result}}"
                spellCheck={false}
              />
              <p className="text-xs text-gray-500 mt-1">
                Use {"{{variable}}"} for variable interpolation
              </p>
            </div>
          )}

          {data.type === 'decision' && (
            <div>
              <label className="label">Condition Expression</label>
              <input
                type="text"
                value={data.condition || ''}
                onChange={(e) => handleChange('condition', e.target.value)}
                className="input w-full font-mono text-sm"
                placeholder="${input.value} > 0"
              />
              <p className="text-xs text-gray-500 mt-1">
                Use {"${variable}"} to reference inputs. Return truthy/falsy.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Inputs Tab */}
      {activeTab === 'inputs' && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            Map inputs from other nodes. Use {"${node_id.output}"} syntax.
          </p>
          
          {Object.entries(data.inputs || {}).map(([key, value]: [string, any]) => (
            <div key={key} className="flex gap-2 items-start">
              <input
                type="text"
                defaultValue={key}
                onBlur={(e) => updateInput(key, e.target.value, value)}
                className="input w-24 text-sm"
                placeholder="key"
              />
              <input
                type="text"
                value={value}
                onChange={(e) => updateInput(key, key, e.target.value)}
                className="input flex-1 text-sm font-mono"
                placeholder="${node_1.output}"
              />
              <button
                onClick={() => removeInput(key)}
                className="p-2 text-red-500 hover:bg-red-50 rounded"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          
          <button
            onClick={addInput}
            className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
          >
            <Plus className="w-4 h-4" />
            Add Input Mapping
          </button>
        </div>
      )}

      {/* Advanced Tab */}
      {activeTab === 'advanced' && (
        <div className="space-y-4">
          <div>
            <label className="label">Retry Count</label>
            <input
              type="number"
              value={data.retry_count ?? 0}
              onChange={(e) => handleChange('retry_count', parseInt(e.target.value) || 0)}
              className="input w-full"
              min="0"
              max="5"
            />
          </div>
          
          <div>
            <label className="label">Timeout (seconds)</label>
            <input
              type="number"
              value={data.timeout_seconds ?? 300}
              onChange={(e) => handleChange('timeout_seconds', parseInt(e.target.value) || 300)}
              className="input w-full"
              min="1"
              max="3600"
            />
          </div>

          {data.type === 'skill' && (
            <>
              <div>
                <label className="label">Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={data.temperature ?? 0.7}
                  onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                  className="input w-full"
                />
              </div>
              
              <div>
                <label className="label">Determinism Level</label>
                <select
                  value={data.determinism_level || 'balanced'}
                  onChange={(e) => handleChange('determinism_level', e.target.value)}
                  className="input w-full"
                >
                  <option value="strict">Strict (cached only)</option>
                  <option value="balanced">Balanced (security updates)</option>
                  <option value="relaxed">Relaxed (minor updates)</option>
                </select>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
