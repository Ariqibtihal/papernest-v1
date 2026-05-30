# Implementation Plan — PaperNest Redesign (Landing + Search)

**Spec:** [`2026-05-30-papernest-redesign-design.md`](./2026-05-30-papernest-redesign-design.md)
**Strategi:** Bertahap dari fondasi (token & primitif) ke konsumen (kartu, halaman). Backend dulu untuk membuka data badge, lalu frontend dari komponen kecil ke besar.

---

## Tahap 1 — Backend: expose `quartile`

**Tujuan:** Memunculkan field `quartile` (Q1-Q4) di setiap paper response supaya frontend bisa render badge.

### 1.1. Tambah field di schema

**File:** `schemas/paper.py`

Tambah field di `PaperDTO`:
```python
quartile: str | None = None  # "Q1" | "Q2" | "Q3" | "Q4"
```

Tempatkan dekat `journal_quality_score` agar terbaca berkelompok.

### 1.2. Tambah method lookup di journal quality service

**File:** `services/journal_quality_service.py`

Tambah method publik `get_record(title, issn)`:
```python
def get_record(
    self, journal_title: str | None = None, issn: str | None = None
) -> JournalRecord | None:
    """Public lookup: by ISSN first, fallback ke fuzzy title."""
    if issn:
        rec = self.get_by_issn(issn)
        if rec:
            return rec
    if journal_title:
        return self.get_by_title(journal_title)
    return None
```

Method ini hanya membungkus logika yang sudah ada; tidak ada perubahan perilaku.

### 1.3. Isi quartile saat scoring

**File:** `services/ranking_service.py`

Di method `score()` (atau di mana `journal_quality_score` di-set), setelah memanggil `score_journal`, lakukan lookup record dan isi `paper.quartile`:
```python
record = jq_service.get_record(journal_title=paper.venue, issn=paper.venue_issn)
if record and record.quartile != JournalQuartile.UNKNOWN:
    paper.quartile = record.quartile.value  # "Q1"/"Q2"/"Q3"/"Q4"
```

### 1.4. Verifikasi

```powershell
uv run pytest tests/test_dedup.py -v
uv run python -c "from schemas.paper import PaperDTO; p = PaperDTO(title='x', source='y', quartile='Q1'); print(p.quartile)"
```

Lalu jalankan ulang search di browser, inspect response `/api/v1/search` di Network tab — pastikan paper dari jurnal Q1 punya field `quartile: "Q1"`.

**Checkpoint:** field `quartile` muncul di response. Lanjut ke Tahap 2.

---

## Tahap 2 — Frontend: fondasi sistem desain

**Tujuan:** Pasang token warna, font, radius, shadow di Tailwind & CSS supaya komponen berikutnya tinggal pakai.

### 2.1. Install Inter

```powershell
cd frontend
npm install @fontsource-variable/inter
```

Import di `frontend/src/main.tsx` (paling atas):
```typescript
import "@fontsource-variable/inter"
```

### 2.2. Self-host Open Runde

Buat folder `frontend/src/assets/fonts/`. Download tiga file woff2 dari URL di `Style.json.fontLinks`:
- `open-runde-400.woff2`
- `open-runde-500.woff2`
- `open-runde-600.woff2`

Saya akan jalankan PowerShell `Invoke-WebRequest` untuk download. Lisensi Open Runde adalah SIL OFL (open-source) jadi aman.

### 2.3. CSS variables & font-face

**File:** `frontend/src/index.css`

Update / tambah blok:
```css
@font-face {
  font-family: "Open Runde";
  font-weight: 400;
  src: url("./assets/fonts/open-runde-400.woff2") format("woff2");
  font-display: swap;
}
/* … 500 dan 600 sama pola */

@layer base {
  :root {
    --background: 250 251 252;
    --foreground: 15 23 42;
    --muted-foreground: 71 85 105;
    --border: 226 232 240;
    --card: 255 255 255;
    --accent: 238 245 251;

    --primary: 30 107 184;
    --primary-soft: 177 216 244;
    --primary-foreground: 255 255 255;

    --q1: 22 163 74;
    --q2: 2 132 199;
    --q3: 202 138 4;
    --q4: 148 163 184;

    --destructive: 220 38 38;

    --shadow-card: 0 1.6px 1.6px rgb(22 107 197 / 0.04), 0 7px 7px rgb(22 107 197 / 0.10);
    --shadow-elevated: 0 4px 8px rgb(22 107 197 / 0.06), 0 12px 24px rgb(22 107 197 / 0.14);
  }
}
```

