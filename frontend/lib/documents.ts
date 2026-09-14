import authApi from "./api";

// ============================================================
// Types
// ============================================================

export interface DocumentUploadResponse {
  document_id: string;
  job_id?: string | null;
  status: string;
  message?: string;
}

export interface DocumentResponse {
  id: string;
  name: string;
  filename?: string;
  content_type?: string;
  size?: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface DocumentListResponse {
  items: DocumentResponse[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface ProcessingRequest {
  document_id: string;
  force?: boolean;
}

export interface ProcessingStatusResponse {
  processing_id: string;
  document_id: string;
  document_version_id?: string;
  status: string;
  current_stage?: string | null;
  progress?: number;
  error?: string | null;
  steps?: unknown[];
  extraction?: unknown;
  validation?: unknown;
  intelligence?: unknown;
  review?: unknown;
  completed_at?: string | null;
}

export interface ProcessingStartResponse {
  processing_id: string;
  document_id: string;
  document_version_id?: string;
  status: string;
  current_stage?: string | null;
  progress?: number;
  error?: string | null;
  steps?: unknown[];
}

// ============================================================
// Upload Document
// ============================================================

export async function uploadDocument(
  file: File
): Promise<DocumentUploadResponse> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await authApi.post<DocumentUploadResponse>(
    "/documents",
    formData
  );

  return response.data;
}

// ============================================================
// Start Processing
// ============================================================

export async function startDocumentProcessing(
  documentId: string,
  force: boolean = false
): Promise<ProcessingStartResponse> {
  const payload: ProcessingRequest = {
    document_id: documentId,
    force,
  };

  const response = await authApi.post<ProcessingStartResponse>(
    "/processing/jobs",
    payload
  );

  return response.data;
}

// ============================================================
// Upload + Start Processing
// ============================================================

export async function uploadAndProcessDocument(
  file: File,
  force: boolean = false
): Promise<{
  upload: DocumentUploadResponse;
  processing: ProcessingStartResponse;
}> {
  const upload = await uploadDocument(file);

  const processing = await startDocumentProcessing(
    upload.document_id,
    force
  );

  return {
    upload,
    processing,
  };
}

// ============================================================
// Get All Documents
// ============================================================

export async function getDocuments(
  page: number = 1,
  pageSize: number = 20
): Promise<DocumentListResponse> {
  try {
    const response = await authApi.get<DocumentListResponse>(
      "/documents",
      {
        params: {
          page,
          page_size: pageSize,
        },
      }
    );

    return response.data;
  } catch (error: any) {
    console.error("========================================");
    console.error("GET /documents FAILED");
    console.error("========================================");
    console.error("Status:", error?.response?.status);
    console.error("Response:", error?.response?.data);
    console.error("URL:", error?.config?.url);
    console.error("Params:", error?.config?.params);
    console.error("========================================");

    throw error;
  }
}

// ============================================================
// Get Single Document
// ============================================================

export async function getDocument(
  documentId: string
): Promise<DocumentResponse> {
  const response = await authApi.get<DocumentResponse>(
    `/documents/${documentId}`
  );

  return response.data;
}

// ============================================================
// Delete Document
// ============================================================

export async function deleteDocument(
  documentId: string
): Promise<void> {
  await authApi.delete(`/documents/${documentId}`);
}

// ============================================================
// Get Processing Status
// ============================================================

export async function getProcessingStatus(
  processingId: string
): Promise<ProcessingStatusResponse> {
  const response =
    await authApi.get<ProcessingStatusResponse>(
      `/processing/jobs/${processingId}`
    );

  return response.data;
}

// ============================================================
// Cancel Processing
// ============================================================

export async function cancelDocumentProcessing(
  processingId: string
): Promise<ProcessingStatusResponse> {
  const response =
    await authApi.post<ProcessingStatusResponse>(
      `/processing/jobs/${processingId}/cancel`
    );

  return response.data;
}

// ============================================================
// Get Processing Result
// ============================================================

export async function getProcessingResult(
  processingId: string
): Promise<unknown> {
  const response = await authApi.get(
    `/processing/jobs/${processingId}/result`
  );

  return response.data;
}

// ============================================================
// Download Document
// ============================================================

export async function downloadDocument(
  documentId: string
): Promise<Blob> {
  const response = await authApi.get(
    `/documents/${documentId}/download`,
    {
      responseType: "blob",
    }
  );

  return response.data;
}

// ============================================================
// Create Browser Download
// ============================================================

export async function saveDocumentToBrowser(
  documentId: string,
  filename: string
): Promise<void> {
  const blob = await downloadDocument(documentId);

  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}