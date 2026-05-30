# Research Paper Intelligence Aggregator (RPIA)

Dokumen planning lengkap project portfolio mahasiswa Informatika.
Bahasa: Indonesia. Versi: v1.0.

---

## 1. Nama Project & Positioning Produk

### Nama yang direkomendasikan
- **Utama:** `PaperLens` — "Lens for academic literature"
- **Alternatif:**
  - `ScholarMesh` — menekankan agregasi multi-source.
  - `CiteHub` — fokus ke citation graph.
  - `RPIA` (Research Paper Intelligence Aggregator) — nama internal/teknis.

### Value Proposition
> "Satu pencarian, banyak sumber bereputasi, hasil ter-rangking dan bebas duplikat — dari Crossref sampai arXiv, dalam satu dashboard."

PaperLens membantu user menemukan paper relevan **lebih cepat 5–10x** dibanding pencarian manual karena:
1. **Multi-source aggregation:** 1 query → 10+ sumber akademik resmi.
2. **Smart deduplication:** paper yang sama dari arXiv, Crossref, OpenAlex hanya muncul 1 kali.
3. **Composite ranking:** kombinasi relevansi + sitasi + recency + venue + OA.
4. **Metadata-rich:** abstract, citation count, DOI, OA link, venue, semua di satu kartu.
5. **Export-ready:** CSV, JSON, BibTeX, Markdown table — siap untuk skripsi/literature review.

### Kenapa lebih baik dari search manual?
| Search Manual (Google Scholar dkk.) | PaperLens |
|---|---|
| 1 sumber per pencarian | 10+ sumber paralel |
| Duplikat banyak | Auto-dedup by DOI/arXiv/title |
| Tidak bisa filter advanced (OA, citation min) | Filter granular |
| Tidak ada export structured | CSV/JSON/BibTeX/MD |
| Tidak ada scoring transparan | Composite score terbuka |
| Tidak ada alert | Alert email/Telegram/Discord |

---

## 2. Problem Statement

### Masalah utama user
1. **Information overload:** ribuan paper baru per hari, sulit memilah yang relevan.
2. **Source fragmentation:** harus buka Scholar, arXiv, PubMed, IEEE secara terpisah.
3. **Duplicate noise:** 1 paper bisa muncul 5x (preprint arXiv + Crossref + OpenAlex + venue + repository).
4. **Metadata inkonsisten:** citation count Scholar ≠ OpenAlex ≠ Semantic Scholar.
5. **Tidak ada ranking transparan:** user tidak tahu kenapa paper A muncul di atas paper B.
6. **Susah filter open access:** banyak paper berbayar, susah dicek mana yang gratis legal.

### Pain point spesifik
- **Mahasiswa skripsi:** bingung memilih 30–50 referensi berkualitas dari ribuan hasil.
- **Peneliti:** literature review makan waktu mingguan, sulit tracking paper baru.
- **Dosen:** monitoring tren riset di bidangnya butuh effort manual besar.
- **Developer AI/ML:** mencari dataset/model SOTA tersebar di banyak venue.

### Kenapa multi-source aggregator lebih baik?
- **Coverage lebih luas:** Crossref (metadata DOI), OpenAlex (citation graph), arXiv (preprint terbaru), PubMed (biomedical), DOAJ (OA jurnal).
- **Cross-validation citation:** ambil max/median dari beberapa sumber → lebih akurat.
- **Deduplication cerdas:** 1 paper = 1 entry, dengan metadata terlengkap dari gabungan sumber.
- **Open access detection:** OpenAlex + DOAJ + CORE + Europe PMC memberikan info OA yang lengkap.

---

## 3. Scope MVP

### WAJIB (MVP — 6 minggu)
1. Search paper by keyword (multi-source paralel).
2. Filter: tahun, sumber, OA, min citation.
3. Deduplication berbasis DOI + arXiv ID + normalized title.
4. Composite ranking score.
5. Paper detail page (title, authors, abstract, year, DOI, source, citation, URL, OA PDF).
6. Export: CSV, JSON, BibTeX, Markdown table.
7. Connector: **Crossref, OpenAlex, arXiv, Semantic Scholar** (4 sumber utama, gratis, no key wajib).
8. REST API + Streamlit UI sederhana.
9. SQLite local cache.

### TIDAK PERLU dulu (post-MVP)
1. AI summarizer (butuh OpenAI key / GPU).
2. Auto literature review generator.
3. Citation network visualization (D3/Cytoscape).
4. Email/Telegram/Discord alert (butuh worker + SMTP).
5. Trend tracker dashboard.
6. Research gap detection.
7. Dataset/model extraction (NER specialized).
8. Comparison matrix antar paper.
9. User authentication & multi-tenant.
10. Connector berbayar (IEEE, Springer, Scopus) — masuk fase 2.

