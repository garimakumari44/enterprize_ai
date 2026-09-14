export const EVENTS = {
  AGENT_STARTED: "agent.started",
  AGENT_COMPLETED: "agent.completed",
  AGENT_FAILED: "agent.failed",

  TOOL_STARTED: "tool.started",
  TOOL_COMPLETED: "tool.completed",
  TOOL_FAILED: "tool.failed",

  WORKFLOW_STARTED: "workflow.started",
  WORKFLOW_COMPLETED: "workflow.completed",
  WORKFLOW_FAILED: "workflow.failed",
} as const;