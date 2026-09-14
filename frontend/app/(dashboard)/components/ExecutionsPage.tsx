'use client';

import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  Activity,
  CheckCircle2,
  ChevronRight,
  Circle,
  Download,
  Eye,
  Loader2,
  RefreshCw,
  Trash2,
  X,
  XCircle,
} from 'lucide-react';

import { Card } from './ui/Card';

import {
  downloadProcessingResult,
  getProcessingIntelligence,
  getProcessingJob,
  type BackendProcessingStep,
  type ProcessingIntelligenceResult,
} from '../../../lib/api/processingApi';

import {
  applyCurrentStage,
  applyProgressToSteps,
  createDefaultExecutionSteps,
  deleteExecution,
  formatDuration,
  getExecutions,
  normalizeExecutionStatus,
  updateExecution,
  type ExecutionRecord,
  type ExecutionStep,
} from '../../../lib/execution';


/* =========================================================
   STATUS BADGE
========================================================= */

function ExecutionStatusBadge({
  status,
}: {
  status: ExecutionRecord['status'];
}) {
  const config: Record<
    ExecutionRecord['status'],
    {
      label: string;
      className: string;
    }
  > = {
    pending: {
      label: 'Pending',
      className:
        'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
    },

    queued: {
      label: 'Queued',
      className:
        'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400',
    },

    processing: {
      label: 'Processing',
      className:
        'bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-400',
    },

    completed: {
      label: 'Completed',
      className:
        'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400',
    },

    failed: {
      label: 'Failed',
      className:
        'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400',
    },

    review_required: {
      label: 'Needs Review',
      className:
        'bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-400',
    },
  };

  const value =
    config[status] ??
    config.processing;

  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${value.className}`}
    >
      {value.label}
    </span>
  );
}


/* =========================================================
   STEP ICON
========================================================= */

function StepIcon({
  status,
}: {
  status: ExecutionStep['status'];
}) {
  switch (status) {
    case 'done':
      return (
        <CheckCircle2
          size={16}
          className="text-emerald-500"
        />
      );

    case 'active':
      return (
        <Loader2
          size={16}
          className="animate-spin text-cyan-500"
        />
      );

    case 'failed':
      return (
        <XCircle
          size={16}
          className="text-rose-500"
        />
      );

    default:
      return (
        <Circle
          size={16}
          className="text-slate-300 dark:text-slate-600"
        />
      );
  }
}


/* =========================================================
   STEP COLOR
========================================================= */

function stepColor(
  status: ExecutionStep['status'],
) {
  switch (status) {
    case 'done':
      return 'bg-emerald-500';

    case 'active':
      return 'bg-cyan-500';

    case 'failed':
      return 'bg-rose-500';

    default:
      return 'bg-slate-300 dark:bg-slate-600';
  }
}


/* =========================================================
   SAFE STRING
========================================================= */

function safeString(
  value: unknown,
): string | undefined {
  if (
    value === null ||
    value === undefined
  ) {
    return undefined;
  }

  const normalized =
    String(value).trim();

  return normalized
    ? normalized
    : undefined;
}


/* =========================================================
   STEP DURATION
========================================================= */

function formatStepDuration(
  durationMs:
    | number
    | null
    | undefined,
): string | undefined {
  if (
    typeof durationMs !== 'number' ||
    !Number.isFinite(durationMs) ||
    durationMs < 0
  ) {
    return undefined;
  }

  if (durationMs < 1000) {
    return `${durationMs}ms`;
  }

  const seconds =
    durationMs / 1000;

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  const minutes =
    Math.floor(
      seconds / 60,
    );

  const remainingSeconds =
    Math.round(
      seconds % 60,
    );

  return `${minutes}m ${remainingSeconds}s`;
}


/* =========================================================
   STEP LABEL
========================================================= */

function humanizeStepName(
  value: string,
): string {
  return value
    .replace(
      /[_-]+/g,
      ' ',
    )
    .replace(
      /\b\w/g,
      (char) =>
        char.toUpperCase(),
    );
}


/* =========================================================
   BACKEND STEPS -> FRONTEND STEPS
========================================================= */

/**
 * Backend is the source of truth for processing stages.
 *
 * Example backend:
 *
 * classification
 * layout_analysis
 * text_extraction
 * ocr
 * structure_detection
 * cleaning
 * chunking
 * metadata_enrichment
 * embedding
 * indexing
 *
 * This prevents the old local 6-step execution model from
 * being displayed for completed backend jobs.
 */
function mapBackendSteps(
  backendSteps: BackendProcessingStep[],
): ExecutionStep[] {
  return backendSteps
    .slice()
    .sort(
      (a, b) =>
        (a.step_order ?? 0) -
        (b.step_order ?? 0),
    )
    .map(
      (
        step,
        index,
      ) => {
        const rawStatus =
          safeString(
            step.status,
          )?.toLowerCase();

        let status:
          ExecutionStep['status'] =
          'pending';

        if (
          rawStatus ===
            'completed' ||
          rawStatus === 'done' ||
          rawStatus ===
            'success'
        ) {
          status = 'done';
        } else if (
          rawStatus ===
            'processing' ||
          rawStatus === 'running' ||
          rawStatus ===
            'active'
        ) {
          status = 'active';
        } else if (
          rawStatus ===
            'failed' ||
          rawStatus === 'error' ||
          rawStatus ===
            'failure'
        ) {
          status = 'failed';
        }

        const name =
          safeString(
            step.name,
          ) ??
          safeString(
            step.stage,
          ) ??
          safeString(
            step.step_name,
          ) ??
          safeString(
            step.step,
          ) ??
          `step-${index + 1}`;

        const error =
          safeString(
            step.error_message,
          ) ??
          safeString(
            step.error_code,
          );

        return {
          id: name,

          label:
            humanizeStepName(
              name,
            ),

          status,

          duration:
            formatStepDuration(
              step.duration_ms,
            ),

          error,
        };
      },
    );
}


/* =========================================================
   SAFE STEP NORMALIZATION
========================================================= */

function normalizeSteps(
  execution: ExecutionRecord,
): ExecutionStep[] {
  if (
    Array.isArray(
      execution.steps,
    ) &&
    execution.steps.length > 0
  ) {
    return execution.steps;
  }

  return createDefaultExecutionSteps();
}


/* =========================================================
   TERMINAL STATUS
========================================================= */

function isTerminalStatus(
  execution: ExecutionRecord,
): boolean {
  /*
   * Do not stop polling a job that says completed while
   * progress is still below 100 and completedAt is missing.
   */
  if (
    execution.status ===
      'completed' &&
    execution.progress < 100 &&
    !execution.completedAt
  ) {
    return false;
  }

  return (
    execution.status ===
      'completed' ||
    execution.status ===
      'failed' ||
    execution.status ===
      'review_required'
  );
}


/* =========================================================
   BACKEND JOB SHAPE
========================================================= */

type ProcessingJobWithDetails = {
  current_stage?: string | null;
  steps?: BackendProcessingStep[];
};


/* =========================================================
   BUILD EXECUTION STATE
========================================================= */

function buildExecutionState(
  execution: ExecutionRecord,
  job: {
    status?: string | null;
    progress?: number | null;
    completed_at?: string | null;
    error?: string | null;
    message?: string | null;
    current_stage?: string | null;
    steps?: BackendProcessingStep[];
  },
): Partial<ExecutionRecord> {
  /*
   * Backend status is authoritative.
   */
  const rawStatus =
    safeString(
      job.status,
    ) ?? 'processing';

  let status =
    normalizeExecutionStatus(
      rawStatus,
    );

  /*
   * Normalize progress.
   */
  const backendProgress =
    typeof job.progress ===
    'number'
      ? Math.min(
          Math.max(
            job.progress,
            0,
          ),
          100,
        )
      : undefined;

  /*
   * Defensive completion handling.
   */
  if (
    status ===
      'completed' &&
    !job.completed_at &&
    (backendProgress ?? 0) <
      100
  ) {
    status =
      'processing';
  }


  /* =======================================================
     BACKEND STEP SOURCE OF TRUTH
  ======================================================= */

  const backendSteps =
    Array.isArray(
      job.steps,
    )
      ? job.steps
      : [];

  let steps: ExecutionStep[];

  if (
    backendSteps.length > 0
  ) {
    /*
     * IMPORTANT:
     *
     * Do NOT merge backend steps with the old frontend
     * default steps.
     *
     * The backend currently returns the real 10-stage
     * processing pipeline.
     */
    steps =
      mapBackendSteps(
        backendSteps,
      );
  } else {
    /*
     * Backward compatibility for executions where the
     * backend does not expose steps.
     */
    steps =
      normalizeSteps(
        execution,
      );
  }


  /* =======================================================
     CURRENT STAGE
  ======================================================= */

  if (
    job.current_stage
  ) {
    steps =
      applyCurrentStage(
        steps,
        job.current_stage,
        status,
      );
  } else if (
    typeof backendProgress ===
    'number'
  ) {
    /*
     * Only apply calculated progress when there is no
     * explicit current stage.
     *
     * Backend step statuses still remain authoritative
     * because completion is handled below.
     */
    steps =
      applyProgressToSteps(
        steps,
        backendProgress,
      );
  }


  /* =======================================================
     COMPLETED JOB
  ======================================================= */

  if (
    status ===
      'completed' &&
    (
      job.completed_at ||
      backendProgress ===
        100
    )
  ) {
    /*
     * A successfully completed processing job must show
     * every backend processing stage as completed.
     */
    steps =
      steps.map(
        (step) => ({
          ...step,
          status: 'done',
        }),
      );
  }


  /* =======================================================
     FAILED JOB
  ======================================================= */

  if (
    status ===
    'failed'
  ) {
    const backendFailedStep =
      backendSteps.find(
        (step) => {
          const value =
            safeString(
              step.status,
            )?.toLowerCase();

          return (
            value ===
              'failed' ||
            value ===
              'error' ||
            value ===
              'failure'
          );
        },
      );

    if (
      backendFailedStep
    ) {
      const backendName =
        safeString(
          backendFailedStep.name,
        ) ??
        safeString(
          backendFailedStep.stage,
        ) ??
        safeString(
          backendFailedStep.step_name,
        ) ??
        safeString(
          backendFailedStep.step,
        );

      const normalizedName =
        safeString(
          backendName,
        )
          ?.toLowerCase()
          .replace(
            /[\s-]+/g,
            '_',
          );

      if (
        normalizedName
      ) {
        const failedIndex =
          steps.findIndex(
            (step) => {
              const normalizedId =
                safeString(
                  step.id,
                )
                  ?.toLowerCase()
                  .replace(
                    /[\s-]+/g,
                    '_',
                  );

              const normalizedLabel =
                safeString(
                  step.label,
                )
                  ?.toLowerCase()
                  .replace(
                    /[\s-]+/g,
                    '_',
                  );

              return (
                normalizedId ===
                  normalizedName ||
                normalizedLabel ===
                  normalizedName
              );
            },
          );

        if (
          failedIndex >= 0
        ) {
          const backendError =
            safeString(
              backendFailedStep.error_message,
            ) ??
            safeString(
              backendFailedStep.error_code,
            ) ??
            safeString(
              job.error,
            ) ??
            'Processing step failed.';

          steps =
            steps.map(
              (
                step,
                index,
              ) =>
                index ===
                failedIndex
                  ? {
                      ...step,
                      status:
                        'failed',
                      error:
                        backendError,
                    }
                  : step,
            );
        }
      }
    } else {
      /*
       * If backend does not identify a failed step, mark
       * the currently active step as failed.
       */
      const activeIndex =
        steps.findIndex(
          (step) =>
            step.status ===
            'active',
        );

      if (
        activeIndex >= 0
      ) {
        steps =
          steps.map(
            (
              step,
              index,
            ) =>
              index ===
              activeIndex
                ? {
                    ...step,
                    status:
                      'failed',
                    error:
                      safeString(
                        job.error,
                      ) ??
                      'Processing step failed.',
                  }
                : step,
          );
      }
    }
  }


  /* =======================================================
     FINAL PROGRESS
  ======================================================= */

  let progress =
    backendProgress ??
    execution.progress ??
    0;

  if (
    status ===
      'completed' &&
    (
      job.completed_at ||
      progress >= 100
    )
  ) {
    progress = 100;
  }


  /* =======================================================
     FINAL EXECUTION STATE
  ======================================================= */

  return {
    status,

    progress,

    message:
      safeString(
        job.message,
      ) ?? null,

    error:
      safeString(
        job.error,
      ) ?? null,

    completedAt:
      job.completed_at ??
      undefined,

    duration:
      formatDuration(
        execution.createdAt,
        job.completed_at ??
          undefined,
      ),

    steps,
  };
}


/* =========================================================
   RESULT MODAL
========================================================= */

function ResultModal({
  result,
  documentName,
  onClose,
}: {
  result:
    | ProcessingIntelligenceResult
    | null;

  documentName: string;

  onClose: () => void;
}) {
  if (!result) {
    return null;
  }

  const processingJobId =
    result.processing_job_id ??
    result.processing_id;

  const status =
    result.status ??
    'completed';

  const confidence =
    typeof result.confidence ===
    'number'
      ? result.confidence
      : null;

  const validationStatus =
    result.validation_status ??
    null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Document Intelligence Result"
    >
      <div className="flex max-h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900">

        {/* HEADER */}

        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Eye
                size={16}
                className="shrink-0 text-cyan-500"
              />

              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Document Intelligence Result
              </h2>
            </div>

            <p className="mt-1 truncate text-xs text-slate-400">
              {documentName}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-white"
            title="Close"
            aria-label="Close result"
          >
            <X size={17} />
          </button>
        </div>


        {/* SUMMARY */}

        <div className="grid grid-cols-2 gap-3 border-b border-slate-200 p-5 sm:grid-cols-4 dark:border-slate-700">

          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
            <div className="text-[10px] uppercase tracking-wide text-slate-400">
              Status
            </div>

            <div className="mt-1 text-xs font-semibold text-emerald-500">
              {status}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
            <div className="text-[10px] uppercase tracking-wide text-slate-400">
              Confidence
            </div>

            <div className="mt-1 text-sm font-semibold text-slate-800 dark:text-white">
              {confidence !==
              null
                ? `${Math.round(
                    confidence <=
                      1
                      ? confidence *
                          100
                      : confidence,
                  )}%`
                : '—'}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
            <div className="text-[10px] uppercase tracking-wide text-slate-400">
              Validation
            </div>

            <div className="mt-1 text-xs font-semibold text-slate-800 dark:text-white">
              {validationStatus ??
                '—'}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
            <div className="text-[10px] uppercase tracking-wide text-slate-400">
              Document Type
            </div>

            <div className="mt-1 truncate text-xs font-semibold text-slate-800 dark:text-white">
              {result.document_type ??
                '—'}
            </div>
          </div>
        </div>


        {/* RESULT CONTENT */}

        <div className="min-h-0 flex-1 overflow-y-auto p-5">

          {result.error && (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-600 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-400">
              {result.error}
            </div>
          )}


          {/* PROCESSING ID */}

          <div className="mb-4 rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
            <div className="text-[10px] uppercase tracking-wide text-slate-400">
              Processing Job ID
            </div>

            <div className="mt-1 break-all font-mono text-[10px] text-slate-600 dark:text-slate-300">
              {processingJobId}
            </div>
          </div>


          {/* STRUCTURED DATA */}

          <section className="mb-5">
            <div className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
              Structured Data
            </div>

            <div className="rounded-lg border border-slate-200 dark:border-slate-700">
              <pre className="max-h-[24rem] overflow-auto whitespace-pre-wrap break-words p-4 text-[10px] leading-5 text-slate-600 dark:text-slate-300">
                {JSON.stringify(
                  result.structured_data,
                  null,
                  2,
                )}
              </pre>
            </div>
          </section>


          {/* VALIDATION */}

          <section className="mb-5">
            <div className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
              Validation Results
            </div>

            <div className="rounded-lg border border-slate-200 dark:border-slate-700">
              <pre className="max-h-[20rem] overflow-auto whitespace-pre-wrap break-words p-4 text-[10px] leading-5 text-slate-600 dark:text-slate-300">
                {JSON.stringify(
                  result.validation_results,
                  null,
                  2,
                )}
              </pre>
            </div>
          </section>


          {/* KNOWLEDGE */}

          <section className="mb-5">
            <div className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
              Knowledge
            </div>

            <div className="rounded-lg border border-slate-200 dark:border-slate-700">
              <pre className="max-h-[20rem] overflow-auto whitespace-pre-wrap break-words p-4 text-[10px] leading-5 text-slate-600 dark:text-slate-300">
                {JSON.stringify(
                  result.knowledge,
                  null,
                  2,
                )}
              </pre>
            </div>
          </section>


          {/* ARTIFACTS */}

          <section className="mb-5">
            <div className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
              Artifacts
            </div>

            <div className="rounded-lg border border-slate-200 dark:border-slate-700">
              <pre className="max-h-[20rem] overflow-auto whitespace-pre-wrap break-words p-4 text-[10px] leading-5 text-slate-600 dark:text-slate-300">
                {JSON.stringify(
                  result.artifacts,
                  null,
                  2,
                )}
              </pre>
            </div>
          </section>


          {/* RAW TEXT */}

          {result.raw_text && (
            <section className="mb-5">
              <div className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
                Raw Text
              </div>

              <div className="rounded-lg border border-slate-200 dark:border-slate-700">
                <pre className="max-h-[24rem] overflow-auto whitespace-pre-wrap break-words p-4 text-[10px] leading-5 text-slate-600 dark:text-slate-300">
                  {result.raw_text}
                </pre>
              </div>
            </section>
          )}


          {/* RAW RESULT */}

          <details className="mt-4">
            <summary className="cursor-pointer text-xs font-medium text-slate-500 hover:text-cyan-500">
              View complete raw result JSON
            </summary>

            <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-slate-950 p-4 text-[10px] leading-5 text-slate-300">
              {JSON.stringify(
                result,
                null,
                2,
              )}
            </pre>
          </details>
        </div>


        {/* FOOTER */}

        <div className="flex items-center justify-end border-t border-slate-200 px-5 py-3 dark:border-slate-700">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


/* =========================================================
   EXECUTIONS PAGE
========================================================= */

export function ExecutionsPage() {
  const [
    executions,
    setExecutions,
  ] =
    useState<ExecutionRecord[]>(
      [],
    );

  const [
    selected,
    setSelected,
  ] =
    useState<string | null>(
      null,
    );

  const [
    refreshing,
    setRefreshing,
  ] =
    useState(false);


  /* =======================================================
     RESULT STATE
  ======================================================= */

  const [
    loadingResultId,
    setLoadingResultId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    downloadingResultId,
    setDownloadingResultId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    selectedResult,
    setSelectedResult,
  ] =
    useState<
      ProcessingIntelligenceResult | null
    >(null);

  const [
    resultModalOpen,
    setResultModalOpen,
  ] =
    useState(false);

  const [
    resultError,
    setResultError,
  ] =
    useState<string | null>(
      null,
    );


  /* =======================================================
     LOAD EXECUTIONS
  ======================================================= */

  function loadExecutions() {
    const records =
      getExecutions();

    setExecutions(
      records,
    );

    setSelected(
      (
        currentSelected,
      ) => {
        if (
          currentSelected &&
          records.some(
            (item) =>
              item.processingId ===
              currentSelected,
          )
        ) {
          return currentSelected;
        }

        return (
          records[0]
            ?.processingId ??
          null
        );
      },
    );
  }


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    loadExecutions();
  }, []);


  /* =======================================================
     REFRESH ONE EXECUTION
  ======================================================= */

  async function refreshExecution(
    execution: ExecutionRecord,
  ) {
    try {
      const job =
        await getProcessingJob(
          execution.processingId,
        );

      if (!job) {
        console.warn(
          '[ExecutionsPage] Processing job not found:',
          execution.processingId,
        );

        return;
      }

      const detailedJob =
        job as ProcessingJobWithDetails;

      const state =
        buildExecutionState(
          execution,
          {
            status:
              job.status,

            progress:
              job.progress,

            completed_at:
              job.completed_at,

            error:
              job.error,

            message:
              job.message,

            current_stage:
              detailedJob.current_stage ??
              job.current_stage,

            steps:
              detailedJob.steps ??
              job.steps,
          },
        );

      updateExecution(
        execution.processingId,
        state,
      );
    } catch (error) {
      console.error(
        '[ExecutionsPage] Failed to refresh processing job:',
        execution.processingId,
        error,
      );
    }
  }


  /* =======================================================
     POLLING + INITIAL BACKEND HYDRATION
  ======================================================= */

  useEffect(() => {
    let cancelled =
      false;

    let initialHydration =
      true;

    async function refreshJobs() {
      const current =
        getExecutions();

      /*
       * FIRST RUN:
       *
       * Refresh every execution.
       *
       * This is critical because completed executions may
       * still contain the old local 6-step state.
       *
       * The backend returns the authoritative 10 steps.
       */
      const targets =
        initialHydration
          ? current
          : current.filter(
              (execution) =>
                !isTerminalStatus(
                  execution,
                ),
            );

      initialHydration =
        false;

      for (
        const execution of targets
      ) {
        if (cancelled) {
          return;
        }

        await refreshExecution(
          execution,
        );
      }

      if (!cancelled) {
        loadExecutions();
      }
    }

    void refreshJobs();

    const interval =
      window.setInterval(
        () => {
          void refreshJobs();
        },
        2000,
      );

    return () => {
      cancelled = true;

      window.clearInterval(
        interval,
      );
    };
  }, []);


  /* =======================================================
     MANUAL REFRESH
  ======================================================= */

  async function handleRefresh() {
    setRefreshing(
      true,
    );

    try {
      const current =
        getExecutions();

      /*
       * Manual refresh hydrates every execution.
       *
       * This is useful when a user opens the execution page
       * after an execution has already completed.
       */
      for (
        const execution of current
      ) {
        await refreshExecution(
          execution,
        );
      }

      loadExecutions();
    } finally {
      setRefreshing(
        false,
      );
    }
  }


  /* =======================================================
     DELETE EXECUTION
  ======================================================= */

  function handleDeleteExecution(
    processingId: string,
  ) {
    const normalizedId =
      processingId?.trim();

    if (!normalizedId) {
      return;
    }

    const execution =
      executions.find(
        (item) =>
          item.processingId ===
          normalizedId,
      );

    if (!execution) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete "${execution.documentName}" from execution history?\n\nThis removes it from the execution history shown in this UI.`,
      );

    if (!confirmed) {
      return;
    }

    /*
     * Delete the local execution-history record.
     *
     * This does NOT delete the backend document,
     * ProcessingJob, intelligence result, MinIO object,
     * PostgreSQL data, or any other backend resource.
     */
    deleteExecution(
      normalizedId,
    );

    /*
     * Update React state immediately.
     */
    setExecutions(
      (current) =>
        current.filter(
          (item) =>
            item.processingId !==
            normalizedId,
        ),
    );

    /*
     * If the deleted execution was selected,
     * select the first remaining execution.
     */
    setSelected(
      (currentSelected) => {
        if (
          currentSelected !==
          normalizedId
        ) {
          return currentSelected;
        }

        const remaining =
          getExecutions();

        return (
          remaining[0]
            ?.processingId ??
          null
        );
      },
    );

    /*
     * Close any result modal associated with
     * the deleted execution.
     */
    if (
      selected ===
      normalizedId
    ) {
      setSelectedResult(
        null,
      );

      setResultModalOpen(
        false,
      );

      setResultError(
        null,
      );

      setLoadingResultId(
        null,
      );

      setDownloadingResultId(
        null,
      );
    }
  }


  /* =======================================================
     SELECTED EXECUTION
  ======================================================= */

  const exec =
    useMemo(
      () =>
        executions.find(
          (execution) =>
            execution.processingId ===
            selected,
        ) ??
        executions[0] ??
        null,
      [
        executions,
        selected,
      ],
    );


  /* =======================================================
     VIEW RESULT
  ======================================================= */

  async function handleViewResult(
    processingJobId: string,
  ) {
    const normalizedId =
      processingJobId?.trim();

    if (!normalizedId) {
      setResultError(
        'A valid processing job ID is required.',
      );

      return;
    }

    try {
      setLoadingResultId(
        normalizedId,
      );

      setResultError(
        null,
      );

      setSelectedResult(
        null,
      );

      setResultModalOpen(
        false,
      );

      const result =
        await getProcessingIntelligence(
          normalizedId,
        );

      /*
       * At this point the backend has already been verified
       * with curl to return a populated intelligence object.
       */
      if (!result) {
        setResultError(
          'The Document Intelligence result is not available yet.',
        );

        return;
      }

      setSelectedResult(
        result,
      );

      setResultModalOpen(
        true,
      );
    } catch (error) {
      console.error(
        '[ExecutionsPage] Failed to load intelligence result:',
        error,
      );

      setResultError(
        error instanceof Error
          ? error.message
          : 'Unable to load processing result.',
      );

      setResultModalOpen(
        false,
      );
    } finally {
      setLoadingResultId(
        null,
      );
    }
  }


  /* =======================================================
     DOWNLOAD RESULT
  ======================================================= */

  async function handleDownloadResult(
    processingJobId: string,
  ) {
    const normalizedId =
      processingJobId?.trim();

    if (!normalizedId) {
      setResultError(
        'A valid processing job ID is required.',
      );

      return;
    }

    try {
      setDownloadingResultId(
        normalizedId,
      );

      setResultError(
        null,
      );

      const result =
        await downloadProcessingResult(
          normalizedId,
          exec?.documentName,
        );

      if (!result) {
        setResultError(
          'The Document Intelligence result is not available yet.',
        );
      }
    } catch (error) {
      console.error(
        '[ExecutionsPage] Failed to download intelligence result:',
        error,
      );

      setResultError(
        error instanceof Error
          ? error.message
          : 'Unable to download processing result.',
      );
    } finally {
      setDownloadingResultId(
        null,
      );
    }
  }


  /* =======================================================
     EMPTY STATE
  ======================================================= */

  if (!exec) {
    return (
      <Card className="p-10">
        <div className="text-center">
          <Activity
            size={40}
            className="mx-auto text-slate-300"
          />

          <h2 className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
            No executions yet
          </h2>

          <p className="mt-1 text-xs text-slate-400">
            Run a workflow to see
            its processing history
            here.
          </p>
        </div>
      </Card>
    );
  }


  /* =======================================================
     EXECUTION CALCULATIONS
  ======================================================= */

  const steps =
    normalizeSteps(
      exec,
    );

  const completedSteps =
    steps.filter(
      (step) =>
        step.status ===
        'done',
    ).length;

  const totalSteps =
    steps.length;

  const progress =
    typeof exec.progress ===
    'number'
      ? Math.min(
          Math.max(
            exec.progress,
            0,
          ),
          100,
        )
      : totalSteps > 0
        ? Math.round(
            (
              completedSteps /
              totalSteps
            ) *
              100,
          )
        : 0;


  /* =======================================================
     RESULT AVAILABILITY
  ======================================================= */

  const resultAvailable =
    exec.status ===
      'completed' ||
    exec.status ===
      'review_required';

  const isLoadingResult =
    loadingResultId ===
    exec.processingId;

  const isDownloadingResult =
    downloadingResultId ===
    exec.processingId;


  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <>
      <div className="grid grid-cols-1 gap-4 animate-fade-in lg:grid-cols-[1fr_1.2fr]">

        {/* =================================================
            EXECUTION HISTORY
        ================================================= */}

        <Card className="overflow-hidden">

          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-slate-800">

            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Execution History
              </h2>

              <p className="mt-0.5 text-xs text-slate-400">
                Track AI workflow
                runs and processing
                timelines
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                void handleRefresh()
              }
              disabled={refreshing}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-cyan-500 disabled:cursor-not-allowed disabled:opacity-50 dark:hover:bg-slate-800"
              title="Refresh executions"
              aria-label="Refresh executions"
            >
              <RefreshCw
                size={15}
                className={
                  refreshing
                    ? 'animate-spin'
                    : ''
                }
              />
            </button>
          </div>


          <div className="max-h-[calc(100vh-220px)] divide-y divide-slate-50 overflow-y-auto dark:divide-slate-800/50">

            {executions.length ===
              0 && (
              <div className="p-6 text-center text-xs text-slate-400">
                No executions found.
              </div>
            )}

            {executions.map(
              (
                execution,
              ) => (
                <div
                  key={
                    execution.processingId
                  }
                  className={`flex w-full items-center gap-3 px-5 py-3.5 transition-colors ${
                    selected ===
                    execution.processingId
                      ? 'bg-cyan-50 dark:bg-cyan-500/10'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                  }`}
                >

                  {/* EXECUTION SELECTOR */}

                  <button
                    type="button"
                    onClick={() =>
                      setSelected(
                        execution.processingId,
                      )
                    }
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
                        {
                          execution.documentName
                        }
                      </span>
                    </div>

                    <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
                      <span>
                        {
                          execution.workflowName
                        }
                      </span>

                      <span>
                        ·
                      </span>

                      <span>
                        {new Date(
                          execution.createdAt,
                        ).toLocaleString()}
                      </span>
                    </div>
                  </button>


                  {/* STATUS + DURATION */}

                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <ExecutionStatusBadge
                      status={
                        execution.status
                      }
                    />

                    <span className="text-[10px] text-slate-400">
                      {
                        execution.duration
                      }
                    </span>
                  </div>


                  {/* DELETE */}

                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();

                      handleDeleteExecution(
                        execution.processingId,
                      );
                    }}
                    className="shrink-0 rounded-lg p-2 text-slate-300 transition hover:bg-rose-50 hover:text-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-200 dark:text-slate-600 dark:hover:bg-rose-500/10 dark:hover:text-rose-400 dark:focus:ring-rose-500/20"
                    title="Delete execution history"
                    aria-label={`Delete ${execution.documentName} from execution history`}
                  >
                    <Trash2
                      size={15}
                    />
                  </button>


                  {/* CHEVRON */}

                  <ChevronRight
                    size={16}
                    className={`shrink-0 transition-colors ${
                      selected ===
                      execution.processingId
                        ? 'text-cyan-500'
                        : 'text-slate-300 dark:text-slate-600'
                    }`}
                  />
                </div>
              ),
            )}
          </div>
        </Card>


        {/* =================================================
            EXECUTION DETAIL
        ================================================= */}

        <Card>

          {/* HEADER */}

          <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">

            <div className="flex items-center gap-2">
              <Activity
                size={15}
                className="text-cyan-500"
              />

              <h2 className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {
                  exec.workflowName
                }
              </h2>
            </div>

            <div className="mt-2">
              <ExecutionStatusBadge
                status={
                  exec.status
                }
              />
            </div>

            <p className="mt-2 text-xs text-slate-400">
              {
                exec.documentName
              }
              {' · '}
              {
                exec.duration
              }
            </p>

            <p className="mt-1 truncate text-[10px] text-slate-400">
              Processing ID:{' '}
              {
                exec.processingId
              }
            </p>
          </div>


          {/* PROGRESS */}

          <div className="px-5 py-4">

            <div className="mb-2 flex items-center justify-between text-xs">

              <span className="font-medium text-slate-600 dark:text-slate-400">
                Progress
              </span>

              <span className="font-semibold text-slate-900 dark:text-white">
                {progress}%
              </span>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-teal-500 transition-all duration-500"
                style={{
                  width:
                    `${progress}%`,
                }}
              />
            </div>
          </div>


          {/* TIMELINE */}

          <div className="px-5 pb-6">

            <div className="relative">

              {steps.map(
                (
                  step,
                  index,
                ) => (
                  <div
                    key={
                      step.id
                    }
                    className="relative flex gap-4 pb-6 last:pb-0"
                  >

                    {index <
                      steps.length -
                        1 && (
                      <div
                        className={`absolute left-2 top-5 h-full w-px ${
                          step.status ===
                          'done'
                            ? 'bg-emerald-300 dark:bg-emerald-500/30'
                            : 'bg-slate-200 dark:bg-slate-700'
                        }`}
                      />
                    )}

                    <div className="relative z-10 mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-white dark:bg-slate-900">
                      <StepIcon
                        status={
                          step.status
                        }
                      />
                    </div>

                    <div className="flex flex-1 items-center justify-between gap-4">

                      <div>

                        <div
                          className={`text-sm font-medium ${
                            step.status ===
                            'pending'
                              ? 'text-slate-400'
                              : 'text-slate-700 dark:text-slate-200'
                          }`}
                        >
                          {
                            step.label
                          }
                        </div>

                        {step.status ===
                          'active' && (
                          <div className="mt-1 flex items-center gap-1.5">

                            <span className="h-1 w-20 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                              <span className="block h-full w-1/2 animate-pulse rounded-full bg-cyan-500" />
                            </span>

                            <span className="text-[10px] text-cyan-500">
                              Processing…
                            </span>
                          </div>
                        )}

                        {step.status ===
                          'failed' && (
                          <div className="mt-1 text-[10px] text-rose-500">
                            {
                              step.error ||
                              'Step failed — execution halted'
                            }
                          </div>
                        )}

                        {step.status ===
                          'done' && (
                          <div className="mt-0.5 text-[10px] text-slate-400">
                            Completed
                          </div>
                        )}
                      </div>

                      {step.duration && (
                        <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                          {
                            step.duration
                          }
                        </span>
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>


          {/* RESULT ACTIONS */}

          {resultAvailable && (
            <div className="border-t border-slate-100 px-5 py-4 dark:border-slate-800">

              <div className="mb-3">
                <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                  Document Intelligence Result
                </h3>

                <p className="mt-0.5 text-[10px] text-slate-400">
                  View the persisted intelligence result or download it as JSON.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">

                {/* VIEW RESULT */}

                <button
                  type="button"
                  onClick={() =>
                    void handleViewResult(
                      exec.processingId,
                    )
                  }
                  disabled={
                    isLoadingResult ||
                    isDownloadingResult
                  }
                  className="flex items-center gap-2 rounded-lg border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-600 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-400 dark:hover:bg-cyan-500/20"
                >
                  {isLoadingResult ? (
                    <Loader2
                      size={14}
                      className="animate-spin"
                    />
                  ) : (
                    <Eye
                      size={14}
                    />
                  )}

                  {isLoadingResult
                    ? 'Loading…'
                    : 'View Results'}
                </button>


                {/* DOWNLOAD RESULT */}

                <button
                  type="button"
                  onClick={() =>
                    void handleDownloadResult(
                      exec.processingId,
                    )
                  }
                  disabled={
                    isLoadingResult ||
                    isDownloadingResult
                  }
                  className="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
                >
                  {isDownloadingResult ? (
                    <Loader2
                      size={14}
                      className="animate-spin"
                    />
                  ) : (
                    <Download
                      size={14}
                    />
                  )}

                  {isDownloadingResult
                    ? 'Downloading…'
                    : 'Download Result'}
                </button>
              </div>


              {/* RESULT ERROR */}

              {resultError && (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[10px] text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400">
                  {resultError}
                </div>
              )}
            </div>
          )}


          {/* RESULT ERROR WHEN ACTIONS ARE HIDDEN */}

          {!resultAvailable &&
            resultError && (
              <div className="border-t border-slate-100 px-5 py-4 dark:border-slate-800">
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[10px] text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400">
                  {resultError}
                </div>
              </div>
            )}


          {/* FOOTER */}

          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 dark:border-slate-800">

            <div className="flex min-w-0 items-center gap-1.5">

              <span
                className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                  exec.status ===
                  'completed'
                    ? stepColor(
                        'done',
                      )
                    : exec.status ===
                        'failed'
                      ? stepColor(
                          'failed',
                        )
                      : exec.status ===
                          'review_required'
                        ? 'bg-violet-500'
                        : stepColor(
                            'active',
                          )
                }`}
              />

              <span className="text-xs text-slate-500 dark:text-slate-400">
                {
                  completedSteps
                }{' '}
                of{' '}
                {
                  totalSteps
                }{' '}
                steps complete
              </span>
            </div>


            {(
              exec.status ===
                'processing' ||
              exec.status ===
                'queued' ||
              exec.status ===
                'pending'
            ) && (
              <span className="text-xs text-cyan-500">
                Processing…
              </span>
            )}

            {exec.status ===
              'completed' && (
              <span className="text-xs text-emerald-500">
                Completed
              </span>
            )}

            {exec.status ===
              'failed' && (
              <span className="text-xs text-rose-500">
                Failed
              </span>
            )}

            {exec.status ===
              'review_required' && (
              <span className="text-xs text-violet-500">
                Needs Review
              </span>
            )}

            {exec.error && (
              <span
                className="ml-3 max-w-xs truncate text-xs text-rose-500"
                title={
                  exec.error
                }
              >
                {
                  exec.error
                }
              </span>
            )}
          </div>
        </Card>
      </div>


      {/* =====================================================
          RESULT MODAL
      ===================================================== */}

      {resultModalOpen &&
        selectedResult && (
          <ResultModal
            result={
              selectedResult
            }
            documentName={
              exec.documentName
            }
            onClose={() => {
              setResultModalOpen(
                false,
              );

              setSelectedResult(
                null,
              );

              setResultError(
                null,
              );
            }}
          />
        )}
    </>
  );
}