### Prioritas pengembangan
```
P0 (must have)   : search, dedup, ranking, detail, export, 4 connector core
P1 (should have) : PubMed, DOAJ, CORE, Europe PMC connector
P2 (nice to have): AI summary, alert, trend dashboard
P3 (future)      : IEEE, Springer, Scopus, citation viz, gap detection
```

---

## 4. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Streamlit/React)                  │
│   Search │ Results │ Detail │ Saved │ Trend │ Export │ Alerts    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST/JSON
┌─────────────────────────────▼───────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│   /search /papers/{id} /export /alerts /recommend /trends        │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌───────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐
│ Connector │  │  Dedup     │  │ Ranking  │  │  AI Module   │
│   Layer   │  │  Engine    │  │  Engine  │  │  (optional)  │
│           │  │            │  │          │  │              │
│ Crossref  │  │ DOI/arXiv  │  │ relevance│  │ Summarizer   │
│ OpenAlex  │  │ title norm │  │ recency  │  │ Keyword ext. │
│ arXiv     │  │ fuzzy      │  │ citation │  │ Method/      │
│ Sem.Schol.│  │ author+yr  │  │ venue    │  │  Dataset NER │
│ PubMed    │  │            │  │ OA       │  │              │
│ DOAJ      │  └────────────┘  └──────────┘  └──────────────┘
│ CORE      │
│ EuropePMC │  ┌──────────────────────────────────────────┐
│ IEEE      │  │   Worker / Scheduler (APScheduler)        │
│ Springer  │  │  - cache refresh                          │
└─────┬─────┘  │  - alert dispatcher                       │
      │        │  - trend snapshot harian                  │
      │        └──────────────────────────────────────────┘
      ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATABASE (SQLite MVP / PostgreSQL prod)             │
