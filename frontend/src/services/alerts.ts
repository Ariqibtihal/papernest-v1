export interface AlertCreate {
  query: string
  filters_json?: string | null
  email?: string | null
  frequency?: string
}

export interface AlertOut {
  id: number
  query: string
  filters_json: string | null
  email: string | null
  frequency: string
  is_active: boolean
  created_at: string
  last_run_at: string | null
}

export interface AlertList {
  total: number
  items: AlertOut[]
}

export async function createAlert(data: AlertCreate): Promise<AlertOut> {
  const res = await fetch("/api/v1/alerts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error("Failed to create alert")
  return res.json()
}

export async function listAlerts(): Promise<AlertList> {
  const res = await fetch("/api/v1/alerts")
  if (!res.ok) throw new Error("Failed to list alerts")
  return res.json()
}

export async function toggleAlert(id: number): Promise<AlertOut> {
  const res = await fetch(`/api/v1/alerts/${id}/toggle`, { method: "PATCH" })
  if (!res.ok) throw new Error("Failed to toggle alert")
  return res.json()
}

export async function deleteAlert(id: number): Promise<void> {
  const res = await fetch(`/api/v1/alerts/${id}`, { method: "DELETE" })
  if (!res.ok) throw new Error("Failed to delete alert")
}
