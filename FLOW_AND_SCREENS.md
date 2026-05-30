# PaperLens — User Flow, Admin Flow & Desain Tampilan Frontend

Dokumen ini mendefinisikan alur pengguna (user flow), alur admin, serta deskripsi tampilan setiap halaman frontend.

---

## 1. User Flow (Pengguna Biasa)

### 1.1 Flow Diagram

```
                    ┌─────────────┐
                    │  Landing    │
                    │  Page       │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Login   │ │  Ketik   │ │  Klik    │
        │          │ │  Query   │ │  Kategori│
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             ▼            ▼            ▼
        ┌──────────┐ ┌────────────────────────┐
        │ Register │ │  Halaman Pencarian     │
        └────┬─────┘ │  (Topbar + Filter +    │
             │       │   Hasil Jurnal)        │
             ▼       └────────┬───────────────┘
        ┌──────────┐          │
        │ Dashboard│          ├─── Klik paper ──► Detail Paper (Modal)
        │ (search) │          │                    ├── Abstrak lengkap
        └──────────┘          │                    ├── Authors + Afiliasi
                              │                    ├── DOI / PDF link
                              │                    └── Tombol Simpan
                              │
                              ├─── Simpan paper ──► Tersimpan (Tab)
                              │                      ├── Daftar bacaan
                              │                      ├── Hapus
                              │                      └── Ekspor
                              │
                              ├─── Ekspor ──► Download file
                              │                ├── JSON
                              │                ├── CSV
                              │                └── BibTeX
                              │
                              └─── Notifikasi ──► Alert (Tab)
                                                   ├── Buat alert baru
                                                   ├── Aktif/Nonaktif
                                                   └── Hapus alert
```

### 1.2 Langkah-langkah Detail

| # | Aksi User | Halaman | Yang Terjadi |
|---|-----------|---------|--------------|
| 1 | Buka website | Landing Page | Lihat hero, fitur, kategori, contoh hasil |
| 2 | Ketik query di search bar hero | Landing Page | Input aktif, placeholder hilang |
| 3 | Tekan Enter | → Pencarian | Auto-trigger search, langsung tampil hasil |
| 4 | Klik kategori (misal "Ilmu Komputer") | → Pencarian | Query otomatis terisi "computer science", auto-search |
| 5 | Klik "Mulai Cari" (tanpa query) | → Pencarian | Halaman pencarian kosong, search bar fokus di topbar |
| 6 | Atur filter (tahun, sumber, OA, min sitasi) | Pencarian | Hasil ter-filter real-time |
| 7 | Klik judul paper | Pencarian | Modal detail terbuka |
| 8 | Klik "Simpan" di paper | Pencarian | Paper masuk daftar tersimpan |
| 9 | Klik "PDF" / "DOI" | Pencarian | Buka tab baru ke sumber asli |
| 10 | Klik tab "Tersimpan" | Tersimpan | Lihat daftar bacaan, bisa hapus |
| 11 | Klik ekspor (JSON/CSV/BibTeX) | Pencarian/Tersimpan | Download file |
| 12 | Klik tab "Notifikasi" | Notifikasi | Kelola alert pencarian |
| 13 | Klik logo PaperLens | → Landing Page | Kembali ke beranda |

---

## 2. Admin Flow

### 2.1 Flow Diagram

```
                    ┌─────────────┐
                    │ Admin Login │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Dashboard  │
                    │  Admin      │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────────┐
          │                │                    │
          ▼                ▼                    ▼
   ┌─────────────┐  ┌─────────────┐   ┌──────────────┐
   │  Monitoring │  │  Connector  │   │  User        │
   │  Sistem     │  │  Management │   │  Management  │
   └──────┬──────┘  └──────┬──────┘   └──────┬───────┘
          │                │                  │
          ├── Statistik    ├── Status API     ├── List user
          ├── Query log    ├── On/Off source  ├── Aktivitas
          ├── Latency      ├── API key mgmt   ├── Quota
          └── Error rate   └── Rate limit     └── Ban/unban
```

### 2.2 Halaman Admin yang Dibutuhkan

| # | Halaman | Fungsi | Prioritas |
|---|---------|--------|-----------|
| 1 | **Dashboard Overview** | Statistik: total query hari ini, total paper di DB, rata-rata latency, error rate | P0 |
| 2 | **Connector Status** | Health check semua sumber (Crossref, OpenAlex, arXiv, dll), on/off toggle, last response time | P0 |
| 3 | **API Key Management** | Kelola API key per connector (Semantic Scholar, CORE, dll), status valid/expired | P1 |
| 4 | **Query Log** | Riwayat semua pencarian user: query, filter, jumlah hasil, latency, timestamp | P1 |
| 5 | **User Management** | Daftar user terdaftar, aktivitas, status akun (jika multi-user) | P2 |
| 6 | **Cache Management** | Ukuran cache, TTL setting, tombol purge cache | P2 |
| 7 | **Alert Monitor** | Semua alert aktif, jadwal, status terakhir, error log | P2 |
| 8 | **System Config** | Ranking weights, dedup threshold, rate limit setting | P3 |

