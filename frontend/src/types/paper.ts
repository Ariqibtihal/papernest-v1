export interface AuthorDTO {
  name: string
  orcid?: string | null
  affiliation?: string | null
}

export interface PaperDTO {
  title: string
  authors: AuthorDTO[]
  abstract?: string | null
  year?: number | null
  publication_date?: string | null
  doi?: string | null
  arxiv_id?: string | null
  pubmed_id?: string | null
  source: string
  sources: string[]
  venue?: string | null
  venue_issn?: string | null
  publisher?: string | null
  citation_count?: number | null
  reference_count?: number | null
  is_open_access: boolean
  oa_url?: string | null
  landing_url?: string | null
  topics: string[]
  relevance_score?: number | null
  recency_score?: number | null
  citation_score?: number | null
  venue_score?: number | null
  journal_quality_score?: number | null
  open_access_score?: number | null
  semantic_score?: number | null
  is_predatory?: boolean
  quartile?: "Q1" | "Q2" | "Q3" | "Q4" | null
  final_score?: number | null
}

export interface SearchFilters {
  year_from?: number | null
  year_to?: number | null
  sources?: string[] | null
  open_access?: boolean | null
  min_citations?: number | null
  venue_contains?: string | null
  topic?: string | null
  institution?: string | null
  type?: string | null
}

export interface SearchRequest {
  query: string
  filters: SearchFilters
  limit: number
  offset?: number
  sort_by?: "relevance" | "year_desc" | "year_asc" | "citations"
}

export interface SearchResponse {
  total: number
  latency_ms: number
  results: PaperDTO[]
  offset: number
  has_more: boolean
  warnings?: string[]
}
