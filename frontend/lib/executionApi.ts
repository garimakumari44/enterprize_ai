
/* =========================================================
   EXECUTION / PROCESSING API
=========================================================

Frontend API client for execution and document processing.

Responsibilities
----------------
- Start processing jobs
- Read processing job state
- Read Document Intelligence results
- Download processing results

Backend endpoints
-----------------
POST /api/v1/processing/jobs
GET  /api/v1/processing/jobs/{processing_id}
GET  /api/v1/processing/jobs/{processing_id}/intelligence

Important behavior
------------------
- Processing job 404 => null
- Intelligence result 404 => null
- Other API errors are re-thrown
- 409 from intelligence remains a typed API error
- Intelligence download creates exactly one Blob

This module is intentionally independent from workflowApi.ts.
========================================================= */

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000/api/v1'
).replace(/\/+$/, '');


/* =========================================================
   ERROR
========================================================= */

export class ExecutionApiError extends Error {
  readonly status: number;

  readonly responseBody: unknown;

  constructor(
    message: string,
    status: number,
    responseBody?: unknown,
  ) {
    super(message);

    this.name = 'ExecutionApiError';

    this.status = status;

    this.responseBody = responseBody;

    Object.setPrototypeOf(
      this,
      ExecutionApiError.prototype,
    );
  }
}


