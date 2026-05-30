import { useState, useEffect } from "react"
import { Bell, Plus, Trash2, Pause, Play, Zap } from "lucide-react"
import { createAlert, listAlerts, toggleAlert, deleteAlert, type AlertOut } from "@/services/alerts"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<AlertOut[]>([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState("")
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    setLoading(true)
    try {
      const data = await listAlerts()
      setAlerts(data.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load alerts")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const handleCreate = async () => {
    if (!query.trim()) return
    try {
      await createAlert({ query: query.trim(), frequency: "daily" })
      setQuery("")
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create alert")
    }
  }

  const handleToggle = async (id: number) => {
    try {
      await toggleAlert(id)
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Toggle failed")
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteAlert(id)
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed")
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-serif text-xl font-bold tracking-tight">Search Alerts</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Get notified when new papers matching your keywords are published.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <span className="font-medium">Error.</span>{" "}
          {error}
        </div>
      )}

      <div className="flex max-w-lg gap-2">
        <Input
          type="text"
          placeholder="Enter keywords to monitor..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={!query.trim()}>
          <Plus className="mr-1.5 h-4 w-4" />
          Create Alert
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Zap className="h-4 w-4 animate-pulse" />
          Loading alerts...
        </div>
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-12 text-center">
          <Bell className="h-10 w-10 text-muted-foreground/20" />
          <div>
            <p className="text-lg font-semibold">No alerts yet</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Add keywords to monitor and get notified when new papers appear.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-2">
          {alerts.map((alert) => (
            <Card key={alert.id} className="border-border/60">
              <CardContent className="flex items-start justify-between gap-3 p-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{alert.query}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="capitalize">{alert.frequency}</span>
                    <span>·</span>
                    <Badge variant={alert.is_active ? "default" : "secondary"} className="text-[10px] px-1.5 py-0">
                      {alert.is_active ? "Active" : "Paused"}
                    </Badge>
                    {alert.last_run_at && (
                      <>
                        <span>·</span>
                        <span>Last run {new Date(alert.last_run_at).toLocaleDateString()}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleToggle(alert.id)}
                    title={alert.is_active ? "Pause" : "Resume"}
                  >
                    {alert.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={() => handleDelete(alert.id)}
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
