# Restaurant SEO

A comprehensive SEO audit platform for restaurant websites.

## Phase 1 (v0.1.0)

- Async FastAPI application
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations
- Restaurant, location, project, audit, and finding models
- Deterministic audit engine with stub analyzers
- REST API endpoints
- Docker + docker-compose setup
- Automated CI/CD with GHCR publishing

## Development

### Prerequisites

- Python 3.12
- Docker and docker-compose
- PostgreSQL 16 (or use docker-compose)

### Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r dev-requirements.txt
```

### Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Database

Start PostgreSQL:

```bash
docker-compose up -d postgres
```

Run migrations:

```bash
alembic upgrade head
```

### Running the API

```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`.

Health check: `GET /health`

### Testing

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Docker

Build and run the full stack:

```bash
docker-compose up
```

## License

MIT
