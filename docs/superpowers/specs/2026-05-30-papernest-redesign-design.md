# PaperNest Frontend Redesign — Landing & Search

**Tanggal:** 30 Mei 2026
**Cakupan:** Landing page + Search page (bertahap; halaman lain menyusul setelah ini disetujui)
**Pendekatan visual:** Adopsi selektif dari Letters.app — terinspirasi tipografi rounded, aksen pastel biru, dan tombol pill, tapi tetap mengutamakan kepadatan informasi untuk konteks akademik.

---

## 1. Tujuan & non-tujuan

### Tujuan
- Menyatukan bahasa visual landing dan search di sekitar token desain yang konsisten.
- Memberi karakter (hangat, modern, dapat dipercaya) tanpa mengorbankan kemudahan baca abstrak panjang dan kepadatan metadata hasil pencarian.
- Mengangkat fitur journal quality ke permukaan: badge Q1/Q2/Q3/Q4 dan flag predator yang sudah ada di backend tapi belum tampak di UI.

### Non-tujuan
- Mengubah logika pencarian, dedup, ranking, atau routing.
- Mengubah struktur search bar (state, dropdown, submit) — hanya styling.
- Merombak halaman Saved, Alerts, Login, atau PaperDetail logic. Halaman ini akan ikut menyesuaikan secara otomatis karena pakai komponen UI yang sama.
- Menambah dark mode (light mode saja).

### Search bar
Search bar di hero landing dan di header search page dipertahankan strukturnya. Yang berubah hanya: radius, shadow, tipografi, warna, dan bentuk tombol Search di kanan toolbar.

---

## 2. Sistem desain

### 2.1 Warna (CSS custom properties)

```css
:root {
  /* Surface */
  --background: #fafbfc;       /* off-white hangat */
  --foreground: #0f172a;       /* slate-900 */
  --muted-foreground: #475569; /* slate-600 */
  --border: #e2e8f0;           /* slate-200 */
  --card: #ffffff;
  --accent: #eef5fb;           /* section sekunder */

  /* Brand */
  --primary: #1e6bb8;          /* deep ocean blue */
  --primary-soft: #b1d8f4;     /* Blue Rice dari Brand.json */
  --primary-foreground: #ffffff;

  /* Quartile */
  --q1: #16a34a;  /* emerald-600 */
  --q2: #0284c7;  /* sky-600 */
  --q3: #ca8a04;  /* amber-600 */
  --q4: #94a3b8;  /* slate-400 */

  /* Status */
  --predatory: #dc2626;        /* red-600 */
  --destructive: #dc2626;
}
```

### 2.2 Tipografi

- **Heading**: `Open Runde` (400/500/600). Self-hosted dari URL `Style.json.fontLinks` (woff2). Letter-spacing rapat sesuai Style.json (H1 -2.24px, H2 -1.52px, H3 -0.84px, H4 -0.2px).
- **Body & UI**: `Inter Variable` via `@fontsource-variable/inter`. Default 15px / line-height 1.55.
- Tailwind `fontFamily.sans` → Inter. Tailwind `fontFamily.display` → Open Runde.
- Heading di JSX pakai class utility `font-display`. Default elemen lain mewarisi Inter.

Skala (mengikuti Style.json):

| Token | Size / Line-height | Weight | Tracking |
|---|---|---|---|
| `text-h1` | 56 / 67 (mobile 40 / 48) | 600 | -2.24px |
| `text-h2` | 38 / 42 | 600 | -1.52px |
| `text-h3` | 28 / 34 | 500 | -0.84px |
| `text-h4` | 20 / 28 | 500 | -0.2px |
| `text-body` | 15 / 24 | 400 | 0 |
| `text-meta` | 13 / 20 | 400 | 0 |
| `text-eyebrow` | 11 / 16 | 600 (uppercase) | wide |

### 2.3 Bentuk

| Komponen | Radius |
|---|---|
| Paper card | 12px |
| Card section landing | 24px |
| Input | 12px |
| Button standar | 8px |
| Button pill (CTA primer) | 999px |
| Modal / sheet | 16px |

Tombol pill **hanya** untuk: tombol primer hero (Search di hero, Sign in di nav), CTA section, Apply Filters mobile sheet.

### 2.4 Shadow

- `--shadow-card`: `rgba(22,107,197,0.04) 0 1.6px 1.6px, rgba(22,107,197,0.1) 0 7px 7px`
- `--shadow-elevated`: `rgba(22,107,197,0.06) 0 4px 8px, rgba(22,107,197,0.14) 0 12px 24px`
- Section landing besar: tanpa shadow (Style.json `xl: none`).

### 2.5 Spacing

