import { useState } from "react"
import {
  Sparkles,
  FileText,
  Hash,
  Tag,
  Quote,
  ChevronDown,
} from "lucide-react"

interface HeroSectionProps {
  /** Submit dari search bar di hero — diterima dari LandingPage onSearch. */
  onSearch?: (query: string) => void
}

/**
 * HeroSection
 * ──────────────────────────────────────────────────────────────
 * Komposisi (dari belakang ke depan):
 *   1. Background gradient biru
 *   2. Decorative blurred shapes + partikel putih
 *   3. Headline + subheadline
 *   4. PaperFan: 7 halaman jurnal akademik fan/arc layout
 *   5. ExtractSearchBar (z-20, focal point)
 *   6. MetadataChips (z-20, di bawah search bar)
 *
 * Tidak ada CTA tombol di hero — search bar adalah primary action.
 * Discovery menu (Use cases, Why, FAQ) ada di top nav.
 */
export function HeroSection({ onSearch }: HeroSectionProps) {
  return (
    <section
      aria-label="PaperNest hero"
      className="relative isolate flex min-h-[100svh] flex-col items-center justify-center overflow-hidden"
    >
      {/* Background gradient — deep blue → lighter at bottom */}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-20"
        style={{
          background:
            "linear-gradient(180deg, hsl(213 70% 30%) 0%, hsl(210 72% 46%) 40%, hsl(205 72% 70%) 100%)",
        }}
      />

      {/* White particle field — depth + atmosphere */}
      <ParticleField />

      {/* Decorative blurred paper shapes — pakai % + viewport units agar ikut zoom */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-[8vw] bottom-[18%] aspect-[3/4] w-[clamp(8rem,18vw,14rem)] rotate-12 rounded-2xl bg-white/15 blur-2xl" />
        <div className="absolute -right-[6vw] bottom-[12%] aspect-[3/4] w-[clamp(9rem,20vw,15rem)] -rotate-6 rounded-2xl bg-white/10 blur-2xl" />
        <div className="absolute left-[15%] top-[18%] aspect-[3/4] w-[clamp(5rem,10vw,8rem)] rotate-3 rounded-2xl bg-white/10 blur-3xl" />
        <div className="absolute right-[12%] top-[8%] aspect-[3/4] w-[clamp(4rem,8vw,6rem)] -rotate-12 rounded-2xl bg-white/10 blur-2xl" />
      </div>

      {/* Content stack — vertically centered di viewport */}
      <div
        className="relative mx-auto flex w-full flex-col items-center px-4 py-20 sm:px-6 sm:py-24 lg:px-8"
        style={{
          maxWidth: "min(70rem, 100%)", // 1120px equivalent, fluid
        }}
      >
        <h1
          className="font-display text-center font-semibold leading-[1.1] tracking-[-0.035em] text-white"
          style={{
            // Headline turun: 2rem (32px) di mobile sempit → 4rem (64px)
            // di desktop. Sebelumnya 40-88px terasa terlalu dominan.
            fontSize: "clamp(2rem, 5vw + 0.5rem, 4rem)",
          }}
        >
          Scrape papers,
          <br />
          not pages.
        </h1>

        <p
          className="mt-5 text-center text-white/85 leading-relaxed"
          style={{
            maxWidth: "38rem",
            fontSize: "clamp(0.9375rem, 0.4vw + 0.85rem, 1.0625rem)",
          }}
        >
          Extract clean insights from research papers, PDFs, and academic
          documents in seconds.
        </p>

        {/* Illustration block — paper fan + search bar + chips.
            Setelah CTA tombol dihilangkan, search bar adalah primary
            action — naikkan jarak dengan subtitle agar fokus visual jelas. */}
        <div
          className="relative mx-auto w-full"
          style={{ marginTop: "clamp(1.5rem, 3vw, 2.5rem)" }}
        >
          <HeroIllustration onSearch={onSearch} />
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Hero illustration container
 *
 * Tinggi paper-fan dan negative margin search bar memakai clamp() biar
 * proporsi tetap terjaga di semua zoom level dan viewport. Pakai rem +
 * vw — jangan px hardcode.
 * ───────────────────────────────────────────────────────────── */
function HeroIllustration({ onSearch }: { onSearch?: (q: string) => void }) {
  return (
    <div className="relative mx-auto w-full" style={{ maxWidth: "67.5rem" /* ~1080px */ }}>
      {/* Paper fan — purely decorative */}
      <div
        aria-hidden="true"
        className="relative w-full"
        style={{
          // Fluid height: ~14rem (224px) di mobile → ~22.5rem (360px) di desktop.
          // Tetap proporsional saat browser zoom karena rem-based.
          height: "clamp(14rem, 28vw + 6rem, 22.5rem)",
        }}
      >
        <PaperFan />
      </div>

      {/* Search bar — naik untuk overlap bawah paper. Negative margin fluid
          agar tidak pernah overlap konten utama atau gap di antaranya. */}
      <div
        className="relative z-20 px-2 sm:px-4"
        style={{ marginTop: "clamp(-8.75rem, -10vw, -6rem)" }}
      >
        <ExtractSearchBar onSearch={onSearch} />
      </div>

      {/* Chips — dekorasi, di bawah search bar */}
      <div
        aria-hidden="true"
        className="relative z-20 mt-6 px-4"
      >
        <MetadataChips />
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Paper fan — 7 papers spread wide
 * ───────────────────────────────────────────────────────────── */
type PaperData = {
  journal: string
  title: string
  authors: string
  year: string
  doi: string
  section: "Abstract" | "Introduction" | "Methods" | "Results"
}

const PAPERS: PaperData[] = [
  {
    journal: "J. Comp. Bio.",
    title: "Self-supervised learning for protein structure prediction",
    authors: "Tan H, Wright C, et al.",
    year: "2024",
    doi: "10.1093/jcb.2024.0218",
    section: "Abstract",
  },
  {
    journal: "Nature Methods",
    title: "Graph attention networks in early-stage drug discovery",
    authors: "Park L, Mendoza A, et al.",
    year: "2024",
    doi: "10.1038/nmeth.2024.119",
    section: "Abstract",
  },
  {
    journal: "Phys. Rev. X",
    title: "Quantum error correction in NISQ-era processors",
    authors: "Liu W, Okafor C, et al.",
    year: "2025",
    doi: "10.1103/PhysRevX.15.031022",
    section: "Introduction",
  },
  {
    journal: "Nature",
    title: "Federated learning for privacy-aware medical imaging",
    authors: "Smith J, Park L, +3",
    year: "2024",
    doi: "10.1038/s41586.2024.0341",
    section: "Abstract",
  },
  {
    journal: "Nat. Climate",
    title: "Physics-informed networks for regional climate modeling",
    authors: "Reyes M, Anand P, et al.",
    year: "2025",
    doi: "10.1038/s41558.2025.0117",
    section: "Methods",
  },
  {
    journal: "PNAS",
    title: "Causal inference in observational genomics studies",
    authors: "Carter D, Abebe T, et al.",
    year: "2024",
    doi: "10.1073/pnas.2024.087",
    section: "Results",
  },
  {
    journal: "IEEE Xplore",
    title: "Neuro-symbolic reasoning for autonomous scientific discovery",
    authors: "Hassan O, Lim S, et al.",
    year: "2025",
    doi: "10.1109/IEEE.2025.04",
    section: "Abstract",
  },
]

/**
 * Per-paper config — sesuai posisi spesifik di spec.
 * desktopX/Y/etc untuk ≥md, tabletX untuk sm-md (override),
 * showAt: breakpoint mulai paper ini muncul.
 *
 * showAt = "mobile" → tampil di semua ukuran (paper 3, 4, 5)
 * showAt = "tablet" → tampil mulai sm (paper 2, 6)
 * showAt = "desktop" → tampil mulai md (paper 1, 7)
 */
type FanItem = {
  data: PaperData
  /** Desktop ≥md */
  desktop: { x: number; y: number; rot: number; scale: number; opacity: number }
  /** Tablet sm..md */
  tablet: { x: number; y: number; rot: number; scale: number; opacity: number }
  /** Mobile <sm */
  mobile?: { x: number; y: number; rot: number; scale: number; opacity: number }
  z: number
  blur: string
  showAt: "mobile" | "tablet" | "desktop"
}

const FAN_ITEMS: FanItem[] = [
  // Paper 1 — paling kiri (desktop only)
  {
    data: PAPERS[0],
    desktop: { x: -360, y: 80, rot: -18, scale: 0.85, opacity: 0.45 },
    tablet: { x: 0, y: 0, rot: 0, scale: 0, opacity: 0 }, // not shown
    z: 1,
    blur: "blur-[1px]",
    showAt: "desktop",
  },
  // Paper 2 — kiri (tablet & desktop)
  {
    data: PAPERS[1],
    desktop: { x: -240, y: 45, rot: -12, scale: 0.92, opacity: 0.65 },
    tablet: { x: -200, y: 50, rot: -14, scale: 0.78, opacity: 0.6 },
    z: 2,
    blur: "blur-[0.5px]",
    showAt: "tablet",
  },
  // Paper 3 — kiri tengah (semua viewport)
  {
    data: PAPERS[2],
    desktop: { x: -120, y: 20, rot: -6, scale: 0.98, opacity: 0.85 },
    tablet: { x: -110, y: 25, rot: -8, scale: 0.85, opacity: 0.85 },
    mobile: { x: -78, y: 22, rot: -9, scale: 0.7, opacity: 0.75 },
    z: 4,
    blur: "",
    showAt: "mobile",
  },
  // Paper 4 — TENGAH dominant (semua viewport)
  {
    data: PAPERS[3],
    desktop: { x: 0, y: -10, rot: 0, scale: 1.05, opacity: 1 },
    tablet: { x: 0, y: -5, rot: 0, scale: 0.92, opacity: 1 },
    mobile: { x: 0, y: 0, rot: 0, scale: 0.78, opacity: 1 },
    z: 6,
    blur: "",
    showAt: "mobile",
  },
  // Paper 5 — kanan tengah (semua viewport)
  {
    data: PAPERS[4],
    desktop: { x: 120, y: 20, rot: 6, scale: 0.98, opacity: 0.85 },
    tablet: { x: 110, y: 25, rot: 8, scale: 0.85, opacity: 0.85 },
    mobile: { x: 78, y: 22, rot: 9, scale: 0.7, opacity: 0.75 },
    z: 4,
    blur: "",
    showAt: "mobile",
  },
  // Paper 6 — kanan (tablet & desktop)
  {
    data: PAPERS[5],
    desktop: { x: 240, y: 45, rot: 12, scale: 0.92, opacity: 0.65 },
    tablet: { x: 200, y: 50, rot: 14, scale: 0.78, opacity: 0.6 },
    z: 2,
    blur: "blur-[0.5px]",
    showAt: "tablet",
  },
  // Paper 7 — paling kanan (desktop only)
  {
    data: PAPERS[6],
    desktop: { x: 360, y: 80, rot: 18, scale: 0.85, opacity: 0.45 },
    tablet: { x: 0, y: 0, rot: 0, scale: 0, opacity: 0 },
    z: 1,
    blur: "blur-[1px]",
    showAt: "desktop",
  },
]

function PaperFan() {
  return (
    <div className="absolute inset-x-0 top-0 z-10 mx-auto h-full">
      {FAN_ITEMS.map((p, i) => {
        const animClass = i % 2 === 0 ? "animate-float-left" : "animate-float-right"
        const delay = `${(i * 0.35).toFixed(2)}s`

        // Visibility per breakpoint
        const visibilityClass =
          p.showAt === "desktop"
            ? "hidden md:block"
            : p.showAt === "tablet"
            ? "hidden sm:block"
            : "" // mobile = always

        return (
          <FanPaperWrapper
            key={i}
            item={p}
            visibilityClass={visibilityClass}
          >
            <div
              className={`${p.blur} ${animClass} motion-reduce:animate-none`}
              style={{
                ["--paper-rot" as string]: `0deg`,
                animationDelay: delay,
                transformOrigin: "center center",
              }}
            >
              <PaperPage data={p.data} />
            </div>
          </FanPaperWrapper>
        )
      })}
    </div>
  )
}

/**
 * Wrapper paper: handle posisi per breakpoint.
 *
 * Posisi dipake `rem`-based (px input dibagi 16 saat render) — ini bikin
 * fan tetap proporsional saat browser zoom in/out. Pakai px hardcode di
 * transform akan freeze posisi terhadap layout yang sudah scaled.
 *
 * Strategi: render 3 div dengan visibility responsive (block/hidden via
 * Tailwind), masing-masing pakai konfigurasi sendiri.
 */
function FanPaperWrapper({
  item,
  visibilityClass,
  children,
}: {
  item: FanItem
  visibilityClass: string
  children: React.ReactNode
}) {
  const { desktop, tablet, mobile } = item

  // Helper: konversi posisi config dari px ke rem string
  // (16px = 1rem). Ini bikin transform mengikuti zoom level browser.
  const toRem = (px: number) => `${px / 16}rem`

  const transformOf = (cfg: { x: number; y: number; rot: number; scale: number }) =>
    `translate(calc(-50% + ${toRem(cfg.x)}), calc(-50% + ${toRem(cfg.y)})) rotate(${cfg.rot}deg) scale(${cfg.scale})`

  return (
    <>
      {/* Mobile (<640px) */}
      {mobile && (
        <div
          className={`absolute left-1/2 top-1/2 sm:hidden ${visibilityClass}`}
          style={{
            transform: transformOf(mobile),
            zIndex: item.z,
            opacity: mobile.opacity,
          }}
        >
          {children}
        </div>
      )}

      {/* Tablet (sm..md) */}
      <div
        className={`absolute left-1/2 top-1/2 hidden sm:block md:hidden ${visibilityClass}`}
        style={{
          transform: transformOf(tablet),
          zIndex: item.z,
          opacity: tablet.opacity,
        }}
      >
        {children}
      </div>

      {/* Desktop (≥md) */}
      <div
        className={`absolute left-1/2 top-1/2 hidden md:block ${visibilityClass}`}
        style={{
          transform: transformOf(desktop),
          zIndex: item.z,
          opacity: desktop.opacity,
        }}
      >
        {children}
      </div>
    </>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Single academic paper page
 * ───────────────────────────────────────────────────────────── */
function PaperPage({ data }: { data: PaperData }) {
  const lineWidths = [
    [98, 92, 95, 88, 70, 82],
    [96, 90, 94, 82, 76, 88],
    [94, 88, 96, 86, 68, 78],
  ]
  const variant = data.title.length % lineWidths.length
  const lines = lineWidths[variant]

  return (
    <div className="w-[14.375rem] rounded-[0.875rem] border border-border/30 bg-white px-4 py-3.5 shadow-elevated">
      <div className="flex items-center justify-between border-b border-border/40 pb-1.5">
        <span className="font-mono text-[0.5rem] font-semibold uppercase tracking-wider text-foreground/55">
          {data.journal}
        </span>
        <span className="font-mono text-[0.5rem] text-muted-foreground/70">p. 01</span>
      </div>

      <h4 className="mt-2.5 font-display text-[0.75rem] font-semibold leading-tight tracking-tight text-foreground">
        {data.title}
      </h4>

      <p className="mt-1 text-[0.5625rem] italic leading-snug text-foreground/70">
        {data.authors}
      </p>

      <p className="mt-0.5 font-mono text-[0.5rem] leading-snug text-muted-foreground">
        {data.year} · DOI: {data.doi}
      </p>

      <p className="mt-2.5 text-[0.5rem] font-bold uppercase tracking-[0.12em] text-foreground/75">
        {data.section}
      </p>

      <div className="mt-1 space-y-[3px]">
        {lines.map((w, i) => (
          <div
            key={i}
            className="h-[3px] rounded-sm bg-foreground/22"
            style={{ width: `${w}%` }}
          />
        ))}
      </div>

      <p className="mt-2.5 text-[0.5rem] font-bold uppercase tracking-[0.12em] text-foreground/70">
        1. Introduction
      </p>
      <div className="mt-1 space-y-[3px]">
        {[100, 90, 84, 92].map((w, i) => (
          <div
            key={i}
            className="h-[3px] rounded-sm bg-foreground/18"
            style={{ width: `${w}%` }}
          />
        ))}
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Extract search bar — INTERACTIVE form, two-row layout
 * Konsisten dengan SearchPage (input row + toolbar row).
 * ───────────────────────────────────────────────────────────── */
function ExtractSearchBar({ onSearch }: { onSearch?: (q: string) => void }) {
  const [query, setQuery] = useState("")
  const trimmed = query.trim()

  const submit = () => {
    if (!trimmed || !onSearch) return
    onSearch(trimmed)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submit()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="relative mx-auto w-full animate-window-float motion-reduce:animate-none"
      style={{ maxWidth: "48.75rem" /* ~780px */ }}
      role="search"
      aria-label="Extract paper data"
    >
      {/* Soft glow underneath */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 rounded-[1.5rem] bg-white/30 blur-2xl"
      />

      <div className="overflow-hidden rounded-[1.375rem] border border-white/60 bg-card shadow-[0_28px_60px_-20px_rgba(15,40,90,0.55)] transition-all focus-within:border-primary/40 focus-within:shadow-[0_30px_72px_-20px_rgba(30,107,184,0.45)]">
        {/* Row 1 — input */}
        <div className="relative flex items-center px-4 sm:px-5">
          <label htmlFor="hero-search-input" className="sr-only">
            Paper URL, DOI, or query
          </label>

          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-soft/60 text-primary sm:h-10 sm:w-10"
            aria-hidden="true"
          >
            <FileText className="h-4 w-4" strokeWidth={2.2} />
          </div>

          <input
            id="hero-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste paper URL, DOI, or upload PDF..."
            autoComplete="off"
            spellCheck={false}
            className="flex-1 truncate bg-transparent pl-3 pr-2 py-4 text-sm text-foreground placeholder:text-foreground/45 outline-none sm:py-5 sm:text-[0.9375rem]"
          />

          <span
            aria-hidden="true"
            className="hidden font-mono text-[0.6875rem] font-medium text-foreground/40 md:inline"
          >
            ⌘K
          </span>
        </div>

        {/* Row 2 — toolbar */}
        <div className="flex items-center gap-3 border-t border-border/40 bg-muted/30 px-4 py-2 text-xs sm:px-5">
          <div
            className="flex items-center gap-1.5 rounded-md bg-primary-soft/50 px-2 py-1 text-xs font-semibold text-primary"
            aria-hidden="true"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            arXiv
            <ChevronDown className="h-3 w-3 opacity-70" />
          </div>

          <button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            className="hidden items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-foreground/65 transition-colors hover:bg-muted/60 hover:text-foreground sm:inline-flex"
          >
            Year
            <ChevronDown className="h-3 w-3 opacity-70" />
          </button>
          <button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            className="hidden items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-foreground/65 transition-colors hover:bg-muted/60 hover:text-foreground md:inline-flex"
          >
            Open access
            <ChevronDown className="h-3 w-3 opacity-70" />
          </button>

          <div className="flex-1" />

          <button
            type="submit"
            disabled={!trimmed}
            className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-pill bg-primary px-4 text-xs font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/30"
            aria-label="Extract paper data"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Extract
          </button>
        </div>
      </div>
    </form>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Metadata chips
 * ───────────────────────────────────────────────────────────── */
function MetadataChips() {
  const chips: { icon: React.ReactNode; label: string; delay: number }[] = [
    { icon: <FileText className="h-3 w-3" />, label: "PDF", delay: 0 },
    { icon: <Hash className="h-3 w-3" />, label: "DOI", delay: 0.4 },
    { icon: <Tag className="h-3 w-3" />, label: "arXiv", delay: 0.8 },
    { icon: <Quote className="h-3 w-3" />, label: "Citations", delay: 1.2 },
  ]

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-2.5">
      {chips.map((c) => (
        <span
          key={c.label}
          className="inline-flex animate-chip-float items-center gap-1.5 rounded-pill border border-white/30 bg-white/85 px-3 py-1.5 text-xs font-semibold text-primary shadow-card backdrop-blur-sm motion-reduce:animate-none"
          style={{ animationDelay: `${c.delay}s` }}
        >
          {c.icon}
          {c.label}
        </span>
      ))}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Particle field — partikel putih halus melayang
 *
 * Strategi:
 *   • 36 partikel deterministik (tidak random per render — stabil di SSR/dev)
 *   • Tiga ukuran (sm/md/lg) dengan opacity & blur berbeda untuk depth
 *   • Animasi `particle-rise` (terbang ke atas) + `particle-twinkle` (kelap)
 *   • Posisi tersebar via grid 6x6 dengan jitter; menutupi seluruh hero
 *   • aria-hidden, motion-reduce mematikan animasi
 * ───────────────────────────────────────────────────────────── */

type ParticleSize = "sm" | "md" | "lg"

interface Particle {
  size: ParticleSize
  /** % horizontal posisi (0-100) */
  left: number
  /** % vertical posisi (0-100) */
  top: number
  /** detik delay animasi rise */
  riseDelay: number
  /** detik durasi animasi rise */
  riseDuration: number
  /** detik delay animasi twinkle */
  twinkleDelay: number
}

/**
 * Distribusi 36 partikel deterministik. Posisi dipilih untuk
 * menyebar di seluruh hero, sedikit lebih padat di sepertiga bawah
 * (di mana paper-fan & search-bar berada — jadi terasa seperti
 * partikel "naik" dari dasar gradient).
 */
const PARTICLES: Particle[] = (() => {
  const list: Particle[] = []
  const sizes: ParticleSize[] = ["sm", "md", "lg"]

  // Grid 6x6 = 36, dengan jitter berbasis index agar deterministik.
  for (let row = 0; row < 6; row++) {
    for (let col = 0; col < 6; col++) {
      const i = row * 6 + col
      // Jitter sederhana: golden ratio mod, agar sebaran natural.
      const jx = ((i * 137.5) % 12) - 6
      const jy = ((i * 263.1) % 14) - 7

      const left = (col + 0.5) * (100 / 6) + jx
      const top = (row + 0.5) * (100 / 6) + jy

      // Distribusi ukuran 60% sm, 30% md, 10% lg
      const sizeIdx = i % 10 < 6 ? 0 : i % 10 < 9 ? 1 : 2
      const size = sizes[sizeIdx]

      list.push({
        size,
        left: Math.max(0, Math.min(100, left)),
        top: Math.max(0, Math.min(100, top)),
        riseDelay: (i * 0.27) % 8,
        riseDuration: 12 + ((i * 1.7) % 10), // 12–22s
        twinkleDelay: (i * 0.41) % 4,
      })
    }
  }
  return list
})()

const SIZE_CLASS: Record<ParticleSize, string> = {
  sm: "h-[2px] w-[2px]",
  md: "h-[3px] w-[3px]",
  lg: "h-[4px] w-[4px] blur-[0.5px]",
}

const SIZE_PEAK: Record<ParticleSize, number> = {
  sm: 0.6,
  md: 0.78,
  lg: 0.95,
}

function ParticleField() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
    >
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className={`absolute rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,0.45)] animate-particle motion-reduce:animate-none motion-reduce:opacity-60 ${SIZE_CLASS[p.size]}`}
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            // Stagger dua animasi (rise, twinkle) lewat dua delay & dua duration.
            animationDelay: `${p.riseDelay}s, ${p.twinkleDelay}s`,
            animationDuration: `${p.riseDuration}s, 3.2s`,
            // Variabel custom dipakai keyframe particle-twinkle.
            ["--tw-particle-peak" as string]: SIZE_PEAK[p.size].toString(),
          }}
        />
      ))}
    </div>
  )
}
