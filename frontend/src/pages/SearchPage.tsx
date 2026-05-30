import { lazy, Suspense, useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, X, Check, ChevronDown } from "lucide-react";
import { PaperList } from "@/components/PaperList";
import { PaperDetail } from "@/components/PaperDetail";
import { Pagination } from "@/components/Pagination";
import { SearchResultsHeader } from "@/components/SearchResultsHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { searchPapers } from "@/services/api";
import { exportPapers, downloadBlob } from "@/services/export";
import type { PaperDTO, SearchFilters, SearchRequest } from "@/types/paper";

const TrendsChart = lazy(() =>
  import("@/components/TrendsChart").then((m) => ({ default: m.TrendsChart }))
);

type SortOption = "relevance" | "year_desc" | "year_asc" | "citations";

const ALL_SOURCES = [
  "arxiv", "core", "crossref", "doaj",
  "europepmc", "openalex", "pubmed", "semantic_scholar",
];

const DEFAULT_FILTERS: SearchFilters = {
  year_from: null, year_to: null,
  sources: ALL_SOURCES,
  open_access: null, min_citations: null,
  venue_contains: null, topic: null, institution: null, type: null,
};

const MAX_PAGES = 200;

function sortPapers(papers: PaperDTO[], sort: SortOption): PaperDTO[] {
  const s = [...papers];
  if (sort === "year_desc") return s.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
  if (sort === "year_asc") return s.sort((a, b) => (a.year ?? 0) - (b.year ?? 0));
  if (sort === "citations") return s.sort((a, b) => (b.citation_count ?? 0) - (a.citation_count ?? 0));
  return s;
}

function countActiveFilters(f: SearchFilters): number {
  return [
    f.year_from != null, f.year_to != null,
    f.open_access != null, f.min_citations != null,
    !!f.venue_contains,
    f.sources != null && f.sources.length < ALL_SOURCES.length,
  ].filter(Boolean).length;
}

// Generic dropdown used in the search toolbar
function FilterDropdown({
  label, active, children,
}: {
  label: React.ReactNode;
  active?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`flex shrink-0 items-center gap-1 text-[13px] font-medium transition-colors ${
          active
            ? "text-primary"
            : "text-foreground/70 hover:text-foreground"
        }`}
      >
        {label}
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-50 mt-2 min-w-[220px] rounded-xl border border-border bg-white py-2 shadow-xl">
          {children}
        </div>
      )}
    </div>
  );
}

