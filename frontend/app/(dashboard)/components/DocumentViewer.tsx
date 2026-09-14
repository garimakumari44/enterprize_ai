"use client";

import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Download,
  Share2,
  FileText,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Quote,
} from "lucide-react";

import { Card } from "./ui/Card";
import { ConfidenceBadge } from "./ui/ConfidenceBadge";
import { IconByName } from "./ui/IconByName";
import { Button } from "./ui/Button";

import { getDocument } from "../../../lib/documents";
import {
  typeIcon,
  typeColors,
  formatDate,
  riskConfig,
} from "../../../lib/helpers";

import { useNav } from "../../../context/NavContext";

import type { Document } from "../../../types/document";

// ============================================================
// Types
// ============================================================

type PreviewField = {
  label: string;
  value: string;
  confidence: number;
};

type PreviewAnnotation = {
  id: string;
  type: "risk" | "citation";
  label: string;
  text: string;
};

type DocumentPreview = {
  riskLevel?: "low" | "medium" | "high";
  vendor?: string;
  invoiceNumber?: string;
  summary?: string;
  extractedFields?: PreviewField[];
  annotations?: PreviewAnnotation[];
};

/**
 * Viewer-specific document type.
 *
 * The shared Document type may contain fields whose types
 * differ from the API response, so those fields are omitted
 * and redefined here.
 */
type ViewerDocument = Omit<
  Document,
  | "file_type"
  | "file_size"
  | "size"
  | "pages"
  | "confidence"
  | "preview"
> & {
  file_type?: string;
  file_size?: number;
  size?: string;
  pages?: number;
  confidence?: number;
  preview?: DocumentPreview;
};

// ============================================================
// API → Viewer normalization
// ============================================================

function normalizeDocument(
  response: unknown
): ViewerDocument {
  if (
    typeof response !== "object" ||
    response === null
  ) {
    throw new Error(
      "Invalid document response from API."
    );
  }

  const raw =
    response as Record<string, unknown>;

  // ----------------------------------------------------------
  // File type
  // ----------------------------------------------------------

  const fileType =
    typeof raw.file_type === "string"
      ? raw.file_type
      : typeof raw.fileType === "string"
        ? raw.fileType
        : typeof raw.mime_type === "string"
          ? raw.mime_type
          : undefined;

  // ----------------------------------------------------------
  // Preview
  // ----------------------------------------------------------

  const preview =
    typeof raw.preview === "object" &&
    raw.preview !== null
      ? (raw.preview as DocumentPreview)
      : undefined;

  // ----------------------------------------------------------
  // Normalized document
  // ----------------------------------------------------------

  return {
    ...(raw as Omit<
      Document,
      | "file_type"
      | "file_size"
      | "size"
      | "pages"
      | "confidence"
      | "preview"
    >),

    file_type: fileType,

    file_size:
      typeof raw.file_size === "number"
        ? raw.file_size
        : undefined,

    size:
      typeof raw.size === "string"
        ? raw.size
        : undefined,

    pages:
      typeof raw.pages === "number"
        ? raw.pages
        : undefined,

    confidence:
      typeof raw.confidence === "number"
        ? raw.confidence
        : undefined,

    preview,
  };
}

// ============================================================
// Document Type Helpers
// ============================================================

/**
 * Safely resolve an icon from typeIcon.
 *
 * The backend can return arbitrary file types/MIME types,
 * while typeIcon only accepts its predefined DocType keys.
 */
function getDocumentIcon(
  fileType: string
): string {
  const normalizedType =
    fileType.toLowerCase();

  const key =
    normalizedType as keyof typeof typeIcon;

  if (key in typeIcon) {
    return typeIcon[key];
  }

  const values =
    Object.values(typeIcon);

  return values.length > 0
    ? values[0]
    : "";
}

/**
 * Safely resolve an icon color from typeColors.
 */
function getDocumentIconColor(
  fileType: string
): string {
  const normalizedType =
    fileType.toLowerCase();

  const key =
    normalizedType as keyof typeof typeColors;

  if (key in typeColors) {
    return typeColors[key];
  }

  const values =
    Object.values(typeColors);

  return values.length > 0
    ? values[0]
    : "";
}

// ============================================================
// Component
// ============================================================