│   papers │ authors │ paper_authors │ sources │ search_queries    │
│   paper_metrics │ paper_topics │ alerts │ saved_papers │ cache   │
└─────────────────────────────────────────────────────────────────┘
```

### Komponen
- **Backend (FastAPI):** REST API, request validation (Pydantic), async I/O.
- **Database:** SQLite (MVP), PostgreSQL (production); SQLAlchemy ORM.
- **Worker/Scheduler:** APScheduler (MVP) atau Celery+Redis (scale).
- **API Connector Layer:** abstract base + concrete per source.
- **Deduplication Engine:** rule-based pipeline (DOI → arXiv → title → fuzzy).
- **Ranking Engine:** composite scoring; pluggable weights.
- **Frontend:** Streamlit (MVP cepat) atau React+Tailwind (production).
- **AI Module (opsional):** OpenAI API atau local LLM (Ollama+Llama3) untuk summarization.

---

## 5. Tech Stack

| Layer | Tools | Alasan |
|---|---|---|
| Bahasa | Python 3.11+ | ekosistem academic API + ML |
| Web framework | **FastAPI** | async, auto-docs OpenAPI, fast |
| ORM | SQLAlchemy 2.x | mature, supports both SQLite/PG |
| DB | SQLite (MVP) → PostgreSQL | simple → scalable |
| HTTP client | **httpx** (async) | async + connection pooling |
| Data ops | pandas, numpy | normalisasi, export |
| Scheduler | APScheduler | tidak butuh Redis untuk MVP |
| Frontend | **Streamlit** (MVP), React+Tailwind+shadcn (v2) | cepat → polished |
| Cache | sqlite cache table + `cachetools` | tanpa Redis di MVP |
| Fuzzy matching | `rapidfuzz` | dedup title fast |
| Validation | Pydantic v2 | schema kuat |
| Testing | pytest, pytest-asyncio, httpx mock | standar |
| Dependency mgmt | `uv` atau `poetry` | reproducible |
| Container | Docker (opsional) | deploy mudah |
| AI (opsional) | OpenAI API / Ollama+Llama3 / `transformers` | summary |
| Logging | `loguru` | simple |
| BibTeX | `bibtexparser` | export |

---

## 6. Struktur Folder

```
paperlens/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # settings (pydantic-settings)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # dependencies (db session, auth)
│   │   ├── routes_search.py
│   │   ├── routes_papers.py
│   │   ├── routes_export.py
│   │   ├── routes_alerts.py
│   │   └── routes_trends.py
│   ├── core/
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── rate_limit.py
│   └── db/
│       ├── base.py
│       ├── session.py
│       └── migrations/          # alembic
├── connectors/
│   ├── __init__.py
│   ├── base.py                  # BaseConnector ABC
│   ├── crossref.py
│   ├── openalex.py
│   ├── semantic_scholar.py
│   ├── arxiv.py
│   ├── pubmed.py
│   ├── doaj.py
│   ├── core_ac.py
│   ├── europepmc.py
│   ├── ieee.py
│   └── springer.py
├── services/
│   ├── __init__.py
│   ├── search_service.py        # orchestrator multi-source
│   ├── dedup_service.py
│   ├── ranking_service.py
│   ├── export_service.py
│   ├── alert_service.py
│   ├── recommendation_service.py
│   ├── trend_service.py
│   └── ai/
│       ├── summarizer.py
│       └── extractor.py         # dataset/method NER
├── models/                      # SQLAlchemy ORM
│   ├── __init__.py
│   ├── paper.py
│   ├── author.py
│   ├── source.py
│   ├── metric.py
│   ├── topic.py
│   ├── alert.py
│   └── saved_paper.py
├── schemas/                     # Pydantic
│   ├── __init__.py
│   ├── paper.py
│   ├── search.py
│   └── export.py
├── workers/
│   ├── __init__.py
│   ├── scheduler.py             # APScheduler bootstrap
│   ├── jobs_alert.py
│   ├── jobs_cache_refresh.py
│   └── jobs_trend_snapshot.py
├── utils/
│   ├── __init__.py
│   ├── normalize.py             # title normalization, DOI clean
│   ├── similarity.py            # fuzzy ratio
│   ├── http.py                  # retry, backoff, cache
│   └── bibtex.py
├── frontend/
│   ├── streamlit_app.py         # MVP UI
│   └── react/                   # v2 (optional)
├── tests/
│   ├── conftest.py
│   ├── test_connectors/
│   ├── test_dedup.py
│   ├── test_ranking.py
│   ├── test_api.py
│   └── fixtures/
├── scripts/
│   ├── seed_sources.py
│   └── benchmark_search.py
├── .env.example
├── pyproject.toml
├── README.md
├── docker-compose.yml           # opsional
└── Dockerfile                   # opsional
```

---

## 7. Desain Database

### `sources`
| Field | Tipe | Keterangan |
|---|---|---|
| id | INT PK | |
| name | VARCHAR | crossref, openalex, arxiv, dst |
| base_url | VARCHAR | |
| reputation_score | FLOAT | 0–1, manual seed |
| rate_limit_per_sec | INT | |
| requires_api_key | BOOL | |
| is_active | BOOL | |

### `papers`
| Field | Tipe | Keterangan |
|---|---|---|
| id | UUID/INT PK | |
| doi | VARCHAR UNIQUE NULL | dinormalisasi lowercase |
| arxiv_id | VARCHAR UNIQUE NULL | |
| pubmed_id | VARCHAR NULL | |
| title | TEXT | original |
| title_normalized | TEXT INDEX | lowercase, no punctuation, stopword off |
| abstract | TEXT NULL | |
| year | INT INDEX | |
| publication_date | DATE NULL | |
| venue | VARCHAR NULL | journal/conference |
| venue_issn | VARCHAR NULL | |
| publisher | VARCHAR NULL | |
| language | VARCHAR(8) NULL | |
| is_open_access | BOOL | |
| oa_url | VARCHAR NULL | PDF link if OA |
| landing_url | VARCHAR | |
| primary_source_id | FK sources | first ingested |
| created_at, updated_at | TIMESTAMP | |

### `authors`
| Field | Tipe |
|---|---|
| id | PK |
| full_name | VARCHAR |
| orcid | VARCHAR NULL UNIQUE |
| affiliation | VARCHAR NULL |
| openalex_id | VARCHAR NULL |

### `paper_authors`
| paper_id | FK | |
| author_id | FK | |
| position | INT | urutan author |
| is_corresponding | BOOL | |
PK composite (paper_id, author_id, position).

### `paper_metrics`
Per-source metric (karena beda sumber beda angka):
| paper_id | FK |
| source_id | FK |
| citation_count | INT |
| influential_citation_count | INT NULL |
| reference_count | INT NULL |
| fetched_at | TIMESTAMP |
PK (paper_id, source_id).

### `paper_topics`
| paper_id | FK |
| topic | VARCHAR | concept dari OpenAlex / keyword |
| score | FLOAT |
| source | VARCHAR | openalex / arxiv-cat / extracted |

### `search_queries`
Audit + cache key:
| id | PK |
| query_text | TEXT |
| filters_json | JSON |
| user_id | NULL (multi-user later) |
| executed_at | TIMESTAMP |
| result_count | INT |
| latency_ms | INT |

### `alerts`
| id | PK |
| user_id | NULL/FK |
| query_text | TEXT |
| filters_json | JSON |
| channel | ENUM(email, telegram, discord) |
| target | VARCHAR |
| frequency | ENUM(daily, weekly) |
| last_run_at | TIMESTAMP |
| is_active | BOOL |

### `saved_papers`
| id | PK |
| user_id | NULL/FK |
| paper_id | FK |
| tag | VARCHAR NULL |
| note | TEXT NULL |
| saved_at | TIMESTAMP |

### `api_cache` (opsional, MVP friendly)
| cache_key | PK (hash query+source) |
| response_json | TEXT |
| expires_at | TIMESTAMP |

---

## 8. Data Pipeline

```
[USER] → query "graph neural network drug discovery", filter year>=2022, OA=true
   │
   ▼
