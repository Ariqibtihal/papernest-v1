import { ExternalLink, Download, Bookmark, BookmarkCheck, AlertTriangle, Quote } from "lucide-react"
import { useState } from "react"
import type { PaperDTO } from "@/types/paper"
import { formatCitation } from "@/services/api"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Badge, type BadgeVariant } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { savePaper, paperToCreate } from "@/services/savedPapers"

interface PaperDetailProps {
  paper: PaperDTO
  onClose: () => void
}

const QUARTILE_VARIANT: Record<"Q1" | "Q2" | "Q3" | "Q4", BadgeVariant> = {
  Q1: "q1",
  Q2: "q2",
  Q3: "q3",
  Q4: "q4",
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </p>
  )
}

export function PaperDetail({ paper, onClose }: PaperDetailProps) {
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (saved || saving) return
    setSaving(true)
    try {
      await savePaper(paperToCreate(paper))
      setSaved(true)
    } catch {
      // silently fail — user can retry
    } finally {
      setSaving(false)
    }
  }

  const quartile = paper.quartile ?? null

  return (
    <Dialog open onOpenChange={(open: boolean) => { if (!open) onClose() }}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Top badges row */}
        <div className="flex flex-wrap items-center gap-1.5">
          {quartile && (
            <Badge variant={QUARTILE_VARIANT[quartile]} title="Peringkat kuartil menurut Scimago Journal Rank">
              {quartile}
            </Badge>
          )}
          {paper.is_open_access && <Badge variant="oa">Open Access</Badge>}
          {paper.year && (
            <span className="text-[12px] font-medium text-muted-foreground">
              {paper.year}
            </span>
          )}
          {paper.venue && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="text-[12px] italic text-muted-foreground truncate max-w-[20rem]">
                {paper.venue}
              </span>
            </>
          )}
          {paper.is_predatory && (
            <Badge
              variant="predatory"
              className="ml-auto"
              title="Heuristik berdasarkan kriteria Beall's List — verifikasi manual disarankan"
            >
              <AlertTriangle className="mr-1 h-3 w-3" /> Predatory
            </Badge>
          )}
        </div>

        <DialogHeader className="mt-2">
          <DialogTitle className="font-display text-2xl font-semibold leading-tight tracking-tight text-foreground pr-8">
            {paper.title}
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {paper.authors.map((a) => a.name).join(", ") || "—"}
          </DialogDescription>
        </DialogHeader>

        {/* Citation count chip */}
        {paper.citation_count != null && (
          <div className="mt-1 inline-flex items-center gap-1.5 text-[13px] text-muted-foreground">
            <Quote className="h-3.5 w-3.5 rotate-180 fill-current opacity-60" />
            <span className="font-semibold text-foreground">{formatCitation(paper.citation_count)}</span>
            <span>citations</span>
          </div>
        )}

        {paper.abstract && (
          <div className="mt-5">
            <Eyebrow>Abstract</Eyebrow>
            <p className="mt-2 text-[14px] leading-relaxed text-foreground/85">{paper.abstract}</p>
          </div>
        )}

        {paper.topics.length > 0 && (
          <div className="mt-5">
            <Eyebrow>Topics</Eyebrow>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {paper.topics.map((t) => (
                <Badge key={t} variant="source" className="font-normal">
                  {t}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Eyebrow>DOI</Eyebrow>
            <p className="mt-1 text-sm text-foreground/85 break-all">{paper.doi || "—"}</p>
          </div>
          <div>
            <Eyebrow>Publisher</Eyebrow>
            <p className="mt-1 text-sm text-foreground/85">{paper.publisher || "—"}</p>
          </div>
          <div>
            <Eyebrow>Sources</Eyebrow>
            <p className="mt-1 text-sm text-foreground/85 capitalize">
              {paper.sources.map((s) => s.replace("_", " ")).join(", ")}
            </p>
          </div>
          <div>
            <Eyebrow>Venue ISSN</Eyebrow>
            <p className="mt-1 text-sm text-foreground/85">{paper.venue_issn || "—"}</p>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-5">
          {paper.oa_url && (
            <Button variant="pillPrimary" asChild>
              <a href={paper.oa_url} target="_blank" rel="noreferrer">
                <Download className="mr-2 h-4 w-4" /> Open PDF
              </a>
            </Button>
          )}
          {paper.landing_url && (
            <Button variant="pillOutline" asChild>
              <a href={paper.landing_url} target="_blank" rel="noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" /> View Source
              </a>
            </Button>
          )}
          {paper.doi && (
            <Button variant="pillOutline" asChild>
              <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" /> DOI
              </a>
            </Button>
          )}
          <Button
            variant={saved ? "secondary" : "ghost"}
            onClick={handleSave}
            disabled={saved || saving}
            className="ml-auto rounded-pill"
          >
            {saved ? (
              <><BookmarkCheck className="mr-2 h-4 w-4" /> Saved</>
            ) : (
              <><Bookmark className="mr-2 h-4 w-4" /> {saving ? "Saving..." : "Save Paper"}</>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