export function DocumentViewer({
  docId,
}: {
  docId: string;
}) {
  const {
    setSelectedDocId,
    setPage,
  } = useNav();

  const [doc, setDoc] =
    useState<ViewerDocument | null>(null);

  const [loading, setLoading] =
    useState<boolean>(true);

  const [error, setError] =
    useState<string | null>(null);

  // ==========================================================
  // Load Document
  // ==========================================================

  useEffect(() => {
    let mounted = true;

    const loadDocument = async () => {
      try {
        setLoading(true);
        setError(null);

        const response =
          await getDocument(docId);

        if (!mounted) {
          return;
        }

        const normalizedDocument =
          normalizeDocument(response);

        setDoc(normalizedDocument);
      } catch (err) {
        console.error(
          "Failed to load document:",
          err
        );

        if (!mounted) {
          return;
        }

        setDoc(null);

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load document."
        );
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    if (docId) {
      loadDocument();
    } else {
      setDoc(null);
      setLoading(false);
      setError(null);
    }

    return () => {
      mounted = false;
    };
  }, [docId]);

  // ==========================================================
  // Close Viewer
  // ==========================================================

  const close = () => {
    setSelectedDocId(null);
    setPage("documents");
  };

  // ==========================================================
  // Loading State
  // ==========================================================

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-cyan-500" />

        <p className="mt-4 text-sm text-slate-500">
          Loading document...
        </p>
      </div>
    );
  }

  // ==========================================================
  // Error / Not Found
  // ==========================================================

  if (error || !doc) {
    return (
      <div className="py-20 text-center">
        <FileText
          size={32}
          className="mx-auto text-slate-300 dark:text-slate-700"
        />

        <p className="mt-3 text-sm text-slate-500">
          {error ?? "Document not found."}
        </p>

        <Button
          variant="secondary"
          size="sm"
          className="mt-4"
          onClick={close}
        >
          <ArrowLeft size={14} />
          Back to documents
        </Button>
      </div>
    );
  }

  // ==========================================================
  // Document Data
  // ==========================================================

  const preview = doc.preview;

  const risk = preview?.riskLevel
    ? riskConfig(preview.riskLevel)
    : null;

  const fileType =
    doc.file_type?.toLowerCase() ??
    "unknown";

  const iconName =
    getDocumentIcon(fileType);

  const iconColor =
    getDocumentIconColor(fileType);

  // ==========================================================
  // Render
  // ==========================================================

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ======================================================
          Top Bar
          ====================================================== */}

      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Document information */}

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={close}
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Back to documents"
          >
            <ArrowLeft size={18} />
          </button>

          <div className="flex items-center gap-2.5">
            {iconName ? (
              <IconByName
                name={iconName}
                size={18}
                className={iconColor}
              />
            ) : (
              <FileText
                size={18}
                className="text-slate-400"
              />
            )}

            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                {doc.name}
              </h2>

              <p className="text-xs text-slate-400">
                {doc.size ??
                  formatFileSize(
                    doc.file_size
                  )}

                {" · "}

                {doc.pages
                  ? `${doc.pages} pages · `
                  : ""}

                {formatDate(
                  doc.created_at
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
          >
            <Share2 size={14} />

            <span className="hidden sm:inline">
              Share
            </span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
          >
            <Download size={14} />

            <span className="hidden sm:inline">
              Export
            </span>
          </Button>
        </div>
      </div>

      {/* ======================================================
          Main Content
          ====================================================== */}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* ====================================================
            LEFT: Document Preview
            ==================================================== */}

        <Card className="overflow-hidden">
          {/* Preview Header */}

          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <FileText
                size={15}
                className="text-slate-400"
              />

              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                Document Preview
              </span>
            </div>

            {doc.pages && (
              <span className="text-xs text-slate-400">
                Page 1 of {doc.pages}
              </span>
            )}
          </div>

          {/* Preview Content */}

          <div className="bg-slate-50 p-6 dark:bg-slate-900/50">
            {/* Simulated document page */}

            <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
              {/* Document Header */}

              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-sky-400 via-cyan-500 to-teal-500">
                    <FileText
                      size={16}
                      className="text-white"
                    />
                  </div>

                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">
                    {preview?.vendor ??
                      "Document"}
                  </span>
                </div>

                <span className="text-[10px] text-slate-400">
                  {preview?.invoiceNumber ??
                    doc.id.toUpperCase()}
                </span>
              </div>

              {/* Extracted Fields */}

              {preview?.extractedFields &&
              preview.extractedFields.length >
                0 ? (
                <div className="space-y-3">
                  {preview.extractedFields
                    .slice(0, 6)
                    .map(
                      (
                        field,
                        index
                      ) => (
                        <div
                          key={`${field.label}-${index}`}
                          className="flex justify-between gap-4 border-b border-dashed border-slate-100 pb-2 dark:border-slate-700/50"
                        >
                          <span className="text-xs text-slate-400">
                            {field.label}
                          </span>

                          <span className="text-right text-xs font-medium text-slate-700 dark:text-slate-200">
                            {field.value}
                          </span>
                        </div>
                      )
                    )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="h-3 w-full rounded bg-slate-100 dark:bg-slate-700" />

                  <div className="h-3 w-4/5 rounded bg-slate-100 dark:bg-slate-700" />

                  <div className="h-3 w-3/5 rounded bg-slate-100 dark:bg-slate-700" />

                  <div className="h-3 w-5/6 rounded bg-slate-100 dark:bg-slate-700" />
                </div>
              )}

              {/* Annotations */}

              {preview?.annotations &&
                preview.annotations.length >
                  0 && (
                  <div className="mt-4 space-y-1.5">
                    {preview.annotations.map(
                      (
                        annotation
                      ) => (
                        <div
                          key={
                            annotation.id
                          }
                          className={`rounded px-2 py-1 text-[10px] font-medium ${
                            annotation.type ===
                            "risk"
                              ? "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
                              : "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300"
                          }`}
                        >
                          <span className="flex items-start gap-1">
                            {annotation.type ===
                            "risk" ? (
                              <AlertTriangle
                                size={
                                  10
                                }
                                className="mt-0.5 shrink-0"
                              />
                            ) : (
                              <Quote
                                size={
                                  10
                                }
                                className="mt-0.5 shrink-0"
                              />
                            )}

                            <span>
                              {
                                annotation.label
                              }
                              :{" "}
                              &quot;
                              {
                                annotation.text
                              }
                              &quot;
                            </span>
                          </span>
                        </div>
                      )
                    )}
                  </div>
                )}
            </div>
          </div>
        </Card>

        {/* ====================================================
            RIGHT: AI Analysis
            ==================================================== */}

        <div className="space-y-4">
          {/* ==================================================
              AI Summary
              ================================================== */}

          {preview?.summary && (
            <Card>
              <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                <Sparkles
                  size={15}
                  className="text-cyan-500"
                />

                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  AI Summary
                </span>
              </div>

              <div className="p-4">
                <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                  {preview.summary}
                </p>

                {/* Risk */}

                {risk && (
                  <div
                    className={`mt-3 flex items-center gap-2 rounded-lg px-3 py-2 ${risk.bg}`}
                  >
                    {preview.riskLevel ===
                    "low" ? (
                      <CheckCircle2
                        size={15}
                        className={
                          risk.color
                        }
                      />
                    ) : (
                      <AlertTriangle
                        size={15}
                        className={
                          risk.color
                        }
                      />
                    )}

                    <span
                      className={`text-xs font-medium ${risk.color}`}
                    >
                      {risk.label}
                    </span>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* ==================================================
              Extracted Fields
              ================================================== */}

          {preview?.extractedFields &&
            preview.extractedFields.length >
              0 && (
              <Card>
                <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Extracted Fields
                  </span>

                  <span className="text-xs text-slate-400">
                    {
                      preview
                        .extractedFields
                        .length
                    }{" "}
                    fields
                  </span>
                </div>

                <div className="divide-y divide-slate-50 dark:divide-slate-800/50">
                  {preview.extractedFields.map(
                    (
                      field,
                      index
                    ) => (
                      <div
                        key={`${field.label}-${index}`}
                        className="flex items-center justify-between gap-4 px-4 py-2.5"
                      >
                        <div className="min-w-0">
                          <div className="text-xs text-slate-400">
                            {
                              field.label
                            }
                          </div>

                          <div className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
                            {
                              field.value
                            }
                          </div>
                        </div>

                        <ConfidenceBadge
                          value={
                            field.confidence
                          }
                        />
                      </div>
                    )
                  )}
                </div>
              </Card>
            )}

          {/* ==================================================
              No Analysis
              ================================================== */}

          {!preview && (
            <Card className="p-8 text-center">
              <FileText
                size={32}
                className="mx-auto text-slate-300 dark:text-slate-700"
              />

              <p className="mt-3 text-sm text-slate-500">
                {doc.status ===
                "processing"
                  ? "AI processing in progress — analysis will appear here shortly."
                  : doc.status ===
                      "queued"
                    ? "Document is queued for AI processing."
                    : doc.status ===
                        "pending"
                      ? "Document is waiting to be processed."
                      : "No AI analysis available for this document."}
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// File Size Helper
// ============================================================

function formatFileSize(
  bytes?: number
): string {
  if (
    bytes === undefined ||
    bytes === null ||
    Number.isNaN(bytes) ||
    bytes <= 0
  ) {
    return "Unknown size";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(
      bytes / 1024
    ).toFixed(0)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}