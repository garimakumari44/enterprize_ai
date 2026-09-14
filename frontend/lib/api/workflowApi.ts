/* =========================================================
   WORKFLOW + DOCUMENT API

   Frontend API client for:

   Workflow:
       GET    /api/v1/workflows
       POST   /api/v1/workflows
       GET    /api/v1/workflows/{workflow_id}
       PATCH  /api/v1/workflows/{workflow_id}
       DELETE /api/v1/workflows/{workflow_id}

   Documents:
       GET /api/v1/documents

   Responsibilities:
       - Workflow APIs
       - Document library APIs
       - Backend -> frontend normalization
       - Frontend -> backend payload transformation

   NOT responsible for:
       - Processing jobs
       - Execution
       - Processing intelligence
       - Validation
       - Reviews

   Shared HTTP handling:
       lib/api/client.ts
========================================================= */

import {
  request,
  ApiError,
} from "./client";

import type {
  WorkflowDefinition,
  WorkflowNode,
  WorkflowOperation,
  WorkflowType,
  WorkflowNodeType,
  WorkflowNodeConfig,
  LibraryDocument,
} from "../../types/workflow";


/* =========================================================
   BACKWARD-COMPATIBLE ERROR
========================================================= */

export class WorkflowApiError extends ApiError {
  constructor(
    message: string,
    status: number,
    responseBody?: unknown,
  ) {
    super(
      message,
      status,
      responseBody,
    );

    this.name = "WorkflowApiError";

    Object.setPrototypeOf(
      this,
      WorkflowApiError.prototype,
    );
  }
}


/* =========================================================
   TYPE RE-EXPORTS

   Existing components that import these types from
   workflowApi.ts will continue to work.

   There is still only ONE actual type definition.
========================================================= */

export type {
  WorkflowDefinition,
  WorkflowNode,
  WorkflowOperation,
  WorkflowType,
  WorkflowNodeType,
  WorkflowNodeConfig,
  LibraryDocument,
};


/* =========================================================
   BACKEND WORKFLOW RESPONSE
========================================================= */

interface BackendWorkflow {
  id: string;

  name: string;

  description?: string | null;

  workflow_type?: string | null;

  is_active?: boolean | null;

  config?: Record<
    string,
    unknown
  > | null;

  created_at?: string | null;

  updated_at?: string | null;

  [key: string]: unknown;
}


/* =========================================================
   WORKFLOW TYPE GUARDS
========================================================= */

function isWorkflowType(
  value: unknown,
): value is WorkflowType {
  return (
    value === "document_processing" ||
    value === "knowledge" ||
    value === "ai" ||
    value === "automation"
  );
}


function isWorkflowNodeType(
  value: unknown,
): value is WorkflowNodeType {
  return (
    value === "input" ||
    value === "document_processing" ||
    value === "transformation" ||
    value === "ai" ||
    value === "knowledge" ||
    value === "logic" ||
    value === "output"
  );
}


function isWorkflowOperation(
  value: unknown,
): value is WorkflowOperation {
  return (
    value === "library_document" ||
    value === "ocr" ||
    value === "text_extraction" ||
    value === "document_classification" ||
    value === "document_splitting" ||
    value === "chunking" ||
    value === "cleaning" ||
    value === "normalization" ||
    value === "extraction" ||
    value === "summarization" ||
    value === "classification" ||
    value === "ai_model" ||
    value === "embedding" ||
    value === "vector_store" ||
    value === "index" ||
    value === "condition" ||
    value === "validation" ||
    value === "human_review" ||
    value === "save_result" ||
    value === "export" ||
    value === "webhook"
  );
}


/* =========================================================
   NORMALIZE NODE
========================================================= */

