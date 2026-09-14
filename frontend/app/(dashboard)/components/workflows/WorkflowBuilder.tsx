'use client';

import {
  useEffect,
  useState,
} from 'react';

import {
  Plus,
  Workflow as WorkflowIcon,
  Zap,
  Loader2,
} from 'lucide-react';

import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

import {
  workflowPalette,
  type PaletteCategory,
} from '../../../../lib/workflowPalette';

import {
  getLibraryDocuments,
} from '../../../../lib/api/workflowApi';

import type {
  LibraryDocument,
  WorkflowDefinition,
  WorkflowOperation,
} from '../../../../types/workflow';

import {
  colorMap,
  categoryForOperation,
  createNode,
  normalizeWorkflow,
} from '../WorkflowsPage';

import {
  WorkflowNodeCard,
} from './WorkflowNodeCard';

/* =========================================================
   TYPES
========================================================= */

interface WorkflowBuilderProps {
  workflow: WorkflowDefinition;

  onChange: (
    workflow: WorkflowDefinition
  ) => void;

  onSave: (
    workflow: WorkflowDefinition
  ) => Promise<void>;

  onBack: () => void;
}

/* =========================================================
   CATEGORY ICON
========================================================= */

function getCategoryIcon(
  category: PaletteCategory
) {
  return category.items[0]?.icon;
}

/* =========================================================
   BUILDER
========================================================= */

