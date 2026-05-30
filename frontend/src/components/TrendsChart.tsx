import { useMemo, useState } from "react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChevronDown } from "lucide-react"
import type { PaperDTO } from "@/types/paper"

interface TrendsChartProps {
  papers: PaperDTO[]
}

export function TrendsChart({ papers }: TrendsChartProps) {
  const [open, setOpen] = useState(false)

  const chartData = useMemo(() => {
    if (!papers.length) return []
    const yearCounts: Record<number, number> = {}
    papers.forEach(p => { if (p.year) yearCounts[p.year] = (yearCounts[p.year] || 0) + 1 })
    const sortedYears = Object.keys(yearCounts).map(Number).sort((a, b) => a - b)
    if (!sortedYears.length) return []
    const data = []
    for (let y = sortedYears[0]; y <= sortedYears[sortedYears.length - 1]; y++) {
      data.push({ year: y, count: yearCounts[y] || 0 })
    }
    return data
  }, [papers])

  if (!chartData.length) return null

  return (
    <div className="mb-4 rounded-2xl border border-border/40 bg-card shadow-card overflow-hidden">
      {/* Header — always visible, tap to expand on mobile */}
      <button
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center justify-between px-5 py-3.5 text-left sm:cursor-default"
      >
        <span className="font-display text-[15px] font-semibold tracking-tight text-foreground">
          Publication Trends
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground hidden sm:inline">
            Loaded Results
          </span>
          {/* Chevron only on mobile */}
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform sm:hidden ${open ? "rotate-180" : ""}`} />
        </div>
      </button>

      {/* Chart — always visible on sm+, toggle on mobile */}
      <div className={`px-5 pb-5 ${open ? "block" : "hidden sm:block"}`}>
        <div className="h-[100px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.32} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="year" fontSize={10} tickLine={false} axisLine={false}
                tick={{ fill: "hsl(var(--muted-foreground))" }} minTickGap={30} />
              <YAxis hide />
              <Tooltip
                contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "hsl(var(--border))", borderRadius: "10px", fontSize: "12px" }}
                itemStyle={{ color: "hsl(var(--primary))" }}
                labelStyle={{ fontWeight: "bold", marginBottom: "4px" }}
              />
              <Area type="monotone" dataKey="count" stroke="hsl(var(--primary))"
                fillOpacity={1} fill="url(#colorCount)" strokeWidth={2.2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
