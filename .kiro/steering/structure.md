# Project Structure

## Root Directory Layout
```
├── app/                    # FastAPI application
├── connectors/             # API connectors for academic sources
├── services/              # Business logic layer (search, dedup, ranking)
├── models/                # SQLAlchemy ORM models
├── schemas/               # Pydantic schemas (PaperDTO, SearchFilters)
├── workers/               # Background jobs (APScheduler)
├── utils/                 # Helper utilities
├── frontend/              # Frontend applications
├── tests/                 # Test suite
├── .kiro/                 # Kiro configuration and steering
├── pyproject.toml         # Python dependencies and config
└── .env.example           # Environment template
```

## Backend Structure

### `/app` - FastAPI Application
- `main.py` - Application entry point with lifespan management
- `config.py` - Settings and environment configuration
- `api/` - API route handlers organized by feature
  - `routes_search.py` - Search endpoints
  - `routes_saved.py` - Saved papers CRUD
  - `routes_export.py` - Export functionality
  - `routes_alert.py` - Alert management
- `core/` - Core application services
  - `http.py` - HTTP client management
  - `logging.py` - Logging configuration
- `db/` - Database configuration
  - `session.py` - Database session management
  - `base.py` - Base model classes

### `/connectors` - Academic Source Integrations
- `base.py` - Abstract base connector class
- `registry.py` - Connector registration and management
- Individual connector files:
  - `crossref.py` - Crossref API
  - `openalex.py` - OpenAlex API
  - `arxiv.py` - arXiv feed
  - `semantic_scholar.py` - Semantic Scholar API
  - `pubmed.py` - PubMed API
  - `doaj.py` - DOAJ API
  - `europepmc.py` - Europe PMC API
  - `core.py` - CORE API

### `/services` - Business Logic
- Search orchestration and result aggregation
- Deduplication algorithms using fuzzy matching
- Ranking and scoring logic
- Export format generation
- Alert processing

## Frontend Structure

### `/frontend` - React Application
```
├── src/
│   ├── App.tsx            # Main application component
│   ├── components/        # React components
│   │   ├── ui/           # Reusable UI components (Radix-based)
│   │   ├── LandingPage.tsx
│   │   ├── SearchBar.tsx
│   │   ├── PaperList.tsx
│   │   ├── PaperCard.tsx
│   │   ├── PaperDetail.tsx
│   │   ├── FilterPanel.tsx
│   │   ├── AlertsPanel.tsx
│   │   └── SideNav.tsx
│   └── assets/           # Static assets (logos, images)
├── dist/                 # Production build output
├── package.json          # Node.js dependencies
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── postcss.config.js     # PostCSS configuration
```

## Code Organization Patterns

### Connector Pattern
All academic source integrations follow the `BaseConnector` abstract class:
- Standardized `search()` and `get_by_doi()` methods
- Built-in rate limiting and retry logic
- Consistent error handling and logging
- Normalized output via `PaperDTO` schema

### API Route Organization
Routes are organized by feature domain:
- `/api/v1/search` - Search functionality
- `/api/v1/saved` - Saved papers management
- `/api/v1/export` - Data export
- `/api/v1/alerts` - Alert management

### Component Architecture
React components follow a hierarchical structure:
- Page-level components (LandingPage, SearchView)
- Feature components (SearchBar, PaperList, FilterPanel)
- UI primitives in `/components/ui/` (reusable across features)

### Data Flow
1. User input → React components
2. API calls → FastAPI routes
3. Business logic → Services layer
4. External APIs → Connectors
5. Data persistence → SQLAlchemy models
6. Response → Pydantic schemas → JSON

## Configuration Files

### Environment Configuration
- `.env` - Local environment variables (not committed)
- `.env.example` - Template with required variables
- `app/config.py` - Pydantic settings with validation

### Build Configuration
- `pyproject.toml` - Python project metadata and dependencies
- `package.json` - Node.js dependencies and scripts
- `vite.config.ts` - Frontend build configuration
- `tailwind.config.js` - CSS framework configuration

## Development Conventions

### File Naming
- Python: snake_case for modules and functions
- TypeScript: PascalCase for components, camelCase for functions
- API routes: kebab-case URLs (`/api/v1/saved-papers`)

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Absolute imports preferred over relative

### Error Handling
- Use FastAPI's HTTPException for API errors
- Implement retry logic in connectors via tenacity
- Log errors with structured context using loguru