function normalizeWorkflowNode(
  value: unknown,
  index: number,
): WorkflowNode {
  const raw =
    value &&
    typeof value === "object" &&
    !Array.isArray(value)
      ? value as Record<string, unknown>
      : {};

  const rawOperation =
    raw.operation;

  const operation: WorkflowOperation =
    isWorkflowOperation(rawOperation)
      ? rawOperation
      : "ai_model";

  const rawType =
    raw.type;

  const type: WorkflowNodeType =
    isWorkflowNodeType(rawType)
      ? rawType
      : "ai";

  const id =
    typeof raw.id === "string" &&
    raw.id.trim().length > 0
      ? raw.id
      : `node-${index}`;

  const label =
    typeof raw.label === "string" &&
    raw.label.trim().length > 0
      ? raw.label
      : operation;

  const description =
    typeof raw.description === "string"
      ? raw.description
      : "";

  const config =
    raw.config &&
    typeof raw.config === "object" &&
    !Array.isArray(raw.config)
      ? raw.config as WorkflowNodeConfig
      : {};

  return {
    id,
    type,
    operation,
    label,
    description,
    config,
  };
}


/* =========================================================
   NORMALIZE WORKFLOW FROM BACKEND
========================================================= */

function normalizeWorkflowFromBackend(
  workflow: BackendWorkflow,
): WorkflowDefinition {
  const config =
    workflow.config &&
    typeof workflow.config === "object" &&
    !Array.isArray(workflow.config)
      ? workflow.config
      : {};

  const backendNodes =
    Array.isArray(config.nodes)
      ? config.nodes
      : [];

  const nodes =
    backendNodes.map(
      normalizeWorkflowNode,
    );

  const workflowType =
    isWorkflowType(
      workflow.workflow_type,
    )
      ? workflow.workflow_type
      : "document_processing";

  return {
    id:
      typeof workflow.id === "string"
        ? workflow.id
        : undefined,

    name:
      typeof workflow.name === "string" &&
      workflow.name.trim().length > 0
        ? workflow.name.trim()
        : "Untitled Workflow",

    description:
      typeof workflow.description === "string"
        ? workflow.description
        : "",

    workflow_type:
      workflowType,

    enabled:
      Boolean(
        workflow.is_active,
      ),

    nodes,

    config,
  };
}


/* =========================================================
   WORKFLOW PAYLOAD
========================================================= */

function buildWorkflowPayload(
  workflow: WorkflowDefinition,
): Record<string, unknown> {
  const nodes =
    Array.isArray(workflow.nodes)
      ? workflow.nodes
      : [];

  const existingConfig =
    workflow.config &&
    typeof workflow.config === "object" &&
    !Array.isArray(workflow.config)
      ? workflow.config
      : {};

  return {
    name:
      workflow.name.trim() ||
      "Untitled Workflow",

    description:
      typeof workflow.description === "string"
        ? workflow.description
        : "",

    workflow_type:
      workflow.workflow_type ||
      "document_processing",

    is_active:
      Boolean(workflow.enabled),

    config: {
      ...existingConfig,
      nodes,
    },
  };
}


/* =========================================================
   GET WORKFLOWS
========================================================= */

export async function getWorkflows(): Promise<
  WorkflowDefinition[]
> {
  const result =
    await request<BackendWorkflow[]>(
      "/workflows",
      {
        method: "GET",
      },
    );

  if (!Array.isArray(result)) {
    return [];
  }

  return result.map(
    normalizeWorkflowFromBackend,
  );
}


/* =========================================================
   GET SINGLE WORKFLOW
========================================================= */

export async function getWorkflow(
  workflowId: string,
): Promise<WorkflowDefinition> {
  const normalizedId =
    workflowId.trim();

  if (!normalizedId) {
    throw new Error(
      "workflowId is required.",
    );
  }

  const result =
    await request<BackendWorkflow>(
      `/workflows/${encodeURIComponent(
        normalizedId,
      )}`,
      {
        method: "GET",
      },
    );

  return normalizeWorkflowFromBackend(
    result,
  );
}


/* =========================================================
   CREATE WORKFLOW
========================================================= */

