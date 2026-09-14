import { useState } from "react";
import {
  Search,
  FileText,
  Sparkles,
  ArrowRight,
  Database,
  Loader2,
  AlertCircle,
} from "lucide-react";

import { Card } from "./ui/Card";
import { ConfidenceBadge } from "./ui/ConfidenceBadge";

import {
  searchKnowledge,
  type SearchResult as ApiSearchResult,
} from "../../../lib/knowledge";

import type { SearchResult } from "../../../types";

// ============================================================
// SAMPLE QUERIES
// ============================================================

const sampleQueries = [
  "Find all invoices above $100,000",
  "Contracts with liability clauses",
  "Resumes with Kubernetes experience",
  "Documents processed this week",
];

// ============================================================
// FRONTEND RESULT MAPPER
// ============================================================

/**
 * Converts the backend SearchResult format into the format
 * expected by the existing Knowledge Search UI.
 *
 * Backend:
 *
 * {
 *   chunk_id,
 *   document_id,
 *   collection_id,
 *   content,
 *   score,
 *   metadata
 * }
 *
 * Frontend:
 *
 * {
 *   id,
 *   docName,
 *   excerpt,
 *   workflow,
 *   page,
 *   confidence
 * }
 */
function mapSearchResult(
  result: ApiSearchResult
): SearchResult {
  const metadata = result.metadata ?? {};

  const documentName =
    metadata.document_name ??
    metadata.documentName ??
    metadata.filename ??
    metadata.file_name ??
    metadata.title ??
    "Unknown document";

  const workflow =
    metadata.workflow ??
    metadata.workflow_name ??
    metadata.document_type ??
    metadata.type ??
    "Knowledge Base";

  const pageValue =
    metadata.page ??
    metadata.page_number ??
    metadata.pageNumber ??
    1;

  const page =
    typeof pageValue === "number"
      ? pageValue
      : Number(pageValue) || 1;

  const id =
    result.chunk_id ??
    result.document_id ??
    `result-${Math.random().toString(36).slice(2)}`;

  return {
    id: String(id),
    docName: String(documentName),
    excerpt: result.content ?? "",
    workflow: String(workflow),
    page,
    confidence: Number(result.score ?? 0),
  };
}

// ============================================================
// COMPONENT
// ============================================================

