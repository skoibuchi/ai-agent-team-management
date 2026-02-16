import { create } from 'zustand'
import type { Agent, Task, Tool, LLMSetting } from '@/types'
import { api } from '@/services/api'

interface AppState {
  // Agents
  agents: Agent[]
  selectedAgent: Agent | null
  setAgents: (agents: Agent[]) => void
  setSelectedAgent: (agent: Agent | null) => void
  addAgent: (agent: Agent) => void
  updateAgent: (id: number, agent: Partial<Agent>) => void
  removeAgent: (id: number) => void
  fetchAgents: () => Promise<void>

  // Tasks
  tasks: Task[]
  selectedTask: Task | null
  setTasks: (tasks: Task[]) => void
  setSelectedTask: (task: Task | null) => void
  addTask: (task: Task) => void
  updateTask: (id: number, task: Partial<Task>) => void
  removeTask: (id: number) => void
  fetchTasks: () => Promise<void>

  // Tools
  tools: Tool[]
  setTools: (tools: Tool[]) => void
  addTool: (tool: Tool) => void
  updateTool: (id: number, tool: Partial<Tool>) => void
  removeTool: (id: number) => void
  fetchTools: () => Promise<void>

  // LLM Settings
  llmSettings: LLMSetting[]
  setLLMSettings: (settings: LLMSetting[]) => void
  addLLMSetting: (setting: LLMSetting) => void
  updateLLMSetting: (provider: string, setting: Partial<LLMSetting>) => void
  removeLLMSetting: (provider: string) => void
  fetchLLMSettings: () => Promise<void>

  // UI State
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  loading: boolean
  error: string | null
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useStore = create<AppState>((set) => ({
  // Agents
  agents: [],
  selectedAgent: null,
  setAgents: (agents) => set({ agents }),
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  addAgent: (agent) => set((state) => ({ agents: [...state.agents, agent] })),
  updateAgent: (id, updatedAgent) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === id ? { ...agent, ...updatedAgent } : agent
      ),
    })),
  removeAgent: (id) =>
    set((state) => ({
      agents: state.agents.filter((agent) => agent.id !== id),
    })),
  fetchAgents: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.getAgents()
      set({ agents: response.data || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  // Tasks
  tasks: [],
  selectedTask: null,
  setTasks: (tasks) => set({ tasks }),
  setSelectedTask: (task) => set({ selectedTask: task }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (id, updatedTask) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === id ? { ...task, ...updatedTask } : task
      ),
    })),
  removeTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== id),
    })),
  fetchTasks: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.getTasks()
      set({ tasks: response.data || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  // Tools
  tools: [],
  setTools: (tools) => set({ tools }),
  addTool: (tool) => set((state) => ({ tools: [...state.tools, tool] })),
  updateTool: (id, updatedTool) =>
    set((state) => ({
      tools: state.tools.map((tool) =>
        tool.id === id ? { ...tool, ...updatedTool } : tool
      ),
    })),
  removeTool: (id) =>
    set((state) => ({
      tools: state.tools.filter((tool) => tool.id !== id),
    })),
  fetchTools: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.getTools()
      set({ tools: response.data || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  // LLM Settings
  llmSettings: [],
  setLLMSettings: (settings) => set({ llmSettings: settings }),
  addLLMSetting: (setting) =>
    set((state) => ({ llmSettings: [...state.llmSettings, setting] })),
  updateLLMSetting: (provider, updatedSetting) =>
    set((state) => ({
      llmSettings: state.llmSettings.map((setting) =>
        setting.provider === provider ? { ...setting, ...updatedSetting } : setting
      ),
    })),
  removeLLMSetting: (provider) =>
    set((state) => ({
      llmSettings: state.llmSettings.filter((setting) => setting.provider !== provider),
    })),
  fetchLLMSettings: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.getLLMSettings()
      set({ llmSettings: response.data || [], loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  // UI State
  sidebarOpen: true,
  theme: 'light',
  loading: false,
  error: null,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))

export default useStore