Format `R G B` (tanpa koma) supaya bisa dipakai dengan `bg-primary/40` di Tailwind v3.

### 2.4. Tailwind config

**File:** `frontend/tailwind.config.js`

Extend theme:
```js
theme: {
  extend: {
    colors: {
      background: "rgb(var(--background) / <alpha-value>)",
      foreground: "rgb(var(--foreground) / <alpha-value>)",
      "muted-foreground": "rgb(var(--muted-foreground) / <alpha-value>)",
      border: "rgb(var(--border) / <alpha-value>)",
      card: "rgb(var(--card) / <alpha-value>)",
      accent: "rgb(var(--accent) / <alpha-value>)",
      primary: {
        DEFAULT: "rgb(var(--primary) / <alpha-value>)",
        soft: "rgb(var(--primary-soft) / <alpha-value>)",
        foreground: "rgb(var(--primary-foreground) / <alpha-value>)",
      },
      q1: "rgb(var(--q1) / <alpha-value>)",
      q2: "rgb(var(--q2) / <alpha-value>)",
      q3: "rgb(var(--q3) / <alpha-value>)",
      q4: "rgb(var(--q4) / <alpha-value>)",
      destructive: "rgb(var(--destructive) / <alpha-value>)",
    },
    fontFamily: {
      sans: ['"Inter Variable"', "Inter", "system-ui", "sans-serif"],
      display: ['"Open Runde"', "Inter", "sans-serif"],
    },
    boxShadow: {
      card: "var(--shadow-card)",
      elevated: "var(--shadow-elevated)",
    },
    borderRadius: {
      pill: "9999px",
    },
  },
}
```

Catatan: kompatibilitas dengan token Tailwind yang sudah dipakai komponen lama (`bg-primary`, `text-foreground`, dll) tetap terjaga karena nama tokennya sama.

### 2.5. Verifikasi

```powershell
npm run build
```

Build harus tetap hijau. Visual belum berubah — token dipasang tapi belum digunakan komponen baru.

**Checkpoint:** build hijau, font Open Runde muncul saat dipakai class `font-display` (test cepat di browser DevTools).

---

## Tahap 3 — Frontend: komponen UI primitif

**Tujuan:** Update Button & Badge supaya punya variant pill dan badge quartile/OA/predatory.

### 3.1. Update Button

**File:** `frontend/src/components/ui/button.tsx`

Tambah variant `pillPrimary` di `cva` config:
```ts
pillPrimary:
  "bg-primary text-primary-foreground rounded-pill hover:bg-primary/90 shadow-sm",
```

Pastikan variant lama (`default`, `outline`, `ghost`, `link`, `secondary`, `destructive`) tetap. Tambah size `xs: "h-8 px-3 text-xs"` jika belum ada.

### 3.2. Update Badge

**File:** `frontend/src/components/ui/badge.tsx`

Tambah variants:
```ts
q1: "bg-q1 text-white border-transparent",
q2: "bg-q2 text-white border-transparent",
q3: "bg-q3 text-white border-transparent",
q4: "bg-transparent text-q4 border border-q4",
oa: "bg-primary-soft text-primary border-transparent",
predatory: "bg-red-50 text-red-700 border border-red-200",
source: "bg-accent text-muted-foreground border-transparent",
```

Setiap badge tetap punya prop `title` untuk tooltip native.

### 3.3. Update Input

**File:** `frontend/src/components/ui/input.tsx`

Naikkan radius ke `rounded-xl` (12px), focus ring `focus:ring-2 focus:ring-primary/20 focus:border-primary/40`.

### 3.4. Verifikasi

```powershell
npm run build
```

Build hijau. Tidak ada perubahan visual halaman karena variant baru belum dipakai.

**Checkpoint:** primitif siap dipakai komponen besar.

---

## Tahap 4 — Frontend: PaperCard dengan badge baru

**Tujuan:** Halaman search langsung punya hasil visual yang nyata — kartu paper dengan badge Q1/Q2/Q3/Q4, OA, dan predatory.

### 4.1. Update tipe TS

**File:** `frontend/src/types/paper.ts`

Tambah field di `PaperDTO`:
```typescript
quartile?: "Q1" | "Q2" | "Q3" | "Q4" | null
```

