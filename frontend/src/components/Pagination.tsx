import { ChevronLeft, ChevronRight } from "lucide-react"

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  loading?: boolean
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  loading = false,
}: PaginationProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push("...")
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      for (let i = start; i <= end; i++) pages.push(i)
      if (currentPage < totalPages - 2) pages.push("...")
      pages.push(totalPages)
    }
    return pages
  }

  if (totalPages <= 1) return null

  const navBtn =
    "flex h-9 items-center gap-1 rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground shadow-sm hover:border-primary/40 hover:text-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"

  return (
    <div className="flex flex-col items-center gap-3 py-6">
      {/* Results info */}
      <p className="text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{startItem.toLocaleString()}</span>
        {" – "}
        <span className="font-medium text-foreground">{endItem.toLocaleString()}</span>
        {" of "}
        <span className="font-medium text-foreground">{totalItems.toLocaleString()}</span>
      </p>

      {/* Controls */}
      <div className="flex items-center gap-1.5">
        {/* Prev */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || loading}
          className={navBtn}
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Prev</span>
        </button>

        {/* Page numbers — desktop only */}
        <div className="hidden sm:flex items-center gap-1">
          {getPageNumbers().map((page, i) => {
            if (page === "...") return (
              <span key={`e-${i}`} className="px-2 text-sm text-muted-foreground">…</span>
            )
            const n = page as number
            const active = n === currentPage
            return (
              <button
                key={n}
                onClick={() => onPageChange(n)}
                disabled={loading || active}
                className={`flex h-9 w-9 items-center justify-center rounded-full text-[13px] font-medium transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground cursor-default shadow-sm"
                    : "text-foreground/70 hover:bg-accent hover:text-foreground"
                }`}
              >
                {n}
              </button>
            )
          })}
        </div>

        {/* Mobile: page indicator */}
        <div className="sm:hidden flex h-9 items-center rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground shadow-sm">
          {currentPage} / {totalPages}
        </div>

        {/* Next */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || loading}
          className={navBtn}
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
