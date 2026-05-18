# CLAUDE CODE SESSION PROMPT — SEO ANALYSIS PORTAL
# Paste this entire prompt at the start of every Claude Code session for this project.
# ─────────────────────────────────────────────────────────────────────────────────

You are building the **Building10X SEO Portal** — a standalone web application and REST API for automated SEO auditing of websites. This is a real production project. Build complete, working code.

## READ THESE DOCUMENTS FIRST (mandatory before writing any code)

1. `SEO_PORTAL_BUILD_DOC.md` — Full architecture, schema, API contract, build sequence
2. `SEO_STRATEGY_CLAUDE_CODE.md` — SEO rules and standards that power the scoring engine

Read both documents fully before writing a single line of code. Every decision — folder structure, database schema, API shapes, scoring weights, SEO rules — is specified in these documents. Follow them exactly.

## YOUR CONSTRAINTS

**Stack:** FastAPI (Python 3.12) + Next.js 14 (TypeScript) + Supabase (PostgreSQL) + Tailwind CSS  
**External integrations:** All three (Firecrawl, GSC, Claude API) are PLACEHOLDERS. Build the interface and mock responses. Do not skip building them — build the full function with the mock returning realistic data and a `TODO` comment for the real implementation.  
**Tests:** Write tests for the scoring engine and SEO rules engine. These must pass.  
**Docs:** FastAPI auto-docs (/docs) must be complete. Generate openapi.json.

## WHAT "COMPLETE" MEANS

A step is complete when:
- Code runs without errors
- The API endpoint or page renders correctly
- Edge cases handled: empty state, error state, loading state
- No TODO left unmarked with a [PLACEHOLDER] comment

## BUILD ORDER

Follow the 11-step sequence in Section 11 of the build doc exactly. Do not skip steps. Confirm completion of each step before proceeding.

## PLACEHOLDERS — HOW TO HANDLE

For every external service credential (FIRECRAWL_API_KEY, GSC_CREDENTIALS_PATH, ANTHROPIC_API_KEY, RESEND_API_KEY, UPSTASH_REDIS_URL, SUPABASE_URL):

1. Read from environment variable
2. If env var is empty or not set: use the mock function defined in the build doc
3. If env var is set: call the real service (stubbed with `raise NotImplementedError` for now)
4. Add comment: `# TODO: implement real [ServiceName] integration when [ENV_VAR] is set`

The portal must be 100% functional using only mock data with no credentials set.

## DESIGN DIRECTION (Frontend)

- Dark slate sidebar (slate-900), light content area (white/slate-50)
- Score gauge: SVG arc, Emerald (≥80), Amber (50–79), Red (<50)
- Font: Geist + Geist Mono (built into Next.js)
- Issue severity: Red badge (critical), Amber badge (warning), Blue badge (info)
- No purple gradients. No Inter font. No cookie-cutter SaaS layout.
- Every page must handle: loading skeleton, error boundary, empty state with CTA

## CURRENT SESSION GOAL

[REPLACE THIS LINE with which step you are building, e.g.:]
"Build Step 3: SEO rules engine. Implement all rules in utils/seo_rules.py and scorer.py from Section 5 of the build doc. Write and run tests."

## IF YOU ARE UNSURE ABOUT ANYTHING

Check the build doc first. If still unclear, make the most reasonable decision and add a comment: `# DECISION: [what you decided and why]` so I can review it.

## ON COMPLETION OF THIS SESSION

At the end of the session, output:
1. A list of all files created or modified
2. Any decisions you made that deviated from the build doc
3. What the next session should build (next step in the sequence)
4. Any blockers or questions for me to resolve before the next session
