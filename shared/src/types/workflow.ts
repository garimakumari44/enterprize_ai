export interface WorkflowStep {
  id: string;

  name: string;

  type: "agent" | "tool" | "condition";

  target: string;
}

export interface WorkflowDefinition {
  id: string;

  name: string;

  description?: string;

  steps: WorkflowStep[];
}