[FastAPI /search]
   │
   ▼
[SearchService.run(query, filters)]
   │
   ├─► async dispatch ke N connector secara paralel (asyncio.gather)
   │      ├─ CrossrefConnector.search(...)
   │      ├─ OpenAlexConnector.search(...)
   │      ├─ ArxivConnector.search(...)
   │      └─ SemanticScholarConnector.search(...)
   │
   ├─► tiap connector: rate-limit guard → HTTP call → normalize() → List[PaperDTO]
   │
   ▼
[Normalisasi global]  → semua paper jadi schema kanonik PaperDTO
   │
   ▼
[DedupService.dedupe(papers)]
   │   prioritas: DOI > arXiv ID > title_norm > fuzzy(title)+author+year
   │   merge metadata: ambil yang non-null/terbaru/tertinggi (citation = max)
   │
   ▼
[RankingService.score(papers, query)]
   │   hitung 5 sub-skor → final_score
   │
   ▼
[Persistence]  upsert ke `papers`, `authors`, `paper_metrics`, `paper_topics`
   │   simpan `search_queries` row untuk audit
   │
   ▼
[Response]  sorted by final_score desc, paginated
   │
   ▼
[Frontend renders]   list + detail + button export
   │
   ▼
[ExportService]  CSV / JSON / BibTeX / Markdown
```

---

## 9. Desain Scoring / Ranking

```
final_score =
    relevance_score   * 0.35 +
    recency_score     * 0.20 +
    citation_score    * 0.20 +
    venue_score       * 0.15 +
    open_access_score * 0.10
```

Semua sub-skor dinormalisasi ke `[0, 1]`.

### relevance_score (0–1)
- BM25/TF-IDF antara `query` vs concat(`title` + `abstract` + `keywords`).
- MVP simple: `rapidfuzz.token_set_ratio` + bonus jika query token muncul di title.
- Formula MVP:
  ```
  title_match = token_set_ratio(query, title) / 100
  abs_match   = token_set_ratio(query, abstract[:500]) / 100
  relevance   = 0.7 * title_match + 0.3 * abs_match
  ```
- Upgrade: sentence-transformers cosine similarity (MiniLM).

### recency_score (0–1)
Decay eksponensial:
```
age_years = current_year - paper.year
recency_score = exp(-age_years / 5)     # half-life ~3.5 tahun
```
- 2025 → 1.0, 2020 → ~0.37, 2015 → ~0.13.

### citation_score (0–1)
Log-normalisasi karena distribusi sitasi sangat skewed:
```
citation_score = min(1.0, log10(1 + citation_count) / log10(1 + CAP))
CAP = 1000   # paper dengan ≥1000 sitasi → 1.0
```

### venue_score (0–1)
Lookup table (seed manual + augment dari OpenAlex `host_venue.is_in_doaj`, h-index, SJR):
```
top_tier (Nature, Science, NeurIPS, CVPR, ACL, ICML, ICLR, ...) → 1.0
strong   (IEEE TPAMI, JMLR, ACM, well-known journals)            → 0.8
mid      (indexed Scopus/WoS)                                     → 0.6
preprint (arXiv only, no venue)                                   → 0.4
unknown  / predator-suspect                                       → 0.2
```

### open_access_score (0–1)
```
OA gold (DOAJ, official OA journal)     → 1.0
OA green (repository, arXiv, EuropePMC) → 0.8
OA bronze (free at publisher, no license)→ 0.6
closed                                   → 0.0
```

> Bobot bersifat **pluggable** — user bisa override per-search untuk eksperimen.

---

## 10. Strategi Deduplication

Pipeline berurutan (early-exit jika match):

1. **DOI exact match** (setelah normalisasi: lowercase, strip `https://doi.org/`, trim).
2. **arXiv ID exact match** (normalisasi versi: `2301.12345v3` → `2301.12345`).
3. **PubMed ID exact match.**
4. **Normalized title exact match:**
   - lowercase
   - hapus tanda baca, multiple spaces → single space
   - hapus stopwords ringan (a, an, the, of, on, in, for)
   - remove diacritics (`unicodedata.NFKD`)
