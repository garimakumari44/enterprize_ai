/* =========================================================
   PROCESSING API
=========================================================

Canonical frontend API client for document processing.

Backend:
    POST /api/v1/processing/jobs
    GET  /api/v1/processing/jobs/{processing_id}
    POST /api/v1/processing/jobs/{processing_id}/cancel
    POST /api/v1/processing/jobs/{processing_id}/review
    POST /api/v1/processing/jobs/{processing_id}/review/approve
    POST /api/v1/processing/jobs/{processing_id}/review/reject

The aggregate GET endpoint is the canonical processing
read model.

It returns:
    job state
    steps
    extraction
    validation
    intelligence
    review

The frontend should therefore not depend on a separate
/intelligence endpoint.

========================================================= */

import {
  ApiError,
  request,
} from './client';


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
   EXTRACTION
========================================================= */

export interface ProcessingExtraction {
  id?: string;

  processing_id?: string;

  document_id?: string;

  document_version_id?: string;

  document_type?: string | null;

  overall_confidence?: number | null;

  status?: string | null;

  raw_text?: string | null;

  structured_data?: Record<
    string,
    unknown
  >;

  validation_status?: string | null;

  extraction_method?: string | null;

  metadata?: Record<
    string,
    unknown
  >;

  fields?: Array<
    Record<
      string,
      unknown
    >
  >;

  created_at?: string | null;

  updated_at?: string | null;

  [key: string]: unknown;
}


/* =========================================================
   VALIDATION
========================================================= */

export interface ProcessingValidation {
  id?: string;

  processing_id?: string;

  status?: string | null;

  overall_status?: string | null;

  issues?: Array<
    Record<
      string,
      unknown
    >
  >;

  created_at?: string | null;

  updated_at?: string | null;

  [key: string]: unknown;
}


/* =========================================================
   INTELLIGENCE RESULT
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
   * Compatibility/UI fields.
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
   REVIEW
========================================================= */

export interface ProcessingReview {
  id?: string;

  processing_id?: string;

  decision?: string | null;

  comments?: string | null;

  corrections?: Array<
    Record<
      string,
      unknown
    >
  >;

  status?: string | null;

  created_at?: string | null;

  updated_at?: string | null;

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

  current_stage?: string | null;

  progress?: number | null;

  message?: string | null;

  error?: string | null;

  created_at?: string | null;

  updated_at?: string | null;

  started_at?: string | null;

  completed_at?: string | null;

  steps?: BackendProcessingStep[];

  extraction?: ProcessingExtraction | null;

  validation?: ProcessingValidation | null;

  intelligence?:
    | ProcessingIntelligenceResult
    | null;

  review?:
    | ProcessingReview
    | null;

  [key: string]: unknown;
}


/* =========================================================
   START REQUEST
========================================================= */

export interface StartProcessingJobRequest {
  documentId: string;

  /*
   * The workflow can still be known by the UI,
   * but the current backend ProcessingRequest
   * does not accept workflow_id.
   *
   * Therefore it is intentionally NOT sent.
   */
  workflowId?: string;

  includeWorkflowId?: boolean;

  force?: boolean;
}


/* =========================================================
   START RESPONSE
========================================================= */

export interface StartProcessingJobResponse {
  processing_id: string;

  document_id: string;

  document_version_id: string;

  status: string;

  message: string;
}


/* =========================================================
   REVIEW REQUEST
========================================================= */

export interface ReviewCorrection {
  field: string;

  value: unknown;

  reason?: string;
}


export interface ReviewSubmission {
  decision: string;

  comments?: string;

  corrections?: ReviewCorrection[];
}


/* =========================================================
   NORMALIZE START RESPONSE
========================================================= */

function normalizeStartResponse(
  result: StartProcessingJobResponse,
): ProcessingJob {
  const now =
    new Date().toISOString();

  const completed =
    result.status === 'completed';

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
      completed
        ? 100
        : 0,

    current_stage:
      null,

    error:
      null,

    created_at:
      now,

    updated_at:
      now,

    started_at:
      null,

    completed_at:
      completed
        ? now
        : null,

    steps:
      [],
  };
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

  return normalizeStartResponse(
    result,
  );
}


/* =========================================================
   GET PROCESSING JOB
========================================================= */

