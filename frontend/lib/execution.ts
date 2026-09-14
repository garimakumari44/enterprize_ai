/* ============================================================
   frontend/lib/execution.ts

   Frontend execution-history store.

   Responsibilities:
   - Save processing runs started from WorkflowsPage
   - Keep execution history in localStorage
   - Read execution history
   - Update execution status
   - Remove execution records
   - Clear all execution records
   - Keep frontend history after page refresh

   IMPORTANT:
   This does NOT create or modify anything in the backend.

   DELETE BEHAVIOR:
   deleteExecution() removes only the frontend execution-history
   record from localStorage. It does NOT delete the underlying
   document, processing job, intelligence result, or artifacts
   from the backend.
   ============================================================ */


/* ============================================================
   TYPES
============================================================ */

export type ExecutionStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'review_required';

export type ExecutionStepStatus =
  | 'pending'
  | 'active'
  | 'done'
  | 'failed';

export interface ExecutionStep {
  id: string;

  label: string;

  status: ExecutionStepStatus;

  duration?: string;

  startedAt?: string;

  completedAt?: string;

  error?: string | null;
}

export interface ExecutionRecord {
  id: string;

  processingId: string;

  documentId: string;

  documentVersionId?: string;

  workflowId: string;

  documentName: string;

  workflowName: string;

  status: ExecutionStatus;

  progress: number;

  duration: string;

  createdAt: string;

  completedAt?: string;

  error?: string | null;

  message?: string | null;

  steps: ExecutionStep[];
}


/* ============================================================
   STORAGE
============================================================ */

const STORAGE_KEY =
  'enterprise-ai.execution-history';


/* ============================================================
   SAFE STORAGE
============================================================ */

/**
 * Check whether localStorage is available.
 *
 * This keeps the module safe during:
 * - Next.js SSR
 * - static rendering
 * - environments where localStorage is unavailable
 */
function canUseStorage(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.localStorage !== 'undefined'
  );
}


/* ============================================================
   READ
============================================================ */

/**
 * Return all execution-history records.
 *
 * Invalid entries are ignored defensively.
 */
export function getExecutions(): ExecutionRecord[] {
  if (!canUseStorage()) {
    return [];
  }

  try {
    const raw =
      window.localStorage.getItem(
        STORAGE_KEY,
      );

    if (!raw) {
      return [];
    }

    const parsed: unknown =
      JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(
      (
        item,
      ): item is ExecutionRecord =>
        Boolean(
          item &&
            typeof item === 'object' &&
            'processingId' in item,
        ),
    );
  } catch (error) {
    console.error(
      '[execution] Failed to read execution history:',
      error,
    );

    return [];
  }
}


/* ============================================================
   WRITE
============================================================ */

/**
 * Persist execution records to localStorage.
 */
function saveExecutions(
  executions: ExecutionRecord[],
): void {
  if (!canUseStorage()) {
    return;
  }

  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(executions),
    );
  } catch (error) {
    console.error(
      '[execution] Failed to save execution history:',
      error,
    );
  }
}


/* ============================================================
   CREATE
============================================================ */

/**
 * Create a new execution record.
 *
 * If the processingId already exists, replace the existing
 * record instead of creating a duplicate.
 */
export function createExecution(
  execution: ExecutionRecord,
): ExecutionRecord {
  const executions =
    getExecutions();

  const existingIndex =
    executions.findIndex(
      (item) =>
        item.processingId ===
        execution.processingId,
    );

  if (existingIndex >= 0) {
    executions[existingIndex] =
      execution;
  } else {
    executions.unshift(
      execution,
    );
  }

  saveExecutions(
    executions,
  );

  return execution;
}


/* ============================================================
   UPDATE
============================================================ */

/**
 * Update an existing execution record.
 *
 * Returns the updated record or null when the execution
 * cannot be found.
 */
export function updateExecution(
  processingId: string,
  updates: Partial<ExecutionRecord>,
): ExecutionRecord | null {
  const executions =
    getExecutions();

  const index =
    executions.findIndex(
      (item) =>
        item.processingId ===
        processingId,
    );

  if (index === -1) {
    return null;
  }

  const updated: ExecutionRecord = {
    ...executions[index],
    ...updates,
  };

  executions[index] =
    updated;

  saveExecutions(
    executions,
  );

  return updated;
}


