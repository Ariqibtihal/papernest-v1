import { useState, useRef, useEffect } from "react"
import { ArrowUpDown, Download, ChevronDown, Check } from "lucide-react"

type SortOption = "relevance" | "year_desc" | "year_asc" | "citations"

interface SearchResultsHeaderProps {
  total: number
  currentPage: number
  itemsPerPage: number
  sortBy: SortOption
  onSortChange: (sort: SortOption) => void
  onExport: (format: "json" | "csv" | "bibtex") => void
  loading?: boolean
}

const SORT_LABELS: Record<SortOption, string> = {
  relevance: "Relevance",
  year_desc: "Newest",
  year_asc: "Oldest",
  citations: "Most Cited",
}

function formatTotal(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (n >= 1_000) return (n / 1_000).toFixed(0) + "k"
  return n.toLocaleString()
}

export function SearchResultsHeader({
  total,
  currentPage,
  itemsPerPage,
  sortBy,
  onSortChange,
  onExport,
  loading = false,
}: SearchResultsHeaderProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, total)

  const [sortOpen, setSortOpen] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const sortRef = useRef<HTMLDivElement>(null)
  const exportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (sortRef.current && !sortRef.current.contains(e.target as Node)) setSortOpen(false)
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) setExportOpen(false)
    }
    document.addEventListener("mousedown", h)
    return () => document.removeEventListener("mousedown", h)
  }, [])

  if (total === 0) return null

  // Pill control: rounded-full with icon + label
  const pillBtn =
    "flex h-9 items-center gap-1.5 rounded-full border border-border bg-card px-3.5 text-[12px] font-medium text-foreground shadow-sm transition-colors hover:border-primary/40 hover:text-primary disabled:opacity-50"

  return (
    <div className="mb-5">
      <div className="flex items-center justify-between gap-2 mb-3">
        {/* Count */}
        <div>
          <div className="font-display text-2xl font-semibold tracking-tight text-foreground sm:text-[28px]">
            {formatTotal(total)}
            <span className="ml-1.5 font-sans text-sm font-normal text-muted-foreground sm:text-base">
              {total === 1 ? "article" : "articles"}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground sm:text-xs">
            {startItem.toLocaleString()}–{endItem.toLocaleString()} of {total.toLocaleString()}
          </p>
        </div>

        {/* Sort + Export */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Sort dropdown */}
          <div ref={sortRef} className="relative">
            <button
              onClick={() => { setSortOpen(v => !v); setExportOpen(false) }}
              disabled={loading}
              className={pillBtn}
            >
              <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
              <span className="hidden xs:inline sm:inline">{SORT_LABELS[sortBy]}</span>
              {sortBy === "relevance" && (
                <span className="rounded bg-primary/12 px-1 text-[9px] font-bold text-primary">AI</span>
              )}
              <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${sortOpen ? "rotate-180" : ""}`} />
            </button>
            {sortOpen && (
              <div className="absolute right-0 top-full z-50 mt-1.5 w-44 rounded-xl border border-border bg-card py-1 shadow-elevated">
                {(["relevance", "year_desc", "year_asc", "citations"] as SortOption[]).map(opt => (
                  <button
                    key={opt}
                    onClick={() => { onSortChange(opt); setSortOpen(false) }}
                    className={`flex w-full items-center gap-2 px-3 py-2 text-[13px] transition-colors hover:bg-accent ${sortBy === opt ? "font-semibold text-primary" : "text-muted-foreground"}`}
                  >
                    {sortBy === opt && <Check className="h-3.5 w-3.5 shrink-0" />}
                    <span className={sortBy === opt ? "" : "pl-5"}>
                      {SORT_LABELS[opt]}
                      {opt === "relevance" && <span className="ml-1 text-[9px] font-bold text-primary">AI</span>}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Export dropdown */}
          <div ref={exportRef} className="relative">
            <button
              onClick={() => { setExportOpen(v => !v); setSortOpen(false) }}
              disabled={loading}
              className={pillBtn}
            >
              <Download className="h-3 w-3 text-muted-foreground" />
              <span className="hidden xs:inline sm:inline">Export</span>
              <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${exportOpen ? "rotate-180" : ""}`} />
            </button>
            {exportOpen && (
              <div className="absolute right-0 top-full z-50 mt-1.5 w-36 rounded-xl border border-border bg-card py-1 shadow-elevated">
                {[
                  { key: "json" as const, label: "JSON" },
                  { key: "csv" as const, label: "CSV" },
                  { key: "bibtex" as const, label: "BibTeX" },
                ].map(fmt => (
                  <button
                    key={fmt.key}
                    onClick={() => { onExport(fmt.key); setExportOpen(false) }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                  >
                    {fmt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI badge — single line */}
      {sortBy === "relevance" && (
        <div className="flex items-center gap-2 mb-3">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft/40 px-2.5 py-0.5 text-[11px] font-semibold text-primary border border-primary/20">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary" />
            </span>
            AI Semantic Ranking
          </div>
        </div>
      )}
    </div>
  )
}
