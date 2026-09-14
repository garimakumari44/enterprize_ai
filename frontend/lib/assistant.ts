import { authApi } from "./api"

import type {
  AssistantRequest,
  AssistantResponse,
  AssistantSession,
  SessionCreate,
  SessionResponse,
} from "../types/assistant";

// ============================================================
// SEND MESSAGE
// POST /api/v1/assistant/chat
// ============================================================

export async function sendAssistantMessage(
  request: AssistantRequest
): Promise<AssistantResponse> {
  const response = await authApi.post<AssistantResponse>(
    "/assistant/chat",
    request
  );

  return response.data;
}

// ============================================================
// CREATE SESSION
// POST /api/v1/assistant/sessions
// ============================================================

export async function createAssistantSession(
  request: SessionCreate = {}
): Promise<AssistantSession> {
  const response = await authApi.post<AssistantSession>(
    "/assistant/sessions",
    request
  );

  return response.data;
}

// ============================================================
// GET ALL SESSIONS
// GET /api/v1/assistant/sessions
// ============================================================

export async function getAssistantSessions(): Promise<
  AssistantSession[]
> {
  const response = await authApi.get<
    AssistantSession[] | { sessions: AssistantSession[] }
  >("/assistant/sessions");

  if (Array.isArray(response.data)) {
    return response.data;
  }

  return response.data.sessions;
}

// ============================================================
// GET SINGLE SESSION
// GET /api/v1/assistant/sessions/{session_id}
// ============================================================

export async function getAssistantSession(
  sessionId: string
): Promise<SessionResponse> {
  const response = await authApi.get<SessionResponse>(
    `/assistant/sessions/${encodeURIComponent(sessionId)}`
  );

  return response.data;
}

// ============================================================
// DELETE SESSION
// DELETE /api/v1/assistant/sessions/{session_id}
// ============================================================

export async function deleteAssistantSession(
  sessionId: string
): Promise<void> {
  await authApi.delete(
    `/assistant/sessions/${encodeURIComponent(sessionId)}`
  );
}