# Building10X SEO Portal — API Usage

Base URL (local): `http://localhost:8000`
All endpoints are under `/api/v1/` except `GET /health`.

## Interactive docs

| What | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI schema | `http://localhost:8000/openapi.json` (also committed at `docs/openapi.json`) |

## Authentication

Every endpoint except `/health` requires a bearer token:

```
Authorization: Bearer <token>
```

Two kinds are accepted:

- **API token** — starts with `pse_`. Created via `POST /api/v1/tokens`
  (shown once). Scoped: `audit:read`, `audit:write`, `site:read`,
  `site:write`, `webhook:read`, `webhook:write`.
- **JWT** — HS256, signed with `JWT_SECRET`. Portal/admin sessions get the
  wildcard scope `*`. **Token management endpoints (`/api/v1/tokens`) require
  a JWT — an API token cannot manage tokens.**

Scope per endpoint group: reads need `*:read`, writes need `*:write`,
reports need `site:read`, `/tokens` needs an admin JWT.

Set a token once for the examples below:

```bash
export TOKEN="pse_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export BASE="http://localhost:8000"
```

---

## Health

```bash
curl $BASE/health
# {"status":"ok","version":"1.0.0","timestamp":"2026-05-18T..."}
```

---

## Sites — `/api/v1/sites`

List:

```bash
curl $BASE/api/v1/sites -H "Authorization: Bearer $TOKEN"
```

Create:

```bash
curl -X POST $BASE/api/v1/sites \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "Kedar Estate",
    "domain": "kedar.estate",
    "url": "https://kedar.estate",
    "site_type": "brokerage",
    "schedule": "weekly",
    "max_pages": 100
  }'
```

Get / update / delete (soft delete sets `is_active=false`):

```bash
curl $BASE/api/v1/sites/$SITE_ID -H "Authorization: Bearer $TOKEN"

curl -X PATCH $BASE/api/v1/sites/$SITE_ID \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"schedule": "monthly"}'

curl -X DELETE $BASE/api/v1/sites/$SITE_ID -H "Authorization: Bearer $TOKEN"
```

---

## Audits — `/api/v1/audits`

Trigger (returns immediately; runs in the background):

```bash
curl -X POST $BASE/api/v1/audits \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"site_id": "'"$SITE_ID"'", "triggered_by": "api"}'
# 202 {"audit_id":"...","status":"pending","estimated_seconds":120,...}
```

Poll status, then fetch the full result:

```bash
curl $BASE/api/v1/audits/$AUDIT_ID/status -H "Authorization: Bearer $TOKEN"

curl $BASE/api/v1/audits/$AUDIT_ID -H "Authorization: Bearer $TOKEN"
# scores, issues, analysis, gsc_snapshot, backlinks (v1.1), pagespeed (v1.2)
```

List (filterable / paginated) and issues (filterable):

```bash
curl "$BASE/api/v1/audits?site_id=$SITE_ID&limit=50&offset=0" \
  -H "Authorization: Bearer $TOKEN"

curl "$BASE/api/v1/audits/$AUDIT_ID/issues?severity=critical&category=technical" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Reports — `/api/v1/reports`

```bash
# Dashboard summary across all sites
curl $BASE/api/v1/reports/summary -H "Authorization: Bearer $TOKEN"

# Audit history + score trend for one site
curl $BASE/api/v1/reports/site/$SITE_ID/history \
  -H "Authorization: Bearer $TOKEN"

# Compare two audits of the same site
curl "$BASE/api/v1/reports/site/$SITE_ID/compare?a=$AUDIT_A&b=$AUDIT_B" \
  -H "Authorization: Bearer $TOKEN"

# Addendum v1.1 — cross-site comparison (2–5 sites)
curl "$BASE/api/v1/reports/compare?site_ids=$SITE_1,$SITE_2,$SITE_3" \
  -H "Authorization: Bearer $TOKEN"
# 400 if <2 or >5 site_ids · 404 if a site is unknown ·
# 422 if a site has no completed audit yet
```

---

## API Tokens — `/api/v1/tokens` (admin JWT only)

```bash
curl $BASE/api/v1/tokens -H "Authorization: Bearer $JWT"

curl -X POST $BASE/api/v1/tokens \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d '{"name":"PropOS Production","scopes":["site:read","site:write","audit:read","audit:write","webhook:write"]}'
# Response includes "token" — shown ONCE, store it now.

curl -X DELETE $BASE/api/v1/tokens/$TOKEN_ID -H "Authorization: Bearer $JWT"
```

---

## Webhooks — `/api/v1/webhooks`

```bash
curl $BASE/api/v1/webhooks -H "Authorization: Bearer $TOKEN"

curl -X POST $BASE/api/v1/webhooks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "PropOS",
    "url": "https://propos.in/hooks/seo",
    "events": ["audit.complete", "audit.failed"],
    "secret": "whsec_xxx"
  }'

# Send a signed test payload to a URL
curl -X POST $BASE/api/v1/webhooks/test \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"https://propos.in/hooks/seo","secret":"whsec_xxx"}'

curl -X DELETE $BASE/api/v1/webhooks/$WEBHOOK_ID \
  -H "Authorization: Bearer $TOKEN"
```

Webhook deliveries are signed: header
`X-SEO-Signature: sha256=<hmac-sha256(secret, body)>`. Payload envelope:

```json
{
  "event": "audit.complete",
  "timestamp": "2026-05-18T10:02:30+00:00",
  "data": {
    "audit_id": "uuid", "site_id": "uuid",
    "site_url": "https://kedar.estate",
    "score_overall": 74, "issues_critical": 2,
    "issues_warning": 8, "status": "complete"
  }
}
```

---

## PropOS integration (Section 12)

1. `POST /api/v1/sites` — register the broker page (needs `site:write`)
2. `POST /api/v1/audits` — trigger on publish (`triggered_by:"deploy_hook"`)
3. Poll `GET /api/v1/audits/{id}/status` every 5s, **or** subscribe a
   webhook via `POST /api/v1/webhooks`
4. On `audit.complete`: read `score_overall` / issue counts
5. `GET /api/v1/audits/{id}/issues?severity=critical` for the detail

Recommended PropOS token scopes:
`["site:read","site:write","audit:read","audit:write","webhook:write"]`.
