/* =========================================================
   WORKFLOW DOMAIN TYPES

   Single source of truth for frontend workflow types.

   IMPORTANT:
   Do not redefine WorkflowDefinition / WorkflowNode inside
   API modules. Import these types from this file instead.
========================================================= */


/* =========================================================
   WORKFLOW NODE TYPE
========================================================= */

export type WorkflowNodeType =
  | "input"
  | "document_processing"
  | "transformation"
  | "ai"
  | "knowledge"
  | "logic"
  | "output";


/* =========================================================
   WORKFLOW OPERATION
========================================================= */

export type WorkflowOperation =
  | "library_document"
  | "ocr"
  | "text_extraction"
  | "document_classification"
  | "document_splitting"
  | "chunking"
  | "cleaning"
  | "normalization"
  | "extraction"
  | "summarization"
  | "classification"
  | "ai_model"
  | "embedding"
  | "vector_store"
  | "index"
  | "condition"
  | "validation"
  | "human_review"
  | "save_result"
  | "export"
  | "webhook";


/* =========================================================
   WORKFLOW TYPE
========================================================= */

export type WorkflowType =
  | "document_processing"
  | "knowledge"
  | "ai"
  | "automation";


/* =========================================================
   WORKFLOW NODE CONFIG
========================================================= */

export interface WorkflowNodeConfig {
  [key: string]: unknown;
}


/* =========================================================
   LIBRARY DOCUMENT NODE CONFIG
========================================================= */

export interface LibraryDocumentNodeConfig
  extends WorkflowNodeConfig {
  document_id?: string;
}


/* =========================================================
   WORKFLOW NODE
========================================================= */

export interface WorkflowNode {
  id: string;

  type: WorkflowNodeType;

  operation: WorkflowOperation;

  label: string;

  description: string;

  config: WorkflowNodeConfig;
}


/* =========================================================
   WORKFLOW DEFINITION
========================================================= */

export interface WorkflowDefinition {
  /**
   * Existing workflows have an ID.
   * New workflows may not have one yet.
   */
  id?: string;

  /**
   * Workflow display name.
   */
  name: string;

  /**
   * Workflow description.
   */
  description: string;

  /**
   * High-level workflow category.
   */
  workflow_type: WorkflowType;

  /**
   * Ordered workflow nodes.
   */
  nodes: WorkflowNode[];

  /**
   * Whether the workflow is enabled.
   */
  enabled?: boolean;

  /**
   * Backend configuration that is not directly represented
   * by the frontend workflow fields.
   *
   * Nodes are persisted inside config.nodes.
   */
  config?: WorkflowNodeConfig;
}


/* =========================================================
   LIBRARY DOCUMENT
========================================================= */

export interface LibraryDocument {
  id: string;

  name?: string;

  filename?: string;

  document_id?: string;

  document_version_id?: string;

  mime_type?: string;

  content_type?: string;

  file_name?: string;

  status?: string;

  created_at?: string;

  updated_at?: string;

  size?: number;

  [key: string]: unknown;
}


/* =========================================================
   PROCESSING JOB
========================================================= */

export type ProcessingJobStatus =
  | "queued"
  | "running"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | string;


/**
 * Backend processing job.
 *
 * Some API implementations may return optional/null fields,
 * so the fields that are not guaranteed by the backend are
 * represented accordingly.
 */
export interface ProcessingJob {
  /**
   * Canonical processing/job identifier.
   */
  processing_id?: string | null;

  /**
   * Document being processed.
   */
  document_id?: string | null;

  /**
   * Immutable document version being processed.
   */
  document_version_id?: string | null;

  /**
   * Workflow used for processing.
   */
  workflow_id?: string | null;

  /**
   * Current processing state.
   */
  status?: ProcessingJobStatus | null;

  /**
   * Human-readable backend message.
   */
  message?: string | null;

  /**
   * Progress percentage.
   */
  progress?: number | null;

  /**
   * Creation timestamp.
   */
  created_at?: string | null;

  /**
   * Completion timestamp.
   */
  completed_at?: string | null;

  /**
   * Processing error.
   */
  error?: string | null;
}