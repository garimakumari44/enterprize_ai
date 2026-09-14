export interface ToolDefinition {
  id: string;

  name: string;

  description: string;

  inputSchema?: object;

  outputSchema?: object;
}