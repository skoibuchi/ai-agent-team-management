/**
 * タスクインタラクション関連の型定義
 */

export type InteractionType =
  | 'agent_thinking'
  | 'tool_call'
  | 'tool_result'
  | 'question'
  | 'user_response'
  | 'info'
  | 'error'
  | 'result';

export interface TaskInteraction {
  id: number;
  task_id: number;
  interaction_type: InteractionType;
  content: string;
  metadata?: Record<string, any>;
  requires_response: boolean;
  response?: string;
  created_at: string;
  responded_at?: string;
}

export interface TaskInteractionResponse {
  task_id: number;
  interactions: TaskInteraction[];
}

export interface PendingInteractionsResponse {
  task_id: number;
  pending_interactions: TaskInteraction[];
}

export interface InteractionRespondRequest {
  response: string;
}
