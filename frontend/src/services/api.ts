import type { SearchRequest, SearchResponse } from "@/types/paper"

const API_BASE = "/api/v1"

export async function searchPapers(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Search failed: ${response.status}`)
  }
  return response.json()
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "-"
  return score.toFixed(2)
}

export function formatCitation(count: number | null | undefined): string {
  if (count === null || count === undefined) return "-"
  return count.toLocaleString()
}