// Active filter chips row
function ActiveFilterChips({
  filters, onChange, onApply,
}: {
  filters: SearchFilters;
  onChange: (f: SearchFilters) => void;
  onApply: () => void;
}) {  const chips: { label: string; onRemove: () => void }[] = [];
  if (filters.year_from != null || filters.year_to != null)
    chips.push({ label: `${filters.year_from ?? "…"}–${filters.year_to ?? "…"}`, onRemove: () => { onChange({ ...filters, year_from: null, year_to: null }); onApply(); } });
  if (filters.open_access === true)
    chips.push({ label: "Open Access", onRemove: () => { onChange({ ...filters, open_access: null }); onApply(); } });
  if (filters.min_citations != null)
    chips.push({ label: `≥${filters.min_citations} cited`, onRemove: () => { onChange({ ...filters, min_citations: null }); onApply(); } });
  if (filters.venue_contains)
    chips.push({ label: filters.venue_contains, onRemove: () => { onChange({ ...filters, venue_contains: null }); onApply(); } });
  if (filters.sources && filters.sources.length < ALL_SOURCES.length)
    chips.push({ label: `${filters.sources.length} sources`, onRemove: () => { onChange({ ...filters, sources: ALL_SOURCES }); onApply(); } });

  if (chips.length === 0) return null;
  return (
    <>
      {chips.map((chip, i) => (
        <Badge key={i} variant="oa" className="flex items-center gap-1 pr-1 text-[12px] font-medium h-6 shrink-0">
          {chip.label}
          <button onClick={chip.onRemove} className="ml-0.5 rounded-full p-0.5 hover:bg-primary/15">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
    </>
  );
}

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const searchBarRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const [pendingFilters, setPendingFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const [results, setResults] = useState<PaperDTO[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState<PaperDTO | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>("relevance");
  const [page, setPage] = useState(1);
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  const doSearch = useCallback(async (q: string, f: SearchFilters, pg = 1) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    setPage(pg);
    if (pg === 1) setSearchParams({ q });
    window.scrollTo({ top: 0, behavior: "smooth" });
    try {
      const res = await searchPapers({ query: q.trim(), filters: f, limit: 25, offset: (pg - 1) * 25 } as SearchRequest);
      setResults(res.results);
      setTotal(res.total);
      res.warnings?.forEach((w) => toast({ title: "Source Warning", description: w, variant: "destructive" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, [setSearchParams, toast]);

  const handleSearch = useCallback((sq?: string) => {
    const q = (sq ?? query).trim();
    setFilters(pendingFilters);
    doSearch(q, pendingFilters, 1);
  }, [query, pendingFilters, doSearch]);

  const handlePageChange = useCallback((p: number) => {
    if (!query.trim() || loading) return;
    doSearch(query, filters, p);
  }, [query, filters, loading, doSearch]);

  const applyFilters = useCallback((f: SearchFilters) => {
    setPendingFilters(f);
    setFilters(f);
    doSearch(query, f, 1);
  }, [query, doSearch]);

  const handleExport = async (papers: PaperDTO[], format: "json" | "csv" | "bibtex") => {
    try {
      const blob = await exportPapers(papers, format);
      const ext = format === "bibtex" ? "bib" : format;
      downloadBlob(blob, `papers.${ext}`);
      toast({ title: `Exported ${papers.length} papers (.${ext})` });
    } catch (err) {
      toast({ title: "Export failed", description: err instanceof Error ? err.message : "Export failed", variant: "destructive" });
    }
  };

  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !searched) { setQuery(q); doSearch(q, DEFAULT_FILTERS, 1); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (selectedPaper) setSelectedPaper(null);
        else if (mobileFilterOpen) setMobileFilterOpen(false);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [selectedPaper, mobileFilterOpen]);

  const activeFilterCount = countActiveFilters(filters);
  const totalPages = Math.min(Math.ceil(total / 25), MAX_PAGES);
  const srcCounts: Record<string, number> = {};
  results.forEach((p) => p.sources.forEach((s) => { srcCounts[s] = (srcCounts[s] ?? 0) + 1; }));
  const oaCount = results.filter((p) => p.is_open_access).length;
  const oaPct = results.length > 0 ? Math.round((oaCount / results.length) * 100) : 0;

  return (
    <div className="flex min-h-screen flex-col bg-background">

      {/* STICKY HEADER */}
      <header className="sticky top-0 z-30 border-b border-border/40 bg-card/95 backdrop-blur-md shadow-sm">
        <div className="mx-auto max-w-[1400px] px-4 sm:px-6">
          <div className="py-3">

            {/* ── MOBILE: single-row search bar ── */}
            <div className="flex items-center gap-2 sm:hidden">
              <div className="flex-1 flex items-center rounded-xl border border-border bg-card shadow-card overflow-hidden focus-within:border-primary/40 focus-within:shadow-elevated transition-all">
                <Search className="ml-3 h-4 w-4 shrink-0 text-muted-foreground/60 pointer-events-none" />
                <input
                  ref={searchBarRef}
                  type="text"
                  placeholder="Search papers…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
                  className="h-11 flex-1 bg-transparent px-2 text-[15px] text-foreground placeholder:text-muted-foreground/50 outline-none"
                />
                {query && (
                  <button
                    onClick={() => { setQuery(""); searchBarRef.current?.focus(); }}
                    className="mr-2 text-muted-foreground/50 hover:text-foreground transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {/* Search button — pill primary, icon only on mobile */}
              <button
                onClick={() => handleSearch()}
                disabled={loading || !query.trim()}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-pill bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                aria-label="Search"
              >
                {loading
                  ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  : <Search className="h-4 w-4" />
                }
              </button>

              {/* Filters button — icon + count badge */}
              <button
                onClick={() => setMobileFilterOpen(true)}
                className={`relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border shadow-card transition-colors ${
                  activeFilterCount > 0
                    ? "border-primary/30 bg-primary-soft/30 text-primary"
                    : "border-border bg-card text-foreground/60 hover:text-foreground"
                }`}
                aria-label="Filters"
              >
                <svg className="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M2 4h12M4 8h8M6 12h4" />
                </svg>
                {activeFilterCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-primary-foreground">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>

            {/* ── DESKTOP: two-row search bar ── */}
            <div className="hidden sm:block rounded-2xl border border-border bg-card shadow-card transition-all focus-within:shadow-elevated focus-within:border-primary/40">
              {/* Row 1: input */}
              <div className="relative flex items-center">
                <Search className="absolute left-4 h-4 w-4 text-muted-foreground/60 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search 480M scholarly works…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
                  className="h-12 w-full bg-transparent pl-11 pr-10 text-[15px] text-foreground placeholder:text-muted-foreground/50 outline-none rounded-t-2xl"
                />
                {query && (
                  <button
                    onClick={() => { setQuery(""); }}
                    className="absolute right-3 text-muted-foreground/50 hover:text-foreground transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {/* Row 2: filter dropdowns toolbar */}
              <div className="flex items-center gap-4 border-t border-border/50 px-4 py-2 text-[13px] text-muted-foreground overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">

                {/* Year dropdown */}
                <FilterDropdown
                  label={<span>{filters.year_from || filters.year_to ? `${filters.year_from ?? "…"}–${filters.year_to ?? "…"}` : "Year"}</span>}
                  active={filters.year_from != null || filters.year_to != null}
                >
                  <div className="px-3 py-2">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Year Range</p>
                    <div className="flex items-center gap-2">
                      <input
                        type="number" placeholder="From"
                        value={pendingFilters.year_from ?? ""}
                        onChange={(e) => setPendingFilters((f) => ({ ...f, year_from: e.target.value ? +e.target.value : null }))}
                        className="h-8 w-full rounded-md border border-border px-2 text-xs outline-none focus:border-primary"
                      />
                      <span className="text-muted-foreground shrink-0">–</span>
                      <input
                        type="number" placeholder="To"
                        value={pendingFilters.year_to ?? ""}
                        onChange={(e) => setPendingFilters((f) => ({ ...f, year_to: e.target.value ? +e.target.value : null }))}
                        className="h-8 w-full rounded-md border border-border px-2 text-xs outline-none focus:border-primary"
                      />
                    </div>
                    <div className="mt-2 flex gap-2">
                      <button onClick={() => applyFilters(pendingFilters)} className="flex-1 rounded-md bg-foreground py-1.5 text-[12px] font-medium text-background hover:bg-foreground/80 transition-colors">Apply</button>
                      <button onClick={() => applyFilters({ ...pendingFilters, year_from: null, year_to: null })} className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground transition-colors">Clear</button>
                    </div>
                  </div>
                </FilterDropdown>

                {/* Open Access dropdown */}
                <FilterDropdown
                  label={<span>{filters.open_access === true ? "Open Access ✓" : "Open Access"}</span>}
                  active={filters.open_access === true}
                >
                  <div className="px-3 py-2">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Access Type</p>
                    {[
                      { val: null, label: "All papers" },
                      { val: true, label: `Open Access only${results.length > 0 ? ` (${oaPct}%)` : ""}` },
                    ].map((opt) => (
                      <button
                        key={String(opt.val)}
                        onClick={() => applyFilters({ ...pendingFilters, open_access: opt.val as boolean | null })}
                        className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-[13px] transition-colors hover:bg-accent ${filters.open_access === opt.val ? "font-semibold text-foreground" : "text-muted-foreground"}`}
                      >
                        {filters.open_access === opt.val && <Check className="h-3.5 w-3.5 shrink-0" />}
                        <span className={filters.open_access === opt.val ? "" : "pl-5"}>{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </FilterDropdown>

                {/* Citations dropdown */}
                <FilterDropdown
                  label={<span>{filters.min_citations != null ? `≥${filters.min_citations} cited` : "Citations"}</span>}
                  active={filters.min_citations != null}
                >
                  <div className="px-3 py-2">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Min Citations</p>
                    {[0, 10, 50, 100, 500].map((n) => (
                      <button
                        key={n}
                        onClick={() => applyFilters({ ...pendingFilters, min_citations: n === 0 ? null : n })}
                        className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] transition-colors hover:bg-accent ${(n === 0 ? filters.min_citations == null : filters.min_citations === n) ? "font-semibold text-foreground" : "text-muted-foreground"}`}
                      >
                        {(n === 0 ? filters.min_citations == null : filters.min_citations === n) && <Check className="h-3.5 w-3.5 shrink-0" />}
                        <span className={(n === 0 ? filters.min_citations == null : filters.min_citations === n) ? "" : "pl-5"}>
                          {n === 0 ? "Any" : `≥ ${n}`}
                        </span>
                      </button>
                    ))}
                    <div className="mt-2 border-t border-border pt-2">
                      <input
                        type="number" placeholder="Custom…"
                        value={pendingFilters.min_citations ?? ""}
                        onChange={(e) => setPendingFilters((f) => ({ ...f, min_citations: e.target.value ? +e.target.value : null }))}
                        className="h-8 w-full rounded-md border border-border px-2 text-xs outline-none focus:border-primary"
                      />
                      <button onClick={() => applyFilters(pendingFilters)} className="mt-1.5 w-full rounded-md bg-foreground py-1.5 text-[12px] font-medium text-background hover:bg-foreground/80 transition-colors">Apply</button>
                    </div>
                  </div>
                </FilterDropdown>

                {/* Sources dropdown */}
                <FilterDropdown
                  label={<span>{filters.sources && filters.sources.length < ALL_SOURCES.length ? `${filters.sources.length} sources` : "Sources"}</span>}
                  active={filters.sources != null && filters.sources.length < ALL_SOURCES.length}
                >
                  <div className="px-3 py-2">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Data Sources</p>
                    {ALL_SOURCES.map((src) => {
                      const active = (pendingFilters.sources ?? ALL_SOURCES).includes(src);
                      const count = srcCounts[src];
                      return (
                        <button
                          key={src}
                          onClick={() => {
                            const cur = pendingFilters.sources ?? ALL_SOURCES;
                            const next = cur.includes(src) ? cur.filter((s) => s !== src) : [...cur, src];
                            setPendingFilters((f) => ({ ...f, sources: next.length === 0 ? ALL_SOURCES : next }));
                          }}
                          className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-foreground/80 hover:bg-accent transition-colors"
                        >
                          <div className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${active ? "border-foreground bg-foreground text-background" : "border-input bg-background"}`}>
                            {active && <Check className="h-3 w-3" />}
                          </div>
                          <span className="flex-1 text-left capitalize">{src.replace("_", " ")}</span>
                          {count != null && <span className="text-[11px] text-muted-foreground">{count}</span>}
                        </button>
                      );
                    })}
                    <div className="mt-2 border-t border-border pt-2">
                      <button onClick={() => applyFilters(pendingFilters)} className="w-full rounded-md bg-foreground py-1.5 text-[12px] font-medium text-background hover:bg-foreground/80 transition-colors">Apply</button>
                    </div>
                  </div>
                </FilterDropdown>

                <div className="flex-1" />

                {/* Active chips — hidden on mobile to save space */}
                <div className="hidden sm:flex items-center gap-1.5 overflow-x-auto">
                  <ActiveFilterChips filters={filters} onChange={setPendingFilters} onApply={() => applyFilters(pendingFilters)} />
                </div>

                {/* Search button — pill primer */}
                <button
                  onClick={() => handleSearch()}
                  disabled={loading || !query.trim()}
                  className="flex h-8 shrink-0 items-center gap-1.5 rounded-pill bg-primary px-4 text-[12px] font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground/40 border-t-primary-foreground" />
                  ) : (
                    <>
                      <Search className="h-3.5 w-3.5" />
                      Search
                    </>
                  )}
                </button>
              </div>
            </div>{/* end desktop two-row box */}
          </div>
        </div>
      </header>

      {/* MOBILE FILTER BOTTOM SHEET */}
      {mobileFilterOpen && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end sm:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileFilterOpen(false)} />
          <div className="relative rounded-t-2xl bg-white shadow-2xl max-h-[85vh] flex flex-col">
            {/* Handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="h-1 w-10 rounded-full bg-border" />
            </div>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-border">
              <p className="font-semibold text-foreground">Filters</p>
              <div className="flex items-center gap-3">
                {activeFilterCount > 0 && (
                  <button
                    onClick={() => applyFilters(DEFAULT_FILTERS)}
                    className="text-[13px] text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Clear all
                  </button>
                )}
                <button onClick={() => setMobileFilterOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            {/* Content */}
            <div className="overflow-y-auto px-5 py-4 space-y-5">
              {/* Year */}
              <div>
                <p className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">Year</p>
                <div className="flex items-center gap-2">
                  <input type="number" placeholder="From"
                    value={pendingFilters.year_from ?? ""}
                    onChange={(e) => setPendingFilters((f) => ({ ...f, year_from: e.target.value ? +e.target.value : null }))}
                    className="h-10 w-full rounded-xl border border-border px-3 text-[14px] outline-none focus:border-primary"
                  />
                  <span className="text-muted-foreground shrink-0">–</span>
                  <input type="number" placeholder="To"
                    value={pendingFilters.year_to ?? ""}
                    onChange={(e) => setPendingFilters((f) => ({ ...f, year_to: e.target.value ? +e.target.value : null }))}
                    className="h-10 w-full rounded-xl border border-border px-3 text-[14px] outline-none focus:border-primary"
                  />
                </div>
              </div>
              {/* Open Access */}
              <div>
                <p className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">Access</p>
                <div className="flex gap-2">
                  {[
                    { val: null, label: "All" },
                    { val: true, label: `Open Access${results.length > 0 ? ` (${oaPct}%)` : ""}` },
                  ].map((opt) => (
                    <button
                      key={String(opt.val)}
                      onClick={() => setPendingFilters((f) => ({ ...f, open_access: opt.val as boolean | null }))}
                      className={`flex-1 rounded-xl border py-2.5 text-[13px] font-medium transition-colors ${
                        pendingFilters.open_access === opt.val
                          ? "border-primary bg-primary/5 text-primary"
                          : "border-border text-muted-foreground hover:border-foreground/20"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              {/* Citations */}
              <div>
                <p className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">Min Citations</p>
                <div className="grid grid-cols-3 gap-2">
                  {[0, 10, 50, 100, 500].map((n) => (
                    <button
                      key={n}
                      onClick={() => setPendingFilters((f) => ({ ...f, min_citations: n === 0 ? null : n }))}
                      className={`rounded-xl border py-2.5 text-[13px] font-medium transition-colors ${
                        (n === 0 ? pendingFilters.min_citations == null : pendingFilters.min_citations === n)
                          ? "border-primary bg-primary/5 text-primary"
                          : "border-border text-muted-foreground hover:border-foreground/20"
                      }`}
                    >
                      {n === 0 ? "Any" : `≥${n}`}
                    </button>
                  ))}
                </div>
              </div>
              {/* Sources */}
              <div>
                <p className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">Sources</p>
                <div className="grid grid-cols-2 gap-2">
                  {ALL_SOURCES.map((src) => {
                    const active = (pendingFilters.sources ?? ALL_SOURCES).includes(src);
                    return (
                      <button
                        key={src}
                        onClick={() => {
                          const cur = pendingFilters.sources ?? ALL_SOURCES;
                          const next = cur.includes(src) ? cur.filter((s) => s !== src) : [...cur, src];
                          setPendingFilters((f) => ({ ...f, sources: next.length === 0 ? ALL_SOURCES : next }));
                        }}
                        className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 text-[13px] transition-colors ${
                          active
                            ? "border-primary bg-primary/5 text-primary"
                            : "border-border text-muted-foreground hover:border-foreground/20"
                        }`}
                      >
                        <div className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${active ? "border-primary bg-primary text-primary-foreground" : "border-input"}`}>
                          {active && <Check className="h-3 w-3" />}
                        </div>
                        <span className="capitalize truncate">{src.replace("_", " ")}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
            {/* Apply button */}
            <div className="px-5 py-4 border-t border-border">
              <button
                onClick={() => { applyFilters(pendingFilters); setMobileFilterOpen(false); }}
                className="w-full rounded-xl bg-foreground py-3.5 text-[15px] font-semibold text-background hover:bg-foreground/80 transition-colors"
              >
                Apply Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="mx-auto w-full max-w-[1400px] px-4 pb-20 pt-6 sm:px-6">
        {error && (
          <div className="mb-4 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <span className="font-medium">Error.</span> {error}
          </div>
        )}

        <div className="min-w-0">
          {!loading && results.length > 0 && (
            <SearchResultsHeader
              total={total} currentPage={page} itemsPerPage={25}
              sortBy={sortBy} onSortChange={setSortBy}
              onExport={(fmt) => handleExport(results, fmt)} loading={loading}
            />
          )}

          {!loading && results.length > 0 && (
            <Suspense fallback={<div className="h-32 animate-pulse bg-muted rounded-xl mb-4" />}>
              <TrendsChart papers={results} />
            </Suspense>
          )}

          <PaperList papers={sortPapers(results, sortBy)} onSelect={setSelectedPaper} loading={loading} searched={searched} />

          {!loading && total > 25 && results.length > 0 && (
            <>
              <Pagination currentPage={page} totalPages={totalPages} totalItems={total} itemsPerPage={25} onPageChange={handlePageChange} loading={loading} />
              {Math.ceil(total / 25) > MAX_PAGES && (
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  Showing top {(MAX_PAGES * 25).toLocaleString()} of {total.toLocaleString()} results. Use filters to narrow down.
                </p>
              )}
            </>
          )}

          {!loading && !error && results.length === 0 && searched && (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <Search className="h-10 w-10 text-muted-foreground/20" />
              <p className="text-lg font-semibold">No results found</p>
              <p className="text-sm text-muted-foreground">Try a different keyword or clear your filters.</p>
              {activeFilterCount > 0 && (
                <Button variant="outline" size="sm" onClick={() => applyFilters(DEFAULT_FILTERS)}>Clear filters</Button>
              )}
            </div>
          )}

          {!searched && !loading && (
            <div className="flex flex-col items-center gap-3 py-24 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/5 border border-primary/10">
                <Search className="h-8 w-8 text-primary/40" />
              </div>
              <div>
                <p className="text-xl font-semibold text-foreground">Search scholarly works</p>
                <p className="mt-1.5 text-sm text-muted-foreground">Search across 200M+ papers from 8 academic sources</p>
              </div>
              <div className="mt-3 flex flex-wrap justify-center gap-2">
                {["machine learning", "CRISPR", "climate change", "quantum computing"].map((q) => (
                  <button key={q} onClick={() => { setQuery(q); handleSearch(q); }}
                    className="rounded-full border border-border bg-white px-4 py-1.5 text-[13px] text-muted-foreground shadow-sm hover:border-primary/30 hover:text-primary hover:shadow-md transition-all">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedPaper && <PaperDetail paper={selectedPaper} onClose={() => setSelectedPaper(null)} />}
    </div>
  );
}
