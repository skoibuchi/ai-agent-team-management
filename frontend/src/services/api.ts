import axios from 'axios'
import type { Agent, Task, Team, Tool, LLMSetting, ExecutionLog, ApiResponse } from '@/types'
import type { TaskInteractionResponse, PendingInteractionsResponse, InteractionRespondRequest } from '@/types/interaction'

const axiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Agent API
export const agentApi = {
  getAll: () => axiosInstance.get<ApiResponse<Agent[]>>('/agents'),
  getById: (id: number) => axiosInstance.get<ApiResponse<Agent>>(`/agents/${id}`),
  create: (data: Partial<Agent>) => axiosInstance.post<ApiResponse<Agent>>('/agents', data),
  update: (id: number, data: Partial<Agent>) => axiosInstance.put<ApiResponse<Agent>>(`/agents/${id}`, data),
  delete: (id: number) => axiosInstance.delete<ApiResponse<void>>(`/agents/${id}`),
  getStatistics: (id: number) => axiosInstance.get<ApiResponse<any>>(`/agents/${id}/statistics`),
  getTools: (id: number) => axiosInstance.get<ApiResponse<Tool[]>>(`/agents/${id}/tools`),
  getSupervisors: () => axiosInstance.get<ApiResponse<Agent[]>>('/agents/supervisors'),
  getWorkers: () => axiosInstance.get<ApiResponse<Agent[]>>('/agents/workers'),
  getWorkersBySupervisor: (id: number) => axiosInstance.get<ApiResponse<Agent[]>>(`/agents/${id}/workers`),
  assignSupervisor: (id: number, supervisorId: number) => axiosInstance.post<ApiResponse<Agent>>(`/agents/${id}/assign-supervisor`, { supervisor_id: supervisorId }),
  removeSupervisor: (id: number) => axiosInstance.post<ApiResponse<Agent>>(`/agents/${id}/remove-supervisor`),
}

// Task API
export const taskApi = {
  getAll: (params?: { status?: string; agent_id?: number; updated_since?: string }) =>
    axiosInstance.get<ApiResponse<Task[]>>('/tasks', { params }),
  getById: (id: number) => axiosInstance.get<ApiResponse<Task>>(`/tasks/${id}`),
  create: (data: Partial<Task>) => axiosInstance.post<ApiResponse<Task>>('/tasks', data),
  update: (id: number, data: Partial<Task>) => axiosInstance.put<ApiResponse<Task>>(`/tasks/${id}`, data),
  delete: (id: number) => axiosInstance.delete<ApiResponse<void>>(`/tasks/${id}`),
  execute: (id: number) => axiosInstance.post<ApiResponse<Task>>(`/tasks/${id}/execute`),
  getLogs: (id: number) => axiosInstance.get<ApiResponse<ExecutionLog[]>>(`/tasks/${id}/logs`),
  cancel: (id: number) => axiosInstance.post<ApiResponse<Task>>(`/tasks/${id}/cancel`),
  toggleAutoMode: (id: number) => axiosInstance.post<ApiResponse<Task>>(`/tasks/${id}/toggle-auto-mode`),
}

// Team API
export const teamApi = {
  getAll: (params?: { is_active?: boolean }) =>
    axiosInstance.get<ApiResponse<Team[]>>('/teams', { params }),
  getById: (id: number) => axiosInstance.get<ApiResponse<Team>>(`/teams/${id}`),
  create: (data: Partial<Team>) => axiosInstance.post<ApiResponse<Team>>('/teams', data),
  update: (id: number, data: Partial<Team>) => axiosInstance.put<ApiResponse<Team>>(`/teams/${id}`, data),
  delete: (id: number) => axiosInstance.delete<ApiResponse<void>>(`/teams/${id}`),
}

// Tool API
export const toolApi = {
  getAll: (params?: { category?: string; is_active?: boolean }) =>
    axiosInstance.get<ApiResponse<Tool[]>>('/tools', { params }),
  getById: (id: number) => axiosInstance.get<ApiResponse<Tool>>(`/tools/${id}`),
  create: (data: Partial<Tool>) => axiosInstance.post<ApiResponse<Tool>>('/tools', data),
  update: (id: number, data: Partial<Tool>) => axiosInstance.put<ApiResponse<Tool>>(`/tools/${id}`, data),
  delete: (id: number) => axiosInstance.delete<ApiResponse<void>>(`/tools/${id}`),
  getCategories: () => axiosInstance.get<ApiResponse<any[]>>('/tools/categories'),
  test: (id: number, parameters: Record<string, any>) =>
    axiosInstance.post<ApiResponse<any>>(`/tools/${id}/test`, { parameters }),
  generate: (data: { description: string; category?: string }) =>
    axiosInstance.post<ApiResponse<Tool>>('/tools/generate', data),
  register: (data: { code: string; category?: string }) =>
    axiosInstance.post<ApiResponse<Tool>>('/tools/register', data),
}

