import { BaseError } from "./BaseError";

export class ToolError extends BaseError {
  constructor(message: string) {
    super(message, "TOOL_ERROR");
  }
}