import * as React from "react"
import { cn } from "@/lib/utils"

export type BadgeVariant =
  | "default"
  | "secondary"
  | "destructive"
  | "outline"
  | "q1"
  | "q2"
  | "q3"
  | "q4"
  | "oa"
  | "predatory"
  | "source"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant
  children?: React.ReactNode
}

const variantClasses: Record<BadgeVariant, string> = {
  default:
    "border-transparent bg-primary text-primary-foreground hover:bg-primary/90",
  secondary:
    "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
  destructive:
    "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
  outline: "border border-border text-foreground",
  // Journal quality
  q1: "border-transparent bg-q1 text-white",
  q2: "border-transparent bg-q2 text-white",
  q3: "border-transparent bg-q3 text-white",
  q4: "bg-transparent text-q4 border border-q4",
  // Open access — pakai blue rice background dengan teks primary
  oa: "border-transparent bg-primary-soft text-primary",
  // Predatory — warning halus
  predatory: "bg-red-50 text-red-700 border border-red-200",
  // Source chip — netral
  source:
    "border-transparent bg-accent text-muted-foreground",
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
