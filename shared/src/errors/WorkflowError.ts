import { BaseError } from "./BaseError";

export class WorkflowError extends BaseError {
  constructor(message: string) {
    super(message, "WORKFLOW_ERROR");
  }
}