Mengikuti Style.json: `xs: 6px / sm: 16px / md: 24px / lg: 36px / xl: 56px`. Tailwind sudah punya skala dasar (4/8/12/16/24/32/...); kami tambah token semantic via `@apply` saat dibutuhkan.

---

## 3. Komponen primitif

### 3.1 `Button` (`components/ui/button.tsx`)

Variants:
- `primary` (default): bg `--primary`, text putih, hover `--primary` 90%
- `pill-primary`: sama, tapi `rounded-full` dan `px-6 h-10`
- `ghost`: transparan, hover `bg-accent`
- `outline`: border `--border`, hover bg `--accent`
- `link`: teks `--primary`, no bg, underline saat hover

Size: `sm` (h-8), `default` (h-10), `lg` (h-12).

### 3.2 `Badge` (`components/ui/badge.tsx`)

Variants baru:
- `q1`: bg `--q1`, text putih, "Q1"
- `q2`: bg `--q2`, text putih, "Q2"
- `q3`: bg `--q3`, text putih, "Q3"
- `q4`: outline `--q4`, text `--q4`, "Q4"
- `oa`: bg `--primary-soft`, text `--primary`, "OA"
- `predatory`: bg `red-50`, text `red-700`, border `red-200`, ikon warning, label "Predatory"
- `source`: bg `--accent`, text `--muted-foreground`, label sumber (Crossref/OpenAlex/...)
- `count`: bg transparan, label angka kecil

Setiap badge punya `title` untuk tooltip native. Q1-Q4: "Quartile menurut Scimago Journal Rank". Predatory: "Memenuhi heuristik jurnal predator (Beall's List criteria)".

### 3.3 `Input` (`components/ui/input.tsx`)

Radius `12px`, height `40px`, focus ring 2px `--primary/20`, border `--primary/40` saat focus.

---

## 4. Landing page

Path file: `frontend/src/components/LandingPage.tsx`

