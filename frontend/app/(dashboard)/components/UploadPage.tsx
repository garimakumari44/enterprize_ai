"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  UploadCloud,
  FileText,
  X,
  CheckCircle2,
  Zap,
  AlertCircle,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { Card } from "./ui/Card";
import { Button } from "./ui/Button";
import { uploadDocument } from "../../../lib/documents";
import { useNav } from "../../../context/NavContext";

/* ============================================================
   API BASE URL
   ============================================================ */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api/v1";

/* ============================================================
   Types
   ============================================================ */

type Workflow = {
  id: string;
  name: string;
  description?: string;
  is_active?: boolean;
};

type StagedFile = {
  file: File;
  name: string;
  size: string;
  status: "ready" | "uploading" | "done" | "failed";
  documentId?: string;
  jobId?: string | null;
  error?: string;
};

type WorkflowResponse = {
  items?: Workflow[];
  workflows?: Workflow[];
  data?: Workflow[];
};

/* ============================================================
   Helpers
   ============================================================ */

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(0)} KB`;
  }

  if (size < 1024 * 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function getAuthHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("accessToken")
      : null;

  const headers: HeadersInit = {
    Accept: "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

/* ============================================================
   Upload Error Normalization
   ============================================================ */

/**
 * FastAPI validation errors commonly look like:
 *
 * {
 *   "detail": [
 *     {
 *       "type": "missing",
 *       "loc": ["body", "file"],
 *       "msg": "Field required",
 *       "input": null
 *     }
 *   ]
 * }
 *
 * Never return an object or array from this function because
 * the result is rendered directly by React.
 */
function getUploadError(error: unknown): string {
  /*
   * Axios-style error.
   */
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const axiosError = error as {
      response?: {
        status?: number;
        data?: {
          detail?:
            | string
            | {
                msg?: string;
                message?: string;
                detail?: string;
              }
            | Array<{
                type?: string;
                loc?: Array<string | number>;
                msg?: string;
                input?: unknown;
              }>;
          message?: string;
        };
      };
      message?: string;
    };

    const responseData =
      axiosError.response?.data;

    const detail = responseData?.detail;

    /*
     * Normal FastAPI HTTPException:
     *
     * {
     *   "detail": "Unsupported document type..."
     * }
     */
    if (typeof detail === "string") {
      return detail;
    }

    /*
     * FastAPI / Pydantic validation error:
     *
     * {
     *   "detail": [...]
     * }
     */
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            item &&
            typeof item === "object" &&
            typeof item.msg === "string"
          ) {
            return item.msg;
          }

          return null;
        })
        .filter(
          (message): message is string =>
            Boolean(message)
        );

      if (messages.length > 0) {
        return messages.join("; ");
      }

      return "The upload request failed validation.";
    }

    /*
     * Some APIs may return an object as detail.
     */
    if (
      detail &&
      typeof detail === "object"
    ) {
      if (
        typeof detail.msg === "string"
      ) {
        return detail.msg;
      }

      if (
        typeof detail.message === "string"
      ) {
        return detail.message;
      }

      if (
        typeof detail.detail === "string"
      ) {
        return detail.detail;
      }
    }

    /*
     * Generic API message.
     */
    if (
      typeof responseData?.message ===
      "string"
    ) {
      return responseData.message;
    }

    /*
     * Axios fallback.
     */
    if (
      typeof axiosError.message === "string" &&
      axiosError.message.trim()
    ) {
      return axiosError.message;
    }

    /*
     * HTTP status fallback.
     */
    if (axiosError.response?.status) {
      return `Upload failed (${axiosError.response.status}).`;
    }
  }

  /*
   * Standard JavaScript Error.
   */
  if (error instanceof Error) {
    return error.message;
  }

  /*
   * Safe final fallback.
   */
  return "Upload failed.";
}

/* ============================================================
   Fetch Workflows
   ============================================================ */

async function fetchWorkflows(): Promise<Workflow[]> {
  const response = await fetch(
    `${API_BASE_URL}/workflows`,
    {
      method: "GET",
      headers: getAuthHeaders(),
      credentials: "include",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    let message = `Failed to load workflows (${response.status})`;

    try {
      const data = await response.json();

      if (
        typeof data?.detail === "string"
      ) {
        message = data.detail;
      } else if (
        typeof data?.message === "string"
      ) {
        message = data.message;
      }
    } catch {
      // Ignore invalid JSON responses.
    }

    throw new Error(message);
  }

  const data:
    | WorkflowResponse
    | Workflow[] =
    await response.json();

  if (Array.isArray(data)) {
    return data;
  }

  return (
    data.items ??
    data.workflows ??
    data.data ??
    []
  );
}

/* ============================================================
   Component
   ============================================================ */

export function UploadPage() {
  const { setPage } = useNav();

  const inputRef =
    useRef<HTMLInputElement>(null);

  const [dragging, setDragging] =
    useState(false);

  const [files, setFiles] =
    useState<StagedFile[]>([]);

  const [workflows, setWorkflows] =
    useState<Workflow[]>([]);

  const [selectedWorkflow, setSelectedWorkflow] =
    useState("");

  const [loadingWorkflows, setLoadingWorkflows] =
    useState(true);

  const [workflowError, setWorkflowError] =
    useState<string | null>(null);

  const [uploading, setUploading] =
    useState(false);

  /* ============================================================
     Load Workflows
     ============================================================ */

  const loadWorkflows = async () => {
    try {
      setLoadingWorkflows(true);
      setWorkflowError(null);

      const data = await fetchWorkflows();

      const activeWorkflows = data.filter(
        (workflow) =>
          workflow.is_active !== false
      );

      setWorkflows(activeWorkflows);

      setSelectedWorkflow((current) => {
        const stillExists =
          current &&
          activeWorkflows.some(
            (workflow) =>
              workflow.id === current
          );

        if (stillExists) {
          return current;
        }

        return (
          activeWorkflows[0]?.id ?? ""
        );
      });
    } catch (error) {
      console.error(
        "Failed to load workflows:",
        error
      );

      setWorkflowError(
        error instanceof Error
          ? error.message
          : "Failed to load workflows"
      );

      setWorkflows([]);
      setSelectedWorkflow("");
    } finally {
      setLoadingWorkflows(false);
    }
  };

  /* ============================================================
     Initial Workflow Load
     ============================================================ */

  useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        setLoadingWorkflows(true);
        setWorkflowError(null);

        const data =
          await fetchWorkflows();

        if (!mounted) {
          return;
        }

        const activeWorkflows =
          data.filter(
            (workflow) =>
              workflow.is_active !== false
          );

        setWorkflows(activeWorkflows);

        setSelectedWorkflow(
          activeWorkflows[0]?.id ?? ""
        );
      } catch (error) {
        if (!mounted) {
          return;
        }

        console.error(
          "Failed to load workflows:",
          error
        );

        setWorkflowError(
          error instanceof Error
            ? error.message
            : "Failed to load workflows"
        );

        setWorkflows([]);
        setSelectedWorkflow("");
      } finally {
        if (mounted) {
          setLoadingWorkflows(false);
        }
      }
    };

    initialize();

    return () => {
      mounted = false;
    };
  }, []);

  /* ============================================================
     Stage Files
     ============================================================ */

  const stageFiles = (
    list: FileList | null
  ) => {
    if (!list || uploading) {
      return;
    }

    const incomingFiles =
      Array.from(list);

    if (incomingFiles.length === 0) {
      return;
    }

    const staged: StagedFile[] =
      incomingFiles.map((file) => ({
        file,
        name: file.name,
        size: formatFileSize(file.size),
        status: "ready",
      }));

    setFiles((previous) => [
      ...previous,
      ...staged,
    ]);
  };

  /* ============================================================
     Remove File
     ============================================================ */

  const removeFile = (index: number) => {
    if (uploading) {
      return;
    }

    setFiles((previous) =>
      previous.filter(
        (_, currentIndex) =>
          currentIndex !== index
      )
    );
  };

  /* ============================================================
     Upload Files
     ============================================================ */

  const process = async () => {
    if (uploading) {
      return;
    }

    const pendingFiles =
      files.filter(
        (file) =>
          file.status === "ready" ||
          file.status === "failed"
      );

    if (pendingFiles.length === 0) {
      return;
    }

    if (!selectedWorkflow) {
      setFiles((previous) =>
        previous.map((file) =>
          file.status === "ready" ||
          file.status === "failed"
            ? {
                ...file,
                status: "failed",
                error:
                  "Please select an AI workflow before uploading.",
              }
            : file
        )
      );

      return;
    }

    setUploading(true);

    try {
      for (const stagedFile of pendingFiles) {
        /*
         * Mark current file as uploading.
         */
        setFiles((previous) =>
          previous.map((file) =>
            file.file === stagedFile.file
              ? {
                  ...file,
                  status: "uploading",
                  error: undefined,
                }
              : file
          )
        );

        try {
          /*
           * uploadDocument() accepts the File object.
           */
          const response =
            await uploadDocument(
              stagedFile.file
            );

          /*
           * Upload succeeded.
           */
          setFiles((previous) =>
            previous.map((file) =>
              file.file === stagedFile.file
                ? {
                    ...file,
                    status: "done",
                    documentId:
                      response.document_id,
                    jobId:
                      response.job_id,
                    error: undefined,
                  }
                : file
            )
          );
        } catch (error) {
          console.error(
            `Failed to upload document: ${stagedFile.name}`,
            error
          );

          const errorMessage =
            getUploadError(error);

          console.error(
            "Normalized upload error:",
            errorMessage
          );

          /*
           * IMPORTANT:
           * errorMessage is guaranteed to be
           * a string, so React can safely render it.
           */
          setFiles((previous) =>
            previous.map((file) =>
              file.file === stagedFile.file
                ? {
                    ...file,
                    status: "failed",
                    error: errorMessage,
                  }
                : file
            )
          );
        }
      }
    } finally {
      setUploading(false);
    }
  };

  /* ============================================================
     Drag & Drop
     ============================================================ */

  const handleDrop = (
    event: React.DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();

    setDragging(false);

    if (uploading) {
      return;
    }

    stageFiles(
      event.dataTransfer.files
    );
  };

  /* ============================================================
     Derived State
     ============================================================ */

  const hasFiles =
    files.length > 0;

  const allDone =
    hasFiles &&
    files.every(
      (file) =>
        file.status === "done"
    );

  const hasFailed =
    files.some(
      (file) =>
        file.status === "failed"
    );

  const hasPendingFiles =
    files.some(
      (file) =>
        file.status === "ready" ||
        file.status === "failed"
    );

  const canProcess =
    !uploading &&
    !loadingWorkflows &&
    Boolean(selectedWorkflow) &&
    hasPendingFiles;

  const selectedWorkflowObject =
    workflows.find(
      (workflow) =>
        workflow.id === selectedWorkflow
    );

  /* ============================================================
     Render
     ============================================================ */

  return (
    <div className="mx-auto max-w-3xl space-y-5 animate-fade-in">

      {/* ======================================================
          Drop Zone
          ====================================================== */}

      <Card
        className={`overflow-hidden transition-all ${
          dragging
            ? "border-cyan-400 ring-2 ring-cyan-500/20"
            : ""
        }`}
      >
        <div
          onDragOver={(event) => {
            event.preventDefault();

            if (!uploading) {
              setDragging(true);
            }
          }}
          onDragLeave={() =>
            setDragging(false)
          }
          onDrop={handleDrop}
          onClick={() => {
            if (!uploading) {
              inputRef.current?.click();
            }
          }}
          className={`cursor-pointer p-12 text-center ${
            uploading
              ? "cursor-not-allowed opacity-80"
              : ""
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            disabled={uploading}
            accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.eml"
            onChange={(event) => {
              stageFiles(
                event.target.files
              );

              event.target.value = "";
            }}
          />

          <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-sky-50 to-cyan-50 dark:from-slate-800 dark:to-slate-800/50">
            <UploadCloud
              size={32}
              className="text-cyan-500"
            />
          </div>

          <h3 className="mt-4 text-base font-semibold text-slate-800 dark:text-white">
            {dragging
              ? "Drop files to upload"
              : "Drag & drop documents here"}
          </h3>

          <p className="mt-1 text-sm text-slate-400">
            or click to browse — PDF, DOCX,
            XLSX, JPG, PNG, EML
          </p>

          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {[
              "PDF",
              "DOCX",
              "XLSX",
              "JPG",
              "PNG",
              "EML",
            ].map((type) => (
              <span
                key={type}
                className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[10px] font-medium text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      </Card>

      {/* ======================================================
          Workflow Selector
          ====================================================== */}

      <Card className="p-5">
        <div className="mb-2 flex items-center justify-between">
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">
            Select AI Workflow
          </label>

          {!loadingWorkflows && (
            <button
              type="button"
              onClick={loadWorkflows}
              disabled={uploading}
              className="flex items-center gap-1 text-xs text-slate-400 transition-colors hover:text-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw size={12} />
              Refresh
            </button>
          )}
        </div>

        {loadingWorkflows ? (
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 p-4 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <Loader2
              size={16}
              className="animate-spin"
            />
            Loading workflows...
          </div>
        ) : workflowError ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 dark:border-rose-500/20 dark:bg-rose-500/10">
            <div className="flex items-start gap-2 text-sm text-rose-600 dark:text-rose-400">
              <AlertCircle
                size={16}
                className="mt-0.5 shrink-0"
              />

              <div>
                <div className="font-medium">
                  Unable to load workflows
                </div>

                <div className="mt-1 text-xs opacity-80">
                  {workflowError}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={loadWorkflows}
              disabled={loadingWorkflows}
              className="mt-3 flex items-center gap-1.5 text-xs font-medium text-rose-600 hover:text-rose-700 dark:text-rose-400"
            >
              <RefreshCw size={12} />
              Try again
            </button>
          </div>
        ) : workflows.length === 0 ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/20 dark:bg-amber-500/10">
            <div className="flex items-start gap-2 text-sm text-amber-700 dark:text-amber-400">
              <AlertCircle
                size={16}
                className="mt-0.5 shrink-0"
              />

              <div>
                <div className="font-medium">
                  No active workflows
                </div>

                <div className="mt-1 text-xs opacity-80">
                  Create or activate a workflow
                  before processing documents.
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {workflows.map(
                (workflow) => (
                  <button
                    key={workflow.id}
                    type="button"
                    disabled={uploading}
                    onClick={() =>
                      setSelectedWorkflow(
                        workflow.id
                      )
                    }
                    className={`rounded-lg border p-3 text-left transition-all ${
                      selectedWorkflow ===
                      workflow.id
                        ? "border-cyan-400 bg-cyan-50 ring-1 ring-cyan-400/20 dark:border-cyan-500/40 dark:bg-cyan-500/10"
                        : "border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600"
                    } ${
                      uploading
                        ? "cursor-not-allowed opacity-60"
                        : ""
                    }`}
                  >
                    <div className="text-sm font-medium text-slate-800 dark:text-white">
                      {workflow.name}
                    </div>

                    {workflow.description && (
                      <div className="mt-1 line-clamp-2 text-[11px] text-slate-400">
                        {
                          workflow.description
                        }
                      </div>
                    )}
                  </button>
                )
              )}
            </div>

            {selectedWorkflowObject && (
              <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                Selected workflow:{" "}
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  {
                    selectedWorkflowObject.name
                  }
                </span>
              </div>
            )}
          </>
        )}
      </Card>

      {/* ======================================================
          Staged Files
          ====================================================== */}

      {hasFiles && (
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-800 dark:text-white">
                {files.length}{" "}
                {files.length === 1
                  ? "file"
                  : "files"}
              </h3>

              {selectedWorkflowObject && (
                <p className="mt-0.5 text-xs text-slate-400">
                  Workflow:{" "}
                  {
                    selectedWorkflowObject.name
                  }
                </p>
              )}
            </div>

            <Button
              size="sm"
              onClick={process}
              disabled={!canProcess}
            >
              {uploading ? (
                <Loader2
                  size={14}
                  className="animate-spin"
                />
              ) : (
                <Zap size={14} />
              )}

              {uploading
                ? "Uploading..."
                : hasFailed
                  ? "Retry Upload"
                  : "Process with AI"}
            </Button>
          </div>

          <div className="space-y-2">
            {files.map(
              (file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="rounded-lg border border-slate-200 p-3 dark:border-slate-800"
                >
                  <div className="flex items-center gap-3">
                    <FileText
                      size={18}
                      className="shrink-0 text-cyan-500"
                    />

                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
                        {file.name}
                      </div>

                      <div className="text-xs text-slate-400">
                        {file.size}
                      </div>
                    </div>

                    {file.status ===
                      "uploading" && (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                          <div className="h-full w-1/2 animate-pulse rounded-full bg-cyan-500" />
                        </div>

                        <Loader2
                          size={15}
                          className="animate-spin text-cyan-500"
                        />
                      </div>
                    )}

                    {file.status ===
                      "done" && (
                      <CheckCircle2
                        size={18}
                        className="shrink-0 text-emerald-500"
                      />
                    )}

                    {file.status ===
                      "failed" && (
                      <AlertCircle
                        size={18}
                        className="shrink-0 text-rose-500"
                      />
                    )}

                    {file.status ===
                      "ready" &&
                      !uploading && (
                        <button
                          type="button"
                          onClick={() =>
                            removeFile(
                              index
                            )
                          }
                          className="text-slate-400 transition-colors hover:text-rose-500"
                          aria-label={`Remove ${file.name}`}
                        >
                          <X size={16} />
                        </button>
                      )}
                  </div>

                  {file.status ===
                    "failed" &&
                    file.error && (
                      <div className="mt-2 rounded-md bg-rose-50 px-2.5 py-2 text-xs text-rose-500 dark:bg-rose-500/10 dark:text-rose-400">
                        {file.error}
                      </div>
                    )}

                  {file.status ===
                    "done" &&
                    file.jobId && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        Processing job created:{" "}
                        <span className="font-mono text-slate-500 dark:text-slate-300">
                          {file.jobId}
                        </span>
                      </div>
                    )}

                  {file.status ===
                    "done" &&
                    !file.jobId && (
                      <div className="mt-2 text-[11px] text-emerald-500">
                        Document uploaded
                        successfully.
                      </div>
                    )}
                </div>
              )
            )}
          </div>

          {/* ==================================================
              Success
              ================================================== */}

          {allDone && (
            <div className="mt-4 flex flex-col gap-3 rounded-lg bg-emerald-50 p-3 sm:flex-row sm:items-center dark:bg-emerald-500/10">
              <div className="flex items-center gap-2">
                <CheckCircle2
                  size={16}
                  className="shrink-0 text-emerald-600 dark:text-emerald-400"
                />

                <span className="text-sm text-emerald-700 dark:text-emerald-400">
                  All files uploaded and
                  queued for AI
                  processing.
                </span>
              </div>

              <button
                type="button"
                onClick={() =>
                  setPage("documents")
                }
                className="sm:ml-auto text-left text-xs font-medium text-cyan-600 hover:text-cyan-700 dark:text-cyan-400"
              >
                View documents →
              </button>
            </div>
          )}

          {/* ==================================================
              Partial Failure
              ================================================== */}

          {!uploading &&
            hasFailed &&
            !allDone && (
              <div className="mt-4 flex items-start gap-2 rounded-lg bg-amber-50 p-3 dark:bg-amber-500/10">
                <AlertCircle
                  size={16}
                  className="mt-0.5 shrink-0 text-amber-600 dark:text-amber-400"
                />

                <div className="text-xs text-amber-700 dark:text-amber-400">
                  Some files could not be
                  uploaded. Fix the failed
                  files and select{" "}
                  <span className="font-medium">
                    Retry Upload
                  </span>{" "}
                  to try again.
                </div>
              </div>
            )}
        </Card>
      )}
    </div>
  );
}