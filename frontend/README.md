# Visusta Frontend

Locale-aware Next.js app for the Visusta ESG Regulatory Intelligence platform.

## Overview

- App Router pages live under `src/app/[lang]/...`.
- Supported locales come from `src/lib/i18n/locales.ts`.
- `src/proxy.ts` redirects `/` and other unscoped routes to the best matching locale, defaulting to `en`.
- Invalid locale prefixes return Next.js `notFound`.

Primary areas of the UI:

- dashboard and client overview
- regulatory changelog browsing
- templates and versioning
- client drafts, approvals, and exports
- sources, keywords, evidence, and reports

## API Contract

The frontend calls the FastAPI backend directly with `fetch`.

- Default base URL: `http://localhost:8000`
- Override with `NEXT_PUBLIC_API_URL`
- API health check: `GET /api/health`
- Client, template, locale, draft, source, evidence, and export routes are all prefixed with `/api`

The Playwright config uses `NEXT_PUBLIC_API_URL=http://localhost:8010` so the browser suite talks to the local test backend.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The app will redirect to a locale path such as `/en`.

## Build

```bash
cd frontend
npm run build
npm run start -- --port 3100
```

To point at a different API server:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8010 npm run dev
```

## Tests

- Lint: `npm run lint`
- E2E: `npx playwright test`

`frontend/playwright.config.ts` launches the API on `8010` and the app on `3100`, then runs the browser suite in Chromium.
