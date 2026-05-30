import { useState } from "react"
import { Quote, Bookmark, BookmarkCheck, AlertTriangle } from "lucide-react"
import type { PaperDTO } from "@/types/paper"
import { formatCitation } from "@/services/api"
import { Badge, type BadgeVariant } from "@/components/ui/badge"
import { savePaper, paperToCreate } from "@/services/savedPapers"

interface PaperCardProps {
  paper: PaperDTO
  onSelect: (paper: PaperDTO) => void
}

const QUARTILE_VARIANT: Record<"Q1" | "Q2" | "Q3" | "Q4", BadgeVariant> = {
  Q1: "q1",
  Q2: "q2",
  Q3: "q3",
  Q4: "q4",
}

const QUARTILE_TOOLTIP =
  "Peringkat kuartil menurut Scimago Journal Rank. Q1 adalah top 25% dalam bidangnya."

export function PaperCard({ paper, onSelect }: PaperCardProps) {
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  const authorText =
    paper.authors.length > 0
      ? paper.authors.slice(0, 3).map((a) => a.name).join(", ") +
        (paper.authors.length > 3 ? ` +${paper.authors.length - 3} more` : "")
      : "Authors unavailable"

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (saved || saving) return
    setSaving(true)
    try {
      await savePaper(paperToCreate(paper))
      setSaved(true)
    } catch {
      // silently fail
    } finally {
      setSaving(false)
    }
  }

  const quartile = paper.quartile ?? null
  const sourceList = paper.sources && paper.sources.length > 0 ? paper.sources : [paper.source]

  return (
    <article
      onClick={() => onSelect(paper)}
      className="group cursor-pointer rounded-xl border border-border/60 bg-card p-5 shadow-card transition-all hover:shadow-elevated hover:border-primary/30 active:scale-[0.998]"
    >
      {/* Row 1 — meta badges */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {quartile && (
            <Badge variant={QUARTILE_VARIANT[quartile]} title={QUARTILE_TOOLTIP}>
              {quartile}
            </Badge>
          )}
          {paper.is_open_access && (
            <Badge variant="oa" title="Open Access — full text tersedia gratis">
              OA
            </Badge>
          )}
          {paper.year && (
            <span className="text-[12px] font-medium text-muted-foreground">
              {paper.year}
            </span>
          )}
          {paper.venue && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="max-w-[14rem] truncate text-[12px] italic text-muted-foreground">
                {paper.venue}
              </span>
            </>
          )}
        </div>

        {paper.is_predatory && (
          <Badge
            variant="predatory"
            title="Heuristik berdasarkan kriteria Beall's List — verifikasi manual disarankan"
            className="shrink-0"
          >
            <AlertTriangle className="mr-1 h-3 w-3" /> Predatory
          </Badge>
        )}
      </div>

      {/* Row 2 — title */}
      <h3 className="mt-2.5 font-display text-[18px] font-semibold leading-snug tracking-tight text-foreground transition-colors group-hover:text-primary">
        {paper.title}
      </h3>

      {/* Row 3 — authors */}
      <p className="mt-1.5 text-[13px] text-muted-foreground">{authorText}</p>

      {/* Row 4 — abstract excerpt */}
      {paper.abstract && (
        <p className="mt-2.5 line-clamp-2 text-[14px] leading-relaxed text-foreground/75">
          {paper.abstract}
        </p>
      )}

      {/* Row 5 — footer: citations + source chips + save */}
      <div className="mt-3.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          {paper.citation_count != null && (
            <span className="flex items-center gap-1 text-[12px] text-muted-foreground">
              <Quote className="h-3 w-3 rotate-180 fill-current opacity-60" />
              <span className="font-medium text-foreground/80">
                {formatCitation(paper.citation_count)}
              </span>
              <span>citations</span>
            </span>
          )}
          {sourceList.length > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <div className="flex items-center gap-1 min-w-0">
                <Badge variant="source" className="capitalize text-[10px] px-2 py-0">
                  {sourceList[0].replace("_", " ")}
                </Badge>
                {sourceList.length > 1 && (
                  <span className="text-[11px] text-muted-foreground">
                    +{sourceList.length - 1} more
                  </span>
                )}
              </div>
            </>
          )}
        </div>

        <button
          onClick={handleSave}
          title={saved ? "Saved" : "Save paper"}
          className={`flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-[12px] font-medium transition-all ${
            saved
              ? "text-primary"
              : "text-muted-foreground hover:bg-accent hover:text-foreground"
          }`}
        >
          {saved ? (
            <BookmarkCheck className="h-3.5 w-3.5" />
          ) : saving ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
          ) : (
            <Bookmark className="h-3.5 w-3.5" />
          )}
          <span className="hidden sm:inline">{saved ? "Saved" : "Save"}</span>
        </button>
      </div>
    </article>
  )
}
