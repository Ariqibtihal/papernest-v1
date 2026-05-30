import type { PaperDTO } from "@/types/paper"
import { PaperCard } from "./PaperCard"

interface PaperListProps {
  papers: PaperDTO[]
  onSelect: (paper: PaperDTO) => void
  loading?: boolean
  searched?: boolean
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-border/40 bg-card p-5 shadow-card">
      <div className="flex items-center gap-2">
        <div className="h-5 w-8 rounded-full bg-primary-soft/60" />
        <div className="h-5 w-10 rounded-full bg-primary-soft/40" />
        <div className="h-3 w-12 rounded bg-muted" />
      </div>
      <div className="mt-3 h-5 w-4/5 rounded bg-muted" />
      <div className="mt-2 h-3 w-1/2 rounded bg-muted/60" />
      <div className="mt-3 space-y-1.5">
        <div className="h-3 w-full rounded bg-muted/50" />
        <div className="h-3 w-3/4 rounded bg-muted/50" />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="h-3 w-24 rounded bg-muted/50" />
        <div className="h-3 w-12 rounded bg-muted/50" />
      </div>
    </div>
  )
}

export function PaperList({ papers, onSelect, loading, searched }: PaperListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (papers.length === 0 && searched) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/60 py-16 text-center text-sm text-muted-foreground">
        <p className="font-medium text-foreground">No results found.</p>
        <p className="mt-1 text-[13px]">Try a different query or relax your filters.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {papers.map((paper, idx) => (
        <PaperCard
          key={`${paper.doi || paper.title}-${idx}`}
          paper={paper}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}
