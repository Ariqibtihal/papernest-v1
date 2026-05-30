import { useState, useEffect, useCallback, createContext, useContext } from "react"
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react"

type ToastType = "success" | "error" | "info"

interface ToastItem {
  id: number
  message: string
  type: ToastType
}

interface ToastContextType {
  toast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

let nextId = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const toast = useCallback((message: string, type: ToastType = "success") => {
    const id = nextId++
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((t) => (
          <ToastItem key={t.id} item={t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ item, onDismiss }: { item: ToastItem; onDismiss: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(item.id), 3500)
    return () => clearTimeout(timer)
  }, [item.id, onDismiss])

  const Icon = item.type === "success" ? CheckCircle2 : item.type === "error" ? AlertCircle : Info
  const colors =
    item.type === "success"
      ? "border-[#14532D]/20 bg-[#14532D]/5 text-[#14532D]"
      : item.type === "error"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-[#DDE7DF] bg-white text-[#1F2933]"

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border px-4 py-3 text-sm shadow-lg animate-in slide-in-from-right-5 ${colors}`}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="font-medium">{item.message}</span>
      <button onClick={() => onDismiss(item.id)} className="ml-2 shrink-0 opacity-50 hover:opacity-100">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