### 4.2. Refaktor PaperCard

**File:** `frontend/src/components/PaperCard.tsx`

Struktur baru sesuai spec § 5.4:
- Row 1: badges meta (Quartile + OA + Year + venue) di kiri, Predatory di kanan jika `is_predatory === true`.
- Row 2: judul `font-display text-[18px] font-semibold` hover ke `text-primary`.
- Row 3: authors muted.
- Row 4: abstract `line-clamp-2`.
- Row 5: footer (citation count + source chips + Save/View action).

Card wrapper:
```tsx
<article className="rounded-xl bg-card border border-border/40 p-5 shadow-card hover:shadow-elevated transition-shadow">
```

Badge usage:
```tsx
{paper.quartile && (
  <Badge variant={paper.quartile.toLowerCase() as "q1"|"q2"|"q3"|"q4"} title={`Quartile menurut Scimago Journal Rank (${paper.quartile})`}>
    {paper.quartile}
  </Badge>
)}
{paper.is_open_access && <Badge variant="oa" title="Open Access">OA</Badge>}
{paper.is_predatory && (
  <Badge variant="predatory" title="Memenuhi heuristik jurnal predator (Beall's List)">
    <AlertTriangle className="h-3 w-3 mr-1" /> Predatory
  </Badge>
)}
```

### 4.3. Update PaperList

**File:** `frontend/src/components/PaperList.tsx`

Gap antar kartu `gap-3`. Loading skeleton: card placeholder dengan shimmer halus (`animate-pulse bg-primary-soft/30`).

### 4.4. Verifikasi

```powershell
npm run build
```

Lalu `npm run dev`, buka search page, lakukan query (mis. "machine learning"). Pastikan:
- Kartu paper punya badge Q (untuk paper dari jurnal Scimago).
- OA badge muncul untuk paper yang `is_open_access`.
- Predatory badge muncul jika ada (jarang, mungkin perlu cari query khusus).

**Checkpoint:** kartu paper visual sudah memuaskan. Lanjut ke Tahap 5.

---

## Tahap 5 — Frontend: SearchPage polish

**Tujuan:** Sticky header, sort, pagination, mobile sheet sesuai token baru. Search bar struktur tidak berubah.

### 5.1. Background & header

**File:** `frontend/src/pages/SearchPage.tsx`

- Ganti `bg-[#f8f9fb]` → `bg-background`.
- Sticky header sudah `bg-white/95 backdrop-blur` (oke). Border bawah `border-border/40`.
- Container search bar desktop: `rounded-2xl border-border shadow-card focus-within:shadow-elevated focus-within:border-primary/40`.
- Tombol Search di kanan toolbar (saat ini text "Search"): ubah jadi tombol pill primer kecil `<Button variant="pillPrimary" size="xs">`.
- Active filter chips: ubah dari `Badge variant="secondary"` jadi `Badge variant="oa"` (pakai bg `--primary-soft`).

### 5.2. SearchResultsHeader

**File:** `frontend/src/components/SearchResultsHeader.tsx`

Sort dropdown jadi pill kecil. Export tombol ghost.

### 5.3. TrendsChart

**File:** `frontend/src/components/TrendsChart.tsx`

Bungkus card `rounded-2xl bg-card p-6 shadow-card border border-border/40`. Ubah Recharts bar `fill="rgb(var(--primary))" fillOpacity={0.85}`.

### 5.4. Pagination

**File:** `frontend/src/components/Pagination.tsx`

Nomor halaman: button bulat 36px, active `bg-primary text-white`, idle ghost.

### 5.5. PaperDetail (slide-over)

**File:** `frontend/src/components/PaperDetail.tsx`

Header panel pakai badges Q/OA/Predatory di atas judul. Section heading `text-[11px] uppercase tracking-wide text-muted-foreground font-semibold`. Tombol Save / View source jadi pill primer.

### 5.6. Mobile filter bottom sheet

Active button state pakai `border-primary bg-primary-soft text-primary` (sebelumnya `border-primary bg-primary/5 text-primary` — bedanya: `bg-primary-soft` lebih saturated dan konsisten dengan token).

### 5.7. Verifikasi

```powershell
npm run build
```

`npm run dev` → buka /search, lakukan query, cek:
- Search bar shadow & border konsisten.
- Sort & filter dropdown buka rapi, pakai warna primary saat aktif.
- Pagination bulat, active jelas.
- PaperDetail slide-over rapi.
- Mobile (resize browser ke <640px): bottom sheet, single-row search, badge filter count.

