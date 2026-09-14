import type { ModelConfig } from "./model";

export interface AgentDefinition {
  id: string;

  name: string;

  description: string;

  systemPrompt: string;

  model: ModelConfig;

  tools: string[];

  memoryEnabled: boolean;

  maxIterations: number;
}