// Settings API
export const settingsApi = {
  getLLMSettings: () => axiosInstance.get<ApiResponse<LLMSetting[]>>('/settings/llm'),
  getLLMSetting: (provider: string) => axiosInstance.get<ApiResponse<LLMSetting>>(`/settings/llm/${provider}`),
  createLLMSetting: (data: Partial<LLMSetting> & { api_key?: string }) =>
    axiosInstance.post<ApiResponse<LLMSetting>>('/settings/llm', data),
  updateLLMSetting: (provider: string, data: Partial<LLMSetting> & { api_key?: string }) =>
    axiosInstance.put<ApiResponse<LLMSetting>>(`/settings/llm/${provider}`, data),
  deleteLLMSetting: (provider: string) => axiosInstance.delete<ApiResponse<void>>(`/settings/llm/${provider}`),
  getAvailableModels: (provider: string) =>
    axiosInstance.get<ApiResponse<string[]>>(`/settings/llm/${provider}/models`),
  testConnection: (provider: string, data?: any) =>
    axiosInstance.post<ApiResponse<any>>(`/settings/llm/${provider}/test`, data || {}),
  getProviders: () => axiosInstance.get<ApiResponse<any[]>>('/settings/providers'),
}

// Approvals API
export const approvalsApi = {
  getApprovals: (params?: { agent_id?: number; status?: string }) =>
    axiosInstance.get<ApiResponse<any[]>>('/approvals/', { params }),
  getApproval: (id: number) =>
    axiosInstance.get<ApiResponse<any>>(`/approvals/${id}`),
  createApprovalRequest: (data: { agent_id: number; task_id?: number; tools: string[]; reason: string }) =>
    axiosInstance.post<ApiResponse<any>>('/approvals/', data),
  approveRequest: (id: number, note?: string) =>
    axiosInstance.post<ApiResponse<any>>(`/approvals/${id}/approve`, { note }),
  rejectRequest: (id: number, note?: string) =>
    axiosInstance.post<ApiResponse<any>>(`/approvals/${id}/reject`, { note }),
  getPendingRequests: (agent_id?: number) =>
    axiosInstance.get<ApiResponse<any[]>>('/approvals/pending', { params: { agent_id } }),
}

// Task Analysis API
export const taskAnalysisApi = {
  analyze: (data: { task_description: string; provider?: string }) =>
    axiosInstance.post<ApiResponse<any>>('/task-analysis/analyze', data),
  recommendTools: (data: { task_description: string; provider?: string }) =>
    axiosInstance.post<ApiResponse<any>>('/task-analysis/recommend-tools', data),
}

// Interaction API
export const interactionApi = {
  getInteractions: (taskId: number, params?: { type?: string; limit?: number; since?: number }) =>
    axiosInstance.get<TaskInteractionResponse>(`/tasks/${taskId}/interactions`, { params }),
  respondToInteraction: (taskId: number, interactionId: number, data: InteractionRespondRequest) =>
    axiosInstance.post<ApiResponse<any>>(`/tasks/${taskId}/interactions/${interactionId}/respond`, data),
  getPendingInteractions: (taskId: number) =>
    axiosInstance.get<PendingInteractionsResponse>(`/tasks/${taskId}/interactions/pending`),
  sendUserMessage: (taskId: number, message: string) =>
    axiosInstance.post<ApiResponse<any>>(`/tasks/${taskId}/interactions/send-message`, { message }),
}

