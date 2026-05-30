import { useState, useEffect } from 'react';
import { Bookmark, Trash2, ExternalLink, Download } from 'lucide-react';
import { PaperDetail } from '@/components/PaperDetail';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { listSavedPapers, deleteSavedPaper, type SavedPaperOut } from '@/services/savedPapers';
import type { PaperDTO } from '@/types/paper';
import { formatCitation } from '@/services/api';

function savedToPaperDTO(s: SavedPaperOut): PaperDTO {
  return {
    title: s.title,
    authors: s.authors ?? [],
    abstract: s.abstract,
    year: s.year,
    doi: s.doi,
    arxiv_id: s.arxiv_id,
    pubmed_id: s.pubmed_id,
    source: s.source ?? 'saved',
    sources: [s.source ?? 'saved'],
    venue: s.venue,
    publisher: s.publisher,
    citation_count: s.citation_count,
    is_open_access: s.is_open_access,
    landing_url: s.landing_url,
    oa_url: s.oa_url,
    topics: s.topics ?? [],
  };
}

export function SavedPapersPage() {
  const [papers, setPapers] = useState<SavedPaperOut[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<PaperDTO | null>(null);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listSavedPapers(100, 0);
      setPapers(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load saved papers');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: number) => {
    try {
      await deleteSavedPaper(id);
      setPapers(prev => prev.filter(p => p.id !== id));
    } catch {
      setError('Failed to remove paper');
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center gap-3">
        <Bookmark className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold text-foreground">Saved Papers</h1>
          <p className="text-sm text-muted-foreground">
            {isLoading ? 'Loading...' : `${papers.length} paper${papers.length !== 1 ? 's' : ''} saved`}
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse border-b py-4">
              <div className="h-4 w-3/4 rounded bg-muted" />
              <div className="mt-2 h-3 w-1/2 rounded bg-muted" />
            </div>
          ))}
        </div>
      ) : papers.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <Bookmark className="h-12 w-12 text-muted-foreground/20" />
          <div>
            <p className="text-lg font-semibold text-foreground">No saved papers yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Click the bookmark icon on any paper to save it here.
            </p>
          </div>
        </div>
      ) : (
        <div className="divide-y divide-border">
          {papers.map((paper) => (
            <div key={paper.id} className="group py-4">
              <div className="flex items-start justify-between gap-4">
                <div
                  className="flex-1 min-w-0 cursor-pointer"
                  onClick={() => setSelectedPaper(savedToPaperDTO(paper))}
                >
                  <h3 className="text-[15px] font-medium leading-snug text-link group-hover:underline">
                    {paper.title}
                  </h3>
                  <div className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[13px] text-foreground/70">
                    {paper.year && <span>{paper.year}</span>}
                    {paper.year && paper.venue && <span className="text-foreground/40">·</span>}
                    {paper.venue && <span className="italic truncate max-w-[20rem]">{paper.venue}</span>}
                    {paper.citation_count != null && (
                      <>
                        <span className="text-foreground/40">·</span>
                        <span>{formatCitation(paper.citation_count)} citations</span>
                      </>
                    )}
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {paper.is_open_access && (
                      <Badge variant="outline" className="h-5 px-1.5 text-[10px]">Open Access</Badge>
                    )}
                    {paper.source && (
                      <Badge variant="secondary" className="h-5 px-1.5 text-[10px] capitalize">{paper.source}</Badge>
                    )}
                    <span className="text-[11px] text-muted-foreground">
                      Saved {new Date(paper.saved_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  {paper.oa_url && (
                    <Button variant="ghost" size="icon" className="h-8 w-8" asChild title="Download PDF">
                      <a href={paper.oa_url} target="_blank" rel="noreferrer">
                        <Download className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                  {paper.landing_url && (
                    <Button variant="ghost" size="icon" className="h-8 w-8" asChild title="Open source">
                      <a href={paper.landing_url} target="_blank" rel="noreferrer">
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={() => handleDelete(paper.id)}
                    title="Remove"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedPaper && (
        <PaperDetail paper={selectedPaper} onClose={() => setSelectedPaper(null)} />
      )}
    </div>
  );
}
