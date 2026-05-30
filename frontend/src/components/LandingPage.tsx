import { useState } from "react"
import { Plus, Minus, Menu, X, ArrowRight } from "lucide-react"
import { PaperNestLogoFull } from "@/components/SideNav"
import { Button } from "@/components/ui/button"
import { HeroSection } from "@/components/HeroSection"
import { useEffect } from "react"

interface LandingPageProps {
  onSearch: (query: string) => void
}

/* ─────────────────────────────────────────────────────────────
 * Top nav (desktop sticky)
 * ───────────────────────────────────────────────────────────── */
function TopNav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    handler()
    window.addEventListener("scroll", handler, { passive: true })
    return () => window.removeEventListener("scroll", handler)
  }, [])

  const links = [
    { href: "#how-it-works", label: "Use cases" },
    { href: "#why", label: "Why PaperNest" },
    { href: "#faq", label: "FAQ" },
    { href: "/docs", label: "API" },
  ]

  return (
    <header
      className={`hidden md:flex fixed top-0 z-40 w-full justify-center transition-[background-color,backdrop-filter,border-color,box-shadow] duration-250 ease-out ${
        scrolled
          ? "bg-white/55 backdrop-blur-md border-b border-white/40 shadow-[0_4px_20px_-12px_rgba(15,23,42,0.18)]"
          : "bg-transparent border-b border-transparent"
      }`}
      style={{ transitionDuration: "250ms" }}
    >
      <div
        className="flex w-full items-center justify-between gap-6 px-4 py-1.5 sm:px-6 lg:px-8"
        style={{ maxWidth: "75rem" /* 1200px */ }}
      >
        <a
          href="/"
          className={`flex shrink-0 items-center transition-opacity ${
            scrolled ? "" : "drop-shadow-[0_2px_4px_rgba(0,0,0,0.25)]"
          }`}
          aria-label="PaperNest home"
        >
          {/*
            Logo file aslinya berwarna putih (untuk hero gelap).
            Saat user scroll dan masuk section bright, pakai filter
            `brightness(0)` untuk convert seluruh logo jadi solid hitam.

            Ukuran h-12 (48px) di mobile, h-14 (56px) di desktop —
            cukup besar untuk readable, tapi nav tetap ramping.
          */}
          <PaperNestLogoFull
            className={`h-12 w-auto sm:h-14 transition-[filter] duration-300 ${
              scrolled ? "[filter:brightness(0)]" : ""
            }`}
          />
        </a>
        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 lg:gap-x-7">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className={`whitespace-nowrap text-[0.8125rem] font-medium transition-colors ${
                scrolled
                  ? "text-foreground/75 hover:text-primary"
                  : "text-white/85 hover:text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]"
              }`}
            >
              {l.label}
            </a>
          ))}
        </nav>
        {/* Sign-in CTA — adapt ke scroll state.
            Atas hero (transparan): pill outline putih.
            Setelah scroll (semi-transparent): pill primary biru. */}
        <a
          href="/login"
          className={`inline-flex h-9 shrink-0 items-center rounded-pill px-4 text-[0.8125rem] font-semibold transition-all duration-300 focus-visible:outline-none focus-visible:ring-4 ${
            scrolled
              ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:ring-primary/30"
              : "border border-white/45 bg-white/8 text-white backdrop-blur-sm hover:bg-white/18 focus-visible:ring-white/30"
          }`}
        >
          Sign in
        </a>
      </div>
    </header>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Mini visuals untuk use case cards
 * ───────────────────────────────────────────────────────────── */
function MiniLitReview() {
  return (
    <div className="relative h-[140px] overflow-hidden rounded-xl bg-gradient-to-br from-primary-soft/40 to-transparent p-3">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute left-1/2 w-[80%] -translate-x-1/2 rounded-lg border border-border/60 bg-card p-2 shadow-card"
          style={{ top: 16 + i * 24, zIndex: 3 - i, opacity: 1 - i * 0.18 }}
        >
          <div className="flex items-center gap-1.5">
            <span className="rounded-full bg-q1 px-1.5 py-0.5 text-[8px] font-bold text-white">
              Q1
            </span>
            <div className="h-1.5 flex-1 rounded bg-muted/80" />
          </div>
          <div className="mt-1.5 h-1.5 w-3/4 rounded bg-muted/60" />
        </div>
      ))}
    </div>
  )
}

function MiniAlertBell() {
  return (
    <div className="relative flex h-[140px] items-center justify-center rounded-xl bg-gradient-to-br from-primary-soft/40 to-transparent">
      <div className="rounded-2xl border border-border/60 bg-card px-4 py-3 shadow-card">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" className="h-4 w-4">
              <path d="M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M10 21a2 2 0 004 0" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <div className="h-1.5 w-24 rounded bg-foreground/40" />
            <div className="mt-1 h-1.5 w-16 rounded bg-muted/60" />
          </div>
          <span className="rounded-full bg-q2 px-1.5 py-0.5 text-[9px] font-bold text-white">
            +3
          </span>
        </div>
      </div>
    </div>
  )
}

function MiniQuartileBadge() {
  return (
    <div className="relative flex h-[140px] items-center justify-center rounded-xl bg-gradient-to-br from-primary-soft/40 to-transparent">
      <div className="flex items-end gap-3">
        {(["q4", "q3", "q2", "q1"] as const).map((q, i) => (
          <div
            key={q}
            className="flex w-9 items-end justify-center rounded-t-lg pb-1 text-[10px] font-bold text-white"
            style={{
              backgroundColor: `hsl(var(--${q}))`,
              height: 30 + i * 14,
            }}
          >
            {q.toUpperCase()}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Use cases (How researchers use PaperNest)
 * ───────────────────────────────────────────────────────────── */
function UseCases() {
  const cases = [
    {
      n: "01",
      title: "Lit review for thesis",
      body: "Cari sekali, dapat hasil dari delapan sumber sekaligus. Tidak ada duplikat — versi paling kaya metadata yang ditampilkan.",
      visual: <MiniLitReview />,
    },
    {
      n: "02",
      title: "Track topik pencarian",
      body: "Simpan query favoritmu sebagai alert. PaperNest memberitahumu saat ada paper baru yang cocok dengan kriteria.",
      visual: <MiniAlertBell />,
    },
    {
      n: "03",
      title: "Spot Q1 dalam sekali pandang",
      body: "Setiap kartu paper menampilkan kuartil Scimago dan flag predator. Tahu kualitas jurnalnya tanpa harus lookup terpisah.",
      visual: <MiniQuartileBadge />,
    },
  ]

  return (
    <section
      id="how-it-works"
      className="flex min-h-[100svh] items-center py-16 sm:py-20"
    >
      <div className="mx-auto w-full max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[680px] text-center">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
            How researchers use PaperNest
          </p>
          <h2
            className="font-display mt-4 font-semibold leading-[1.05] tracking-[-0.035em] text-foreground"
            style={{ fontSize: "clamp(2rem, 4vw + 0.5rem, 3rem)" }}
          >
            Built around how you actually do research.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3 sm:mt-14">
          {cases.map((c) => (
            <div
              key={c.n}
              className="rounded-3xl border border-border/40 bg-card p-7 shadow-card transition-all hover:shadow-elevated hover:border-primary/30"
            >
              <span className="font-display text-[12px] font-semibold tracking-wider text-primary">
                {c.n}
              </span>
              <h3 className="font-display mt-3 text-[1.375rem] font-semibold leading-tight tracking-tight text-foreground">
                {c.title}
              </h3>
              <p className="mt-2.5 text-[0.875rem] leading-7 text-muted-foreground">
                {c.body}
              </p>
              <div className="mt-5">{c.visual}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Why PaperNest — alternating feature rows
 * ───────────────────────────────────────────────────────────── */
function FeatureRow({
  id,
  eyebrow,
  title,
  description,
  illustration,
  reverse = false,
  background = "default",
}: {
  id?: string
  eyebrow: string
  title: string
  description: string
  illustration: React.ReactNode
  reverse?: boolean
  background?: "default" | "accent"
}) {
  const bg = background === "accent" ? "bg-accent/60" : ""
  return (
    <section
      id={id}
      className={`${bg} flex items-center py-16 sm:py-20`}
    >
      <div
        className={`mx-auto w-full max-w-[1100px] px-4 flex flex-col items-center gap-10 sm:gap-12 sm:px-6 lg:gap-16 lg:px-8 ${
          reverse ? "md:flex-row-reverse" : "md:flex-row"
        }`}
      >
        <div className="flex-1 text-center md:text-left">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
            {eyebrow}
          </p>
          <h2
            className="font-display mt-3 font-semibold leading-tight tracking-[-0.035em] text-foreground"
            style={{ fontSize: "clamp(1.875rem, 3.5vw + 0.5rem, 2.5rem)" }}
          >
            {title}
          </h2>
          <p className="mt-5 max-w-[520px] mx-auto md:mx-0 text-[1rem] leading-8 text-muted-foreground">
            {description}
          </p>
        </div>
        <div className="flex-1 flex justify-center">{illustration}</div>
      </div>
    </section>
  )
}

function DedupVisual() {
  return (
    <div className="relative w-full max-w-[440px] rounded-2xl border border-border/40 bg-card p-6 shadow-elevated">
      <div className="space-y-2.5">
        {["Crossref", "OpenAlex", "PubMed"].map((src, i) => (
          <div
            key={src}
            className="flex items-center gap-3 rounded-lg border border-border/50 bg-muted/40 p-2.5"
            style={{ opacity: 1 - i * 0.18 }}
          >
            <span className="rounded-md bg-accent px-2 py-0.5 text-[10px] font-semibold capitalize text-muted-foreground">
              {src}
            </span>
            <div className="h-2 flex-1 rounded bg-muted/70" />
          </div>
        ))}
      </div>
      <div className="my-3 flex items-center justify-center gap-2 text-primary">
        <div className="h-px flex-1 bg-primary/30" />
        <ArrowRight className="h-4 w-4" />
        <div className="h-px flex-1 bg-primary/30" />
      </div>
      <div className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary-soft/30 p-3">
        <span className="rounded-full bg-q1 px-2 py-0.5 text-[10px] font-bold text-white">Q1</span>
        <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-bold text-primary">OA</span>
        <div className="h-2 flex-1 rounded bg-primary/40" />
      </div>
    </div>
  )
}

function QuartileVisual() {
  return (
    <div className="relative w-full max-w-[440px] rounded-2xl border border-border/40 bg-card p-6 shadow-elevated">
      <div className="space-y-2.5">
        {[
          { q: "q1", title: "Federated learning for medical imaging" },
          { q: "q2", title: "Multi-omics integration in cancer research" },
          { q: "predator" as const, title: "World Journal of Innovative Research" },
        ].map((row, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg border border-border/50 bg-muted/30 p-2.5"
          >
            {row.q === "q1" && (
              <span className="shrink-0 rounded-full bg-q1 px-2 py-0.5 text-[10px] font-bold text-white">
                Q1
              </span>
            )}
            {row.q === "q2" && (
              <span className="shrink-0 rounded-full bg-q2 px-2 py-0.5 text-[10px] font-bold text-white">
                Q2
              </span>
            )}
            {row.q === "predator" && (
              <span className="shrink-0 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-700">
                ⚠ Predatory
              </span>
            )}
            <span className="text-[12px] font-medium text-foreground/80 truncate">
              {row.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function OpenAccessVisual() {
  return (
    <div className="relative w-full max-w-[440px] rounded-2xl border border-border/40 bg-card p-7 shadow-elevated">
      <div className="flex items-center justify-between">
        <span className="font-display text-[14px] font-semibold text-foreground">
          Filter access
        </span>
        <span className="rounded-full bg-primary-soft px-2.5 py-0.5 text-[11px] font-bold text-primary">
          OA
        </span>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border border-primary/30 bg-primary-soft/30 p-3.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-primary">OA</div>
          <div className="mt-1 font-display text-[28px] font-semibold tracking-tight text-foreground">
            68%
          </div>
          <div className="text-[11px] text-muted-foreground">of results</div>
        </div>
        <div className="rounded-xl border border-border/50 bg-muted/30 p-3.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Closed
          </div>
          <div className="mt-1 font-display text-[28px] font-semibold tracking-tight text-foreground/60">
            32%
          </div>
          <div className="text-[11px] text-muted-foreground">of results</div>
        </div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted/40">
        <div className="h-full w-[68%] rounded-full bg-primary" />
      </div>
    </div>
  )
}

function WhyPaperNest() {
  return (
    <div id="why">
      <FeatureRow
        eyebrow="Smart dedup"
        title="Stop reading the same paper twice."
        description="PaperNest merges duplicate records across sources using DOI matching and fuzzy title comparison. You see one paper, with the richest combined metadata from every source it appeared in."
        illustration={<DedupVisual />}
      />
      <FeatureRow
        eyebrow="Journal quality"
        title="Q1 atau Q4? Lihat dalam sekali pandang."
        description="Setiap kartu paper menampilkan kuartil Scimago (Q1–Q4) dan flag predator otomatis. Sumber kualitas jurnal langsung di hasil pencarian — tanpa harus buka tab lain untuk verifikasi."
        illustration={<QuartileVisual />}
        reverse
        background="accent"
      />
      <FeatureRow
        eyebrow="Open access first"
        title="No paywalls in the way."
        description="Filter Open Access dengan satu klik. PaperNest memprioritaskan link ke versi gratis — repository institusi, preprint server, dan publisher OA — saat tersedia."
        illustration={<OpenAccessVisual />}
      />
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────
 * FAQ
 * ───────────────────────────────────────────────────────────── */
function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  const faqs = [
    {
      q: "How is PaperNest different from Google Scholar?",
      a: "PaperNest is fully open: all data is accessible via API with no paywalls. We aggregate eight major sources, deduplicate results, and show transparent journal quality (Q1–Q4) — none of which Scholar offers.",
    },
    {
      q: "Is PaperNest really free?",
      a: "Yes. Search and API are free. No API keys required for basic access. We link to open-access PDFs whenever they are available.",
    },
    {
      q: "Where do quartile badges (Q1–Q4) come from?",
      a: "From the Scimago Journal Rank (SJR) database, refreshed annually. We match each paper's journal by ISSN first, with a fuzzy title match as fallback.",
    },
    {
      q: "How does the predatory journal flag work?",
      a: "It uses heuristics from Beall's List criteria — suspicious naming patterns, publishers, and domains. Treat the badge as a hint, not a verdict; verify manually for important decisions.",
    },
    {
      q: "Does PaperNest host PDFs?",
      a: "No. We link to open access PDFs at their original repositories or publishers. We store metadata only.",
    },
  ]

  return (
    <section
      id="faq"
      className="flex min-h-[100svh] items-center py-16 sm:py-20"
    >
      <div className="mx-auto w-full max-w-[760px] px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">FAQ</p>
          <h2
            className="font-display mt-4 font-semibold tracking-[-0.035em] text-foreground"
            style={{ fontSize: "clamp(2rem, 4vw + 0.5rem, 2.75rem)" }}
          >
            Frequently asked questions
          </h2>
        </div>
        <dl className="mt-10 sm:mt-12">
          {faqs.map((faq, i) => {
            const isOpen = openIdx === i
            const panelId = `faq-panel-${i}`
            const buttonId = `faq-button-${i}`
            return (
              <div key={i} className="border-t border-border">
                <dt>
                  <button
                    id={buttonId}
                    onClick={() => setOpenIdx(isOpen ? null : i)}
                    aria-expanded={isOpen}
                    aria-controls={panelId}
                    className="flex w-full items-center justify-between py-5 text-left transition-colors hover:text-primary"
                  >
                    <span className="pr-4 text-[0.9375rem] font-medium text-foreground">{faq.q}</span>
                    {isOpen ? (
                      <Minus className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                    ) : (
                      <Plus className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    )}
                  </button>
                </dt>
                {isOpen && (
                  <dd id={panelId} role="region" aria-labelledby={buttonId} className="pb-5">
                    <p className="max-w-[660px] text-[0.875rem] leading-7 text-muted-foreground">
                      {faq.a}
                    </p>
                  </dd>
                )}
              </div>
            )
          })}
          <div className="border-t border-border" />
        </dl>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────
 * CTA strip
 * ───────────────────────────────────────────────────────────── */
function CTAStrip({ onSearch }: LandingPageProps) {
  return (
    <section className="relative flex min-h-[100svh] items-center overflow-hidden py-16 sm:py-20">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse 70% 70% at 50% 50%, hsl(var(--primary-soft) / 0.55), transparent 70%)",
        }}
      />
      <div className="mx-auto w-full max-w-[760px] px-4 text-center sm:px-6 lg:px-8">
        <h2
          className="font-display font-semibold leading-[1.05] tracking-[-0.04em] text-foreground"
          style={{ fontSize: "clamp(2rem, 5vw + 0.5rem, 3.5rem)" }}
        >
          Stop hitting paywalls.
        </h2>
        <p
          className="mt-4 text-foreground/75 leading-7"
          style={{ fontSize: "clamp(0.9375rem, 0.4vw + 0.85rem, 1rem)" }}
        >
          Cari sekali, dapat semuanya. Free, open, no API keys for basic access.
        </p>
        <Button
          variant="pillPrimary"
          size="lg"
          className="mt-8 px-8"
          onClick={() => onSearch("")}
        >
          Start searching
        </Button>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Footer
 * ───────────────────────────────────────────────────────────── */
function LandingFooter() {
  return (
    <footer className="border-t border-border/40 bg-card">
      <div className="mx-auto grid max-w-[1100px] grid-cols-2 md:grid-cols-[1.6fr_1fr_1fr_1fr] gap-10 px-6 py-14">
        <div className="col-span-2 md:col-span-1">
          <PaperNestLogoFull className="h-7" />
          <p className="mt-4 max-w-[18rem] text-[13px] leading-6 text-muted-foreground">
            Open scholarly search.<br />
            Made with care for open research.
          </p>
        </div>
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-wider text-foreground/80">
            Product
          </p>
          <ul className="mt-3 space-y-2.5 text-[13px]">
            <li><a href="/search" className="link-color">Search</a></li>
            <li><a href="/saved" className="link-color">Saved papers</a></li>
            <li><a href="/alerts" className="link-color">Alerts</a></li>
            <li><a href="/docs" className="link-color">API docs</a></li>
          </ul>
        </div>
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-wider text-foreground/80">
            Learn
          </p>
          <ul className="mt-3 space-y-2.5 text-[13px]">
            <li><a href="#how-it-works" className="link-color">Use cases</a></li>
            <li><a href="#why" className="link-color">Why PaperNest</a></li>
            <li><a href="#faq" className="link-color">FAQ</a></li>
          </ul>
        </div>
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-wider text-foreground/80">
            Connect
          </p>
          <ul className="mt-3 space-y-2.5 text-[13px]">
            <li>
              <a
                href="https://github.com/openalex"
                target="_blank"
                rel="noreferrer"
                className="link-color"
              >
                GitHub
              </a>
            </li>
            <li>
              <a href="mailto:hello@papernest.app" className="link-color">
                Contact
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border/40">
        <div className="mx-auto flex max-w-[1100px] items-center justify-between px-6 py-5 text-[12px] text-muted-foreground">
          <span>© {new Date().getFullYear()} PaperNest</span>
          <span>Built on open data.</span>
        </div>
      </div>
    </footer>
  )
}

/* ─────────────────────────────────────────────────────────────
 * Main
 * ───────────────────────────────────────────────────────────── */
export default function LandingPage({ onSearch }: LandingPageProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-primary/15">
      {/* Skip link untuk keyboard / screen reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[200] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-elevated focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileNavOpen(true)}
        className="fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-xl border border-white/20 bg-white/10 backdrop-blur-md text-white shadow-card hover:bg-white/20 transition-colors md:hidden"
        aria-label="Open menu"
        aria-expanded={mobileNavOpen}
        aria-controls="mobile-nav-drawer"
      >
        <Menu className="h-4 w-4" aria-hidden="true" />
      </button>

      {/* Mobile nav drawer */}
      {mobileNavOpen && (
        <div
          id="mobile-nav-drawer"
          className="fixed inset-0 z-[100] flex md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation"
        >
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="relative flex h-full w-64 flex-col bg-card border-r border-border p-6 shadow-elevated">
            <div className="flex items-center justify-between mb-8">
              <PaperNestLogoFull className="h-7" />
              <button
                onClick={() => setMobileNavOpen(false)}
                className="p-1 rounded-md hover:bg-accent text-muted-foreground"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { href: "/", label: "Home", active: true },
                { href: "/search", label: "Search" },
                { href: "/saved", label: "Saved Papers" },
                { href: "/alerts", label: "Alerts" },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileNavOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-[14px] font-medium transition-colors ${
                    item.active
                      ? "bg-primary-soft/40 text-primary"
                      : "text-foreground/70 hover:bg-accent hover:text-foreground"
                  }`}
                >
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="mt-auto pt-6 border-t border-border">
              <a
                href="/login"
                onClick={() => setMobileNavOpen(false)}
                className="flex items-center justify-center gap-3 rounded-pill bg-primary px-3 py-2.5 text-[14px] font-semibold text-primary-foreground"
              >
                Sign in
              </a>
            </div>
          </div>
        </div>
      )}

      <TopNav />
      <HeroSection onSearch={onSearch} />

      <main id="main-content" className="flex-1">
        <UseCases />
        <WhyPaperNest />
        <FAQ />
        <CTAStrip onSearch={onSearch} />
      </main>

      <LandingFooter />
    </div>
  )
}