5. **Fuzzy title similarity** (`rapidfuzz.token_set_ratio ≥ 92`) **AND** (`year diff ≤ 1`).
6. **Author+year+title-prefix:** first author lastname match + same year + title_norm prefix(40 chars) similarity ≥ 90.

### Merge strategy ketika duplikat ditemukan
- `doi`, `arxiv_id`, `pubmed_id`: ambil non-null (union).
- `abstract`: ambil yang **lebih panjang**.
- `citation_count`: simpan **per-source** di `paper_metrics`; tampilkan **max** di UI.
- `authors`: union by ORCID atau full_name normalized.
- `is_open_access`: OR logic (true jika ada satu sumber bilang OA).
- `oa_url`: prioritaskan publisher → DOAJ → EuropePMC → arXiv.
- `sources`: simpan list semua sumber yang menemukan paper ini (untuk badge UI: "found in 4 sources").

---

## 11. API Connector Design

### Base interface
```python
# connectors/base.py
from abc import ABC, abstractmethod
from typing import Optional
from schemas.paper import PaperDTO, SearchFilters

class BaseConnector(ABC):
    name: str
    base_url: str
    rate_limit_per_sec: float = 1.0
    requires_api_key: bool = False

    def __init__(self, api_key: Optional[str] = None, http_client=None):
        self.api_key = api_key
        self.http = http_client  # shared httpx.AsyncClient

    @abstractmethod
    async def search(self, query: str, filters: SearchFilters, limit: int = 25) -> list[PaperDTO]: ...

    @abstractmethod
    async def get_by_doi(self, doi: str) -> Optional[PaperDTO]: ...

    @abstractmethod
    def normalize(self, raw: dict) -> PaperDTO: ...

    async def handle_rate_limit(self):
        """Token-bucket / sleep aware exponential backoff."""
        ...

    async def health_check(self) -> bool:
        """Ping endpoint untuk dashboard status."""
        ...
```

### Catatan per connector
| Connector | Endpoint utama | Auth | Catatan |
|---|---|---|---|
| Crossref | `api.crossref.org/works` | none (mailto polite) | metadata terlengkap; quality field `is-referenced-by-count` |
| OpenAlex | `api.openalex.org/works` | none (mailto polite) | citation graph + concepts + OA status |
| Semantic Scholar | `api.semanticscholar.org/graph/v1` | API key (free) | recommendations, influential citations |
| arXiv | `export.arxiv.org/api/query` (Atom XML) | none | parse pakai `feedparser` |
| PubMed | E-Utilities `eutils.ncbi.nlm.nih.gov` | optional key | 2-step: esearch → efetch |
| DOAJ | `doaj.org/api/v2/search` | none | hanya OA journals |
| CORE | `api.core.ac.uk/v3` | API key (free) | full text OA |
| Europe PMC | `ebi.ac.uk/europepmc/webservices/rest/search` | none | life sciences |
| IEEE Xplore | `ieeexploreapi.ieee.org` | API key (paid quota) | engineering |
| Springer | `api.springernature.com` | API key (free tier) | OA Springer |

### Polite usage tips
- Set `User-Agent: PaperLens/0.1 (mailto:you@example.com)` (Crossref/OpenAlex prefer this).
- Honor `Retry-After` header.
- Cache responses 24 jam (kunci = hash(source, endpoint, params)).

---

## 12. Frontend / Dashboard

### Halaman MVP (Streamlit)
1. **Search Page**
   - Input: query, year range slider, source multi-select, OA toggle, min citation, venue contains.
   - Tombol: "Search".
2. **Result List**
   - Card per paper: title, authors, year, venue, citation badge, OA badge, source badges, score.
   - Sort dropdown: score | year | citation.
   - Pagination 25/page.
   - Bulk select → "Add to saved" / "Export selected".
3. **Paper Detail**
   - Full abstract, all authors w/ affiliation, references count, similar papers (Semantic Scholar), DOI link, OA PDF button.
   - Tab: Overview | Citations | Similar | Raw metadata.
4. **Saved Papers**
   - Tag, note, filter by tag, export all.
5. **Trend Dashboard** (post-MVP)
   - Line chart: papers/month untuk topic.
   - Top venues / top authors bar chart.
6. **Export Page**
   - Pilih format (CSV/JSON/BibTeX/MD), pilih fields, download.
7. **Alert Settings** (post-MVP)
   - Form: query, frequency, channel, target.

