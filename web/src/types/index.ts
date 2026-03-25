// Node Types
export type NodeType = 'skill' | 'code' | 'template' | 'decision'

export interface WorkflowNode {
  id: string
  type: NodeType
  name: string
  description?: string
  skill_id?: string
  skill_version?: string
  code?: string
  template?: string
  condition?: string
  inputs: Record<string, any>
  retry_count?: number
  timeout_seconds?: number
  temperature?: number
}

export interface WorkflowEdge {
  from: string
  to: string
  condition?: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  version: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  inputs: WorkflowInput[]
  outputs: WorkflowOutput[]
  created_at?: string
  updated_at?: string
}

export interface WorkflowDefinition extends Workflow {
  // Same as Workflow for now
}

export interface WorkflowInput {
  name: string
  type: string
  required: boolean
  default?: any
  description?: string
}

export interface WorkflowOutput {
  name: string
  type: string
  description?: string
}

// Execution Types
export type ExecutionStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'terminated'

export interface Execution {
  id: string
  workflow_id: string
  status: ExecutionStatus
  inputs: Record<string, any>
  outputs?: Record<string, any>
  node_results: NodeResult[]
  started_at: string
  completed_at?: string
  logs?: ExecutionLog[]
  completed_nodes?: string[]
}

export interface NodeResult {
  node_id: string
  status: 'success' | 'failed' | 'pending'
  output?: any
  error?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
}

export interface ExecutionLog {
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  node_id?: string
}

// Planning Types
export interface Analysis4W1H {
  what: string
  why: string
  who: string
  when: string
  how: string
}

export interface CostEstimate {
  estimated_tokens: number
  estimated_cost_usd: number
  estimated_time_minutes: number
}

export interface RiskAssessment {
  type: string
  severity: 'low' | 'medium' | 'high'
  description: string
  mitigation: string
}

export interface WorkflowDraft {
  id: string
  name: string
  description: string
  analysis: Analysis4W1H
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface PlanningResult {
  success: boolean
  draft?: WorkflowDraft
  error?: string
  cost_estimate?: CostEstimate
  risk_assessment?: RiskAssessment[]
}

// Async Planning Task
export interface PlanningTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  goal: string
  created_at: string
  updated_at: string
  progress: number
  current_step: string
  draft?: WorkflowDraft
  error?: string
  elapsed_seconds: number
}

// Scheduler Types
export type TriggerType = 'cron' | 'interval' | 'event' | 'once'
export type ContextPolicy = 'none' | 'recent' | 'filtered' | 'full'

export interface Trigger {
  type: TriggerType
  config: {
    expression?: string          // for cron
    minutes?: number             // for interval
    event_type?: string          // for event
    execute_at?: string          // for once
  }
}

export interface ScheduledTask {
  id: string
  name: string
  workflow_id: string
  trigger: Trigger
  context_policy: ContextPolicy
  enabled: boolean
  last_run?: string
  next_run?: string
  created_at: string
}

// Asset Types
export type AssetType = 'text' | 'image' | 'audio' | 'video' | 'code' | 'binary' | 'directory'

export interface Asset {
  id: string
  name: string
  asset_type: AssetType
  project_id: string
  current_version: string
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
}

export interface AssetVersion {
  id: string
  version: string
  created_at: string
  created_by?: string
  size_bytes: number
  checksum: string
  comment?: string
}

export interface AssetLineage {
  asset_id: string
  source_assets: string[]
  derived_assets: string[]
  workflow_executions: string[]
}
