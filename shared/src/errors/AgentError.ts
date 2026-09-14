import { BaseError } from "./BaseError";

export class AgentError extends BaseError {
  constructor(message: string) {
    super(message, "AGENT_ERROR");
  }
}