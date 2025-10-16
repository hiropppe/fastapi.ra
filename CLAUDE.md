# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack application with FastAPI backend and React Admin frontend, featuring AWS Cognito authentication, MySQL database, and Docker containerization. The project demonstrates multiple API versioning strategies (path-based and header-based).

## Architecture

### Backend (FastAPI)
- **Location**: `/app/back`
- **Entry point**: `src/main.py` (uvicorn server on port 8000)
- **Core module**: `src/tuto/`
- **Language**: Python 3.13 with SQLModel and Alembic migrations
- **Database**: MySQL 9 (async using aiomysql, sync using pymysql)

#### Backend Structure
```
src/tuto/
├── api/           # API routes and FastAPI app configuration
├── auth/          # AWS Cognito authentication and token management
├── datasource/    # Database engine and session management
├── model/         # SQLModel data models
├── repository/    # Repository pattern implementations (Protocol-based)
├── service/       # Business logic layer (Protocol-based)
├── finder/        # Data query/retrieval logic
├── versioning/    # API versioning implementation (path & header-based)
└── utils/         # Utility functions
```

**Key architectural patterns**:
- Repository pattern with Python Protocols for abstraction (`repository.py` defines `RepositoryProtocol[PK, T]`)
- Service layer using Protocols (`auth_protocol.py`)
- Dependency injection via FastAPI dependencies (`get_session()`, `get_async_session()`)
- Both sync and async database sessions are supported

**API Versioning**:
The project implements a custom versioning system (modified from tikon93/fastapi-header-versioning):
- Currently uses **path-based versioning** (e.g., `/v0.1/`, `/v0.1.1/`)
- Header-based versioning available but commented out
- Alternative path versioning (DeanWay's approach) also available in comments
- Versioning logic in `src/tuto/versioning/` (fastapi.py, routing.py, openapi.py)
- Route versions configured in `src/tuto/api/app.py`

### Frontend (React Admin)
- **Location**: `/app/front`
- **Entry point**: `src/index.tsx`
- **Framework**: React 19 with React Admin 5.7, Vite, TypeScript
- **UI**: Material-UI (@mui/material)
- **i18n**: Japanese and English support

#### Frontend Structure
```
src/
├── auth/          # Cognito authentication (login, MFA, password reset)
├── users/         # User resource components
├── ra/            # React Admin data provider
└── i18n/          # Internationalization
```

**Authentication**: Custom Cognito auth provider (`authClient.ts`, `authProvider.ts`, `useCognitoLogin.ts`)

### Database
- MySQL 9 with two instances: `db` (dev on port 3336) and `testdb` (tests on port 3337)
- Migrations managed by Alembic (config: `back/alembic.ini`)
- Migration files: `back/migrations/versions/`
- Connection strings configured via environment variables (DB_URL, ASYNC_DB_URL)

## Development Commands

### Docker Setup
```bash
# Start all services (backend, frontend, db, testdb)
docker compose up -d

# Start only backend and databases
docker compose up -d back db testdb

# Access backend container
docker exec -it fara.back bash

# Access frontend container
docker exec -it fara.front bash
```

### Backend Development
**Inside backend container** (`docker exec -it fara.back bash`):
```bash
# Start FastAPI dev server (auto-reload enabled)
cd /app/back
python src/main.py

# Run linting
ruff check src/

# Format code
ruff format src/

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Frontend Development
**Inside frontend container** (`docker exec -it fara.front bash`):
```bash
cd /app/front

# Start dev server (port 5173, exposed as 15173)
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

### E2E Testing
**From host or e2e directory**:
```bash
cd /app/e2e

# Run Playwright tests
npx playwright test

# Run tests with UI
npx playwright test --ui

# Run specific test file
npx playwright test tests/login.spec.ts
```

## Important Configuration Details

### Environment Files
- `.api.env`: Backend environment (AWS Cognito credentials, cookie settings)
- `.front.env`: Frontend environment
- Database credentials hardcoded in docker-compose.yml (user: tuto, password: tuto)

### Ports
- Frontend dev server: `15173` → container `5173`
- Backend API: `18000` → container `8000`
- MySQL dev DB: `3336` → container `3306`
- MySQL test DB: `3337` → container `3306`

### Code Quality
Backend uses Ruff with strict linting rules:
- Type annotations required (ANN)
- Google-style docstrings (pydocstyle)
- pathlib preferred over os.path
- Line length: 88 characters
- Python target version: 3.13

Frontend uses ESLint + Prettier with TypeScript strict mode.

## Database Migration Workflow
1. Modify models in `src/tuto/model/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `migrations/versions/`
4. Apply: `alembic upgrade head`
5. Test against testdb if needed

## API Versioning Workflow
When adding new API versions:
1. Create new router module in `src/tuto/api/router/` (e.g., `v0_2_0/`)
2. Register routes in `src/tuto/api/app.py` using `root_router.include_router()` with version parameter
3. Version string format: "0.1", "0.1.1", "1.0", etc.
4. Docs are auto-generated per version via `doc_generation()` function

## References
Backend follows patterns from:
- https://github.com/zhanymkanov/fastapi-best-practices
- https://github.com/Netflix/dispatch
