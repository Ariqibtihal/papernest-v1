# Technology Stack

## Backend Architecture
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite with SQLAlchemy ORM and Alembic migrations
- **HTTP Client**: httpx with tenacity for retry logic
- **Background Jobs**: APScheduler for alert notifications
- **Logging**: loguru for structured logging
- **Validation**: Pydantic for data schemas and settings

## Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 6.0
- **Styling**: Tailwind CSS 3.4 with PostCSS
- **UI Components**: Radix UI primitives (avatar, select, slot, switch)
- **Icons**: Lucide React
- **Charts**: Recharts for data visualization
- **Utilities**: clsx and tailwind-merge for conditional styling

## Development Tools
- **Package Manager**: uv (Python) and npm (Node.js)
- **Code Quality**: ruff for linting, mypy for type checking
- **Testing**: pytest with asyncio support, respx for HTTP mocking

## Common Commands

### Backend Development
```powershell
# Setup environment (first time)
uv sync --extra frontend --extra dev

# Start development server
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest -v

# Code quality checks
uv run ruff check .
uv run mypy .
```

### Frontend Development
```powershell
# Setup (first time)
cd frontend
npm install

# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### Production Deployment
```powershell
# Build frontend
cd frontend
npm run build

# Start production server (serves both API and static files)
cd ../..
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Key Dependencies

### Backend Core
- `fastapi>=0.115` - Web framework
- `uvicorn[standard]>=0.30` - ASGI server
- `sqlalchemy>=2.0` - ORM
- `pydantic>=2.7` - Data validation
- `httpx>=0.27` - HTTP client
- `tenacity>=9.0` - Retry logic
- `rapidfuzz>=3.9` - Fuzzy matching for deduplication

### Frontend Core
- `react^18.3.1` - UI framework
- `typescript^5.6.3` - Type safety
- `vite^6.0.0` - Build tool
- `tailwindcss^3.4.15` - CSS framework

## Configuration
- Environment variables in `.env` file (copy from `.env.example`)
- Database URL: `sqlite+aiosqlite:///./paperlens.db`
- API keys are optional for MVP but recommended for better rate limits
- Contact email required for polite API headers