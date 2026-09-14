// frontend/hooks/useAssistant.ts

"use client";

import { useCallback, useEffect, useState } from "react";

import {
  createAssistantSession,
  getAssistantSession,
  getAssistantSessions,
  sendAssistantMessage,
} from "../../lib/assistant";

import type {
  AssistantSession,
  ChatMessage,
} from "../../types/assistant";

export function useAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<AssistantSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    null,
  );

  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load all existing sessions.
   */
  const loadSessions = useCallback(async () => {
    try {
      setLoadingSessions(true);
      setError(null);

      const data = await getAssistantSessions();

      setSessions(data);

      /*
       * If there is no active session but existing sessions are available,
       * automatically open the newest one.
       */
      if (!currentSessionId && data.length > 0) {
        const latest = data[0];

        setCurrentSessionId(latest.id);

        const session = await getAssistantSession(latest.id);

        setMessages(session.messages ?? []);
      }
    } catch (err) {
      console.error("Failed to load assistant sessions:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load assistant sessions.",
      );
    } finally {
      setLoadingSessions(false);
    }
  }, [currentSessionId]);

  /**
   * Create a new conversation.
   */
  const createSession = useCallback(async () => {
    try {
      setError(null);

      const session = await createAssistantSession();

      setSessions((prev) => [session, ...prev]);

      setCurrentSessionId(session.id);
      setMessages([]);

      return session;
    } catch (err) {
      console.error("Failed to create assistant session:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to create a new session.",
      );

      return null;
    }
  }, []);

  /**
   * Open an existing conversation.
   */
  const openSession = useCallback(async (sessionId: string) => {
    try {
      setError(null);
      setLoading(true);

      const session = await getAssistantSession(sessionId);

      setCurrentSessionId(session.id);
      setMessages(session.messages ?? []);
    } catch (err) {
      console.error("Failed to open assistant session:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to open assistant session.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Send a message to the backend.
   */
  const sendMessage = useCallback(
    async (
      content: string,
      context?: Record<string, unknown>,
    ) => {
      const trimmed = content.trim();

      if (!trimmed || loading) {
        return;
      }

      try {
        setError(null);
        setLoading(true);

        let sessionId = currentSessionId;

        /*
         * Automatically create a session if the user starts
         * chatting without one.
         */
        if (!sessionId) {
          const session = await createAssistantSession();

          sessionId = session.id;

          setCurrentSessionId(session.id);
          setSessions((prev) => [session, ...prev]);
        }

        const temporaryUserMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          role: "user",
          content: trimmed,
        };

        setMessages((prev) => [...prev, temporaryUserMessage]);

        const response = await sendAssistantMessage({
          session_id: sessionId,
          message: trimmed,
          context: context ?? null,
        });

        /*
         * The backend owns the authoritative assistant response.
         */
        if (response.message) {
          setMessages((prev) => [...prev, response.message]);
        }

        /*
         * Backend may return/create a different session ID.
         */
        if (response.session_id) {
          setCurrentSessionId(response.session_id);
        }

        return response;
      } catch (err) {
        console.error("Assistant request failed:", err);

        const message =
          err instanceof Error
            ? err.message
            : "The Assistant could not process your request.";

        setError(message);

        return null;
      } finally {
        setLoading(false);
      }
    },
    [currentSessionId, loading],
  );

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    messages,
    sessions,
    currentSessionId,

    loading,
    loadingSessions,
    error,

    sendMessage,
    createSession,
    openSession,
    loadSessions,
  };
}