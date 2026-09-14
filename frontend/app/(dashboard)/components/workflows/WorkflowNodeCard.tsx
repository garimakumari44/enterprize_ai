import {
  FileText,
  RefreshCw,
  Settings2,
  Trash2,
} from 'lucide-react';

import {
  type LibraryDocument,
  type WorkflowNode,
} from '../../../../types/workflow';


/* =========================================================
   TYPES
========================================================= */

interface WorkflowNodeColor {
  bg: string;
  border: string;
  text: string;
  dot: string;
}


interface WorkflowNodeCardProps {
  node: WorkflowNode;

  color: WorkflowNodeColor;

  libraryDocuments: LibraryDocument[];

  documentsLoading: boolean;

  documentsError: string | null;

  onRefreshDocuments: () =>
    Promise<void>;

  onRemove: () => void;

  onConfigChange: (
    config: Record<
      string,
      unknown
    >
  ) => void;
}


/* =========================================================
   FILE SIZE
========================================================= */

function formatFileSize(
  bytes: number
): string {
  if (!bytes || bytes <= 0) {
    return '';
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(
      bytes / 1024
    ).toFixed(1)} KB`;
  }

  if (bytes < 1024 * 1024 * 1024) {
    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  }

  return `${(
    bytes /
    (1024 * 1024 * 1024)
  ).toFixed(1)} GB`;
}


/* =========================================================
   NODE CARD
========================================================= */

export function WorkflowNodeCard({
  node,
  color,
  libraryDocuments,
  documentsLoading,
  documentsError,
  onRefreshDocuments,
  onRemove,
  onConfigChange,
}: WorkflowNodeCardProps) {

  /*
   * Defensive config handling.
   *
   * If an old backend node doesn't have config,
   * the component still renders safely.
   */
  const config =
    node.config &&
    typeof node.config === 'object'
      ? node.config
      : {};


  /* =======================================================
     SELECTED DOCUMENT
  ======================================================= */

  const selectedDocumentId =
    typeof config.document_id ===
    'string'
      ? config.document_id
      : '';


  const selectedDocument =
    libraryDocuments.find(
      document =>
        document.id ===
        selectedDocumentId
    );


  const selectedDocumentName =
    selectedDocument?.name ||
    selectedDocument?.filename ||
    String(
      config.document_name ||
        ''
    );


  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div
      className={`group relative w-72 rounded-xl border ${color.border} ${color.bg} p-3 shadow-sm`}
    >

      {/* =================================================
          HEADER
      ================================================= */}

      <div className="flex items-center gap-2">

        <span
          className={`h-2 w-2 rounded-full ${color.dot}`}
        />

        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          {node.type}
        </span>


        <button
          type="button"
          onClick={
            onRemove
          }
          className="ml-auto rounded p-1 text-slate-400 hover:bg-white/50 hover:text-rose-500 dark:hover:bg-slate-800"
          title="Remove node"
          aria-label="Remove node"
        >
          <Trash2
            size={12}
          />
        </button>

      </div>


      {/* =================================================
          TITLE
      ================================================= */}

      <div className="mt-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
        {node.label}
      </div>


      <div className="mt-1 text-[10px] text-slate-400">
        {node.description}
      </div>


      {/* =================================================
          LIBRARY DOCUMENT
      ================================================= */}

      {node.operation ===
        'library_document' && (

        <div className="mt-3 space-y-2 border-t border-slate-200/70 pt-3 dark:border-slate-700">

          {/* ------------------------------------------------
              SELECTOR HEADER
          ------------------------------------------------ */}

          <div className="flex items-center justify-between">

            <label className="flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-slate-500">

              <FileText
                size={11}
              />

              Select Library Document

            </label>


            <button
              type="button"
              onClick={
                onRefreshDocuments
              }
              disabled={
                documentsLoading
              }
              className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 dark:hover:bg-slate-800"
              title="Refresh library"
              aria-label="Refresh library"
            >

              <RefreshCw
                size={11}
                className={
                  documentsLoading
                    ? 'animate-spin'
                    : ''
                }
              />

            </button>

          </div>


          {/* =================================================
              LOADING
          ================================================= */}

          {documentsLoading && (

            <div className="rounded-md border border-slate-200 bg-white px-2 py-3 text-[10px] text-slate-500 dark:border-slate-700 dark:bg-slate-900">

              Loading documents...

            </div>

          )}


          {/* =================================================
              ERROR
          ================================================= */}

          {!documentsLoading &&
            documentsError && (

            <div className="space-y-2 rounded-md border border-rose-200 bg-rose-50 p-2 dark:border-rose-500/30 dark:bg-rose-500/10">

              <p className="text-[10px] text-rose-600 dark:text-rose-400">
                {
                  documentsError
                }
              </p>


              <button
                type="button"
                onClick={
                  onRefreshDocuments
                }
                className="text-[10px] font-medium text-rose-700 hover:underline dark:text-rose-400"
              >
                Retry
              </button>

            </div>
          )}


          {/* =================================================
              NO DOCUMENTS
          ================================================= */}

          {!documentsLoading &&
            !documentsError &&
            libraryDocuments.length ===
              0 && (

            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/30 dark:bg-amber-500/10">

              <div className="flex items-center gap-2">

                <FileText
                  size={14}
                  className="text-amber-600"
                />

                <p className="text-[10px] font-medium text-amber-700 dark:text-amber-400">
                  No documents found
                </p>

              </div>


              <p className="mt-1 text-[9px] text-amber-600 dark:text-amber-400">
                Upload a document to the
                library first.
              </p>

            </div>
          )}


          {/* =================================================
              DOCUMENT SELECTOR
          ================================================= */}

          {!documentsLoading &&
            !documentsError &&
            libraryDocuments.length >
              0 && (

            <>

              <select
                value={
                  selectedDocumentId
                }
                onChange={
                  event => {

                    const documentId =
                      event.target
                        .value;

                    const document =
                      libraryDocuments.find(
                        item =>
                          item.id ===
                          documentId
                      );

                    onConfigChange({

                      document_id:
                        documentId ||
                        null,

                      document_name:
                        document?.name ||
                        document?.filename ||
                        null,

                      document_filename:
                        document?.filename ||
                        null,

                      content_type:
                        document?.content_type ||
                        null,

                    });
                  }
                }
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-xs text-slate-700 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              >

                <option value="">
                  Select a document...
                </option>


                {libraryDocuments.map(
                  document => (

                    <option
                      key={
                        document.id
                      }
                      value={
                        document.id
                      }
                    >

                      {
                        document.name ||
                        document.filename ||
                        'Unnamed document'
                      }

                    </option>

                  )
                )}

              </select>


              <div className="text-[9px] text-slate-400">

                {
                  libraryDocuments.length
                }{' '}

                document
                {libraryDocuments.length !==
                1
                  ? 's'
                  : ''}{' '}

                available

              </div>

            </>
          )}


          {/* =================================================
              SELECTED DOCUMENT
          ================================================= */}

          {selectedDocumentId && (

            <div className="rounded-md border border-cyan-200 bg-cyan-50 p-2 dark:border-cyan-500/30 dark:bg-cyan-500/10">

              <div className="flex items-start gap-2">

                <FileText
                  size={14}
                  className="mt-0.5 shrink-0 text-cyan-600 dark:text-cyan-400"
                />

                <div className="min-w-0">

                  <div className="text-[9px] font-semibold uppercase tracking-wide text-cyan-600 dark:text-cyan-400">
                    Selected document
                  </div>


                  <div className="mt-0.5 truncate text-[10px] font-medium text-cyan-800 dark:text-cyan-300">

                    {
                      selectedDocumentName ||
                      'Selected document'
                    }

                  </div>


                  {selectedDocument?.content_type && (

                    <div className="mt-0.5 text-[9px] text-cyan-600 dark:text-cyan-400">

                      {
                        selectedDocument.content_type
                      }

                    </div>

                  )}


                  {selectedDocument?.size && (

                    <div className="text-[9px] text-cyan-600 dark:text-cyan-400">

                      {
                        formatFileSize(
                          selectedDocument.size
                        )
                      }

                    </div>

                  )}

                </div>

              </div>

            </div>
          )}

        </div>
      )}


      {/* =================================================
          BACKEND OPERATION
      ================================================= */}

      <div className="mt-3 border-t border-slate-200/70 pt-2 dark:border-slate-700">

        <div className="flex items-center gap-1 text-[9px] uppercase tracking-wide text-slate-400">

          <Settings2
            size={10}
          />

          Backend operation

        </div>


        <code className="mt-1 block text-[10px] text-slate-500">
          {node.operation}
        </code>

      </div>


      {/* =================================================
          CHUNKING CONFIG
      ================================================= */}

      {node.operation ===
        'chunking' && (

        <div className="mt-3 space-y-2">

          <label className="block text-[10px] text-slate-500">

            Chunk size

            <input
              type="number"
              min="1"
              value={Number(
                config.chunk_size ||
                  800
              )}
              onChange={
                event =>
                  onConfigChange({
                    chunk_size:
                      Number(
                        event.target
                          .value
                      ),
                  })
              }
              className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-xs outline-none focus:border-cyan-400 dark:border-slate-700 dark:bg-slate-900"
            />

          </label>


          <label className="block text-[10px] text-slate-500">

            Overlap

            <input
              type="number"
              min="0"
              value={Number(
                config.chunk_overlap ||
                  100
              )}
              onChange={
                event =>
                  onConfigChange({
                    chunk_overlap:
                      Number(
                        event.target
                          .value
                      ),
                  })
              }
              className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-xs outline-none focus:border-cyan-400 dark:border-slate-700 dark:bg-slate-900"
            />

          </label>

        </div>
      )}


      {/* =================================================
          AI MODEL CONFIG
      ================================================= */}

      {node.operation ===
        'ai_model' && (

        <div className="mt-3">

          <label className="block text-[10px] text-slate-500">

            Model

            <select
              value={String(
                config.model ||
                  'default'
              )}
              onChange={
                event =>
                  onConfigChange({
                    model:
                      event.target
                        .value,
                  })
              }
              className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-xs outline-none focus:border-cyan-400 dark:border-slate-700 dark:bg-slate-900"
            >

              <option value="default">
                Default
              </option>

              <option value="llm">
                LLM
              </option>

            </select>

          </label>

        </div>
      )}

    </div>
  );
}