### Wireframe ASCII (Result List)
```
┌──────────────────────────────────────────────────────────────┐
│  PaperLens   [graph neural network drug discovery     🔍]    │
│  Year: [2020 ──●─── 2025]  Source: ☑all  OA:☑  MinCite:[10] │
├──────────────────────────────────────────────────────────────┤
│  📄 GNN-DTI: Drug-Target Interaction via GNN                  │
│     Smith J., Lee K. · 2023 · Nature Mach. Intel.            │
│     ⭐ 0.87  📚 Cite 142  🟢 OA  [crossref][openalex][s2]    │
│     [View] [Save] [BibTeX]                                   │
├──────────────────────────────────────────────────────────────┤
│  📄 Molecular Property Prediction with Pretrained GNNs        │
│     ...                                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 13. Roadmap Pengembangan (6 Minggu)

### Minggu 1 — Foundation
- Riset dokumentasi semua API (Crossref, OpenAlex, S2, arXiv).
- Setup repo, `pyproject.toml`, struktur folder, FastAPI hello world.
- `.env.example`, logging, config.
- Pasang SQLAlchemy + SQLite + migrasi awal (`papers`, `sources`).
- Tulis `BaseConnector` ABC + `PaperDTO`.
- Deliverable: `GET /healthz`, `python -m app.main` jalan.

### Minggu 2 — Core Connectors
- Implement `CrossrefConnector`, `OpenAlexConnector`, `ArxivConnector`.
- Unit test tiap connector (HTTP mock dengan `respx`).
- Unified `PaperDTO` normalization tested.
- Deliverable: `python scripts/benchmark_search.py "diffusion model"` mengeluarkan ≥30 paper dari 3 sumber.

### Minggu 3 — Database, Dedup, Ranking
- Skema lengkap (`authors`, `paper_authors`, `paper_metrics`, `paper_topics`).
- `DedupService` + unit test (DOI, arXiv, title, fuzzy).
- `RankingService` + 5 sub-skor + unit test deterministik.
- `SearchService.run` orkestrasi end-to-end.
- `POST /search` endpoint.
- Deliverable: end-to-end query → JSON terdedup & ter-rangking via REST.

### Minggu 4 — Dashboard MVP
- Streamlit app: search page, result list, detail page.
- Saved papers (in-memory + DB).
- Loading state & error handling.
- Deliverable: demo video/GIF + screenshot.

### Minggu 5 — Connector Tambahan + Recommendation
- `SemanticScholarConnector` (recommendations, influential citations).
- `PubMedConnector`, `DOAJConnector`.
- Endpoint `GET /papers/{id}/similar`.
- Improvement scoring: pakai venue lookup table real.
- Deliverable: 6 connector aktif + tombol "Similar papers".

### Minggu 6 — Export, Alert (basic), Testing, Deploy
- `ExportService` semua format (CSV/JSON/BibTeX/MD).
- `AlertService` minimal: simpan alert, scheduled job harian, channel email (SMTP).
- Coverage test ≥70%.
- Dockerfile + `docker-compose.yml` (Postgres optional).
- Deploy ke Fly.io / Railway / VPS.
- README portfolio: arsitektur, screenshot, demo link.

### Stretch (post-week-6)
- AI summarizer (OpenAI / Ollama).
- Trend dashboard (chart).
- Citation network viz.
- Connector IEEE/Springer dengan API key.

---

## 14. Risiko Teknis & Mitigasi

| # | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| 1 | Rate limit API (Crossref 50/s polite, S2 ketat tanpa key) | request 429, hasil parsial | token-bucket per connector, exponential backoff (`tenacity`), cache response 24j, identifikasi User-Agent + mailto |
| 2 | Metadata tidak konsisten (judul beda kapitalisasi/punktuasi, author urutan beda) | dedup gagal, double entry | normalisasi judul agresif, fuzzy threshold tuned, ORCID-first author matching |
| 3 | Duplikasi paper meski sudah dedup | UX jelek | log false-negative, build test set 100 pasangan ground truth, monitor precision/recall dedup |
| 4 | API key terbatas / berbayar (IEEE, Springer, Scopus) | fitur premium tidak jalan | desain connector opsional + feature flag; gracefully degrade jika key tidak ada |
| 5 | Missing abstract (Crossref sering tanpa abstract) | relevance scoring lemah | enrich dari OpenAlex/S2/EuropePMC; flag paper "abstract: tidak tersedia" |
| 6 | Citation count berbeda antar sumber | user bingung | tampilkan **per-source** di detail, **max** di list, jelaskan di tooltip |
| 7 | Jurnal predator / OA quality issue | hasil sampah | cross-check DOAJ whitelist, blacklist Beall list, tampilkan badge "DOAJ-indexed" / warning |
| 8 | Legal/ToS issue (scraping non-API) | takedown, blacklist IP | **API-only**, no HTML scraping; hormati `robots.txt`; full text hanya jika OA dan license jelas |
| 9 | Disk/DB cache membengkak | lambat | TTL cache, cleanup job mingguan, paper tanpa interaksi >90 hari → archive |
| 10 | Cost AI summarizer | budget habis | quota per user, fallback ke local LLM, summary lazy (on-demand only) |
| 11 | Schema drift API provider | parser pecah | contract test mingguan, version pin endpoint, error monitoring (Sentry/log) |
| 12 | Skewed ranking (citation favors paper lama) | paper baru tenggelam | recency_score dengan decay, eksperimen bobot, izinkan user override |

---

## 15. Output Akhir — Lampiran Konkret

### 15.1 Pseudocode Pipeline

```python
# services/search_service.py
async def run(query: str, filters: SearchFilters, limit: int = 50) -> list[PaperDTO]:
    # 1. Dispatch paralel
    connectors = registry.active_connectors()
    tasks = [c.search(query, filters, limit=limit) for c in connectors]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 2. Flatten + skip yang error
    papers: list[PaperDTO] = []
    for r in raw_results:
        if isinstance(r, Exception):
            log.warning("connector failed", error=r); continue
        papers.extend(r)

    # 3. Deduplication
    deduped = DedupService.dedupe(papers)

    # 4. Filtering tambahan (post-fetch)
    deduped = [p for p in deduped if filters.match(p)]

    # 5. Ranking
    scored = RankingService.score(deduped, query=query)

    # 6. Persist (upsert)
    PaperRepository.upsert_many(scored)

    # 7. Sort & limit
    scored.sort(key=lambda p: p.final_score, reverse=True)
    return scored[:limit]