### 4.1 Top nav (baru)
- Sticky, transparan saat di atas, jadi solid putih + border-bottom saat di-scroll (pakai IntersectionObserver atau scroll listener).
- Kiri: `PaperNestLogoFull` (sudah ada).
- Tengah (desktop ≥ md): link halus ke anchor — "How it works" (#about), "Sources" (#sources), "API" (link ke /docs).
- Kanan: tombol pill primer **Sign in** menuju `/login`.
- Mobile: tetap hamburger drawer kiri (sudah ada di kode).

### 4.2 Hero
- Background: gradient radial `--primary-soft` 0% → transparan 60% di belakang headline (blob lembut, vibe Letters).
- Padding: `pt-32 pb-28` desktop, `pt-20 pb-20` mobile.
- H1 56-68px Open Runde 600, max 760px, copy yang sudah ada dipertahankan ("Your Intelligent Hub for Global Research.").
- Sub-heading 16px Inter regular, max 640px, copy dipertahankan.
- **Search bar** (form pill yang sudah ada) — perubahan styling saja:
  - Container `rounded-2xl` (tetap), border `--border`, shadow `--shadow-card`, focus shadow `--shadow-elevated`.
  - Input dan toolbar internal: tipografi Inter, dropdown teks `--muted-foreground` → `--primary` saat aktif.
  - Tombol di kanan toolbar saat ini hanya icon filter — tambahkan tombol pill primer kecil "Search" dengan ikon `Search` di kiri label (`rounded-full bg-primary text-white px-4 h-8 text-[12px] font-semibold`).
- Trust logos row (Crossref/OpenAlex/DOAJ/arXiv/PubMed) dipertahankan.

### 4.3 Feature blocks (alternating)

3 section yang sudah ada: Federated, Smart Deduplication, Fair & Open Discovery. Sekarang flat & center-only — diubah jadi alternating layout.

Pola: 2 kolom desktop (text-50% + visual-50%), stacked di mobile. Section ke-2 pakai background `--accent` untuk break visual.

Visual sederhana inline SVG (tidak butuh asset baru):
- Federated: 5 lingkaran kecil (sumber-sumber) terhubung garis ke 1 lingkaran besar pusat (PaperNest).
- Dedup: 2 kartu paper bertumpuk dengan ikon merge ✓ di tengah.
- Fair Discovery: 3 bar chart vertikal dengan tinggi berbeda, color graded `--primary-soft → --primary`.

H2 38px Open Runde 600. Body 16px Inter. Padding section `py-24` desktop.

### 4.4 Built for builders

Sudah ada (3 kolom). Perubahan: setiap kolom dibungkus card putih `rounded-3xl p-8 shadow-sm border border-border/40`. Sekarang teks center kosong; dibungkus card jadi punya bentuk dan napas.

### 4.5 FAQ

Tetap accordion. Perubahan kecil: chevron diganti `+` / `−` (lebih halus, lebih editorial). Border-top antar item pakai `--border`.

### 4.6 CTA strip (baru)

Sebelum footer:
- Background `--primary-soft` 30% (subtle), padding lega.
- Headline H2 "Start exploring 480M scholarly works."
- Tombol pill primer "Try it free" → scroll/redirect ke search.

### 4.7 Footer

Struktur 4 kolom dipertahankan. Perubahan: background `--card` (putih bersih), border-top `--border`. Tagline kecil "Made with care for open research." di bawah logo.

---

## 5. Search page

Path file: `frontend/src/pages/SearchPage.tsx`

### 5.1 Sticky header (search bar)

Struktur dipertahankan: 1 row di mobile, 2 row di desktop.

Perubahan styling:
- Container desktop: `rounded-2xl`, border `--border`, shadow `--shadow-card`. Focus state: shadow `--shadow-elevated` + border `--primary/40`.
- Toolbar dropdown (Year/OA/Citations/Sources): tipografi Inter 13px, hover & active state `--primary` (bukan `foreground` generic).
- Tombol "Search" di kanan toolbar (saat ini teks `text-primary` biasa) → **tombol pill primer kecil**: `rounded-full bg-primary text-white px-4 h-8 text-[12px]` dengan ikon `Search`.
- Active filter chips: bg `--primary-soft`, text `--primary` (sebelumnya `Badge variant="secondary"` abu-abu).

Background body halaman: ganti `bg-[#f8f9fb]` → `bg-background` (memakai token).

### 5.2 SearchResultsHeader

Path: `frontend/src/components/SearchResultsHeader.tsx`. Layout: kiri = result count + query echo, kanan = sort dropdown + export menu.
- Sort dropdown jadi pill kecil (`rounded-full px-3 h-8 text-[13px]`) dengan ikon sort kecil.
- Export jadi tombol ghost dengan ikon download.

### 5.3 TrendsChart

Path: `frontend/src/components/TrendsChart.tsx`. Dibungkus card `rounded-2xl p-6 shadow-card border border-border/40`. Recharts bar fill `--primary` opacity 0.85, hover 1.0.

### 5.4 PaperCard (perubahan terbesar)

Path: `frontend/src/components/PaperCard.tsx`. Struktur baru:

```
┌────────────────────────────────────────────────────────────┐
│ [Q1] [OA] [2024] · Nature · Springer       [Predatory?]   │ ← row 1: meta + badges
│                                                            │
│ Paper title that wraps if long, hover → primary color     │ ← row 2: title (Open Runde 18px 600)
│                                                            │
│ Author A, Author B, Author C +5 more                       │ ← row 3: authors (Inter 13px muted)
│                                                            │
│ Lorem ipsum abstract excerpt that line-clamps to 2 lines   │ ← row 4: abstract clamp-2
│ describing what this paper actually says...                │
│                                                            │
│ 📊 1,234 citations  •  Crossref +2 sources       [♡] [⤴] │ ← row 5: footer
└────────────────────────────────────────────────────────────┘
```

Card: `rounded-xl p-5 bg-card border border-border/40 shadow-card hover:shadow-elevated transition-shadow`.

Badge order pada row 1: Quartile (jika ada), OA (jika true), year. Predatory di kanan atas (kanan paling, dengan ikon).

### 5.5 PaperList

Path: `frontend/src/components/PaperList.tsx`. Gap antar kartu `gap-3`. Loading skeleton: card placeholder dengan animasi shimmer halus pakai `--primary-soft`.

### 5.6 PaperDetail (slide-over)

Path: `frontend/src/components/PaperDetail.tsx`. Struktur dipertahankan, perubahan styling:
- Panel bg `--card`, header `border-b --border`.
- Judul Open Runde 24px 600.
- Badges Q/OA/Predatory di atas judul (sama dengan kartu).
- Section heading kecil pakai `text-eyebrow` (11px uppercase tracking-wide muted).
- Tombol Save / View source jadi pill primer.

### 5.7 Pagination

Path: `frontend/src/components/Pagination.tsx`. Nomor halaman jadi button bulat 36px:
- Idle: ghost (text `--muted-foreground`).
- Active: `bg-primary text-white`.
- Hover: `bg-accent text-foreground`.
Prev/Next dengan ikon panah lucide.

### 5.8 Mobile filter bottom sheet

Active state pakai `--primary` & `--primary-soft` (sebelumnya CSS var generic `primary`). Apply button pill primer full-width di bawah.

---

## 6. Perubahan backend (minimal)

### 6.1 `schemas/paper.py`

Tambah satu field di `PaperDTO`:

```python
quartile: str | None = None  # "Q1" | "Q2" | "Q3" | "Q4" | None
```

### 6.2 `services/ranking_service.py`

Saat scoring, ambil `JournalRecord` lewat `JournalQualityService` (sudah dilakukan untuk `score_journal`). Expose quartile ke paper:

```python
record = jq_service._lookup_for_paper(paper)  # ISSN -> title fallback
if record and record.quartile != JournalQuartile.UNKNOWN:
    paper.quartile = record.quartile.value  # "Q1" / "Q2" / ...
```

Karena `score_journal` saat ini hanya mengembalikan float, kita bisa:
- Tambah method publik `get_journal_record(title, issn) -> JournalRecord | None` yang membungkus logika lookup yang sudah ada.
- Atau tambah versi `score_journal_with_record()` yang mengembalikan tuple.

Kami pilih opsi pertama (method baru `get_journal_record`) karena tidak mengubah API method yang sudah dipakai di tes.

Tidak ada migrasi DB. Tidak ada perubahan endpoint. Field `quartile` muncul otomatis di response `/api/v1/search` karena Pydantic mengikuti struktur DTO.

### 6.3 `frontend/src/types/paper.ts`

Tambah field opsional:

```typescript
quartile?: "Q1" | "Q2" | "Q3" | "Q4" | null
```

---

## 7. Setup font

### 7.1 Inter

Install paket: `@fontsource-variable/inter`. Import di `frontend/src/main.tsx`:

```typescript
import "@fontsource-variable/inter"
```

### 7.2 Open Runde

Tidak ada di npm. Kami self-host file woff2 dari `Style.json.fontLinks`:
- Buat folder `frontend/src/assets/fonts/`
- Download 3 file woff2 (weight 400/500/600) saat dev (manual atau via skrip), commit ke repo.
- Definisikan `@font-face` di `index.css`:

```css
@font-face {
  font-family: "Open Runde";
  font-weight: 400;
  src: url("/src/assets/fonts/open-runde-400.woff2") format("woff2");
  font-display: swap;
}
/* ... 500, 600 sama */
```

Catatan: file Open Runde yang ditautkan Style.json adalah aset Framer publik. Bila tidak boleh di-host ulang, fallback ke pasangan `Inter` + `Manrope` (geometric rounded mirip).

---

## 8. Testing & verifikasi

- Tidak ada unit test baru untuk perubahan visual.
- Verifikasi backend:
  - `uv run pytest tests/test_dedup.py -v` (tetap lulus)
  - Tambah test ringan: `tests/test_journal_quality.py` — pastikan paper dengan venue Q1 di response punya `quartile == "Q1"`.
- Verifikasi frontend:
  - `npm run build` harus hijau (tsc + vite build).
  - `npm run dev` — review manual landing & search.
  - Cek visual di breakpoint sm/md/lg.
  - Cek aksesibilitas: kontras `--primary` di atas `--background` (≥ 4.5:1 untuk teks), `--q4` slate-400 di atas putih (cek WCAG AA, fallback `--q4-text` lebih gelap kalau gagal).

---

## 9. Risiko & mitigasi

- **Lookup quartile cocok di semua paper.** Field `venue_issn` tidak selalu terisi dari connector (terutama Crossref kadang missing). Mitigasi: lookup berlapis — pertama by ISSN, fallback by venue title (sudah ada di `JournalQualityService.get_by_title` dengan fuzzy matching). Paper tanpa kecocokan tidak menampilkan badge Q (bukan error).
- **Open Runde hosting.** Jika file Framer di-rotate URL-nya, build tetap aman karena self-hosted setelah commit ke repo. Yang perlu hati-hati: lisensi font (Open Runde adalah open-source, lisensi SIL OFL — aman untuk hosting ulang).
- **Predatory false positive.** Heuristik nama jurnal bisa kena jurnal sah (misal "World Journal of Surgery" sah, tapi pola "world journal of" terdaftar). Mitigasi: badge predatory disertai tooltip "Heuristik berdasarkan Beall's List — verifikasi manual disarankan", supaya user tidak mengambil keputusan absolut dari satu badge.
- **Pemindahan brand "PaperLens" → "PaperNest".** Kode UI sudah pakai PaperNest (`PaperNestIcon`, copy hero). Backend dan README masih pakai "PaperLens". Spec ini tidak menyentuh rename brand backend — biarkan dulu, kerjakan terpisah jika diminta.

---

## 10. Tidak termasuk dalam spec ini (untuk fase berikutnya)

- Halaman SavedPapersPage, AlertsPage, LoginPage redesign.
- Filter `min_quartile` di search (saat ini hanya badge tampil — filter aktif bukan).
- Dark mode.
- Rebrand backend dari PaperLens ke PaperNest.
- Animasi transisi halaman.
- A11y audit menyeluruh dengan reader test.