export function KnowledgeSearchPage() {
  // ==========================================================
  // STATE
  // ==========================================================

  const [query, setQuery] = useState("");

  const [searched, setSearched] = useState(false);

  const [results, setResults] = useState<SearchResult[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [searchTime, setSearchTime] = useState<number | null>(
    null
  );

  // ==========================================================
  // RUN SEARCH
  // ==========================================================

  const runSearch = async (q: string) => {
    const trimmedQuery = q.trim();

    // --------------------------------------------------------
    // Validate query
    // --------------------------------------------------------

    if (!trimmedQuery) {
      setError("Please enter a search query.");
      setResults([]);
      setSearched(false);
      return;
    }

    // --------------------------------------------------------
    // Update UI
    // --------------------------------------------------------

    setQuery(trimmedQuery);
    setSearched(true);
    setLoading(true);
    setError(null);
    setResults([]);
    setSearchTime(null);

    // --------------------------------------------------------
    // Call backend
    // --------------------------------------------------------

    try {
      const response = await searchKnowledge({
        query: trimmedQuery,

        // Your backend supports:
        // semantic | keyword | hybrid
        search_type: "hybrid",

        // Number of results
        top_k: 10,

        // Return everything >= 0
        score_threshold: 0,

        // Return metadata because the UI uses
        // document name, workflow, page, etc.
        include_metadata: true,

        // Ask backend to rerank results
        rerank: true,

        // No collection restriction for now
        collection_id: null,

        // No additional metadata filters
        filters: {},
      });

      // ------------------------------------------------------
      // Save search latency
      // ------------------------------------------------------

      setSearchTime(response.elapsed_ms);

      // ------------------------------------------------------
      // Convert backend results to UI results
      // ------------------------------------------------------

      const mappedResults = response.results.map(
        mapSearchResult
      );

      setResults(mappedResults);
    } catch (err: any) {
      console.error(
        "Knowledge search failed:",
        err
      );

      // ------------------------------------------------------
      // Extract useful backend error
      // ------------------------------------------------------

      let message =
        "Unable to search the knowledge base.";

      if (err?.response?.data?.detail) {
        message = String(
          err.response.data.detail
        );
      } else if (err?.message) {
        message = String(err.message);
      }

      setError(message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================
  // HANDLE ENTER
  // ==========================================================

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === "Enter" && !loading) {
      void runSearch(query);
    }
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ======================================================
          SEARCH HERO
          ====================================================== */}

      <Card className="overflow-hidden">
        <div className="relative bg-gradient-to-br from-slate-50 to-cyan-50/50 p-8 dark:from-slate-800/50 dark:to-slate-900">
          {/* Background glow */}

          <div className="pointer-events-none absolute -right-20 -top-20 h-60 w-60 rounded-full bg-cyan-500/10 blur-[80px]" />

          <div className="relative mx-auto max-w-2xl text-center">
            {/* Knowledge badge */}

            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-cyan-600 dark:border-slate-700 dark:bg-slate-800 dark:text-cyan-400">
              <Database size={13} />

              <span>
                Enterprise Knowledge Base
              </span>
            </div>

            {/* Heading */}

            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              Search across all your documents
            </h2>

            {/* Description */}

            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Ask in natural language — AI finds
              relevant documents, excerpts, and
              sources.
            </p>

            {/* ==================================================
                SEARCH INPUT
                ================================================== */}

            <div className="relative mt-6">
              {/* Search icon */}

              <Search
                size={18}
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
              />

              {/* Input */}

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                onKeyDown={handleKeyDown}
                disabled={loading}
                placeholder="e.g. Find all invoices above ₹500000"
                className="w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-12 pr-32 text-sm text-slate-700 shadow-sm placeholder:text-slate-400 transition-all focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-70 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />

              {/* Search button */}

              <button
                type="button"
                onClick={() => void runSearch(query)}
                disabled={loading || !query.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2 rounded-lg bg-gradient-to-r from-slate-900 to-slate-800 px-4 py-2 text-sm font-medium text-white transition-all hover:from-slate-800 hover:to-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:from-cyan-500 dark:to-teal-500 dark:hover:from-cyan-400 dark:hover:to-teal-400"
              >
                {loading ? (
                  <>
                    <Loader2
                      size={14}
                      className="animate-spin"
                    />

                    <span>Searching...</span>
                  </>
                ) : (
                  <span>Search</span>
                )}
              </button>
            </div>

            {/* ==================================================
                SAMPLE QUERIES
                ================================================== */}

            <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
              {sampleQueries.map((sampleQuery) => (
                <button
                  key={sampleQuery}
                  type="button"
                  disabled={loading}
                  onClick={() =>
                    void runSearch(sampleQuery)
                  }
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 transition-all hover:border-cyan-300 hover:bg-cyan-50 hover:text-cyan-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-cyan-700 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-300"
                >
                  {sampleQuery}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ======================================================
          ERROR
          ====================================================== */}

      {error && (
        <Card className="border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/20">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 shrink-0">
              <AlertCircle
                size={18}
                className="text-red-500"
              />
            </div>

            <div>
              <p className="text-sm font-medium text-red-700 dark:text-red-400">
                Search failed
              </p>

              <p className="mt-1 text-sm text-red-600 dark:text-red-400/80">
                {error}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* ======================================================
          LOADING
          ====================================================== */}

      {loading && (
        <Card className="p-8">
          <div className="flex flex-col items-center justify-center text-center">
            <Loader2
              size={24}
              className="animate-spin text-cyan-500"
            />

            <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-200">
              Searching your knowledge base...
            </p>

            <p className="mt-1 text-xs text-slate-400">
              Finding the most relevant documents
            </p>
          </div>
        </Card>
      )}

      {/* ======================================================
          RESULTS
          ====================================================== */}

      {searched && !loading && !error && (
        <div className="space-y-3">
          {/* Results header */}

          <div className="flex items-center gap-2">
            <Sparkles
              size={15}
              className="text-cyan-500"
            />

            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              {results.length}{" "}
              {results.length === 1
                ? "result"
                : "results"}{" "}
              found
            </span>

            {searchTime !== null && (
              <span className="text-xs text-slate-400">
                ({searchTime.toFixed(0)} ms)
              </span>
            )}
          </div>

          {/* ==================================================
              EMPTY RESULTS
              ================================================== */}

          {results.length === 0 && (
            <Card className="p-8">
              <div className="flex flex-col items-center justify-center text-center">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 dark:bg-slate-800">
                  <Search
                    size={20}
                    className="text-slate-400"
                  />
                </div>

                <h3 className="mt-4 text-sm font-semibold text-slate-800 dark:text-white">
                  No results found
                </h3>

                <p className="mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">
                  We couldn't find documents matching
                  your query. Try using different
                  keywords or a broader question.
                </p>
              </div>
            </Card>
          )}

          {/* ==================================================
              RESULT CARDS
              ================================================== */}

          {results.map((result) => (
            <Card
              key={result.id}
              hover
              className="p-4"
            >
              <div className="flex items-start gap-3">
                {/* Document icon */}

                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-sky-50 to-cyan-50 dark:from-slate-800 dark:to-slate-800/50">
                  <FileText
                    size={16}
                    className="text-cyan-600 dark:text-cyan-400"
                  />
                </div>

                {/* Result content */}

                <div className="min-w-0 flex-1">
                  {/* Result metadata */}

                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800 dark:text-white">
                      {result.docName}
                    </span>

                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                      {result.workflow}
                    </span>

                    <span className="text-[10px] text-slate-400">
                      Page {result.page}
                    </span>
                  </div>

                  {/* Excerpt */}

                  <p className="mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                    {result.excerpt}
                  </p>

                  {/* Bottom actions */}

                  <div className="mt-2.5 flex items-center gap-3">
                    {/* Confidence */}

                    <ConfidenceBadge
                      value={result.confidence}
                      showBar
                    />

                    {/* Open document */}

                    <button
                      type="button"
                      disabled={!result.id}
                      className="ml-auto flex items-center gap-1 text-xs font-medium text-cyan-600 transition-colors hover:text-cyan-700 disabled:cursor-not-allowed disabled:opacity-50 dark:text-cyan-400"
                    >
                      Open document

                      <ArrowRight size={12} />
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}