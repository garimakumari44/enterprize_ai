
"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronRight,
  X,
  Upload as UploadIcon,
  Trash2,
} from "lucide-react";

import { Card } from "./ui/Card";
import { StatusBadge } from "./ui/StatusBadge";
import { ConfidenceBadge } from "./ui/ConfidenceBadge";
import { IconByName } from "./ui/IconByName";
import { Button } from "./ui/Button";

import {
  getDocuments,
  deleteDocument,
} from "../../../lib/documents";

import {
  typeIcon,
  typeColors,
  formatDate,
  statusConfig,
} from "../../../lib/helpers";

import { useNav } from "../../../context/NavContext";

import type {
  Document,
  DocumentStatus,
  DocumentFileType,
} from "../../../types/document";

// ============================================================
// Extended Document Type
// ============================================================

type DocumentWithConfidence = Document & {
  confidence?: number;
};

// ============================================================
// Status Filters
// ============================================================

const statusFilters: (
  | DocumentStatus
  | "all"
)[] = [
  "all",
  "completed",
  "processing",
  "failed",
];

// ============================================================
// Safe Object Helpers
// ============================================================

function getString(
  raw: Record<string, unknown>,
  key: string,
  fallback = ""
): string {
  const value = raw[key];

  return typeof value === "string"
    ? value
    : fallback;
}

function getNumber(
  raw: Record<string, unknown>,
  key: string,
  fallback = 0
): number {
  const value = raw[key];

  return typeof value === "number"
    ? value
    : fallback;
}

// ============================================================
// File Type Normalization
// ============================================================

/**
 * Converts any API file type / MIME type / filename extension
 * into the exact DocumentFileType union used by the frontend.
 */
function normalizeFileType(
  value: unknown,
  filename = "",
  contentType = ""
): DocumentFileType {
  const rawValue =
    typeof value === "string"
      ? value.toLowerCase().trim()
      : "";

  const rawContentType =
    contentType.toLowerCase().trim();

  const extension =
    filename
      .split(".")
      .pop()
      ?.toLowerCase()
      .trim() ?? "";

  // ----------------------------------------------------------
  // Direct frontend values
  // ----------------------------------------------------------

  const knownTypes: DocumentFileType[] = [
    "pdf",
    "doc",
    "docx",
    "txt",
    "md",
    "csv",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "image",
    "other",
  ];

  if (
    knownTypes.includes(
      rawValue as DocumentFileType
    )
  ) {
    return rawValue as DocumentFileType;
  }

  // ----------------------------------------------------------
  // PDF
  // ----------------------------------------------------------

  if (
    rawValue === "application/pdf" ||
    rawContentType === "application/pdf" ||
    extension === "pdf"
  ) {
    return "pdf";
  }

  // ----------------------------------------------------------
  // DOC
  // ----------------------------------------------------------

  if (
    rawValue === "application/msword" ||
    rawContentType === "application/msword" ||
    extension === "doc"
  ) {
    return "doc";
  }

  // ----------------------------------------------------------
  // DOCX
  // ----------------------------------------------------------

  if (
    rawValue.includes(
      "application/vnd.openxmlformats-officedocument.wordprocessingml"
    ) ||
    rawContentType.includes(
      "application/vnd.openxmlformats-officedocument.wordprocessingml"
    ) ||
    extension === "docx"
  ) {
    return "docx";
  }

  // ----------------------------------------------------------
  // TXT
  // ----------------------------------------------------------

  if (
    rawValue === "text/plain" ||
    rawContentType === "text/plain" ||
    extension === "txt"
  ) {
    return "txt";
  }

  // ----------------------------------------------------------
  // Markdown
  // ----------------------------------------------------------

  if (
    rawValue === "text/markdown" ||
    rawValue === "markdown" ||
    rawContentType === "text/markdown" ||
    extension === "md" ||
    extension === "markdown"
  ) {
    return "md";
  }

  // ----------------------------------------------------------
  // CSV
  // ----------------------------------------------------------

  if (
    rawValue === "text/csv" ||
    rawContentType === "text/csv" ||
    extension === "csv"
  ) {
    return "csv";
  }

  // ----------------------------------------------------------
  // XLS
  // ----------------------------------------------------------

  if (
    rawValue === "application/vnd.ms-excel" ||
    rawContentType === "application/vnd.ms-excel" ||
    extension === "xls"
  ) {
    return "xls";
  }

  // ----------------------------------------------------------
  // XLSX
  // ----------------------------------------------------------

  if (
    rawValue.includes(
      "application/vnd.openxmlformats-officedocument.spreadsheetml"
    ) ||
    rawContentType.includes(
      "application/vnd.openxmlformats-officedocument.spreadsheetml"
    ) ||
    extension === "xlsx"
  ) {
    return "xlsx";
  }

  // ----------------------------------------------------------
  // PPT
  // ----------------------------------------------------------

  if (
    rawValue ===
      "application/vnd.ms-powerpoint" ||
    rawContentType ===
      "application/vnd.ms-powerpoint" ||
    extension === "ppt"
  ) {
    return "ppt";
  }

  // ----------------------------------------------------------
  // PPTX
  // ----------------------------------------------------------

  if (
    rawValue.includes(
      "application/vnd.openxmlformats-officedocument.presentationml"
    ) ||
    rawContentType.includes(
      "application/vnd.openxmlformats-officedocument.presentationml"
    ) ||
    extension === "pptx"
  ) {
    return "pptx";
  }

  // ----------------------------------------------------------
  // Images
  // ----------------------------------------------------------

  if (
    rawValue.startsWith("image/") ||
    rawContentType.startsWith("image/") ||
    [
      "jpg",
      "jpeg",
      "png",
      "gif",
      "webp",
      "svg",
      "bmp",
      "tiff",
      "tif",
    ].includes(extension)
  ) {
    return "image";
  }

  // ----------------------------------------------------------
  // Fallback
  // ----------------------------------------------------------

  return "other";
}