---

## 3. Desain Tampilan Frontend — Per Halaman

### 3.1 Landing Page (Sudah Ada)

**Status: ✅ Selesai**

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens    Beranda  Fitur  Cara Kerja  [Cari] │  ← Navbar
├──────────────────────────────────────────────────────────┤
│                                                          │
│     Temukan jurnal ilmiah lebih cepat, akurat,          │  ← Hero
│     dan relevan.                                         │
│                                                          │
│     [🔍 Cari tema, judul, topik, atau penulis...    ]   │  ← Search bar fungsional
│                                                          │
│     Didukung oleh: Crossref  DOAJ  OpenAlex             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  200M+ Paper  │  8 Sumber  │  Gratis  │  Export Ready   │  ← Stats
├──────────────────────────────────────────────────────────┤
│  [🧠] Pencarian  [⚙️] Filter  [👁] Pratinjau            │  ← Features (6 card)
│  [🔬] Metode     [🔗] Ekspor  [📈] Trending             │
├──────────────────────────────────────────────────────────┤
│  Kenapa Memilih PaperLens                                │  ← WhyChoose (3 card)
│  [Relevan]  [Antarmuka Fokus]  [Siap Digunakan]         │
├──────────────────────────────────────────────────────────┤
│  Jelajahi Kategori                                       │  ← Categories (7 btn)
│  [Kesehatan] [Pendidikan] [Teknik] [Komputer] ...       │
├──────────────────────────────────────────────────────────┤
│  Contoh Hasil Pencarian                                  │  ← SearchResults (2 card)
│  ┌─ Paper Card ──────────────────────────────────┐      │
│  │  Title · Authors · Journal · Year · DOI       │      │
│  └───────────────────────────────────────────────┘      │
├──────────────────────────────────────────────────────────┤
│  Testimonials (2 card)                                   │
├──────────────────────────────────────────────────────────┤
│  [CTA] Siap menemukan jurnal? → [Mulai Cari Sekarang]  │
├──────────────────────────────────────────────────────────┤
│  Footer (dark green)                                     │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Halaman Pencarian (Search View)

