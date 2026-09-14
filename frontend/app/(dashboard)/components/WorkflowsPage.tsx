"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  Plus,
  Play,
  MoreHorizontal,
  Workflow as WorkflowIcon,
  Pencil,
  Trash2,
} from "lucide-react";

import { Card } from "./ui/Card";
import { Button } from "./ui/Button";

import {
  workflowPalette,
  type PaletteCategory,
} from "../../../lib/workflowPalette";

import {
  createWorkflow,
  deleteWorkflow,
  getLibraryDocuments,
  getWorkflows,
  updateWorkflow,
} from "../../../lib/api/workflowApi";

import { startProcessingJob } from "../../../lib/executionApi";

import {
  createDefaultExecutionSteps,
  createExecution,
  normalizeExecutionStatus,
} from "../../../lib/execution";

import type {
  WorkflowDefinition,
  WorkflowNode,
  WorkflowOperation,
  WorkflowType,
} from "../../../types/workflow";

import { WorkflowBuilder } from "./workflows/WorkflowBuilder";


/* =========================================================
   COLORS
========================================================= */

export interface WorkflowColor {
  bg: string;
  border: string;
  text: string;
  dot: string;
}

export const colorMap: Record<
  string,
  WorkflowColor
> = {
  sky: {
    bg: "bg-sky-50 dark:bg-sky-500/10",
    border:
      "border-sky-200 dark:border-sky-500/30",
    text:
      "text-sky-700 dark:text-sky-400",
    dot: "bg-sky-500",
  },

  violet: {
    bg:
      "bg-violet-50 dark:bg-violet-500/10",
    border:
      "border-violet-200 dark:border-violet-500/30",
    text:
      "text-violet-700 dark:text-violet-400",
    dot: "bg-violet-500",
  },

  cyan: {
    bg:
      "bg-cyan-50 dark:bg-cyan-500/10",
    border:
      "border-cyan-200 dark:border-cyan-500/30",
    text:
      "text-cyan-700 dark:text-cyan-400",
    dot: "bg-cyan-500",
  },

  indigo: {
    bg:
      "bg-indigo-50 dark:bg-indigo-500/10",
    border:
      "border-indigo-200 dark:border-indigo-500/30",
    text:
      "text-indigo-700 dark:text-indigo-400",
    dot: "bg-indigo-500",
  },

  amber: {
    bg:
      "bg-amber-50 dark:bg-amber-500/10",
    border:
      "border-amber-200 dark:border-amber-500/30",
    text:
      "text-amber-700 dark:text-amber-400",
    dot: "bg-amber-500",
  },

  emerald: {
    bg:
      "bg-emerald-50 dark:bg-emerald-500/10",
    border:
      "border-emerald-200 dark:border-emerald-500/30",
    text:
      "text-emerald-700 dark:text-emerald-400",
    dot: "bg-emerald-500",
  },
};


/* =========================================================
   CATEGORY HELPERS
========================================================= */

export function categoryForOperation(
  operation: WorkflowOperation,
): PaletteCategory | undefined {
  return workflowPalette.find(
    category =>
      category.items.some(
        item =>
          item.operation ===
          operation,
      ),
  );
}


/* =========================================================
   COLOR HELPER
========================================================= */

function getWorkflowColor(
  category:
    | PaletteCategory
    | undefined,
): WorkflowColor {
  const colorName =
    typeof category?.color === "string"
      ? category.color
      : "cyan";

  return (
    colorMap[colorName] ??
    colorMap.cyan
  );
}


/* =========================================================
   CREATE NODE
========================================================= */

