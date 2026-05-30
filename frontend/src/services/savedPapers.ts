import { PaperDTO } from "@/types/paper";

export interface SavedPaperCreate {
  doi?: string | null;
  arxiv_id?: string | null;
  pubmed_id?: string | null;
  title: string;
  authors: { name: string; orcid?: string | null; affiliation?: string | null }[];
  abstract?: string | null;
  year?: number | null;
  venue?: string | null;
  publisher?: string | null;
  source?: string | null;
  citation_count?: number | null;
  is_open_access?: boolean;
  landing_url?: string | null;
  oa_url?: string | null;
  topics?: string[];
  notes?: string | null;
}

export interface SavedPaperOut {
  id: number;
  doi: string | null;
  arxiv_id: string | null;
  pubmed_id: string | null;
  title: string;
  authors: { name: string; orcid?: string | null; affiliation?: string | null }[];
  abstract: string | null;
  year: number | null;
  venue: string | null;
  publisher: string | null;
  source: string | null;
  citation_count: number | null;
  is_open_access: boolean;
  landing_url: string | null;
  oa_url: string | null;
  topics: string[];
  notes: string | null;
  saved_at: string;
}

export interface SavedPaperList {
  total: number;
  items: SavedPaperOut[];
}

export async function savePaper(data: SavedPaperCreate): Promise<SavedPaperOut> {
  const res = await fetch("/api/v1/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save paper");
  return res.json();
}

export async function listSavedPapers(limit = 50, offset = 0): Promise<SavedPaperList> {
  const res = await fetch(`/api/v1/saved?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to list saved papers");
  return res.json();
}

export async function deleteSavedPaper(id: number): Promise<void> {
  const res = await fetch(`/api/v1/saved/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete saved paper");
}

export function paperToCreate(paper: PaperDTO): SavedPaperCreate {
  return {
    doi: paper.doi ?? null,
    arxiv_id: paper.arxiv_id ?? null,
    pubmed_id: paper.pubmed_id ?? null,
    title: paper.title,
    authors: paper.authors.map((a) => ({
      name: a.name,
      orcid: a.orcid ?? null,
      affiliation: a.affiliation ?? null,
    })),
    abstract: paper.abstract ?? null,
    year: paper.year ?? null,
    venue: paper.venue ?? null,
    publisher: paper.publisher ?? null,
    source: paper.source ?? null,
    citation_count: paper.citation_count ?? null,
    is_open_access: paper.is_open_access,
    landing_url: paper.landing_url ? String(paper.landing_url) : null,
    oa_url: paper.oa_url ? String(paper.oa_url) : null,
    topics: paper.topics,
    notes: null,
  };
}
