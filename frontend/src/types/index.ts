// Agent types
export interface Agent {
  id: number
  name: string
  role?: string
  description?: string
  llm_provider: string
  llm_model: string
  llm_config?: Record<string, any>
  personality?: Record<string, any>
  tool_names?: string[]
  status: 'idle' | 'active' | 'running' | 'error'
  created_at: string
  updated_at: string
  tasks_count: number
  tools_count: number
}

export interface AgentStatistics {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
}

// Task types
export interface Task {
  id: number
  title: string
  description: string
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'running' | 'completed' | 'failed'
  detailed_status?: 'pending' | 'running' | 'waiting_input' | 'waiting_approval' | 'completed' | 'failed'
  assigned_to?: number
  parent_task_id?: number
  mode: 'manual' | 'auto' | 'team'
  auto_mode?: boolean  // 自動実行モード（実行中に切り替え可能）
  additional_tool_names?: string[]
  result?: Record<string, any>
  error_message?: string
  deadline?: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  agent?: {
    id: number
    name: string
    role?: string
  }
  subtasks?: Task[]
}

// Tool types
export interface Tool {
  id?: number
  name: string
  category: string
  description?: string
  type?: 'builtin' | 'api' | 'script' | 'cli'
  config?: Record<string, any>
  is_builtin: boolean
  is_mcp: boolean
  is_active: boolean
  created_at?: string
  updated_at?: string
  usage_count?: number
}

// ExecutionLog types
export interface ExecutionLog {
  id: number
  task_id: number
  agent_id: number
  tool_id?: number
  action: string
  input_data?: Record<string, any>
  output_data?: Record<string, any>
  status: 'started' | 'success' | 'failed'
  error_message?: string
  execution_time?: number
  created_at: string
  agent_name?: string
  tool_name?: string
}

// LLM Setting types
export interface LLMSetting {
  id: number
  provider: string
  base_url?: string
  default_model?: string
  config?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
  has_api_key: boolean
}

export interface LLMProvider {
  value: string
  label: string
  description: string
  requires_api_key: boolean
}

// API Response types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// WebSocket Event types
export interface TaskStartedEvent {
  task_id: number
  agent_id: number
}

export interface TaskProgressEvent {
  task_id: number
  progress: number
  message: string
}

export interface TaskCompletedEvent {
  task_id: number
  result: Record<string, any>
}

export interface TaskFailedEvent {
  task_id: number
  error: string
}

export interface AgentStatusChangedEvent {
  agent_id: number
  status: string
}

export interface LogMessageEvent {
  task_id: number
  log: ExecutionLog
}