// Unified API object
export const api = {
  // Agents
  getAgents: () => agentApi.getAll().then(res => res.data),
  getAgent: (id: number) => agentApi.getById(id).then(res => res.data),
  createAgent: (data: Partial<Agent>) => agentApi.create(data).then(res => res.data),
  updateAgent: (id: number, data: Partial<Agent>) => agentApi.update(id, data).then(res => res.data),
  deleteAgent: (id: number) => agentApi.delete(id).then(res => res.data),
  getAgentStatistics: (id: number) => agentApi.getStatistics(id).then(res => res.data),
  getAgentTools: (id: number) => agentApi.getTools(id).then(res => res.data),
  getSupervisors: () => agentApi.getSupervisors().then(res => res.data),
  getWorkers: () => agentApi.getWorkers().then(res => res.data),
  getWorkersBySupervisor: (id: number) => agentApi.getWorkersBySupervisor(id).then(res => res.data),
  assignSupervisor: (id: number, supervisorId: number) => agentApi.assignSupervisor(id, supervisorId).then(res => res.data),
  removeSupervisor: (id: number) => agentApi.removeSupervisor(id).then(res => res.data),

  // Tasks
  getTasks: (params?: { status?: string; agent_id?: number; updated_since?: string }) => taskApi.getAll(params).then(res => res.data),
  getTask: (id: number) => taskApi.getById(id).then(res => res.data),
  createTask: (data: Partial<Task>) => taskApi.create(data).then(res => res.data),
  updateTask: (id: number, data: Partial<Task>) => taskApi.update(id, data).then(res => res.data),
  deleteTask: (id: number) => taskApi.delete(id).then(res => res.data),
  executeTask: (id: number) => taskApi.execute(id).then(res => res.data),
  getTaskLogs: (id: number) => taskApi.getLogs(id).then(res => res.data),
  cancelTask: (id: number) => taskApi.cancel(id).then(res => res.data),
  toggleTaskAutoMode: (id: number) => taskApi.toggleAutoMode(id).then(res => res.data),

  // Tools
  getTools: (params?: { category?: string; is_active?: boolean }) => toolApi.getAll(params).then(res => res.data),
  getTool: (id: number) => toolApi.getById(id).then(res => res.data),
  createTool: (data: Partial<Tool>) => toolApi.create(data).then(res => res.data),
  updateTool: (id: number, data: Partial<Tool>) => toolApi.update(id, data).then(res => res.data),
  deleteTool: (id: number) => toolApi.delete(id).then(res => res.data),
  getToolCategories: () => toolApi.getCategories().then(res => res.data),
  testTool: (id: number, parameters: Record<string, any>) => toolApi.test(id, parameters).then(res => res.data),
  generateTool: (data: { description: string; category?: string }) => toolApi.generate(data).then(res => res.data),
  registerTool: (data: { code: string; category?: string }) => toolApi.register(data).then(res => res.data),

  // Settings
  getLLMSettings: () => settingsApi.getLLMSettings().then(res => res.data),
  getLLMSetting: (provider: string) => settingsApi.getLLMSetting(provider).then(res => res.data),
  createLLMSetting: (data: Partial<LLMSetting> & { api_key?: string }) => settingsApi.createLLMSetting(data).then(res => res.data),
  updateLLMSetting: (provider: string, data: Partial<LLMSetting> & { api_key?: string }) => settingsApi.updateLLMSetting(provider, data).then(res => res.data),
  deleteLLMSetting: (provider: string) => settingsApi.deleteLLMSetting(provider).then(res => res.data),
  getAvailableModels: (provider: string) => settingsApi.getAvailableModels(provider).then(res => res.data),
  testLLMConnection: (provider: string, data?: any) => settingsApi.testConnection(provider, data).then(res => res.data),
  getLLMProviders: () => settingsApi.getProviders().then(res => res.data),

  // Task Analysis
  analyzeTask: (data: { task_description: string; provider?: string }) => taskAnalysisApi.analyze(data).then(res => res.data),
  recommendToolsForTask: (data: { task_description: string; provider?: string }) => taskAnalysisApi.recommendTools(data).then(res => res.data),

  // Approvals
  getApprovals: (params?: { agent_id?: number; status?: string }) => approvalsApi.getApprovals(params).then(res => res.data),
  getApproval: (id: number) => approvalsApi.getApproval(id).then(res => res.data),
  createApprovalRequest: (data: { agent_id: number; task_id?: number; tools: string[]; reason: string }) => approvalsApi.createApprovalRequest(data).then(res => res.data),
  approveToolRequest: (id: number, note?: string) => approvalsApi.approveRequest(id, note).then(res => res.data),
  rejectToolRequest: (id: number, note?: string) => approvalsApi.rejectRequest(id, note).then(res => res.data),
  getPendingApprovals: (agent_id?: number) => approvalsApi.getPendingRequests(agent_id).then(res => res.data),

  // Interactions
  getTaskInteractions: (taskId: number, params?: { type?: string; limit?: number; since?: number }) => interactionApi.getInteractions(taskId, params).then(res => res.data),
  respondToInteraction: (taskId: number, interactionId: number, data: InteractionRespondRequest) => interactionApi.respondToInteraction(taskId, interactionId, data).then(res => res.data),
  getPendingInteractions: (taskId: number) => interactionApi.getPendingInteractions(taskId).then(res => res.data),
  sendUserMessage: (taskId: number, message: string) => interactionApi.sendUserMessage(taskId, message).then(res => res.data),
}

export default api
