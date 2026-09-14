export type DocumentStatus =
  | "pending"
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export type ProcessingStatus =
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export type ProcessingStepStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export type DocumentFileType =
  | "pdf"
  | "doc"
  | "docx"
  | "txt"
  | "md"
  | "csv"
  | "xls"
  | "xlsx"
  | "ppt"
  | "pptx"
  | "image"
  | "other";

// ============================================================
// Document
// ============================================================

export interface Document {
  id: string;

  name: string;

  filename: string;

  content_type: string;

  file_type: DocumentFileType;

  size: number;

  status: DocumentStatus;

  checksum?: string;

  storage_key?: string;

  mime_type?: string;

  created_at: string;

  updated_at: string;

  uploaded_at?: string;

  processed_at?: string | null;

  error_message?: string | null;
}

// ============================================================
// Document Upload
// ============================================================

export interface DocumentUpload {
  file: File;

  name?: string;
}

// ============================================================
// Upload Response
// ============================================================

export interface DocumentUploadResponse {
  document_id: string;

  job_id: string;

  status: DocumentStatus;

  message?: string;
}

// ============================================================
// Processing Job
// ============================================================

export interface ProcessingJob {
  id: string;

  document_id: string;

  status: ProcessingStatus;

  progress: number;

  current_step?: string | null;

  total_steps?: number;

  completed_steps?: number;

  message?: string | null;

  error?: string | null;

  started_at?: string | null;

  completed_at?: string | null;

  created_at: string;

  updated_at: string;
}

// ============================================================
// Processing Step
// ============================================================

export interface ProcessingStep {
  id: string;

  job_id: string;

  name: string;

  status: ProcessingStepStatus;

  progress: number;

  message?: string | null;

  error?: string | null;

  started_at?: string | null;

  completed_at?: string | null;
}

// ============================================================
// Document List
// ============================================================

export interface DocumentListResponse {
  items: Document[];

  total: number;

  page: number;

  page_size: number;

  total_pages?: number;
}

// ============================================================
// Document Detail
// ============================================================

export interface DocumentDetail extends Document {
  processing_job?: ProcessingJob | null;

  processing_steps?: ProcessingStep[];
}

// ============================================================
// Processing Status Response
// ============================================================

export interface ProcessingStatusResponse {
  job_id: string;

  document_id: string;

  status: ProcessingStatus;

  progress: number;

  current_step?: string | null;

  message?: string | null;

  error?: string | null;

  started_at?: string | null;

  completed_at?: string | null;
}

// ============================================================
// Document Filters
// ============================================================

export interface DocumentFilters {
  search?: string;

  status?: DocumentStatus;

  file_type?: DocumentFileType;

  page?: number;

  page_size?: number;
}

// ============================================================
// Pagination
// ============================================================

export interface PaginationParams {
  page?: number;

  page_size?: number;
}

// ============================================================
// Generic API Message
// ============================================================

export interface DocumentApiMessage {
  message: string;
}

// ============================================================
// Delete Response
// ============================================================

export interface DocumentDeleteResponse {
  message: string;

  document_id: string;
}