**Status: ✅ Selesai (baru diupdate)**

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens  Pencarian  Tersimpan  Notifikasi     │  ← Topbar (hijau konsisten)
│                           [🔍 search bar compact     ]  │
├──────────────────────────────────────────────────────────┤
│         │                                                │
│ FILTER  │  3 hasil dalam 1200 ms      [JSON][CSV][BibTeX]│
│         │                                                │
│ Sumber  │  ┌─ Paper ────────────────────────────────┐   │
│ ☑ arxiv │  │  2023 · Nature · Open Access            │   │
│ ☑ core  │  │  GNN-DTI: Drug-Target Interaction...    │   │  ← Serif title
│ ☑ cross │  │  Smith J., Lee K. et al.                │   │
│ ☑ doaj  │  │  Abstract: Lorem ipsum...               │   │
│         │  │  📚 142  ⭐ 0.87  crossref, openalex    │   │
│ Tahun   │  │  [Simpan] [PDF] [DOI] [Detail]          │   │
│ [2020]  │  └─────────────────────────────────────────┘   │
│ [2026]  │                                                │
│         │  ┌─ Paper ────────────────────────────────┐   │
│ Akses   │  │  (paper berikutnya...)                  │   │
│ [Any ▼] │  └─────────────────────────────────────────┘   │
│         │                                                │
│ Min.Cite│                                                │
│ [0    ] │                                                │
│         │                                                │
│ Venue   │                                                │
│ [     ] │                                                │
│         │                                                │
│ [Reset] │                                                │
└──────────────────────────────────────────────────────────┘
```

**Catatan desain:**
- Topbar **identik** dengan landing page (logo, font, warna)
- Search bar compact di topbar (bukan hero terpisah)
- Sidebar filter di kiri, sticky scroll
- Hasil di kanan, single-column divider
- Paper card: year · venue · OA badge di atas, serif title, authors, abstract truncated, metrics + actions

### 3.3 Halaman Pencarian — Empty State (Tanpa Query)

**Status: ✅ Selesai**

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens  Pencarian  Tersimpan  Notifikasi     │
│                           [🔍 search bar compact     ]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                     📖 (icon besar)                      │
│                                                          │
│              Mulai pencarian Anda                        │
│                                                          │
│    Ketik kata kunci di search bar atas, lalu tekan      │
│    Enter untuk menemukan jurnal dari 8 sumber            │
│    akademik terpercaya.                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.4 Detail Paper (Modal)

**Status: ✅ Ada, perlu update styling**

```
┌──────────────────────────────────────────────────────┐
│                                                [✕]   │
│  GNN-DTI: Drug-Target Interaction via GNN            │  ← Judul besar
│                                                       │
│  [Open Access]  [📚 142 citations]  [Score: 0.87]    │  ← Badges
│  [2023]  [Nature Machine Intelligence]               │
│                                                       │
│  Authors                                              │
│  Jane Smith, John Lee, Maria Garcia                  │
│                                                       │
│  Abstract                                             │
│  Graph neural networks have emerged as powerful...    │  ← Full abstract
│                                                       │
│  Topics                                               │
│  [GNN] [drug discovery] [bioinformatics]             │
│                                                       │
│  Sources                                              │
│  crossref · openalex · semantic_scholar              │
│                                                       │
│  [📄 PDF]  [🔗 DOI]  [💾 Simpan]                    │  ← Action buttons
└──────────────────────────────────────────────────────┘
```

### 3.5 Halaman Tersimpan (Saved)

**Status: ✅ Selesai**

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens  Pencarian  Tersimpan(3)  Notifikasi  │
│                           [🔍 search bar compact     ]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Paper Tersimpan                    [JSON][CSV][BibTeX]  │
│  3 paper dalam daftar bacaan Anda                       │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  ┌─ Paper + [🗑 hapus hover] ────────────────────────┐  │
│  │  2023 · Nature · OA                                │  │
│  │  GNN-DTI: Drug-Target Interaction...               │  │
│  │  Smith J., Lee K.                                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Paper + [🗑] ────────────────────────────────────┐  │
│  │  ...                                               │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Empty state (belum ada paper):**
```
│              🔖 (icon besar)                            │
│        Belum ada paper tersimpan                        │
│  Simpan paper dari hasil pencarian untuk                │
│  membangun daftar bacaan Anda.                          │
│            [Mulai pencarian]                            │
```

### 3.6 Halaman Notifikasi / Alert

**Status: ✅ Ada, perlu update styling**

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens  Pencarian  Tersimpan  Notifikasi     │
│                           [🔍 search bar compact     ]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Notifikasi Pencarian                                    │
│  Dapatkan pemberitahuan saat ada paper baru.            │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │  [Kata kunci alert baru...          ] [Buat] │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  ┌─ Alert Card ──────────────────────────────────────┐  │
│  │  "machine learning healthcare"                     │  │
│  │  Frekuensi: Harian  │  Status: ● Aktif            │  │
│  │  Terakhir: 2 jam lalu                              │  │
│  │  [⏸ Pause]  [🗑 Hapus]                            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.7 Login / Register

**Status: ✅ Ada, perlu update styling**

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ┌─────────────────────┬────────────────────────────┐  │
│   │                     │                            │  │
│   │  ✓ Multi-source     │   Masuk ke PaperLens      │  │
│   │    paper search     │                            │  │
│   │  ✓ Daftar bacaan    │   Email                    │  │
│   │    tersimpan        │   [_________________]      │  │
│   │  ✓ Ekspor siap      │                            │  │
│   │    sitasi           │   Kata Sandi               │  │
│   │                     │   [_________________]      │  │
│   │                     │                            │  │
│   │                     │   [     Masuk      →]      │  │
│   │                     │                            │  │
│   │                     │   Belum punya akun?        │  │
│   │                     │   Daftar sekarang          │  │
│   └─────────────────────┴────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Halaman Admin (Belum Ada — Perlu Dibuat)

### 4.1 Admin Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] PaperLens Admin    Dashboard │ Connector │ Log  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │  1,247 │  │  847ms │  │ 15,203 │  │  0.3%  │        │
│  │ Query  │  │  Avg   │  │ Paper  │  │ Error  │        │
│  │ Hari   │  │ Laten. │  │ di DB  │  │ Rate   │        │
│  │ Ini    │  │        │  │        │  │        │        │
│  └────────┘  └────────┘  └────────┘  └────────┘        │
│                                                          │
│  Pencarian Terbaru                                       │
│  ─────────────────────────────────────────────────────  │
│  │ Query                    │ Hasil │ Latency │ Waktu │ │
│  │ "machine learning"       │   25  │  1.2s   │ 10:05 │ │
│  │ "neural network drug"    │   18  │  2.1s   │ 10:02 │ │
│  │ "climate change impact"  │   25  │  0.9s   │ 09:58 │ │
│                                                          │
│  Grafik Query per Jam (line chart)                       │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Admin — Connector Status

```
┌──────────────────────────────────────────────────────────┐
│  Status Connector Sumber Data                            │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  │ Sumber           │ Status  │ Latency │ Key  │ Aktif │ │
│  │ Crossref         │ ● Sehat │  320ms  │ —    │ [✓]  │ │
│  │ OpenAlex         │ ● Sehat │  480ms  │ —    │ [✓]  │ │
│  │ arXiv            │ ● Sehat │  1.2s   │ —    │ [✓]  │ │
│  │ Semantic Scholar │ ⚠ Lambat│  3.4s   │ ✓    │ [✓]  │ │
│  │ PubMed           │ ● Sehat │  890ms  │ —    │ [✓]  │ │
│  │ DOAJ             │ ● Sehat │  450ms  │ —    │ [✓]  │ │
│  │ CORE             │ ✕ Error │  —      │ ✕    │ [ ]  │ │
│  │ Europe PMC       │ ● Sehat │  670ms  │ —    │ [✓]  │ │
│                                                          │
│  [🔄 Refresh Status]  [⚙ Konfigurasi Rate Limit]       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Yang Belum Ada & Rekomendasi Pengembangan