/* ============================================================
   GET SINGLE
============================================================ */

/**
 * Get one execution by processing job ID.
 */
export function getExecution(
  processingId: string,
): ExecutionRecord | null {
  const executions =
    getExecutions();

  return (
    executions.find(
      (item) =>
        item.processingId ===
        processingId,
    ) ?? null
  );
}


/* ============================================================
   DELETE SINGLE EXECUTION
============================================================ */

/**
 * Delete one execution-history record.
 *
 * IMPORTANT:
 * This only removes the frontend history entry from
 * localStorage.
 *
 * It does NOT:
 * - delete the document
 * - delete the processing job
 * - delete intelligence results
 * - delete artifacts
 * - modify PostgreSQL
 * - modify MinIO
 * - modify Redis
 */
export function deleteExecution(
  processingId: string,
): void {
  if (!processingId?.trim()) {
    return;
  }

  const normalizedProcessingId =
    processingId.trim();

  const executions =
    getExecutions();

  const filtered =
    executions.filter(
      (item) =>
        item.processingId !==
        normalizedProcessingId,
    );

  /*
   * Nothing changed.
   * Avoid an unnecessary localStorage write.
   */
  if (
    filtered.length ===
    executions.length
  ) {
    return;
  }

  saveExecutions(
    filtered,
  );
}


/* ============================================================
   CLEAR ALL EXECUTIONS
============================================================ */

/**
 * Remove the entire frontend execution history.
 *
 * IMPORTANT:
 * This only clears localStorage.
 * It does NOT delete backend data.
 */
export function clearExecutions(): void {
  if (!canUseStorage()) {
    return;
  }

  try {
    window.localStorage.removeItem(
      STORAGE_KEY,
    );
  } catch (error) {
    console.error(
      '[execution] Failed to clear execution history:',
      error,
    );
  }
}


/* ============================================================
   FORMAT DURATION
============================================================ */

/**
 * Format execution duration.
 *
 * Examples:
 * - 4s
 * - 42s
 * - 2m 15s
 */
export function formatDuration(
  startedAt: string,
  completedAt?: string,
): string {
  const start =
    new Date(
      startedAt,
    ).getTime();

  if (!Number.isFinite(start)) {
    return '0s';
  }

  const end =
    completedAt
      ? new Date(
          completedAt,
        ).getTime()
      : Date.now();

  const safeEnd =
    Number.isFinite(end)
      ? end
      : Date.now();

  const seconds =
    Math.max(
      0,
      Math.round(
        (safeEnd - start) /
          1000,
      ),
    );

  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes =
    Math.floor(
      seconds / 60,
    );

  const remainingSeconds =
    seconds % 60;

  return `${minutes}m ${remainingSeconds}s`;
}


/* ============================================================
   DEFAULT PROCESSING STEPS

   These IDs intentionally match the canonical frontend
   fallback processing stages.

   Backend pipeline may expose a richer stage list.

   When backend steps are available, ExecutionsPage should
   prefer those backend steps instead of these defaults.

   Upload is frontend-only because the document upload
   happens before the processing job starts.
============================================================ */

export function createDefaultExecutionSteps(): ExecutionStep[] {
  return [
    {
      id: 'upload',

      label: 'Document Upload',

      status: 'done',
    },

    {
      id: 'ocr',

      label: 'OCR',

      status: 'pending',
    },

    {
      id: 'extraction',

      label: 'Extraction',

      status: 'pending',
    },

    {
      id: 'chunking',

      label: 'Chunking',

      status: 'pending',
    },

    {
      id: 'embeddings',

      label: 'Embeddings',

      status: 'pending',
    },

    {
      id: 'indexing',

      label: 'Indexing',

      status: 'pending',
    },
  ];
}


/* ============================================================
   NORMALIZE BACKEND STATUS
============================================================ */

export function normalizeExecutionStatus(
  status?: string | null,
): ExecutionStatus {
  const normalized =
    String(
      status ?? '',
    )
      .trim()
      .toLowerCase()
      .replace(
        /[\s-]+/g,
        '_',
      );

  switch (normalized) {
    case 'pending':
      return 'pending';

    case 'queued':
      return 'queued';

    case 'processing':
    case 'running':
    case 'in_progress':
      return 'processing';

    case 'completed':
    case 'complete':
    case 'success':
    case 'succeeded':
      return 'completed';

    case 'failed':
    case 'failure':
    case 'error':
      return 'failed';

    case 'review_required':
    case 'needs_review':
    case 'review':
      return 'review_required';

    default:
      return 'processing';
  }
}