**Checkpoint:** SearchPage komplit. Lanjut ke Tahap 6.

---

## Tahap 6 — Frontend: LandingPage

**Tujuan:** Nav top, hero dengan blob, alternating feature blocks dengan SVG, CTA strip, footer dipoles.

### 6.1. Top nav

**File:** `frontend/src/components/LandingPage.tsx`

Tambah komponen `<TopNav />`:
- Sticky `top-0 z-40`.
- Background bertransisi: `bg-transparent` → `bg-card/95 backdrop-blur border-b border-border/40` saat scrollY > 50.
- Hamburger mobile yang sudah ada tetap.

### 6.2. Hero

- Background blob: tambahkan `<div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_rgb(var(--primary-soft)/0.45),_transparent_60%)]" />` di parent section.
- H1: tambah class `font-display`.
- Search bar form (yang sudah ada): perubahan styling saja (radius `rounded-2xl`, shadow `shadow-card`, focus `shadow-elevated`).
- Tambah tombol pill primer kecil "Search" di kanan toolbar internal search bar.

### 6.3. Feature blocks alternating

Refactor `<FeatureBlock>` jadi varian dengan visual SVG inline. Buat 3 SVG sederhana (Federated/Dedup/FairDiscovery). Layout 2 kolom desktop dengan `flex-row` dan `flex-row-reverse` bergantian.

Section ke-2 pakai `bg-accent`.

### 6.4. Built for builders

Tiap kolom dibungkus card:
```tsx
<div className="rounded-3xl bg-card border border-border/40 p-8 shadow-card">
```

### 6.5. FAQ

Ganti `ChevronDown/Up` dengan ikon `Plus/Minus` lucide.

### 6.6. CTA strip

Section baru sebelum footer:
```tsx
<section className="bg-primary-soft/40 py-20">
  <div className="mx-auto max-w-[760px] px-6 text-center">
    <h2 className="font-display text-[38px] font-semibold tracking-[-0.04em] text-foreground">
      Start exploring 480M scholarly works.
    </h2>
    <Button variant="pillPrimary" size="lg" className="mt-8" onClick={() => onSearch("")}>
      Try it free
    </Button>
  </div>
</section>
```

### 6.7. Footer

Background `bg-card`, border-top `border-border/40`. Tambah tagline kecil di bawah logo: "Made with care for open research."

### 6.8. Verifikasi

```powershell
npm run build
```

`npm run dev` → buka `/`, scroll dari hero sampai footer. Cek di mobile breakpoint.

**Checkpoint:** Landing page selesai. Visual review menyeluruh.

---

## Tahap 7 — Verifikasi akhir

```powershell
# Backend
uv run pytest -v

# Frontend
cd frontend
npm run build
```

Build hijau di kedua sisi, tidak ada test yang baru gagal.

Visual review:
- Landing: semua section, mobile drawer, FAQ, CTA, footer.
- Search: query, filter, sort, paginate, paper detail, export, alert.
- Cross-page: SideNav konsistensi (mengikuti otomatis karena pakai komponen UI yang sama).

---

## Catatan

- Saya tidak akan menyentuh halaman Saved, Alerts, Login, Streamlit UI lama. Mereka akan otomatis ikut menyesuaikan secara token (warna, border, shadow) tapi tata letak halaman tidak berubah. Jika ada visual yang aneh di sana, saya laporkan tapi tidak perbaiki di scope ini.
- Saya tidak akan rebrand backend dari "PaperLens" → "PaperNest". Itu kerjaan terpisah.
- Search bar struktur dan logika tidak diubah.
- Setelah masing-masing tahap, saya akan stop dan kasih tahu — kamu bisa lihat hasilnya di `npm run dev` sebelum kita lanjut.

---

## Estimasi

| Tahap | Estimasi |
|---|---|
| 1. Backend | 10-15 menit |
| 2. Fondasi desain | 10 menit |
| 3. Primitif | 10 menit |
| 4. PaperCard | 20-30 menit |
| 5. SearchPage polish | 20-30 menit |
| 6. LandingPage | 30-45 menit |
| 7. Verifikasi | 5 menit |

Total: ~2 jam kerja agresif. Akan terasa lebih lama karena saya pause di setiap checkpoint.