// ============================================================
// Document Normalization
// ============================================================

/**
 * Converts the raw API response into the canonical frontend
 * Document type.
 *
 * No unsafe `Record<string, unknown> as Document` cast is used.
 */
function normalizeDocument(
  item: unknown
): DocumentWithConfidence {
  if (
    typeof item !== "object" ||
    item === null
  ) {
    throw new Error(
      "Invalid document returned by API."
    );
  }

  const raw =
    item as Record<string, unknown>;

  // ----------------------------------------------------------
  // Identity
  // ----------------------------------------------------------

  const id = getString(
    raw,
    "id"
  );

  const filename = getString(
    raw,
    "filename",
    "untitled"
  );

  const name = getString(
    raw,
    "name",
    filename
  );

  // ----------------------------------------------------------
  // Content Type
  // ----------------------------------------------------------

  const contentType =
    getString(
      raw,
      "content_type",
      getString(
        raw,
        "contentType",
        getString(
          raw,
          "mime_type",
          "application/octet-stream"
        )
      )
    );

  // ----------------------------------------------------------
  // File Type
  // ----------------------------------------------------------

  const fileType =
    normalizeFileType(
      raw.file_type ??
        raw.fileType ??
        raw.mime_type,
      filename,
      contentType
    );

  // ----------------------------------------------------------
  // Status
  // ----------------------------------------------------------

  const rawStatus =
    getString(
      raw,
      "status",
      "processing"
    );

  const validStatuses: DocumentStatus[] = [
    "pending",
    "queued",
    "processing",
    "completed",
    "failed",
    "cancelled",
  ];

  const status: DocumentStatus =
    validStatuses.includes(
      rawStatus as DocumentStatus
    )
      ? (rawStatus as DocumentStatus)
      : "processing";

  // ----------------------------------------------------------
  // Size
  // ----------------------------------------------------------

  const size = getNumber(
    raw,
    "size",
    getNumber(
      raw,
      "file_size",
      getNumber(
        raw,
        "fileSize",
        0
      )
    )
  );

  // ----------------------------------------------------------
  // Dates
  // ----------------------------------------------------------

  const createdAt =
    getString(
      raw,
      "created_at",
      getString(
        raw,
        "createdAt",
        new Date().toISOString()
      )
    );

  const updatedAt =
    getString(
      raw,
      "updated_at",
      getString(
        raw,
        "updatedAt",
        createdAt
      )
    );

  // ----------------------------------------------------------
  // Optional fields
  // ----------------------------------------------------------

  const checksum =
    typeof raw.checksum === "string"
      ? raw.checksum
      : undefined;

  const storageKey =
    typeof raw.storage_key === "string"
      ? raw.storage_key
      : typeof raw.storageKey === "string"
        ? raw.storageKey
        : undefined;

  const mimeType =
    typeof raw.mime_type === "string"
      ? raw.mime_type
      : undefined;

  const uploadedAt =
    typeof raw.uploaded_at === "string"
      ? raw.uploaded_at
      : typeof raw.uploadedAt === "string"
        ? raw.uploadedAt
        : undefined;

  const processedAt =
    raw.processed_at === null
      ? null
      : typeof raw.processed_at ===
          "string"
        ? raw.processed_at
        : typeof raw.processedAt ===
            "string"
          ? raw.processedAt
          : undefined;

  const errorMessage =
    raw.error_message === null
      ? null
      : typeof raw.error_message ===
          "string"
        ? raw.error_message
        : typeof raw.errorMessage ===
            "string"
          ? raw.errorMessage
          : undefined;

  // ----------------------------------------------------------
  // Confidence
  // ----------------------------------------------------------

  const confidence =
    typeof raw.confidence === "number"
      ? raw.confidence
      : typeof raw.confidence_score ===
          "number"
        ? raw.confidence_score
        : 0;

  // ----------------------------------------------------------
  // Canonical Document
  // ----------------------------------------------------------

  const document: DocumentWithConfidence = {
    id,
    name,
    filename,
    content_type: contentType,
    file_type: fileType,
    size,
    status,
    checksum,
    storage_key: storageKey,
    mime_type: mimeType,
    created_at: createdAt,
    updated_at: updatedAt,
    uploaded_at: uploadedAt,
    processed_at: processedAt,
    error_message: errorMessage,
    confidence,
  };

  return document;
}