/* ============================================================
   NORMALIZE BACKEND STEP STATUS
============================================================ */

function normalizeStepStatus(
  status?: string | null,
): ExecutionStepStatus {
  const normalized =
    String(
      status ?? '',
    )
      .trim()
      .toLowerCase()
      .replace(
        /[\s-]+/g,
        '_',
      );

  switch (normalized) {
    case 'completed':
    case 'complete':
    case 'done':
    case 'success':
    case 'succeeded':
      return 'done';

    case 'processing':
    case 'running':
    case 'active':
    case 'in_progress':
      return 'active';

    case 'failed':
    case 'failure':
    case 'error':
      return 'failed';

    default:
      return 'pending';
  }
}


/* ============================================================
   NORMALIZE STEP NAME
============================================================ */

function normalizeStepName(
  value: unknown,
): string {
  return String(
    value ?? '',
  )
    .trim()
    .toLowerCase()
    .replace(
      /[\s-]+/g,
      '_',
    );
}


/* ============================================================
   BACKEND STEP → FRONTEND STEP ID

   Allows backend aliases without making the UI depend on
   exact backend naming.
============================================================ */

function resolveFrontendStepId(
  value: unknown,
): string | null {
  const normalized =
    normalizeStepName(
      value,
    );

  if (!normalized) {
    return null;
  }

  const aliases: Record<
    string,
    string
  > = {
    upload:
      'upload',

    document_upload:
      'upload',

    ocr:
      'ocr',

    optical_character_recognition:
      'ocr',

    extraction:
      'extraction',

    extract:
      'extraction',

    text_extraction:
      'extraction',

    ai_processing:
      'extraction',

    chunking:
      'chunking',

    chunk:
      'chunking',

    embeddings:
      'embeddings',

    embedding:
      'embeddings',

    indexing:
      'indexing',

    index:
      'indexing',
  };

  return (
    aliases[normalized] ??
    null
  );
}


/* ============================================================
   FORMAT BACKEND DURATION
============================================================ */

function formatBackendDuration(
  duration?:
    | string
    | number
    | null,

  durationMs?:
    | number
    | null,
): string | undefined {
  if (
    typeof duration ===
      'string' &&
    duration.trim()
  ) {
    return duration;
  }

  if (
    typeof duration ===
      'number' &&
    Number.isFinite(
      duration,
    )
  ) {
    if (duration < 1000) {
      return `${Math.round(
        duration,
      )}ms`;
    }

    return formatDuration(
      new Date(
        Date.now() -
          duration,
      ).toISOString(),

      new Date().toISOString(),
    );
  }

  if (
    typeof durationMs ===
      'number' &&
    Number.isFinite(
      durationMs,
    )
  ) {
    if (
      durationMs <
      1000
    ) {
      return `${Math.round(
        durationMs,
      )}ms`;
    }

    const seconds =
      Math.round(
        durationMs /
          1000,
      );

    if (seconds < 60) {
      return `${seconds}s`;
    }

    const minutes =
      Math.floor(
        seconds / 60,
      );

    const remainingSeconds =
      seconds % 60;

    return `${minutes}m ${remainingSeconds}s`;
  }

  return undefined;
}


/* ============================================================
   MERGE BACKEND STEPS

   Supports backend responses such as:

   steps: [
     {
       name: "ocr",
       status: "completed"
     },
     {
       name: "extraction",
       status: "processing"
     }
   ]
============================================================ */