/* =========================================================
   GENERIC API REQUEST
========================================================= */

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url =
    `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;

  const method =
    options.method || 'GET';

  const headers =
    new Headers(options.headers);

  /*
   * JSON is the default request format.
   *
   * Do not overwrite an explicitly supplied
   * Content-Type.
   */
  if (
    options.body !== undefined &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set(
      'Content-Type',
      'application/json',
    );
  }

  let response: Response;

  try {
    response = await fetch(
      url,
      {
        ...options,
        headers,
        credentials: 'include',
      },
    );
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : 'Network request failed.';

    console.error(
      '[Execution API NETWORK ERROR]',
      {
        method,
        url,
        error,
      },
    );

    throw new ExecutionApiError(
      message,
      0,
      null,
    );
  }

  /*
   * 204 No Content.
   */
  if (response.status === 204) {
    return undefined as T;
  }

  /*
   * Read response safely.
   */
  const contentType =
    response.headers.get(
      'content-type',
    ) || '';

  let responseBody: unknown = null;

  if (
    contentType.includes(
      'application/json',
    )
  ) {
    try {
      responseBody =
        await response.json();
    } catch {
      responseBody = null;
    }
  } else {
    try {
      responseBody =
        await response.text();
    } catch {
      responseBody = null;
    }
  }

  /*
   * Convert every non-2xx response
   * into a typed API error.
   */
  if (!response.ok) {
    let message =
      `API request failed with status ${response.status}.`;

    if (
      typeof responseBody === 'object' &&
      responseBody !== null
    ) {
      const body =
        responseBody as Record<
          string,
          unknown
        >;

      if (
        typeof body.detail === 'string'
      ) {
        message =
          body.detail;
      } else if (
        Array.isArray(body.detail)
      ) {
        message =
          `API validation failed with status ${response.status}.`;
      } else if (
        typeof body.message === 'string'
      ) {
        message =
          body.message;
      }
    } else if (
      typeof responseBody === 'string' &&
      responseBody.trim()
    ) {
      message =
        responseBody;
    }

    console.error(
      '[Execution API ERROR]',
      {
        method,
        url,
        status: response.status,
        statusText: response.statusText,
        responseBody,
      },
    );

    throw new ExecutionApiError(
      message,
      response.status,
      responseBody,
    );
  }

  return responseBody as T;
}


/* =========================================================
   PROCESSING STEP
========================================================= */

export interface BackendProcessingStep {
  id?: string;

  processing_step_id?: string;

  processing_id?: string;

  processing_job_id?: string;

  step_name?: string;

  name?: string;

  stage?: string;

  status?: string | null;

  progress?: number | null;

  message?: string | null;

  error?: string | null;

  started_at?: string | null;

  completed_at?: string | null;

  created_at?: string | null;

  updated_at?: string | null;

  step_order?: number | null;

  provider?: string | null;

  provider_operation?: string | null;

  attempt_count?: number;

  duration_ms?: number | null;

  error_code?: string | null;

  error_message?: string | null;

  [key: string]: unknown;
}


/* =========================================================
   PROCESSING JOB
========================================================= */

export interface ProcessingJob {
  id: string;

  processing_id?: string;

  document_id?: string | null;

  document_version_id?: string | null;

  status?: string | null;

  progress?: number | null;

  current_stage?: string | null;

  message?: string | null;

  error?: string | null;

  created_at?: string | null;

  updated_at?: string | null;

  started_at?: string | null;

  completed_at?: string | null;

  steps?: BackendProcessingStep[];

  [key: string]: unknown;
}


/* =========================================================
   START PROCESSING RESPONSE
========================================================= */

export interface StartProcessingJobResponse {
  processing_id: string;

  document_id: string;

  document_version_id: string;

  status: string;

  message: string;
}


/* =========================================================
   START PROCESSING REQUEST
========================================================= */

export interface StartProcessingJobRequest {
  documentId: string;

  /*
   * The frontend may know the selected workflow,
   * but the current backend ProcessingRequest
   * accepts only document_id and force.
   *
   * Keep this field for frontend compatibility,
   * but do not send it to the backend.
   */
  workflowId?: string;

  /*
   * Kept for compatibility with existing
   * workflow-page callers.
   */
  includeWorkflowId?: boolean;

  force?: boolean;
}


/* =========================================================
   START PROCESSING JOB
========================================================= */

export async function startProcessingJob(
  input: StartProcessingJobRequest,
): Promise<ProcessingJob> {
  const documentId =
    input.documentId?.trim();

  if (!documentId) {
    throw new Error(
      'documentId is required.',
    );
  }

  const result =
    await request<
      StartProcessingJobResponse
    >(
      '/processing/jobs',
      {
        method: 'POST',

        body:
          JSON.stringify({
            document_id:
              documentId,

            force:
              Boolean(
                input.force,
              ),
          }),
      },
    );

  /*
   * Normalize creation response
   * into the ProcessingJob shape.
   */
  return {
    id:
      String(
        result.processing_id,
      ),

    processing_id:
      String(
        result.processing_id,
      ),

    document_id:
      String(
        result.document_id,
      ),

    document_version_id:
      String(
        result.document_version_id,
      ),

    status:
      result.status,

    message:
      result.message,

    progress:
      result.status === 'completed'
        ? 100
        : 0,

    current_stage:
      null,

    error:
      null,

    created_at:
      new Date().toISOString(),

    completed_at:
      result.status === 'completed'
        ? new Date().toISOString()
        : null,

    steps:
      [],
  };
}


/* =========================================================
   GET PROCESSING JOB
========================================================= */

export async function getProcessingJob(
  processingJobId: string,
): Promise<ProcessingJob | null> {
  const normalizedProcessingJobId =
    processingJobId?.trim();

  if (!normalizedProcessingJobId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  const path =
    `/processing/jobs/${encodeURIComponent(
      normalizedProcessingJobId,
    )}`;

  try {
    const result =
      await request<ProcessingJob>(
        path,
        {
          method: 'GET',
        },
      );

    return result;
  } catch (
    error: unknown
  ) {
    if (
      error instanceof ExecutionApiError &&
      error.status === 404
    ) {
      return null;
    }

    throw error;
  }
}


/* =========================================================
   DOCUMENT INTELLIGENCE RESULT
========================================================= */

export interface ProcessingIntelligenceResult {
  processing_id: string;

  document_id: string;

  document_version_id: string;

  document_type?: string | null;

  status?: string | null;

  confidence?: number | null;

  structured_data: Record<
    string,
    unknown
  >;

  validation_results: Record<
    string,
    unknown
  >;

  artifacts: Array<
    Record<
      string,
      unknown
    >
  >;

  knowledge: Record<
    string,
    unknown
  >;

  raw_text?: string | null;

  validation_status?: string | null;

  created_at?: string | null;

  updated_at?: string | null;

  completed_at?: string | null;

  /*
   * Compatibility field.
   */
  processing_job_id?: string | null;

  progress?: number | null;

  current_stage?: string | null;

  steps?: BackendProcessingStep[];

  message?: string | null;

  error?: string | null;

  [key: string]: unknown;
}


/* =========================================================
   GET PROCESSING INTELLIGENCE
========================================================= */

export async function getProcessingIntelligence(
  processingJobId: string,
): Promise<
  ProcessingIntelligenceResult | null
> {
  const normalizedProcessingJobId =
    processingJobId?.trim();

  if (!normalizedProcessingJobId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  const path =
    `/processing/jobs/${encodeURIComponent(
      normalizedProcessingJobId,
    )}/intelligence`;

  try {
    const result =
      await request<
        ProcessingIntelligenceResult
      >(
        path,
        {
          method: 'GET',
        },
      );

    return result;
  } catch (
    error: unknown
  ) {
    /*
     * A missing intelligence result
     * is a legitimate application state.
     */
    if (
      error instanceof ExecutionApiError &&
      error.status === 404
    ) {
      return null;
    }

    /*
     * 409 remains an ExecutionApiError
     * so the UI can distinguish
     * processing-in-progress from
     * other failures.
     */
    throw error;
  }
}


/* =========================================================
   INTELLIGENCE RESULT ALIAS
========================================================= */

export async function getIntelligenceResult(
  processingJobId: string,
): Promise<
  ProcessingIntelligenceResult | null
> {
  return getProcessingIntelligence(
    processingJobId,
  );
}


/* =========================================================
   DOWNLOAD PROCESSING RESULT
========================================================= */

export async function downloadProcessingResult(
  processingJobId: string,
  documentName?: string,
): Promise<
  ProcessingIntelligenceResult | null
> {
  const normalizedProcessingJobId =
    processingJobId?.trim();

  if (!normalizedProcessingJobId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  /*
   * Reuse the intelligence request.
   *
   * This guarantees the same 404
   * handling as the result viewer.
   */
  const result =
    await getProcessingIntelligence(
      normalizedProcessingJobId,
    );

  /*
   * No result yet.
   */
  if (result === null) {
    return null;
  }

  /*
   * Browser-only operation.
   */
  if (
    typeof window === 'undefined' ||
    typeof document === 'undefined'
  ) {
    throw new Error(
      'Result download is only available in the browser.',
    );
  }

  /*
   * Serialize the persisted result.
   */
  const json =
    JSON.stringify(
      result,
      null,
      2,
    );

  /*
   * Create exactly one Blob.
   */
  const blob =
    new Blob(
      [json],
      {
        type:
          'application/json;charset=utf-8',
      },
    );

  /*
   * Create temporary URL.
   */
  const url =
    window.URL.createObjectURL(
      blob,
    );

  /*
   * Build safe filename.
   */
  const baseName =
    (
      documentName?.trim() ||
      'processing-result'
    )
      .replace(
        /\.[^/.]+$/,
        '',
      )
      .replace(
        /[^a-zA-Z0-9-_]+/g,
        '_',
      ) ||
    'processing-result';

  const filename =
    `${baseName}-processing-result.json`;

  /*
   * Create temporary anchor.
   */
  const anchor =
    document.createElement(
      'a',
    );

  try {
    anchor.href =
      url;

    anchor.download =
      filename;

    anchor.style.display =
      'none';

    document.body.appendChild(
      anchor,
    );

    anchor.click();
  } finally {
    /*
     * Remove temporary anchor.
     */
    anchor.remove();

    /*
     * Release object URL.
     */
    window.setTimeout(
      () => {
        window.URL.revokeObjectURL(
          url,
        );
      },
      0,
    );
  }

  return result;
}


/* =========================================================
   PUBLIC EXPORTS
========================================================= */

export {
  request,
};