// ============================================================
// Icon Helpers
// ============================================================

function getIconType(
  document: Document
): keyof typeof typeIcon {
  const fileType =
    document.file_type.toLowerCase();

  const key =
    fileType as keyof typeof typeIcon;

  if (key in typeIcon) {
    return key;
  }

  const availableKeys =
    Object.keys(
      typeIcon
    ) as Array<
      keyof typeof typeIcon
    >;

  return (
    availableKeys[0] ??
    ("" as keyof typeof typeIcon)
  );
}

function getIconColor(
  document: Document
): string {
  const iconType =
    getIconType(document);

  if (
    iconType in typeColors
  ) {
    return typeColors[
      iconType
    ];
  }

  const availableColors =
    Object.values(
      typeColors
    );

  return (
    availableColors[0] ?? ""
  );
}

// ============================================================
// Component
// ============================================================

export function DocumentsPage() {
  const {
    setSelectedDocId,
    setPage,
  } = useNav();

  const [
    documents,
    setDocuments,
  ] = useState<
    DocumentWithConfidence[]
  >([]);

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    DocumentStatus | "all"
  >("all");

  const [
    sortBy,
    setSortBy,
  ] = useState<
    "date" | "confidence" | "name"
  >("date");

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  // ==========================================================
  // Delete State
  // ==========================================================

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(null);

  // ==========================================================
  // Load Documents
  // ==========================================================

  useEffect(() => {
    let mounted = true;

    const loadDocuments =
      async () => {
        try {
          setLoading(true);
          setError(null);

          const response =
            await getDocuments();

          if (!mounted) {
            return;
          }

          const normalizedDocuments =
            response.items.map(
              (item) =>
                normalizeDocument(
                  item
                )
            );

          setDocuments(
            normalizedDocuments
          );
        } catch (
          error
        ) {
          console.error(
            "Failed to load documents:",
            error
          );

          if (!mounted) {
            return;
          }

          setError(
            "Unable to load documents. Please try again."
          );
        } finally {
          if (mounted) {
            setLoading(
              false
            );
          }
        }
      };

    loadDocuments();

    return () => {
      mounted = false;
    };
  }, []);

  // ==========================================================
  // Filter + Sort
  // ==========================================================

  const filtered =
    useMemo(() => {
      let list =
        documents.filter(
          (document) => {
            const search =
              query
                .trim()
                .toLowerCase();

            if (!search) {
              return true;
            }

            return (
              document.name
                .toLowerCase()
                .includes(
                  search
                ) ||
              document.filename
                .toLowerCase()
                .includes(
                  search
                )
            );
          }
        );

      if (
        statusFilter !==
        "all"
      ) {
        list =
          list.filter(
            (document) =>
              document.status ===
              statusFilter
          );
      }

      list =
        [...list].sort(
          (a, b) => {
            if (
              sortBy ===
              "date"
            ) {
              return (
                new Date(
                  b.created_at
                ).getTime() -
                new Date(
                  a.created_at
                ).getTime()
              );
            }

            if (
              sortBy ===
              "confidence"
            ) {
              const confidenceA =
                a.confidence ??
                0;

              const confidenceB =
                b.confidence ??
                0;

              return (
                confidenceB -
                confidenceA
              );
            }

            return a.name.localeCompare(
              b.name
            );
          }
        );

      return list;
    }, [
      documents,
      query,
      statusFilter,
      sortBy,
    ]);

  // ==========================================================
  // Open Document
  // ==========================================================

  const openDoc = (
    id: string
  ) => {
    setSelectedDocId(
      id
    );
  };

  // ==========================================================
  // Delete Document
  // ==========================================================

  const handleDelete = async (
    event: React.MouseEvent,
    document: DocumentWithConfidence
  ) => {
    // Prevent the table row click
    // from opening the document.
    event.stopPropagation();

    // Prevent multiple deletes at once.
    if (deletingId) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete "${document.name}"?\n\nThis action cannot be undone.`
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(
        document.id
      );

      setError(null);

      await deleteDocument(
        document.id
      );

      // Remove the document from
      // the local list immediately.
      setDocuments(
        (current) =>
          current.filter(
            (item) =>
              item.id !==
              document.id
          )
      );

      // Clear selection if the deleted
      // document was currently selected.
      setSelectedDocId(null);
    } catch (
      error
    ) {
      console.error(
        "Failed to delete document:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to delete document. Please try again."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ==========================================================
  // Loading State
  // ==========================================================

  if (loading) {
    return (
      <div className="space-y-5 animate-fade-in">
        <div className="flex items-center justify-center py-20">

          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-cyan-500" />

          <span className="ml-3 text-sm text-slate-500">
            Loading documents...
          </span>

        </div>
      </div>
    );
  }

  // ==========================================================
  // Render
  // ==========================================================

  return (
    <div className="space-y-5 animate-fade-in">

      {/* ======================================================
          Toolbar
          ====================================================== */}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

        <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">

          {/* Search */}

          <div className="relative flex-1 sm:max-w-xs">

            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              value={query}
              onChange={(
                event
              ) =>
                setQuery(
                  event.target.value
                )
              }
              placeholder="Search documents…"
              className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-9 text-sm text-slate-700 placeholder:text-slate-400 transition-all focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />

            {query && (
              <button
                type="button"
                onClick={() =>
                  setQuery("")
                }
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X
                  size={15}
                />
              </button>
            )}

          </div>

          {/* Status Filters */}

          <div className="flex items-center gap-1.5 overflow-x-auto">

            {statusFilters.map(
              (
                status
              ) => (
                <button
                  key={
                    status
                  }
                  type="button"
                  onClick={() =>
                    setStatusFilter(
                      status
                    )
                  }
                  className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                    statusFilter ===
                    status
                      ? "bg-slate-900 text-white dark:bg-cyan-500 dark:text-white"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                  }`}
                >
                  {status ===
                  "all"
                    ? "All"
                    : getStatusLabel(
                        status
                      )}
                </button>
              )
            )}

          </div>

        </div>

        {/* Actions */}

        <div className="flex items-center gap-2">

          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              setSortBy(
                sortBy ===
                "date"
                  ? "confidence"
                  : sortBy ===
                      "confidence"
                    ? "name"
                    : "date"
              )
            }
          >

            <ArrowUpDown
              size={14}
            />

            <span className="hidden sm:inline">
              {sortBy ===
              "date"
                ? "Date"
                : sortBy ===
                    "confidence"
                  ? "Confidence"
                  : "Name"}
            </span>

          </Button>

          <Button
            size="sm"
            onClick={() =>
              setPage(
                "upload"
              )
            }
          >

            <UploadIcon
              size={14}
            />

            <span className="hidden sm:inline">
              Upload
            </span>

          </Button>

        </div>

      </div>

      {/* ======================================================
          Error
          ====================================================== */}

      {error && (
        <Card className="p-4">

          <div className="flex items-center justify-between gap-4">

            <span className="text-sm text-rose-500">
              {error}
            </span>

            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                window.location.reload()
              }
            >
              Retry
            </Button>

          </div>

        </Card>
      )}

      {/* ======================================================
          Table
          ====================================================== */}

      <Card>

        <div className="overflow-x-auto">

          <table className="w-full text-sm">

            <thead>

              <tr className="border-b border-slate-100 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:border-slate-800">

                <th className="px-5 py-3">
                  Document
                </th>

                <th className="px-3 py-3">
                  Type
                </th>

                <th className="px-3 py-3">
                  Status
                </th>

                <th className="px-3 py-3">
                  Confidence
                </th>

                <th className="px-5 py-3">
                  Created
                </th>

                <th className="px-3 py-3 text-right">
                  Actions
                </th>

              </tr>

            </thead>

            <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">

              {filtered.map(
                (
                  document
                ) => {

                  const confidence =
                    document.confidence ??
                    0;

                  const iconType =
                    getIconType(
                      document
                    );

                  const iconName =
                    typeIcon[
                      iconType
                    ];

                  const iconColor =
                    getIconColor(
                      document
                    );

                  const isDeleting =
                    deletingId ===
                    document.id;

                  return (
                    <tr
                      key={
                        document.id
                      }
                      onClick={() => {
                        if (!isDeleting) {
                          openDoc(
                            document.id
                          );
                        }
                      }}
                      className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40"
                    >

                      {/* Document */}

                      <td className="px-5 py-3">

                        <div className="flex items-center gap-2.5">

                          <IconByName
                            name={
                              iconName
                            }
                            size={16}
                            className={
                              iconColor
                            }
                          />

                          <span className="truncate font-medium text-slate-700 dark:text-slate-200">
                            {
                              document.name
                            }
                          </span>

                        </div>

                      </td>

                      {/* Type */}

                      <td className="px-3 py-3 text-xs uppercase text-slate-400">
                        {
                          document.file_type
                        }
                      </td>

                      {/* Status */}

                      <td className="px-3 py-3">

                        <StatusBadge
                          status={
                            document.status
                          }
                        />

                      </td>

                      {/* Confidence */}

                      <td className="px-3 py-3">

                        <ConfidenceBadge
                          value={
                            confidence
                          }
                          showBar
                        />

                      </td>

                      {/* Created */}

                      <td className="px-5 py-3 text-xs text-slate-500 dark:text-slate-400">

                        {formatDate(
                          document.created_at
                        )}

                      </td>

                      {/* Actions */}

                      <td className="px-3 py-3">

                        <div className="flex items-center justify-end gap-1">

                          {/* Delete */}

                          <button
                            type="button"
                            disabled={
                              deletingId !==
                                null
                            }
                            onClick={(
                              event
                            ) =>
                              handleDelete(
                                event,
                                document
                              )
                            }
                            className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-500 disabled:cursor-not-allowed disabled:opacity-50 dark:hover:bg-rose-950/30"
                            aria-label={`Delete ${document.name}`}
                            title="Delete document"
                          >

                            {isDeleting ? (
                              <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-rose-500" />
                            ) : (
                              <Trash2
                                size={15}
                              />
                            )}

                          </button>

                          {/* Open */}

                          <button
                            type="button"
                            onClick={(
                              event
                            ) => {
                              event.stopPropagation();

                              openDoc(
                                document.id
                              );
                            }}
                            className="rounded-md p-1.5 text-slate-300 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
                            aria-label={`Open ${document.name}`}
                            title="Open document"
                          >

                            <ChevronRight
                              size={16}
                            />

                          </button>

                        </div>

                      </td>

                    </tr>
                  );
                }
              )}

            </tbody>

          </table>

        </div>

        {/* ====================================================
            Empty State
            ==================================================== */}

        {filtered.length ===
          0 && (
          <div className="py-16 text-center">

            <Filter
              size={32}
              className="mx-auto text-slate-300 dark:text-slate-700"
            />

            <p className="mt-3 text-sm text-slate-500">
              {documents.length ===
              0
                ? "No documents uploaded yet"
                : "No documents match your filters"}
            </p>

            {documents.length ===
              0 && (
              <Button
                size="sm"
                className="mt-4"
                onClick={() =>
                  setPage(
                    "upload"
                  )
                }
              >

                <UploadIcon
                  size={14}
                />

                Upload document

              </Button>
            )}

          </div>
        )}

      </Card>

    </div>
  );
}

// ============================================================
// Status Helpers
// ============================================================

function getStatusLabel(
  status: DocumentStatus
): string {
  const config = (
    statusConfig as Record<
      string,
      {
        label: string;
      }
    >
  )[status];

  return (
    config?.label ??
    capitalize(status)
  );
}

function capitalize(
  value: string
): string {
  return value
    .replace(
      /_/g,
      " "
    )
    .replace(
      /\b\w/g,
      (char) =>
        char.toUpperCase()
    );
}
