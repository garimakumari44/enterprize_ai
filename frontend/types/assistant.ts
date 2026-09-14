// frontend/types/assistant.ts

export type AssistantRole = "user" | "assistant" | "system";

export interface Citation {
  doc: string;
  page?: number;
  excerpt?: string;
}

export interface ChatMessage {
  id: string;
  role: AssistantRole;
  content: string;
  citations?: Citation[];
  created_at?: string;
}

export interface AssistantRequest {
  session_id?: string | null;
  message: string;
  context?: Record<string, unknown> | null;
}

export interface AssistantResponse {
  session_id: string;
  message: ChatMessage;
}

export interface SessionCreate {
  title?: string | null;
}

export interface AssistantSession {
  id: string;
  title?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SessionResponse {
  id: string;
  title?: string | null;
  created_at?: string;
  updated_at?: string;
  messages?: ChatMessage[];
}

export interface AssistantState {
  messages: ChatMessage[];
  sessions: AssistantSession[];
  currentSessionId: string | null;
  loading: boolean;
  loadingSessions: boolean;
  error: string | null;
}