```

```python
# services/dedup_service.py
def dedupe(papers: list[PaperDTO]) -> list[PaperDTO]:
    bucket: dict[str, PaperDTO] = {}
    for p in papers:
        key = _primary_key(p)              # DOI > arxiv > pubmed > title_norm
        if key in bucket:
            bucket[key] = _merge(bucket[key], p)
        else:
            # try fuzzy match terhadap existing
            match = _fuzzy_lookup(bucket, p)
            if match:
                bucket[match] = _merge(bucket[match], p)
            else:
                bucket[key] = p
    return list(bucket.values())
```

```python
# services/ranking_service.py
WEIGHTS = {"relevance": .35, "recency": .20, "citation": .20, "venue": .15, "oa": .10}

def score(papers: list[PaperDTO], query: str) -> list[PaperDTO]:
    for p in papers:
        s = {
            "relevance": _relevance(query, p),
            "recency":   _recency(p.year),
            "citation":  _citation(p.best_citation_count()),
            "venue":     _venue(p.venue, p.venue_issn),
            "oa":        _oa(p.is_open_access, p.oa_type),
        }
        p.sub_scores = s
        p.final_score = sum(WEIGHTS[k] * s[k] for k in WEIGHTS)
    return papers
```

### 15.2 Contoh REST API Endpoints

```
POST   /api/v1/search
       body: { query: str, filters: {...}, limit: int }
       resp: { results: [PaperOut], total: int, latency_ms: int }

GET    /api/v1/papers/{paper_id}
       resp: PaperDetailOut

GET    /api/v1/papers/{paper_id}/similar?limit=10
       resp: { results: [PaperOut] }

POST   /api/v1/export
       body: { paper_ids: [str], format: "csv|json|bibtex|md" }
       resp: file stream

GET    /api/v1/saved
POST   /api/v1/saved          { paper_id, tag?, note? }
DELETE /api/v1/saved/{id}

POST   /api/v1/alerts         { query, filters, channel, target, frequency }
GET    /api/v1/alerts
DELETE /api/v1/alerts/{id}

GET    /api/v1/trends?topic=...&from=2022-01&to=2025-01
       resp: { monthly: [{month, count}], top_venues: [...], top_authors: [...] }

GET    /api/v1/health
GET    /api/v1/sources/status     # health_check semua connector
```

#### Contoh request/response `POST /search`
```json
// request
{
  "query": "graph neural network drug discovery",
  "filters": {
    "year_from": 2022,
    "year_to": 2025,
    "sources": ["crossref","openalex","arxiv","semantic_scholar"],
    "open_access": true,
    "min_citations": 10,
    "venue_contains": null
  },
  "limit": 25
}
```
```json
// response (truncated)
{
  "total": 25,
  "latency_ms": 1843,
  "results": [
    {
      "id": "f3c2...",
      "title": "GNN-DTI: Drug-Target Interaction via Graph Neural Networks",
      "authors": [{"name":"Jane Smith","orcid":"0000-..."}],
      "year": 2023,
      "venue": "Nature Machine Intelligence",
      "doi": "10.1038/s42256-023-00xxx",
      "arxiv_id": null,
      "is_open_access": true,
      "oa_url": "https://...pdf",
      "citation_count": 142,
      "abstract": "...",
      "sources": ["crossref","openalex","semantic_scholar"],
      "sub_scores": {"relevance":0.91,"recency":0.82,"citation":0.74,"venue":1.0,"oa":1.0},
      "final_score": 0.873
    }
  ]
}
```

### 15.3 Contoh UI Sederhana (Streamlit)

```python
# frontend/streamlit_app.py
import streamlit as st, httpx

