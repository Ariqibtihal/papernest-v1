import { useState, useRef, useEffect } from "react"
import { Search, Clock } from "lucide-react"
import { getHistory, clearHistory, type HistoryEntry } from "@/services/history"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading: boolean
  compact?: boolean
  inputRef?: React.Ref<HTMLInputElement>
}

export function SearchBar({ value, onChange, onSubmit, loading, compact, inputRef }: SearchBarProps) {
  const [showRecent, setShowRecent] = useState(false)
  const [recentItems, setRecentItems] = useState<HistoryEntry[]>([])
  const wrapperRef = useRef<HTMLDivElement>(null)

  const openRecent = () => {
    const items = getHistory()
    setRecentItems(items)
    if (items.length > 0) setShowRecent(true)
  }

  const pickRecent = (q: string) => {
    onChange(q)
    setShowRecent(false)
    setTimeout(onSubmit, 50)
  }

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowRecent(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const recentDropdown = showRecent && recentItems.length > 0 && (
    <div className="absolute left-0 top-full z-50 mt-1 w-full rounded-md border border-border bg-popover py-1 shadow-lg">
      <div className="flex items-center justify-between px-3 py-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Pencarian Terakhir</span>
        <button
          onClick={(e) => { e.stopPropagation(); clearHistory(); setShowRecent(false); }}
          className="text-[10px] text-muted-foreground transition-colors hover:text-destructive"
        >
          Hapus
        </button>
      </div>
      {recentItems.slice(0, 5).map((item, i) => (
        <button
          key={i}
          onClick={() => pickRecent(item.query)}
          className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <Clock className="h-3 w-3 shrink-0 text-muted-foreground/50" />
          <span className="truncate">{item.query}</span>
        </button>
      ))}
    </div>
  )

  if (compact) {
    return (
      <div ref={wrapperRef} className="relative flex w-full items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef as React.Ref<HTMLInputElement>}
            type="text"
            placeholder="Cari tema, judul, topik, atau penulis... (Ctrl+K)"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={openRecent}
            onKeyDown={(e) => { if (e.key === "Enter") { setShowRecent(false); onSubmit(); } }}
            className="h-9 pl-9 text-sm"
          />
          {recentDropdown}
        </div>
        <Button
          size="sm"
          onClick={() => { setShowRecent(false); onSubmit(); }}
          disabled={loading || !value.trim()}
        >
          {loading ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
          ) : (
            <Search className="h-3.5 w-3.5" />
          )}
          {loading ? "Mencari..." : "Cari"}
        </Button>
      </div>
    )
  }

  return (
    <div ref={wrapperRef} className="relative flex w-full items-center gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground z-10" />
        <Input
          ref={inputRef as React.Ref<HTMLInputElement>}
          type="text"
          placeholder="Cari tema, judul, topik, atau penulis..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={openRecent}
          onKeyDown={(e) => { if (e.key === "Enter") { setShowRecent(false); onSubmit(); } }}
          className="h-11 pl-11 text-sm"
        />
        {recentDropdown}
      </div>
      <Button
        onClick={() => { setShowRecent(false); onSubmit(); }}
        disabled={loading || !value.trim()}
      >
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
            Mencari...
          </span>
        ) : (
          "Cari"
        )}
      </Button>
    </div>
  )
}
