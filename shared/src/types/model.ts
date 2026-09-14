export interface ModelConfig {
  provider: string;
  model: string;

  temperature?: number;

  maxTokens?: number;
}