st.set_page_config(page_title="PaperLens", layout="wide")
st.title("📚 PaperLens — Research Paper Intelligence Aggregator")

with st.sidebar:
    st.header("Filter")
    year = st.slider("Tahun", 2010, 2025, (2022, 2025))
    sources = st.multiselect("Sumber",
        ["crossref","openalex","arxiv","semantic_scholar","pubmed","doaj"],
        default=["crossref","openalex","arxiv","semantic_scholar"])
    oa_only = st.checkbox("Open Access only", value=False)
    min_cite = st.number_input("Minimal citation", 0, 10000, 0)

query = st.text_input("Cari paper (keyword, judul, topik)", "")
if st.button("🔍 Search") and query:
    with st.spinner("Mengumpulkan dari banyak sumber..."):
        r = httpx.post("http://localhost:8000/api/v1/search", json={
            "query": query,
            "filters": {
                "year_from": year[0], "year_to": year[1],
                "sources": sources, "open_access": oa_only,
                "min_citations": min_cite
            },
            "limit": 25,
        }, timeout=60).json()

    st.success(f"Ditemukan {r['total']} paper dalam {r['latency_ms']} ms")
    for p in r["results"]:
        with st.container(border=True):
            cols = st.columns([6,1,1,1])
            cols[0].markdown(f"### {p['title']}")
            cols[0].caption(
                f"{', '.join(a['name'] for a in p['authors'][:3])} · "
                f"{p['year']} · {p.get('venue') or 'preprint'}"
            )
            cols[1].metric("Score", f"{p['final_score']:.2f}")
            cols[2].metric("Cite", p["citation_count"])
            cols[3].markdown("🟢 OA" if p["is_open_access"] else "🔒")
            if p.get("abstract"):
                with st.expander("Abstract"):
                    st.write(p["abstract"])
            st.write("Sumber:", " · ".join(p["sources"]))
            if p.get("oa_url"):
                st.link_button("📄 PDF", p["oa_url"])
```

### 15.4 Rekomendasi Prioritas Implementasi

Urutan eksekusi disarankan (dari yang paling memberi leverage):

1. **Hari 1–3:** `BaseConnector` + `CrossrefConnector` + `PaperDTO` + 1 endpoint `/search` (single source). Validasi end-to-end.
2. **Hari 4–7:** Tambah `OpenAlexConnector` + `ArxivConnector`, paralel via `asyncio.gather`.
3. **Hari 8–10:** `DedupService` (DOI → title_norm → fuzzy). Buat **test fixture 50 paper** ground truth untuk regression.
4. **Hari 11–13:** `RankingService` 5 sub-skor + bobot pluggable.
5. **Hari 14–17:** Persistence (SQLAlchemy upsert), `paper_metrics` per-source.
6. **Hari 18–22:** Streamlit UI (search + list + detail).
7. **Hari 23–26:** `SemanticScholarConnector` (recommendations) + `PubMed` + `DOAJ`.
8. **Hari 27–30:** Export 4 format + saved papers.
9. **Hari 31–35:** Alerts + APScheduler + email channel.
10. **Hari 36–42:** Testing >70% coverage + Docker + deploy + README portfolio.

**Quick wins yang berdampak besar untuk portfolio:**
- ✅ Demo GIF 30 detik: query → hasil 25 paper dari 4 sumber, dedup, ranked.
- ✅ Diagram arsitektur di README.
- ✅ Live demo URL (Fly.io / Railway gratis tier).
- ✅ Test coverage badge.
- ✅ Section "How ranking works" di README — menunjukkan kedalaman teknis.

---

## Lampiran: Catatan Legal & Etika
- **API-first, no HTML scraping.** Semua sumber di scope sudah punya API resmi.
- **Polite headers.** `User-Agent: PaperLens/0.x (mailto:contact@example.com)` untuk Crossref/OpenAlex.
- **Cache & backoff.** Minimal 24 jam cache, exponential backoff `tenacity` (1s, 2s, 4s, 8s, max 30s).
- **Tidak menyimpan full-text berbayar.** Hanya metadata + URL. Full-text **hanya** untuk OA license jelas (CC-BY/CC-BY-SA/PD).
- **Robots.txt & ToS.** Untuk URL yang akan di-fetch (mis. cek OA validity), patuh `robots.txt`.
- **Atribusi.** Setiap paper menampilkan source list — user tahu data berasal dari mana.
- **Privasi.** Jika multi-user, simpan minimal PII; alert email opt-in dengan unsubscribe link.
