# SIH26146 Dashboard Frontend

Mohammed Saleem's Module E implementation. It consumes the integration API through `NEXT_PUBLIC_API_URL` (for example `http://localhost:8000`) and falls back to the current shared-sample-shaped dashboard data only while that API is unavailable during parallel development.

## Run

```bash
npm install
npm run dev
```

The interface is responsive and includes a drag-rotatable country-labeled globe, playback controls, risk-labelled alert table, alert evidence panel, global search, cluster map, glossary tooltips, and onboarding guidance.

## Verification

```bash
npm test
npm run build
```