export function mergeBackendSteps(
  currentSteps: ExecutionStep[],
  backendSteps?: unknown,
): ExecutionStep[] {
  if (
    !Array.isArray(
      backendSteps,
    )
  ) {
    return currentSteps;
  }

  const result =
    currentSteps.length > 0
      ? [...currentSteps]
      : createDefaultExecutionSteps();

  backendSteps.forEach(
    (rawStep) => {
      if (
        !rawStep ||
        typeof rawStep !==
          'object'
      ) {
        return;
      }

      const step =
        rawStep as Record<
          string,
          unknown
        >;

      const backendName =
        step.name ??
        step.stage ??
        step.step ??
        step.operation;

      const frontendStepId =
        resolveFrontendStepId(
          backendName,
        );

      if (!frontendStepId) {
        return;
      }

      const index =
        result.findIndex(
          (item) =>
            item.id ===
            frontendStepId,
        );

      if (index === -1) {
        return;
      }

      const frontendStatus =
        normalizeStepStatus(
          typeof step.status ===
            'string'
            ? step.status
            : null,
        );

      const duration =
        formatBackendDuration(
          typeof step.duration ===
            'string' ||
          typeof step.duration ===
            'number'
            ? step.duration
            : null,

          typeof step.duration_ms ===
            'number'
            ? step.duration_ms
            : null,
        );

      const error =
        typeof step.error ===
          'string'
          ? step.error
          : typeof step.error_message ===
              'string'
            ? step.error_message
            : typeof step.error_code ===
                'string'
              ? step.error_code
              : null;

      result[index] = {
        ...result[index],

        status:
          frontendStatus,

        duration:
          duration ??
          result[index]
            .duration,

        startedAt:
          typeof step.started_at ===
          'string'
            ? step.started_at
            : result[index]
                .startedAt,

        completedAt:
          typeof step.completed_at ===
          'string'
            ? step.completed_at
            : result[index]
                .completedAt,

        error,
      };
    },
  );

  return result;
}


/* ============================================================
   APPLY CURRENT STAGE
============================================================ */

export function applyCurrentStage(
  steps: ExecutionStep[],

  currentStage:
    | string
    | null
    | undefined,

  backendStatus?:
    | string
    | null,
): ExecutionStep[] {
  if (!currentStage) {
    return steps;
  }

  const frontendStepId =
    resolveFrontendStepId(
      currentStage,
    );

  if (!frontendStepId) {
    return steps;
  }

  const index =
    steps.findIndex(
      (step) =>
        step.id ===
        frontendStepId,
    );

  if (index < 0) {
    return steps;
  }

  const normalizedStatus =
    normalizeExecutionStatus(
      backendStatus,
    );

  return steps.map(
    (
      step,
      stepIndex,
    ) => {
      if (
        stepIndex < index
      ) {
        return {
          ...step,

          status:
            step.status ===
            'failed'
              ? 'failed'
              : 'done',
        };
      }

      if (
        stepIndex === index
      ) {
        return {
          ...step,

          status:
            normalizedStatus ===
            'failed'
              ? 'failed'
              : 'active',
        };
      }

      return {
        ...step,

        status:
          'pending',
      };
    },
  );
}


/* ============================================================
   APPLY PROGRESS TO STEPS

   Used as fallback when backend does not provide
   current_stage.
============================================================ */

export function applyProgressToSteps(
  steps: ExecutionStep[],
  progress: number,
): ExecutionStep[] {
  if (
    steps.length ===
    0
  ) {
    return steps;
  }

  const safeProgress =
    Math.min(
      Math.max(
        Number.isFinite(
          progress,
        )
          ? progress
          : 0,
        0,
      ),
      100,
    );

  if (
    safeProgress <= 0
  ) {
    return steps.map(
      (step) => ({
        ...step,

        status:
          step.id ===
          'upload'
            ? 'done'
            : 'pending',
      }),
    );
  }

  if (
    safeProgress >=
    100
  ) {
    return steps.map(
      (step) => ({
        ...step,

        status:
          'done',
      }),
    );
  }

  /*
   * Upload is already complete before the processing job.
   *
   * Therefore progress is calculated against the actual
   * backend processing stages, not the upload step.
   */

  const processingSteps =
    steps.filter(
      (step) =>
        step.id !==
        'upload',
    );

  const completedCount =
    Math.floor(
      (safeProgress /
        100) *
        processingSteps.length,
    );

  const activeStepIndex =
    completedCount;

  return steps.map(
    (step) => {
      if (
        step.id ===
        'upload'
      ) {
        return {
          ...step,

          status:
            'done',
        };
      }

      const index =
        processingSteps.findIndex(
          (item) =>
            item.id ===
            step.id,
        );

      if (
        index <
        completedCount
      ) {
        return {
          ...step,

          status:
            'done',
        };
      }

      if (
        index ===
        activeStepIndex
      ) {
        return {
          ...step,

          status:
            'active',
        };
      }

      return {
        ...step,

        status:
          'pending',
      };
    },
  );
}