export async function getProcessingJob(
  processingJobId: string,
): Promise<ProcessingJob | null> {
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  try {
    return await request<ProcessingJob>(
      `/processing/jobs/${encodeURIComponent(
        normalizedId,
      )}`,
      {
        method: 'GET',
      },
    );
  } catch (
    error: unknown
  ) {
    /*
     * A missing job is represented as null
     * for the execution UI.
     */
    if (
      error instanceof ApiError &&
      error.status === 404
    ) {
      return null;
    }

    throw error;
  }
}


/* =========================================================
   GET PROCESSING INTELLIGENCE
=========================================================

IMPORTANT:

The canonical backend read endpoint is:

    GET /processing/jobs/{id}

The aggregate response already contains:

    intelligence

Therefore this function intentionally does NOT call:

    /processing/jobs/{id}/intelligence

This prevents another frontend/backend endpoint mismatch.
========================================================= */

export async function getProcessingIntelligence(
  processingJobId: string,
): Promise<
  ProcessingIntelligenceResult | null
> {
  const job =
    await getProcessingJob(
      processingJobId,
    );

  if (!job) {
    return null;
  }

  /*
   * Intelligence may legitimately not exist yet.
   */
  if (
    !job.intelligence
  ) {
    return null;
  }

  return {
    ...job.intelligence,

    processing_id:
      job.intelligence.processing_id ||
      job.processing_id ||
      job.id,

    document_id:
      job.intelligence.document_id ||
      job.document_id ||
      '',

    document_version_id:
      job.intelligence.document_version_id ||
      job.document_version_id ||
      '',

    processing_job_id:
      job.intelligence.processing_job_id ||
      job.processing_id ||
      job.id,

    progress:
      job.intelligence.progress ??
      job.progress,

    current_stage:
      job.intelligence.current_stage ??
      job.current_stage,

    steps:
      job.intelligence.steps ??
      job.steps,

    message:
      job.intelligence.message ??
      job.message,

    error:
      job.intelligence.error ??
      job.error,
  };
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
   CANCEL PROCESSING JOB
========================================================= */

export async function cancelProcessingJob(
  processingJobId: string,
): Promise<ProcessingJob | null> {
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  await request<void>(
    `/processing/jobs/${encodeURIComponent(
      normalizedId,
    )}/cancel`,
    {
      method: 'POST',
    },
  );

  /*
   * Return the canonical aggregate state
   * after cancellation.
   */
  return getProcessingJob(
    normalizedId,
  );
}


/* =========================================================
   SUBMIT REVIEW
========================================================= */

export async function submitProcessingReview(
  processingJobId: string,
  submission: ReviewSubmission,
): Promise<ProcessingJob | null> {
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  await request<unknown>(
    `/processing/jobs/${encodeURIComponent(
      normalizedId,
    )}/review`,
    {
      method: 'POST',

      body:
        JSON.stringify(
          submission,
        ),
    },
  );

  return getProcessingJob(
    normalizedId,
  );
}


/* =========================================================
   APPROVE REVIEW
========================================================= */

export async function approveProcessingReview(
  processingJobId: string,
  comments?: string,
): Promise<ProcessingJob | null> {
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  await request<unknown>(
    `/processing/jobs/${encodeURIComponent(
      normalizedId,
    )}/review/approve`,
    {
      method: 'POST',

      body:
        JSON.stringify({
          comments:
            comments ?? '',
        }),
    },
  );

  return getProcessingJob(
    normalizedId,
  );
}


/* =========================================================
   REJECT REVIEW
========================================================= */

export async function rejectProcessingReview(
  processingJobId: string,
  comments?: string,
): Promise<ProcessingJob | null> {
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  await request<unknown>(
    `/processing/jobs/${encodeURIComponent(
      normalizedId,
    )}/review/reject`,
    {
      method: 'POST',

      body:
        JSON.stringify({
          comments:
            comments ?? '',
        }),
    },
  );

  return getProcessingJob(
    normalizedId,
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
  const normalizedId =
    processingJobId?.trim();

  if (!normalizedId) {
    throw new Error(
      'processingJobId is required.',
    );
  }

  const result =
    await getProcessingIntelligence(
      normalizedId,
    );

  if (!result) {
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

  const json =
    JSON.stringify(
      result,
      null,
      2,
    );

  const blob =
    new Blob(
      [json],
      {
        type:
          'application/json;charset=utf-8',
      },
    );

  const url =
    window.URL.createObjectURL(
      blob,
    );

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
    anchor.remove();

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
   BACKWARD-COMPATIBILITY EXPORT
=========================================================

This lets older callers migrate gradually.
========================================================= */

export {
  ApiError as ProcessingApiError,
};