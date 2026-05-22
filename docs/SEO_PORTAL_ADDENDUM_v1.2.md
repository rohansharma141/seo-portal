# SEO PORTAL — ADDENDUM SPEC v1.2
# PageSpeed Insights (PSI) Integration — Real Performance Scoring
# Feed alongside SEO_PORTAL_BUILD_DOC.md.

Adds real Core Web Vitals via Google's free PageSpeed Insights API,
replacing the estimated/mock performance values.

## CONTEXT

The Performance category currently uses estimated values. This addendum
replaces that with real Lighthouse data from Google's PageSpeed Insights
API — the same engine as pagespeed.web.dev. The API is FREE and works
without a key at low rate limits; a free key raises the limit to 25k/day.

## FEATURE: PSI INTEGRATION

1. New service file `services/pagespeed.py` — `get_pagespeed_data(url,
   strategy)` calls the PSI API, parses Lighthouse result + field data,
   and falls back to a mock on any failure so audits never fail.
2. Wire concurrent, capped PSI calls into `run_audit()` (`PSI_MAX_URLS`,
   default 5). Real CWV drive Performance scoring; full PSI response is
   stored in `audit.metadata["pagespeed"]`.
3. PSI "opportunities" with `savings_ms > 0` become Performance issues
   (`>1000ms` = warning, else info; `rule_id = "psi_<id>"`).
4. `GET /api/v1/audits/{id}` exposes a `pagespeed` field.
5. Frontend: a "Performance (PageSpeed)" panel on the audit report —
   per-URL score, LCP/CLS/INP/FCP/TBT metric cards, Mobile/Desktop
   toggle, top opportunities, lab vs field data.
6. Settings: a PageSpeed Insights integration card (works without key).
7. `.env.example`: `PSI_API_KEY` (free) and `PSI_MAX_URLS` (default 5).

## CONSTRAINTS

- LIVE-capable immediately (no paid dependency). Still ship the mock
  fallback so audits never fail if PSI is rate-limited or times out.
- PSI is slow (10–30s/URL). Always run concurrently, always cap URL
  count, always have the mock fallback on timeout.
- Only PSI-test representative pages (homepage + key templates).

## BUILD ORDER

A. `services/pagespeed.py` (real + mock paths)
B. Concurrent PSI in `run_audit()`, capped by `PSI_MAX_URLS`
C. Real CWV into Performance scoring (`seo_rules.py`)
D. PSI opportunities → Performance issues
E. `pagespeed` in the audit API response
F. Performance panel on the audit report frontend (Mobile/Desktop)
G. PSI card on Settings + env vars

---
*Addendum v1.2 — applied after Addendum v1.1.*
