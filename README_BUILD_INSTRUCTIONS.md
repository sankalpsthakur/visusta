# Visusta Build Instructions

## Prerequisites

- Python 3.11+.
- Node.js 20+.
- `pip install -r requirements.txt`

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8000 --reload
```

The API serves:

- `GET /api/health`
- `GET/POST /api/clients`
- client-scoped routes under `/api/clients/{client_id}`
- template routes under `/api/templates`
- locale routes under `/api/locales`

It also mounts generated assets from `/charts` and `/output`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The app reads `NEXT_PUBLIC_API_URL` and defaults to `http://localhost:8000`.

For a production-style local run:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run start -- --port 3100
```

## Playwright

`frontend/playwright.config.ts` starts both services automatically:

- API: `python3 -m uvicorn api.main:app --port 8010`
- Frontend: `NEXT_PUBLIC_API_URL=http://localhost:8010 npm run build && NEXT_PUBLIC_API_URL=http://localhost:8010 npm run start -- --port 3100`

Run the full browser suite from `frontend/`:

```bash
npx playwright test
```

## Reports

Build the PDF deliverables from the repo root:

```bash
python3 build_monthly_report.py
python3 build_quarterly_brief.py
```

These scripts use the local data and chart assets under `charts/` and `data/`.