export async function createWorkflow(
  workflow: WorkflowDefinition,
): Promise<WorkflowDefinition> {
  const payload =
    buildWorkflowPayload(
      workflow,
    );

  const result =
    await request<BackendWorkflow>(
      "/workflows",
      {
        method: "POST",

        body:
          JSON.stringify(
            payload,
          ),
      },
    );

  return normalizeWorkflowFromBackend(
    result,
  );
}


/* =========================================================
   UPDATE WORKFLOW
========================================================= */

export async function updateWorkflow(
  workflowId: string,
  workflow: WorkflowDefinition,
): Promise<WorkflowDefinition> {
  const normalizedId =
    workflowId.trim();

  if (!normalizedId) {
    throw new Error(
      "workflowId is required.",
    );
  }

  const payload =
    buildWorkflowPayload(
      workflow,
    );

  const result =
    await request<BackendWorkflow>(
      `/workflows/${encodeURIComponent(
        normalizedId,
      )}`,
      {
        method: "PATCH",

        body:
          JSON.stringify(
            payload,
          ),
      },
    );

  return normalizeWorkflowFromBackend(
    result,
  );
}


/* =========================================================
   DELETE WORKFLOW
========================================================= */

export async function deleteWorkflow(
  workflowId: string,
): Promise<void> {
  const normalizedId =
    workflowId.trim();

  if (!normalizedId) {
    throw new Error(
      "workflowId is required.",
    );
  }

  await request<void>(
    `/workflows/${encodeURIComponent(
      normalizedId,
    )}`,
    {
      method: "DELETE",
    },
  );
}


/* =========================================================
   NORMALIZE LIBRARY DOCUMENT
========================================================= */

function normalizeLibraryDocument(
  document: Record<
    string,
    unknown
  >,
): LibraryDocument {
  const id =
    typeof document.id === "string"
      ? document.id
      : typeof document.document_id === "string"
        ? document.document_id
        : "";

  const filename =
    typeof document.filename === "string"
      ? document.filename
      : typeof document.file_name === "string"
        ? document.file_name
        : undefined;

  const name =
    typeof document.name === "string"
      ? document.name
      : filename;

  return {
    ...document,

    id,

    name,

    filename,
  };
}


/* =========================================================
   NORMALIZE DOCUMENT ARRAY
========================================================= */

function normalizeDocumentArray(
  items: unknown[],
): LibraryDocument[] {
  return items
    .filter(
      (
        item,
      ): item is Record<
        string,
        unknown
      > =>
        typeof item === "object" &&
        item !== null &&
        !Array.isArray(item),
    )
    .map(
      normalizeLibraryDocument,
    )
    .filter(
      document =>
        document.id.length > 0,
    );
}


/* =========================================================
   GET LIBRARY DOCUMENTS
========================================================= */

export async function getLibraryDocuments(): Promise<
  LibraryDocument[]
> {
  const result =
    await request<unknown>(
      "/documents",
      {
        method: "GET",
      },
    );

  /* -------------------------------------------------------
     Plain array
  ------------------------------------------------------- */

  if (Array.isArray(result)) {
    return normalizeDocumentArray(
      result,
    );
  }


  /* -------------------------------------------------------
     Object response
  ------------------------------------------------------- */

  if (
    typeof result === "object" &&
    result !== null
  ) {
    const body =
      result as Record<
        string,
        unknown
      >;

    if (Array.isArray(body.items)) {
      return normalizeDocumentArray(
        body.items,
      );
    }

    if (
      Array.isArray(
        body.documents,
      )
    ) {
      return normalizeDocumentArray(
        body.documents,
      );
    }

    if (
      Array.isArray(
        body.results,
      )
    ) {
      return normalizeDocumentArray(
        body.results,
      );
    }
  }

  return [];
}


/* =========================================================
   PUBLIC EXPORTS
========================================================= */

export {
  request,
};