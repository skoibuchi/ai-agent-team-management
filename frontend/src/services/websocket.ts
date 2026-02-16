import { io, Socket } from 'socket.io-client'
import type {
  TaskStartedEvent,
  TaskProgressEvent,
  TaskCompletedEvent,
  TaskFailedEvent,
  AgentStatusChangedEvent,
  LogMessageEvent,
} from '@/types'

class WebSocketService {
  private socket: Socket | null = null
  private listeners: Map<string, Set<Function>> = new Map()

  connect() {
    if (this.socket?.connected) {
      console.log('[WebSocket] Already connected')
      return
    }

    // 既存のソケットがあれば削除
    if (this.socket) {
      this.socket.removeAllListeners()
      this.socket.close()
      this.socket = null
    }

    console.log('[WebSocket] Connecting to server...')
    
    this.socket = io('http://localhost:5000', {
      transports: ['polling', 'websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000,
      forceNew: true,
    })

    this.socket.on('connect', () => {
      console.log('[WebSocket] Connected successfully')
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[WebSocket] Disconnected:', reason)
    })

    this.socket.on('connect_error', (error) => {
      console.error('[WebSocket] Connection error:', error.message)
    })

    this.socket.on('error', (error) => {
      console.error('[WebSocket] Error:', error)
    })

    // Task events
    this.socket.on('task_started', (data: TaskStartedEvent) => {
      this.emit('task_started', data)
    })

    this.socket.on('task_progress', (data: TaskProgressEvent) => {
      this.emit('task_progress', data)
    })

    this.socket.on('task_completed', (data: TaskCompletedEvent) => {
      this.emit('task_completed', data)
    })

    this.socket.on('task_failed', (data: TaskFailedEvent) => {
      this.emit('task_failed', data)
    })

    // Agent events
    this.socket.on('agent_status_changed', (data: AgentStatusChangedEvent) => {
      this.emit('agent_status_changed', data)
    })

    // Log events
    this.socket.on('log_message', (data: LogMessageEvent) => {
      this.emit('log_message', data)
    })

    // Task interaction events
    this.socket.on('task_interaction_new', (data: any) => {
      this.emit('task_interaction_new', data)
    })
  }

  getSocket(): Socket | null {
    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  joinTask(taskId: number) {
    this.socket?.emit('join_task', { task_id: taskId })
  }

  leaveTask(taskId: number) {
    this.socket?.emit('leave_task', { task_id: taskId })
  }

  joinAgent(agentId: number) {
    this.socket?.emit('join_agent', { agent_id: agentId })
  }

  leaveAgent(agentId: number) {
    this.socket?.emit('leave_agent', { agent_id: agentId })
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback: Function) {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.delete(callback)
    }
  }

  private emit(event: string, data: any) {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.forEach((callback) => callback(data))
    }
  }
}

export const websocketService = new WebSocketService()
export default websocketService