export function WorkflowBuilder({
  workflow,
  onChange,
  onSave,
  onBack,
}: WorkflowBuilderProps) {

  /* =======================================================
     NORMALIZED WORKFLOW
  ======================================================= */

  const safeWorkflow =
    normalizeWorkflow(
      workflow
    );

  /* =======================================================
     SAVE STATE
  ======================================================= */

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* =======================================================
     DOCUMENT STATE
  ======================================================= */

  const [
    libraryDocuments,
    setLibraryDocuments,
  ] = useState<
    LibraryDocument[]
  >([]);

  const [
    documentsLoading,
    setDocumentsLoading,
  ] = useState(true);

  const [
    documentsError,
    setDocumentsError,
  ] = useState<string | null>(
    null
  );

  /* =======================================================
     LOAD DOCUMENTS
  ======================================================= */

  async function loadLibraryDocuments() {
    try {
      setDocumentsLoading(
        true
      );

      setDocumentsError(
        null
      );

      const documents =
        await getLibraryDocuments();

      setLibraryDocuments(
        Array.isArray(documents)
          ? documents
          : []
      );
    } catch (error) {
      console.error(
        'Failed to load library documents:',
        error
      );

      setLibraryDocuments(
        []
      );

      setDocumentsError(
        error instanceof Error
          ? error.message
          : 'Failed to load library documents.'
      );
    } finally {
      setDocumentsLoading(
        false
      );
    }
  }

  useEffect(() => {
    void loadLibraryDocuments();
  }, []);

  /* =======================================================
     ADD NODE
  ======================================================= */

  function addNode(
    operation: WorkflowOperation
  ) {
    const node =
      createNode(
        operation
      );

    onChange({
      ...safeWorkflow,

      nodes: [
        ...safeWorkflow.nodes,
        node,
      ],
    });
  }

  /* =======================================================
     REMOVE NODE
  ======================================================= */

  function removeNode(
    nodeId: string
  ) {
    onChange({
      ...safeWorkflow,

      nodes:
        safeWorkflow.nodes.filter(
          node =>
            node.id !== nodeId
        ),
    });
  }

  /* =======================================================
     UPDATE NODE CONFIG
  ======================================================= */

  function updateNodeConfig(
    nodeId: string,
    config: Record<
      string,
      unknown
    >
  ) {
    onChange({
      ...safeWorkflow,

      nodes:
        safeWorkflow.nodes.map(
          node =>
            node.id === nodeId
              ? {
                  ...node,

                  config: {
                    ...node.config,
                    ...config,
                  },
                }
              : node
        ),
    });
  }

  /* =======================================================
     UPDATE NAME
  ======================================================= */

  function updateWorkflowName(
    name: string
  ) {
    onChange({
      ...safeWorkflow,

      name,
    });
  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {
    if (saving) {
      return;
    }

    /* -----------------------------------------------------
       BASIC VALIDATION
    ----------------------------------------------------- */

    const normalizedWorkflow =
      normalizeWorkflow(
        safeWorkflow
      );

    if (
      !normalizedWorkflow.name.trim()
    ) {
      alert(
        'Please enter a workflow name.'
      );

      return;
    }

    if (
      normalizedWorkflow.nodes.length ===
      0
    ) {
      alert(
        'Please add at least one node to the workflow.'
      );

      return;
    }

    try {
      setSaving(true);

      /*
       * Send the complete normalized workflow
       * back to WorkflowsPage.
       */
      await onSave(
        normalizedWorkflow
      );

      /*
       * WorkflowsPage closes the builder
       * after the backend save succeeds.
       */
    } catch (error) {
      console.error(
        'Workflow save failed:',
        error
      );

      /*
       * Keep builder open when save fails.
       */
    } finally {
      setSaving(false);
    }
  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div
      className="flex flex-col animate-fade-in lg:flex-row lg:gap-4"
      style={{
        height:
          'calc(100vh - 140px)',
      }}
    >

      {/* =================================================
          NODE PALETTE
      ================================================= */}

      <div className="mb-4 lg:mb-0 lg:w-72 lg:shrink-0">

        <Card className="h-full">

          <div className="border-b border-slate-100 px-4 py-3 dark:border-slate-800">

            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Node Library
            </span>

          </div>

          <div className="max-h-full space-y-5 overflow-y-auto p-3">

            {workflowPalette.map(
              category => {

                const color =
                  colorMap[
                    category.color
                  ];

                const CategoryIcon =
                  getCategoryIcon(
                    category
                  );

                if (!CategoryIcon) {
                  return null;
                }

                return (
                  <div
                    key={
                      category.type
                    }
                  >

                    <div className="mb-2 flex items-center gap-2 px-1">

                      <CategoryIcon
                        size={14}
                        className={
                          color.text
                        }
                      />

                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                        {
                          category.label
                        }
                      </span>

                    </div>

                    <div className="space-y-1.5">

                      {category.items.map(
                        item => {

                          const Icon =
                            item.icon;

                          return (
                            <button
                              key={
                                item.operation
                              }
                              type="button"
                              onClick={() =>
                                addNode(
                                  item.operation
                                )
                              }
                              disabled={
                                saving
                              }
                              className={`flex w-full items-center gap-2.5 rounded-lg border ${color.border} ${color.bg} px-3 py-2 text-left transition-all hover:scale-[1.01] hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-50`}
                            >

                              <Icon
                                size={14}
                                className={
                                  color.text
                                }
                              />

                              <div className="min-w-0">

                                <div className="truncate text-xs font-medium text-slate-700 dark:text-slate-200">
                                  {
                                    item.label
                                  }
                                </div>

                                <div className="truncate text-[10px] text-slate-400">
                                  {
                                    item.description
                                  }
                                </div>

                              </div>

                              <Plus
                                size={13}
                                className={`ml-auto shrink-0 ${color.text}`}
                              />

                            </button>
                          );
                        }
                      )}

                    </div>

                  </div>
                );
              }
            )}

          </div>

        </Card>

      </div>

      {/* =================================================
          CANVAS
      ================================================= */}

      <div className="flex flex-1 flex-col">

        {/* -------------------------------------------------
            TOOLBAR
        ------------------------------------------------- */}

        <div className="mb-3 flex items-center justify-between">

          <button
            type="button"
            onClick={
              onBack
            }
            disabled={
              saving
            }
            className="text-sm font-medium text-slate-500 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:hover:text-slate-300"
          >
            ← Back to workflows
          </button>

          <div className="flex items-center gap-2">

            <Button
              variant="secondary"
              size="sm"
              onClick={
                onBack
              }
              disabled={
                saving
              }
            >
              Cancel
            </Button>

            <Button
              size="sm"
              onClick={
                handleSave
              }
              disabled={
                saving
              }
            >

              {saving ? (
                <>
                  <Loader2
                    size={14}
                    className="animate-spin"
                  />

                  Saving...
                </>
              ) : (
                <>
                  <Zap
                    size={14}
                  />

                  Save & Deploy
                </>
              )}

            </Button>

          </div>

        </div>

        {/* -------------------------------------------------
            CANVAS CARD
        ------------------------------------------------- */}

        <Card className="relative flex-1 overflow-hidden">

          {/* GRID */}

          <div
            className="pointer-events-none absolute inset-0 opacity-[0.4]"
            style={{
              backgroundImage:
                'radial-gradient(circle, #cbd5e1 1px, transparent 1px)',
              backgroundSize:
                '20px 20px',
            }}
          />

          <div className="relative h-full overflow-auto p-6">

            {/* ------------------------------------------------
                WORKFLOW NAME
            ------------------------------------------------ */}

            <div className="mb-6">

              <input
                value={
                  safeWorkflow.name
                }
                onChange={
                  event =>
                    updateWorkflowName(
                      event.target.value
                    )
                }
                disabled={
                  saving
                }
                className="w-full max-w-lg rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                placeholder="Workflow name"
              />

            </div>

            {/* ------------------------------------------------
                NODES
            ------------------------------------------------ */}

            <div className="flex min-w-max items-center">

              {safeWorkflow.nodes.map(
                (
                  node,
                  index
                ) => {

                  const category =
                    categoryForOperation(
                      node.operation
                    );

                  const color =
                    colorMap[
                      category?.color ||
                        'cyan'
                    ];

                  return (
                    <div
                      key={
                        node.id ||
                        `${node.operation}-${index}`
                      }
                      className="flex items-center"
                    >

                      <WorkflowNodeCard
                        node={
                          node
                        }

                        color={
                          color
                        }

                        libraryDocuments={
                          libraryDocuments
                        }

                        documentsLoading={
                          documentsLoading
                        }

                        documentsError={
                          documentsError
                        }

                        onRefreshDocuments={
                          loadLibraryDocuments
                        }

                        onRemove={() =>
                          removeNode(
                            node.id
                          )
                        }

                        onConfigChange={
                          config =>
                            updateNodeConfig(
                              node.id,
                              config
                            )
                        }
                      />

                      {index <
                        safeWorkflow.nodes.length -
                          1 && (
                        <div className="mx-2 flex items-center">

                          <div className="h-px w-10 bg-slate-300 dark:bg-slate-600" />

                          <div className="h-2 w-2 rotate-45 border-r border-t border-slate-300 dark:border-slate-600" />

                        </div>
                      )}

                    </div>
                  );
                }
              )}

              {/* EMPTY STATE */}

              {safeWorkflow.nodes.length ===
                0 && (

                <div className="grid min-h-[400px] w-full place-items-center">

                  <div className="text-center">

                    <WorkflowIcon
                      size={40}
                      className="mx-auto text-slate-300"
                    />

                    <p className="mt-3 text-sm text-slate-500">
                      Add nodes from the
                      Node Library
                    </p>

                  </div>

                </div>
              )}

            </div>

          </div>

        </Card>

      </div>

    </div>
  );
}