### Frontend — Belum Ada (Harus Dibuat)

| # | Halaman / Fitur | Prioritas | Keterangan |
|---|-----------------|-----------|------------|
| 1 | **Admin Dashboard** | P1 | Monitoring statistik, query log, connector status |
| 2 | **Admin Login** | P1 | Autentikasi terpisah untuk admin |
| 3 | **Sorting hasil pencarian** | P0 | Dropdown: Relevansi / Tahun / Sitasi |
| 4 | **Pagination** | P0 | Load more atau numbered pages |
| 5 | **Recent search dropdown** | P1 | History dari localStorage, muncul saat fokus search bar |
| 6 | **Toast notification** | P1 | Feedback saat simpan/hapus/ekspor berhasil/gagal |
| 7 | **Mobile hamburger menu** | P1 | Navbar responsive untuk mobile |
| 8 | **Dark mode toggle** | P2 | CSS variables sudah ada di index.css |
| 9 | **Paper comparison** | P3 | Bandingkan 2-3 paper side by side |
| 10 | **Tag/folder saved papers** | P2 | Organisasi daftar bacaan |
| 11 | **Keyboard shortcut** | P3 | Ctrl+K = fokus search, Esc = tutup modal |
| 12 | **Profile / Settings** | P2 | Ganti password, preferensi, hapus akun |

### Backend — Sudah Ada vs Belum Ada

| Fitur Backend | Status | Keterangan |
|---------------|--------|------------|
| POST /search | ✅ Ada | Multi-source, dedup, ranking |
| GET /saved, POST /saved, DELETE /saved | ✅ Ada | CRUD saved papers |
| POST /alerts, GET /alerts, DELETE /alerts | ✅ Ada | CRUD alerts |
| POST /export | ✅ Ada | JSON, CSV, BibTeX |
| GET /health | ✅ Ada | Health check |
| GET /sources/status | ❌ Belum | Health check per connector |
| Auth (login/register/JWT) | ❌ Belum | User management |
| Admin endpoints | ❌ Belum | Query log, stats, config |
| GET /papers/{id}/similar | ❌ Belum | Rekomendasi paper |
| GET /trends | ❌ Belum | Trend dashboard data |
| Sorting endpoint (sort_by param) | ❌ Belum | Perlu di search |
| Pagination (offset param) | ❌ Belum | Perlu di search |

---

## 6. Rekomendasi Urutan Pengembangan

### Phase 1 — Fungsionalitas Inti (1-2 minggu)

1. Sorting di hasil pencarian (frontend + backend `sort_by` param)
2. Pagination (frontend "Load More" + backend `offset`)
3. Toast notification (feedback visual)
4. Mobile hamburger menu
5. Kategori landing page → klik = auto-search

### Phase 2 — Auth & Admin (2-3 minggu)

6. Backend: JWT auth (login/register)
7. Frontend: Form login/register terhubung backend
8. Protected routes (saved & alerts butuh login)
9. Admin dashboard sederhana (stats + connector status)
10. Admin: GET /sources/status endpoint

### Phase 3 — UX Enhancement (2-3 minggu)

11. Recent search dropdown
12. Keyboard shortcuts
13. Tag/folder saved papers
14. Dark mode toggle
15. Paper detail: related papers / "Similar"
16. Error boundary (prevent blank page)

### Phase 4 — Advanced (Future)

17. Paper comparison view
18. Trend dashboard (chart)
19. AI summarizer
20. Citation network visualization
