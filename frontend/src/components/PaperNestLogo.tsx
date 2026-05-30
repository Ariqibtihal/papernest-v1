/**
 * PaperNestLogo — komponen logo dari raster file `logoPapernest.webp`.
 *
 * Ekspor:
 *   • <PaperNestIcon />        — icon-only (square crop), untuk sidebar / favicon-pad
 *   • <PaperNestLogoFull />    — alias yang sama (full file sudah berisi
 *                                icon + wordmark sebagai 1 image)
 *   • <PaperNestLogoStacked /> — alias serupa, untuk login splash (vertical area)
 *   • <PaperLensLogo />        — legacy alias untuk backward compat
 *
 * Catatan:
 *   • Vite akan handle hashing & lazy load otomatis lewat ES module import.
 *   • `loading="lazy"` di atas-the-fold (TopNav) bisa skip render awal,
 *     jadi default `eager` untuk logo utama. Override via prop kalau perlu.
 *   • `decoding="async"` agar image decoding tidak block rendering.
 */

import logo from "@/assets/logos/logoPapernest.webp"

interface LogoProps {
  className?: string
  /** Override label aksesibilitas (default: "PaperNest"). */
  title?: string
  /**
   * Hint loading. Default `eager` karena logo biasanya above-the-fold
   * (top nav, login). Set `lazy` kalau dipakai di footer atau modal yang
   * bisa di-defer.
   */
  loading?: "eager" | "lazy"
  /**
   * Diabaikan di komponen ini (raster image tidak punya monochrome mode).
   * Prop dipertahankan untuk backward-compat dengan call-site lama yang
   * mungkin lewatkan `monochrome` ke variant lama (SVG).
   */
  monochrome?: boolean
}

function LogoImage({
  className,
  title = "PaperNest",
  loading = "eager",
}: LogoProps) {
  return (
    <img
      src={logo}
      alt={title}
      className={`object-contain ${className ?? ""}`.trim()}
      loading={loading}
      decoding="async"
      draggable={false}
    />
  )
}

/* ─────────────────────────────────────────────────────────────
 * Icon-only — square crop
 *
 * Note: file `logoPapernest.webp` punya wordmark + icon dalam satu file.
 * Untuk slot square (sidebar 32x32), kita pakai object-contain agar
 * proporsi terjaga. Kalau user butuh icon-only murni nantinya, kasih
 * tau dan saya bikin variant terpisah dari versi crop.
 * ───────────────────────────────────────────────────────────── */
export function PaperNestIcon({
  className = "h-6 w-6",
  title = "PaperNest",
  loading = "eager",
}: LogoProps) {
  return <LogoImage className={className} title={title} loading={loading} />
}

/* ─────────────────────────────────────────────────────────────
 * Full logo — icon + wordmark horizontal (default)
 * ───────────────────────────────────────────────────────────── */
export function PaperNestLogoFull({
  className = "h-7",
  title = "PaperNest",
  loading = "eager",
}: LogoProps) {
  return <LogoImage className={className} title={title} loading={loading} />
}

/* ─────────────────────────────────────────────────────────────
 * Stacked logo — untuk vertical area (login splash)
 * ───────────────────────────────────────────────────────────── */
export function PaperNestLogoStacked({
  className = "h-16",
  title = "PaperNest",
  loading = "eager",
}: LogoProps) {
  return <LogoImage className={className} title={title} loading={loading} />
}

/* Legacy alias */
export function PaperLensLogo(props: LogoProps) {
  return <PaperNestIcon {...props} />
}
