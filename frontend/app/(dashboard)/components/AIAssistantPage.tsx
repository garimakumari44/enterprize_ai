
"use client";

import { useEffect, useRef, useState } from "react";
import {
  Send,
  Bot,
  User,
  FileText,
  Sparkles,
  Plus,
  MessageSquare,
} from "lucide-react";

import { useAssistant } from "@/app/hooks/useAssistant";

export function AIAssistantPage() {
  const {
    messages,
    sessions,
    currentSessionId,
    loading,
    loadingSessions,
    error,
    sendMessage,
    createSession,
    openSession,
  } = useAssistant();

  const [input, setInput] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  /*
   * Scroll to the latest message whenever messages or loading state changes.
   */
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  /*
   * Send a message.
   */
  const send = async (text: string) => {
    const trimmed = text.trim();

    if (!trimmed || loading) {
      return;
    }

    setInput("");

    await sendMessage(trimmed);
  };

  /*
   * Create a new conversation.
   */
  const handleNewChat = async () => {
    if (loading) {
      return;
    }

    await createSession();
  };

  /*
   * -------------------------------------------------------------------------
   * Stable React keys
   * -------------------------------------------------------------------------
   *
   * Backend data should ideally always contain unique IDs.
   *
   * These helpers prevent React warnings if the backend temporarily returns
   * a missing or duplicate ID.
   */

  const sessionKeys = new Set<string>();

  const getSessionKey = (
    session: (typeof sessions)[number],
    index: number,
  ) => {
    const rawId =
      session?.id !== undefined && session?.id !== null
        ? String(session.id).trim()
        : "";

    const baseKey = rawId || `session-${index}`;

    if (!sessionKeys.has(baseKey)) {
      sessionKeys.add(baseKey);
      return baseKey;
    }

    return `${baseKey}-${index}`;
  };

  const messageKeys = new Set<string>();

  const getMessageKey = (
    message: (typeof messages)[number],
    index: number,
  ) => {
    const rawId =
      message?.id !== undefined && message?.id !== null
        ? String(message.id).trim()
        : "";

    const baseKey = rawId || `message-${index}`;

    if (!messageKeys.has(baseKey)) {
      messageKeys.add(baseKey);
      return baseKey;
    }

    return `${baseKey}-${index}`;
  };

  return (
    <div className="flex h-[calc(100vh-140px)] min-h-0 gap-4 animate-fade-in">
      {/* ============================================================
          SESSION SIDEBAR
      ============================================================ */}

      <aside className="flex w-64 shrink-0 flex-col rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        {/* Header */}

        <div className="border-b border-slate-200 p-3 dark:border-slate-800">
          <button
            type="button"
            onClick={handleNewChat}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-slate-900 to-slate-800 px-3 py-2.5 text-sm font-medium text-white transition hover:from-slate-800 hover:to-slate-700 disabled:opacity-50 dark:from-cyan-500 dark:to-teal-500 dark:hover:from-cyan-400 dark:hover:to-teal-400"
          >
            <Plus size={16} />
            New conversation
          </button>
        </div>

        {/* Sessions */}

        <div className="flex-1 overflow-y-auto p-2">
          {loadingSessions ? (
            <div className="space-y-2 p-2">
              {[0, 1, 2].map((item) => (
                <div
                  key={`session-loading-${item}`}
                  className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-4 py-10 text-center">
              <MessageSquare
                size={24}
                className="mb-2 text-slate-300 dark:text-slate-600"
              />

              <p className="text-xs text-slate-400">
                No conversations yet.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session, index) => {
                const sessionKey = getSessionKey(session, index);

                const active =
                  session.id !== undefined &&
                  session.id !== null &&
                  String(session.id) === String(currentSessionId);

                return (
                  <button
                    type="button"
                    key={sessionKey}
                    onClick={() => {
                      if (
                        session.id !== undefined &&
                        session.id !== null
                      ) {
                        openSession(session.id);
                      }
                    }}
                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                      active
                        ? "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300"
                        : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800"
                    }`}
                  >
                    <MessageSquare
                      size={15}
                      className="shrink-0"
                    />

                    <span className="truncate">
                      {session.title || "New conversation"}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </aside>

      {/* ============================================================
          MAIN ASSISTANT
      ============================================================ */}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Messages */}

        <div
          ref={scrollRef}
          className="flex-1 space-y-4 overflow-y-auto pr-1"
        >
          {/* Empty state */}

          {messages.length === 0 && !loading && (
            <div className="flex h-full flex-col items-center justify-center px-6 text-center">
              <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/20">
                <Bot size={28} />
              </div>

              <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                AI Assistant
              </h2>

              <p className="mt-1 max-w-md text-sm text-slate-400">
                Ask questions about your processed documents,
                workflows, invoices, contracts, resumes, and
                knowledge base.
              </p>
            </div>
          )}

          {/* Conversation messages */}

          {messages.map((msg, index) => {
            const messageKey = getMessageKey(msg, index);

            return (
              <div
                key={messageKey}
                className={`flex gap-3 ${
                  msg.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                {/* Avatar */}

                <div
                  className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-slate-700 to-slate-900 text-white dark:from-cyan-500 dark:to-teal-600"
                      : "bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/20"
                  }`}
                >
                  {msg.role === "user" ? (
                    <User size={16} />
                  ) : (
                    <Bot size={16} />
                  )}
                </div>

                {/* Message */}

                <div
                  className={`max-w-[80%] ${
                    msg.role === "user" ? "items-end" : ""
                  }`}
                >
                  <div
                    className={`whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-slate-900 text-white dark:bg-cyan-500"
                        : "border border-slate-200 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Citations */}

                  {msg.citations &&
                    msg.citations.length > 0 && (
                      <div className="mt-2 space-y-1.5">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          Citations
                        </span>

                        {msg.citations.map(
                          (citation, citationIndex) => {
                            const citationDoc =
                              citation?.doc
                                ? String(citation.doc)
                                : "Document";

                            const citationPage =
                              citation?.page !== undefined &&
                              citation?.page !== null
                                ? String(citation.page)
                                : "";

                            const citationKey = [
                              messageKey,
                              citationDoc,
                              citationPage,
                              citationIndex,
                            ].join("-");

                            return (
                              <div
                                key={citationKey}
                                className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-800/50"
                              >
                                <FileText
                                  size={13}
                                  className="shrink-0 text-cyan-500"
                                />

                                <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                                  {citation.doc ||
                                    "Document"}
                                </span>

                                {citation.page !==
                                  undefined &&
                                  citation.page !== null && (
                                    <span className="shrink-0 text-[10px] text-slate-400">
                                      p.{citation.page}
                                    </span>
                                  )}

                                {citation.excerpt && (
                                  <span className="truncate text-[11px] italic text-slate-400">
                                    "{citation.excerpt}"
                                  </span>
                                )}
                              </div>
                            );
                          },
                        )}
                      </div>
                    )}
                </div>
              </div>
            );
          })}

          {/* ============================================================
              TYPING INDICATOR
          ============================================================ */}

          {loading && (
            <div className="flex gap-3">
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/20">
                <Bot size={16} />
              </div>

              <div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
                {[0, 1, 2].map((i) => (
                  <span
                    key={`typing-${i}`}
                    className="h-1.5 w-1.5 rounded-full bg-cyan-500"
                    style={{
                      animation: `pulse 1s ease-in-out ${
                        i * 0.2
                      }s infinite`,
                    }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ============================================================
            ERROR
        ============================================================ */}

        {error && (
          <div className="mb-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400">
            {error}
          </div>
        )}

        {/* ============================================================
            SUGGESTIONS
        ============================================================ */}

        {messages.length === 0 && (
          <div className="py-3">
            <div className="mb-2 flex items-center gap-1.5 text-xs text-slate-400">
              <Sparkles size={13} />
              Try asking
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                "What documents have been processed recently?",
                "Which documents need human review?",
                "Summarize the latest processing activity",
                "What are the highest risk documents?",
              ].map((suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  onClick={() => send(suggestion)}
                  disabled={loading}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition-all hover:border-cyan-300 hover:bg-cyan-50 hover:text-cyan-700 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-cyan-700 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-300"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ============================================================
            INPUT
        ============================================================ */}

        <div className="border-t border-slate-200 pt-3 dark:border-slate-800">
          <div className="relative flex items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  send(input);
                }
              }}
              rows={1}
              disabled={loading}
              placeholder="Ask about your documents…"
              className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 transition-all focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />

            <button
              type="button"
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 text-white transition-all hover:from-slate-800 hover:to-slate-700 disabled:opacity-40 dark:from-cyan-500 dark:to-teal-500 dark:hover:from-cyan-400 dark:hover:to-teal-400"
            >
              <Send size={17} />
            </button>
          </div>

          <p className="mt-2 text-center text-[10px] text-slate-400">
            AI responses are generated by your backend Assistant
            service.
          </p>
        </div>
      </div>
    </div>
  );
}