export function createNode(
  operation: WorkflowOperation,
): WorkflowNode {
  const category =
    categoryForOperation(
      operation,
    );

  const item =
    category?.items.find(
      paletteItem =>
        paletteItem.operation ===
        operation,
    );

  const id =
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`;

  return {
    id,

    type:
      category?.type ?? "ai",

    operation,

    label:
      item?.label ??
      operation,

    description:
      item?.description ??
      "Workflow operation",

    config: {
      ...(item?.defaultConfig ?? {}),
    },
  };
}


/* =========================================================
   WORKFLOW NORMALIZATION
========================================================= */

export function normalizeWorkflow(
  workflow: WorkflowDefinition,
): WorkflowDefinition {
  const workflowType: WorkflowType =
    workflow.workflow_type ??
    "document_processing";

  return {
    ...workflow,

    nodes:
      Array.isArray(workflow.nodes)
        ? workflow.nodes
        : [],

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
      Boolean(workflow.enabled),
  };
}


/* =========================================================
   NORMALIZE WORKFLOWS
========================================================= */

function normalizeWorkflows(
  workflows: WorkflowDefinition[],
): WorkflowDefinition[] {
  if (!Array.isArray(workflows)) {
    return [];
  }

  return workflows.map(
    normalizeWorkflow,
  );
}


/* =========================================================
   INITIAL EXECUTION STATUS
========================================================= */

function getInitialExecutionStatus(
  job: {
    status?: string | null;
    progress?: number | null;
    completed_at?: string | null;
  },
) {
  const status =
    normalizeExecutionStatus(
      job.status,
    );

  if (
    status === "completed" &&
    !job.completed_at &&
    (job.progress ?? 0) < 100
  ) {
    return "processing" as const;
  }

  return status;
}


/* =========================================================
   REQUIRED STRING HELPER

   Converts optional/null backend fields into a safe
   required string or throws a useful error.

   This is what fixes:

   Type 'string | undefined' is not assignable to type 'string'
========================================================= */

function requireString(
  value: unknown,
  fieldName: string,
): string {
  if (
    typeof value !== "string" ||
    value.trim().length === 0
  ) {
    throw new Error(
      `Backend response is missing required field: ${fieldName}`,
    );
  }

  return value;
}


/* =========================================================
   OPTIONAL STRING HELPER
========================================================= */

function optionalString(
  value: unknown,
): string | undefined {
  return typeof value === "string"
    ? value
    : undefined;
}


/* =========================================================
   MAIN PAGE
========================================================= */

export function WorkflowsPage() {
  const [
    showBuilder,
    setShowBuilder,
  ] = useState(false);

  const [
    workflows,
    setWorkflows,
  ] = useState<WorkflowDefinition[]>(
    [],
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    editingWorkflow,
    setEditingWorkflow,
  ] =
    useState<WorkflowDefinition | null>(
      null,
    );

  const [
    runningWorkflowId,
    setRunningWorkflowId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    openMenuWorkflowId,
    setOpenMenuWorkflowId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    deletingWorkflowId,
    setDeletingWorkflowId,
  ] =
    useState<string | null>(
      null,
    );


  /* =======================================================
     LOAD WORKFLOWS
  ======================================================= */

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const data =
          await getWorkflows();

        if (!mounted) {
          return;
        }

        setWorkflows(
          normalizeWorkflows(
            Array.isArray(data)
              ? data
              : [],
          ),
        );
      } catch (error) {
        console.error(
          "Failed to load workflows:",
          error,
        );

        if (mounted) {
          setWorkflows([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, []);


  /* =======================================================
     NEW WORKFLOW
  ======================================================= */

  function handleNewWorkflow() {
    const workflow =
      normalizeWorkflow({
        name: "New Workflow",

        description:
          "AI document processing workflow",

        workflow_type:
          "document_processing",

        nodes: [
          createNode(
            "library_document",
          ),

          createNode(
            "text_extraction",
          ),

          createNode(
            "save_result",
          ),
        ],

        enabled: false,
      });

    setEditingWorkflow(
      workflow,
    );

    setShowBuilder(true);
  }


  /* =======================================================
     EDIT WORKFLOW
  ======================================================= */

  function handleEdit(
    workflow: WorkflowDefinition,
  ) {
    setOpenMenuWorkflowId(
      null,
    );

    setEditingWorkflow(
      normalizeWorkflow(
        workflow,
      ),
    );

    setShowBuilder(true);
  }


  /* =======================================================
     SAVE WORKFLOW
  ======================================================= */

  async function handleSave(
    workflow: WorkflowDefinition,
  ) {
    const safeWorkflow =
      normalizeWorkflow(
        workflow,
      );

    try {
      let saved:
        WorkflowDefinition;

      if (safeWorkflow.id) {
        saved =
          await updateWorkflow(
            safeWorkflow.id,
            safeWorkflow,
          );
      } else {
        saved =
          await createWorkflow(
            safeWorkflow,
          );
      }

      const normalizedSaved =
        normalizeWorkflow(
          saved,
        );

      setWorkflows(
        previous => {
          const existing =
            previous.find(
              item =>
                item.id ===
                normalizedSaved.id,
            );

          if (existing) {
            return previous.map(
              item =>
                item.id ===
                normalizedSaved.id
                  ? normalizedSaved
                  : item,
            );
          }

          return [
            ...previous,
            normalizedSaved,
          ];
        },
      );

      setEditingWorkflow(
        normalizedSaved,
      );

      setShowBuilder(false);

      alert(
        "Workflow saved successfully.",
      );
    } catch (error) {
      console.error(
        "Failed to save workflow:",
        error,
      );

      alert(
        "Failed to save workflow.",
      );

      throw error;
    }
  }


  /* =======================================================
     DELETE WORKFLOW
  ======================================================= */

  async function handleDelete(
    workflow: WorkflowDefinition,
  ) {
    setOpenMenuWorkflowId(
      null,
    );

    if (!workflow.id) {
      alert(
        "Cannot delete a workflow without an ID.",
      );

      return;
    }

    const confirmed =
      window.confirm(
        `Delete workflow "${workflow.name}"?\n\nThis action cannot be undone.`,
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingWorkflowId(
        workflow.id,
      );

      await deleteWorkflow(
        workflow.id,
      );

      setWorkflows(
        previous =>
          previous.filter(
            item =>
              item.id !==
              workflow.id,
          ),
      );

      if (
        editingWorkflow?.id ===
        workflow.id
      ) {
        setEditingWorkflow(
          null,
        );

        setShowBuilder(false);
      }

      alert(
        "Workflow deleted successfully.",
      );
    } catch (error) {
      console.error(
        "Failed to delete workflow:",
        error,
      );

      alert(
        "Failed to delete workflow.",
      );
    } finally {
      setDeletingWorkflowId(
        null,
      );
    }
  }


  /* =======================================================
     RENAME WORKFLOW
  ======================================================= */

  async function handleRename(
    workflow: WorkflowDefinition,
  ) {
    setOpenMenuWorkflowId(
      null,
    );

    if (!workflow.id) {
      alert(
        "Cannot rename a workflow without an ID.",
      );

      return;
    }

    const currentName =
      workflow.name || "";

    const nextName =
      window.prompt(
        "Enter a new workflow name:",
        currentName,
      );

    if (nextName === null) {
      return;
    }

    const trimmedName =
      nextName.trim();

    if (!trimmedName) {
      alert(
        "Workflow name cannot be empty.",
      );

      return;
    }

    if (
      trimmedName ===
      currentName
    ) {
      return;
    }

    try {
      const updatedWorkflow =
        normalizeWorkflow({
          ...workflow,
          name: trimmedName,
        });

      const saved =
        await updateWorkflow(
          workflow.id,
          updatedWorkflow,
        );

      const normalizedSaved =
        normalizeWorkflow(
          saved,
        );

      setWorkflows(
        previous =>
          previous.map(
            item =>
              item.id ===
              normalizedSaved.id
                ? normalizedSaved
                : item,
          ),
      );

      if (
        editingWorkflow?.id ===
        normalizedSaved.id
      ) {
        setEditingWorkflow(
          normalizedSaved,
        );
      }

      alert(
        "Workflow renamed successfully.",
      );
    } catch (error) {
      console.error(
        "Failed to rename workflow:",
        error,
      );

      alert(
        "Failed to rename workflow.",
      );
    }
  }


  /* =======================================================
     RUN WORKFLOW
  ======================================================= */

  async function handleRun(
    workflow: WorkflowDefinition,
  ) {
    const safeWorkflow =
      normalizeWorkflow(
        workflow,
      );

    if (!safeWorkflow.id) {
      alert(
        "Save the workflow before running it.",
      );

      return;
    }

    try {
      setRunningWorkflowId(
        safeWorkflow.id,
      );

      const libraryNode =
        safeWorkflow.nodes.find(
          node =>
            node.operation ===
            "library_document",
        );

      if (!libraryNode) {
        alert(
          "This workflow does not contain a Library Document node.",
        );

        return;
      }


      /* ---------------------------------------------------
         READ DOCUMENT ID
      --------------------------------------------------- */

      const selectedDocumentId =
        libraryNode.config?.[
          "document_id"
        ];

      if (
        typeof selectedDocumentId !==
          "string" ||
        selectedDocumentId.trim()
          .length === 0
      ) {
        alert(
          "Please select a library document in the Library Document node before running the workflow.",
        );

        return;
      }


      /* ---------------------------------------------------
         LOAD DOCUMENTS
      --------------------------------------------------- */

      const documents =
        await getLibraryDocuments();

      const selectedDocument =
        documents.find(
          document =>
            document.id ===
            selectedDocumentId,
        );

      if (!selectedDocument) {
        alert(
          "The selected document is no longer available in the library. Please select another document.",
        );

        return;
      }


      /* ---------------------------------------------------
         START PROCESSING
      --------------------------------------------------- */

      const job =
        await startProcessingJob({
          documentId:
            selectedDocument.id,

          workflowId:
            safeWorkflow.id,

          includeWorkflowId:
            false,
        });

      console.log(
        "[WorkflowsPage] Processing job created:",
        job,
      );


      /* ---------------------------------------------------
         NORMALIZE REQUIRED JOB FIELDS

         IMPORTANT:
         The backend/API type can contain:

             string | undefined
             string | null

         ExecutionRecord requires:

             string

         Therefore we validate before creating it.
      --------------------------------------------------- */

      const processingId =
        requireString(
          job.processing_id,
          "processing_id",
        );

      const documentId =
        requireString(
          job.document_id,
          "document_id",
        );


      /* ---------------------------------------------------
         OPTIONAL DOCUMENT VERSION
      --------------------------------------------------- */

      const documentVersionId =
        optionalString(
          job.document_version_id,
        );


      /* ---------------------------------------------------
         STATUS
      --------------------------------------------------- */

      const initialStatus =
        getInitialExecutionStatus({
          status:
            job.status,

          progress:
            job.progress,

          completed_at:
            job.completed_at,
        });


      /* ---------------------------------------------------
         PROGRESS
      --------------------------------------------------- */

      const initialProgress =
        initialStatus ===
        "completed"
          ? 100
          : typeof job.progress ===
              "number"
            ? job.progress
            : 0;


      /* ---------------------------------------------------
         COMPLETION TIME

         Never pass null.

         ExecutionRecord expects:

             completedAt?: string

         not:

             string | null
      --------------------------------------------------- */

      const completedAt =
        initialStatus ===
          "completed"
          ? optionalString(
              job.completed_at,
            )
          : undefined;


      /* ---------------------------------------------------
         CREATED TIME
      --------------------------------------------------- */

      const createdAt =
        optionalString(
          job.created_at,
        ) ??
        new Date().toISOString();


      /* ---------------------------------------------------
         DOCUMENT NAME
      --------------------------------------------------- */

      const documentName =
        selectedDocument.name ||
        selectedDocument.filename ||
        "Document";


      /* ---------------------------------------------------
         CREATE EXECUTION RECORD

         At this point:

           processingId -> string
           documentId   -> string
           workflowId   -> string

         so TypeScript is satisfied.
      --------------------------------------------------- */

      createExecution({
        id:
          processingId,

        processingId:
          processingId,

        documentId:
          documentId,

        documentVersionId:
          documentVersionId,

        workflowId:
          safeWorkflow.id,

        documentName:
          documentName,

        workflowName:
          safeWorkflow.name,

        status:
          initialStatus,

        progress:
          initialProgress,

        duration:
          "0s",

        createdAt:
          createdAt,

        completedAt:
          completedAt,

        error:
          job.error ?? null,

        message:
          job.message ?? null,

        steps:
          createDefaultExecutionSteps(),
      });


      /* ---------------------------------------------------
         LOG
      --------------------------------------------------- */

      console.log(
        "[WorkflowsPage] Execution saved:",
        {
          processingId,
          status:
            initialStatus,
          progress:
            initialProgress,
        },
      );


      /* ---------------------------------------------------
         SUCCESS
      --------------------------------------------------- */

      alert(
        `Processing started for "${documentName}".`,
      );
    } catch (error) {
      console.error(
        "Failed to start processing:",
        error,
      );

      alert(
        error instanceof Error
          ? error.message
          : "Failed to start processing.",
      );
    } finally {
      setRunningWorkflowId(
        null,
      );
    }
  }


  /* =======================================================
     CLOSE MENU
  ======================================================= */

  useEffect(() => {
    function handleDocumentClick() {
      setOpenMenuWorkflowId(
        null,
      );
    }

    if (openMenuWorkflowId) {
      document.addEventListener(
        "click",
        handleDocumentClick,
      );
    }

    return () => {
      document.removeEventListener(
        "click",
        handleDocumentClick,
      );
    };
  }, [
    openMenuWorkflowId,
  ]);


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="p-6 text-sm text-slate-500">
        Loading workflows...
      </div>
    );
  }


  /* =======================================================
     BUILDER
  ======================================================= */

  if (
    showBuilder &&
    editingWorkflow
  ) {
    return (
      <WorkflowBuilder
        workflow={normalizeWorkflow(
          editingWorkflow,
        )}

        onChange={
          nextWorkflow =>
            setEditingWorkflow(
              normalizeWorkflow(
                nextWorkflow,
              ),
            )
        }

        onSave={
          handleSave
        }

        onBack={() => {
          setShowBuilder(false);
          setEditingWorkflow(
            null,
          );
        }}
      />
    );
  }


  /* =======================================================
     WORKFLOW LIST
  ======================================================= */

  return (
    <div className="space-y-5 animate-fade-in">

      {/* HEADER */}

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {workflows.length}{" "}
          workflows powering document automation
        </p>

        <Button
          size="sm"
          onClick={
            handleNewWorkflow
          }
        >
          <Plus size={14} />

          New Workflow
        </Button>
      </div>


      {/* EMPTY STATE */}

      {workflows.length === 0 ? (
        <Card className="p-10">
          <div className="text-center">

            <WorkflowIcon
              size={40}
              className="mx-auto text-slate-300"
            />

            <h3 className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
              No workflows yet
            </h3>

            <p className="mt-1 text-xs text-slate-400">
              Create your first
              document processing
              workflow.
            </p>

            <Button
              size="sm"
              className="mt-4"
              onClick={
                handleNewWorkflow
              }
            >
              <Plus size={14} />

              Create Workflow
            </Button>

          </div>
        </Card>
      ) : (

        /* WORKFLOW CARDS */

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">

          {workflows.map(
            workflow => {
              const safeWorkflow =
                normalizeWorkflow(
                  workflow,
                );

              const isMenuOpen =
                openMenuWorkflowId ===
                safeWorkflow.id;

              const isDeleting =
                deletingWorkflowId ===
                safeWorkflow.id;

              return (
                <Card
                  key={
                    safeWorkflow.id ??
                    safeWorkflow.name
                  }

                  hover

                  className="p-5"
                >

                  {/* CARD HEADER */}

                  <div className="flex items-start justify-between">

                    <div className="flex items-center gap-3">

                      <div className="grid h-11 w-11 place-items-center rounded-lg bg-cyan-50 dark:bg-slate-800">

                        <WorkflowIcon
                          size={20}
                          className="text-cyan-600"
                        />

                      </div>

                      <div>

                        <div className="text-sm font-semibold text-slate-800 dark:text-white">
                          {
                            safeWorkflow.name
                          }
                        </div>

                        <div className="mt-0.5 text-xs text-slate-400">
                          {
                            safeWorkflow
                              .nodes
                              .length
                          }{" "}
                          steps
                        </div>

                      </div>

                    </div>


                    {/* THREE DOT MENU */}

                    <div
                      className="relative"
                      onClick={event =>
                        event.stopPropagation()
                      }
                    >

                      <button
                        type="button"

                        onClick={() =>
                          setOpenMenuWorkflowId(
                            previous =>
                              previous ===
                              safeWorkflow.id
                                ? null
                                : safeWorkflow.id ??
                                  null,
                          )
                        }

                        className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"

                        aria-label="Workflow options"

                        aria-expanded={
                          isMenuOpen
                        }
                      >

                        <MoreHorizontal
                          size={16}
                        />

                      </button>


                      {/* DROPDOWN */}

                      {isMenuOpen && (
                        <div className="absolute right-0 top-8 z-50 w-40 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900">

                          {/* RENAME */}

                          <button
                            type="button"

                            onClick={() =>
                              void handleRename(
                                safeWorkflow,
                              )
                            }

                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
                          >
                            <Pencil
                              size={13}
                            />

                            Rename
                          </button>


                          {/* EDIT */}

                          <button
                            type="button"

                            onClick={() =>
                              handleEdit(
                                safeWorkflow,
                              )
                            }

                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
                          >
                            <WorkflowIcon
                              size={13}
                            />

                            Edit workflow
                          </button>


                          <div className="my-1 border-t border-slate-100 dark:border-slate-800" />


                          {/* DELETE */}

                          <button
                            type="button"

                            disabled={
                              isDeleting
                            }

                            onClick={() =>
                              void handleDelete(
                                safeWorkflow,
                              )
                            }

                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-rose-600 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50 dark:text-rose-400 dark:hover:bg-rose-500/10"
                          >

                            <Trash2
                              size={13}
                            />

                            {
                              isDeleting
                                ? "Deleting..."
                                : "Delete"
                            }

                          </button>

                        </div>
                      )}

                    </div>

                  </div>


                  {/* DESCRIPTION */}

                  <p className="mt-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    {
                      safeWorkflow.description ||
                      "No description provided."
                    }
                  </p>


                  {/* NODE PIPELINE */}

                  <div className="mt-4 flex items-center gap-1 overflow-hidden">

                    {safeWorkflow.nodes.map(
                      (
                        node,
                        index,
                      ) => {

                        const category =
                          categoryForOperation(
                            node.operation,
                          );

                        const color =
                          getWorkflowColor(
                            category,
                          );

                        return (
                          <div
                            key={
                              node.id ||
                              `${node.operation}-${index}`
                            }

                            className="flex items-center"
                          >

                            <div
                              className={`h-2 w-2 rounded-full ${color.dot}`}

                              title={
                                node.label
                              }
                            />

                            {index <
                              safeWorkflow
                                .nodes
                                .length -
                                1 && (
                              <div className="h-px w-4 bg-slate-200 dark:bg-slate-700" />
                            )}

                          </div>
                        );
                      },
                    )}

                  </div>


                  {/* ACTIONS */}

                  <div className="mt-4 flex gap-2">

                    <Button
                      variant="secondary"
                      size="sm"
                      className="flex-1"

                      onClick={() =>
                        handleEdit(
                          safeWorkflow,
                        )
                      }
                    >
                      <WorkflowIcon
                        size={14}
                      />

                      Edit
                    </Button>


                    <Button
                      size="sm"
                      className="flex-1"

                      disabled={
                        runningWorkflowId ===
                          safeWorkflow.id ||
                        isDeleting
                      }

                      onClick={() =>
                        void handleRun(
                          safeWorkflow,
                        )
                      }
                    >

                      <Play
                        size={14}
                      />

                      {runningWorkflowId ===
                      safeWorkflow.id
                        ? "Starting..."
                        : "Run"}

                    </Button>

                  </div>

                </Card>
              );
            },
          )}

        </div>
      )}

    </div>
  );
}