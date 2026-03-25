import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Panel,
  BackgroundVariant,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  Play,
  Save,
  Settings,
  Trash2,
  Plus,
  AlertCircle,
} from 'lucide-react'
import { workflowsApi, executionsApi } from '../api/client'
import NodeConfigPanel from '../components/NodeConfigPanel'
import SkillPalette from '../components/SkillPalette'
import toast from 'react-hot-toast'

const nodeTypes = {
  skill: SkillNode,
  code: CodeNode,
  template: TemplateNode,
  decision: DecisionNode,
}

function SkillNode({ data }: { data: any }) {
  return (
    <div className="px-4 py-3 bg-white border-2 border-blue-500 rounded-lg shadow-sm min-w-[150px]">
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-blue-500" />
      <div className="flex items-center gap-2 mb-1">
        <Settings className="w-4 h-4 text-blue-500" />
        <span className="font-medium text-sm">{data.name}</span>
      </div>
      <p className="text-xs text-gray-500">{data.skill_id}</p>
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-blue-500" />
    </div>
  )
}

function CodeNode({ data }: { data: any }) {
  return (
    <div className="px-4 py-3 bg-white border-2 border-purple-500 rounded-lg shadow-sm min-w-[150px]">
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-purple-500" />
      <div className="flex items-center gap-2 mb-1">
        <Settings className="w-4 h-4 text-purple-500" />
        <span className="font-medium text-sm">{data.name}</span>
      </div>
      <p className="text-xs text-gray-500">Code Execution</p>
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-purple-500" />
    </div>
  )
}

function TemplateNode({ data }: { data: any }) {
  return (
    <div className="px-4 py-3 bg-white border-2 border-green-500 rounded-lg shadow-sm min-w-[150px]">
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-green-500" />
      <div className="flex items-center gap-2 mb-1">
        <Settings className="w-4 h-4 text-green-500" />
        <span className="font-medium text-sm">{data.name}</span>
      </div>
      <p className="text-xs text-gray-500">Template</p>
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-green-500" />
    </div>
  )
}

function DecisionNode({ data }: { data: any }) {
  return (
    <div className="px-4 py-3 bg-white border-2 border-yellow-500 rounded-lg shadow-sm min-w-[150px]">
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-yellow-500" />
      <div className="flex items-center gap-2 mb-1">
        <AlertCircle className="w-4 h-4 text-yellow-500" />
        <span className="font-medium text-sm">{data.name}</span>
      </div>
      <p className="text-xs text-gray-500">Decision</p>
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-yellow-500" />
    </div>
  )
}

export default function WorkflowEditor() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [workflowName, setWorkflowName] = useState('New Workflow')
  const [workflowDescription, setWorkflowDescription] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (id) {
      loadWorkflow(id)
    }
  }, [id])

  const loadWorkflow = async (workflowId: string) => {
    try {
      const response = await workflowsApi.get(workflowId)
      const workflow = response.data
      setWorkflowName(workflow.name)
      setWorkflowDescription(workflow.description)
      
      // Convert workflow nodes to ReactFlow nodes
      const flowNodes: Node[] = workflow.nodes.map((n: any, index: number) => ({
        id: n.id,
        type: n.type,
        position: { x: 100 + index * 250, y: 100 + (index % 2) * 100 },
        data: { ...n },
      }))
      
      const flowEdges: Edge[] = workflow.edges.map((e: any) => ({
        id: `${e.from}-${e.to}`,
        source: e.from,
        target: e.to,
        label: e.condition,
      }))
      
      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch (error) {
      toast.error('Failed to load workflow')
    }
  }

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const addNode = (type: string, defaults?: Record<string, any>) => {
    const newNode: Node = {
      id: `node_${nodes.length + 1}`,
      type,
      position: { x: 100 + Math.random() * 300, y: 100 + Math.random() * 200 },
      data: { 
        name: defaults?.name || (type === 'skill' ? 'New Skill' : type === 'code' ? 'Code Block' : type === 'template' ? 'Template' : 'Decision'),
        type,
        inputs: {},
        ...defaults,
      },
    }
    setNodes((nds) => [...nds, newNode])
  }

  const deleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
    setSelectedNode(null)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const workflowData = {
        id: id || `wf_${Date.now()}`,
        name: workflowName,
        description: workflowDescription,
        version: '1.0.0',
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          name: n.data.name,
          description: n.data.description,
          skill_id: n.data.skill_id,
          skill_version: n.data.skill_version,
          code: n.data.code,
          template: n.data.template,
          condition: n.data.condition,
          inputs: n.data.inputs,
          temperature: n.data.temperature,
        })),
        edges: edges.map((e) => ({
          from: e.source,
          to: e.target,
          condition: e.label,
        })),
        inputs: [],
        outputs: [],
      }

      if (id) {
        await workflowsApi.update(id, workflowData)
      } else {
        await workflowsApi.create(workflowData)
      }
      
      toast.success('Workflow saved!')
      if (!id) {
        navigate('/workflows')
      }
    } catch (error) {
      toast.error('Failed to save workflow')
    } finally {
      setSaving(false)
    }
  }

  const handleRun = async () => {
    if (!id) {
      toast.error('Please save the workflow first')
      return
    }
    
    try {
      await executionsApi.start(id, {})
      toast.success('Workflow started!')
    } catch (error) {
      toast.error('Failed to start workflow')
    }
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="text-xl font-bold bg-transparent border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:outline-none px-1"
            placeholder="Workflow Name"
          />
          <input
            type="text"
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
            className="text-sm text-gray-500 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:outline-none px-1"
            placeholder="Description"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => addNode('skill')}
            className="btn-secondary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Skill
          </button>
          <button
            onClick={() => addNode('code')}
            className="btn-secondary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Code
          </button>
          <button
            onClick={handleRun}
            className="btn-primary flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Run
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex gap-4">
        <div className="flex-1 card overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            
            <Panel position="top-left" className="bg-white rounded-lg shadow-sm p-2">
              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-blue-500 rounded"></span>
                  Skill
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-purple-500 rounded"></span>
                  Code
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-green-500 rounded"></span>
                  Template
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-yellow-500 rounded"></span>
                  Decision
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Side Panel */}
        {selectedNode ? (
          <div className="w-80 card p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Node Configuration</h3>
              <button
                onClick={() => deleteNode(selectedNode.id)}
                className="p-1 text-red-500 hover:bg-red-50 rounded"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <NodeConfigPanel
              node={selectedNode}
              onChange={(updatedData) => {
                setNodes((nds) =>
                  nds.map((n) =>
                    n.id === selectedNode.id ? { ...n, data: updatedData } : n
                  )
                )
                setSelectedNode({ ...selectedNode, data: updatedData })
              }}
            />
          </div>
        ) : (
          <SkillPalette onAddNode={addNode} />
        )}
      </div>
    </div>
  )
}
