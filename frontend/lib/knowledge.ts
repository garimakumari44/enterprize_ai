import api from "./api";

// ============================================================
// TYPES
// ============================================================

export type SearchType =
  | "semantic"
  | "keyword"
  | "hybrid";

export interface SearchRequest {
  query: string;
  collection_id?: string | null;
  search_type?: SearchType;
  top_k?: number;
  score_threshold?: number;
  filters?: Record<string, unknown>;
  include_metadata?: boolean;
  rerank?: boolean;
}

export interface SearchResult {
  chunk_id: string | null;
  document_id: string | null;
  collection_id: string | null;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
  semantic_score?: number | null;
  keyword_score?: number | null;
}

export interface SearchResponse {
  query: string;
  normalized_query?: string;
  intent?: string;
  filters?: Record<string, unknown>;
  total_results: number;
  elapsed_ms: number;
  search_type: SearchType;
  results: SearchResult[];
}

// ============================================================
// KNOWLEDGE SEARCH
// POST /api/v1/knowledge/
// ============================================================

export async function searchKnowledge(
  request: SearchRequest
): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>(
    "/knowledge/",
    request
  );

  return response.data;
}

// ============================================================
// HYBRID SEARCH
// POST /api/v1/knowledge/hybrid
// ============================================================

export async function hybridSearch(
  request: SearchRequest
): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>(
    "/knowledge/hybrid",
    {
      ...request,
      search_type: "hybrid",
    }
  );

  return response.data;
}

// ============================================================
// SEARCH HISTORY
// GET /api/v1/knowledge/history
// ============================================================

export async function getSearchHistory(
  limit = 20
) {
  const response = await api.get(
    "/knowledge/history",
    {
      params: {
        limit,
      },
    }
  );

  return response.data;
}

// ============================================================
// SIMILAR DOCUMENTS
// GET /api/v1/knowledge/similar/{document_id}
// ============================================================

export async function getSimilarDocuments(
  documentId: string,
  topK = 5
) {
  const response = await api.get(
    `/knowledge/similar/${encodeURIComponent(documentId)}`,
    {
      params: {
        top_k: topK,
      },
    }
  );

  return response.data;
}