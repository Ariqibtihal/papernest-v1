import { RotateCcw } from "lucide-react"
import type { SearchFilters } from "@/types/paper"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

interface FilterPanelProps {
  filters: SearchFilters
  onChange: (filters: SearchFilters) => void
  availableSources: string[]
}

export function FilterPanel({ filters, onChange, availableSources }: FilterPanelProps) {
  const toggleSource = (source: string) => {
    const current = filters.sources || []
    const next = current.includes(source)
      ? current.filter((s) => s !== source)
      : [...current, source]
    onChange({ ...filters, sources: next.length ? next : null })
  }

  const hasActiveFilters =
    filters.year_from != null ||
    filters.year_to != null ||
    filters.min_citations != null ||
    filters.open_access != null ||
    filters.venue_contains != null

  const activeCount = [
    filters.year_from,
    filters.year_to,
    filters.min_citations,
    filters.open_access,
    filters.venue_contains,
  ].filter(Boolean).length

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">Filter</CardTitle>
          {activeCount > 0 && (
            <Badge variant="secondary" className="text-[10px]">{activeCount} aktif</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-[11px] w-full justify-start"
            onClick={() =>
              onChange({
                year_from: null,
                year_to: null,
                sources: [...availableSources],
                open_access: null,
                min_citations: null,
                venue_contains: null,
              })
            }
          >
            <RotateCcw className="mr-1 h-3 w-3" />
            Reset filter
          </Button>
        )}

        <div className="space-y-2">
          <Label className="text-[11px] text-muted-foreground">Sumber</Label>
          <div className="flex flex-col gap-1">
            {availableSources.map((source) => {
              const active = filters.sources?.includes(source)
              return (
                <button
                  key={source}
                  onClick={() => toggleSource(source)}
                  className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition-colors text-left ${
                    active
                      ? "bg-primary/5 text-foreground hover:bg-primary/10"
                      : "text-muted-foreground hover:bg-accent"
                  }`}
                >
                  <div className={`h-3.5 w-3.5 rounded-sm border flex items-center justify-center ${
                    active ? "bg-primary border-primary" : "border-border"
                  }`}>
                    {active && (
                      <svg className="h-2.5 w-2.5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className="capitalize">{source}</span>
                </button>
              )
            })}
          </div>
        </div>

        <Separator />

        <div className="space-y-2">
          <Label className="text-[11px] text-muted-foreground">Rentang Tahun</Label>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              className="h-8 text-sm"
              value={filters.year_from ?? ""}
              onChange={(e) => onChange({ ...filters, year_from: e.target.value ? Number(e.target.value) : null })}
              placeholder="2000"
            />
            <span className="text-muted-foreground text-xs">—</span>
            <Input
              type="number"
              className="h-8 text-sm"
              value={filters.year_to ?? ""}
              onChange={(e) => onChange({ ...filters, year_to: e.target.value ? Number(e.target.value) : null })}
              placeholder="2026"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-[11px] text-muted-foreground">Akses</Label>
          <Select
            value={filters.open_access === true ? "true" : filters.open_access === false ? "false" : "any"}
            onValueChange={(val: string) =>
              onChange({ ...filters, open_access: val === "true" ? true : val === "false" ? false : null })
            }
          >
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Semua</SelectItem>
              <SelectItem value="true">Open Access</SelectItem>
              <SelectItem value="false">Tidak Open Access</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-[11px] text-muted-foreground">Min. Sitasi</Label>
          <Input
            type="number"
            className="h-8 text-sm"
            value={filters.min_citations ?? ""}
            onChange={(e) => onChange({ ...filters, min_citations: e.target.value ? Number(e.target.value) : null })}
            placeholder="0"
          />
        </div>

        <div className="space-y-2">
          <Label className="text-[11px] text-muted-foreground">Venue</Label>
          <Input
            type="text"
            className="h-8 text-sm"
            value={filters.venue_contains ?? ""}
            onChange={(e) => onChange({ ...filters, venue_contains: e.target.value || null })}
            placeholder="Mengandung..."
          />
        </div>
      </CardContent>
    </Card>
  )
}
