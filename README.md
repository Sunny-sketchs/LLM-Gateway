# Guardrailed LLM Gateway (MVP)

A safety and cost-control proxy that sits in front of an LLM API. Every request is validated, rate-limited, checked for prompt injection, scanned for PII, cached, and logged — before it ever reaches the underlying model.

**Live demo:** [Deployed on Render](https://llm-gateway-frontend.onrender.com)
**Demo API access:** currently single guest-user mode, no key required (see [Auth](#auth-current-state) below)

> First request after a period of inactivity may take 30–60s to respond — the free-tier host sleeps when idle and needs to wake up.

---

## What this is

Most AI demos call a model directly and print the response. This is the layer companies actually build *between* an app and an LLM API to keep usage safe, auditable, and within budget — the kind of infrastructure internal AI platform/governance teams maintain, not a chatbot.

```
Client → [Token limit] → [Rate limit] → [Cache lookup] → [Injection check] → [PII redaction] → LLM API
                                              ↓ (hit)
                                       Return cached answer, $0 cost, logged
```

Checks run cheapest-first: a local token count and Redis rate-limit check happen before anything touches the cache, which itself is checked before the heavier PII/NLP step, which runs before the actual (billed) LLM call. A rejection at any stage short-circuits everything after it — no wasted compute, no wasted API cost.

## Features

- **Per-request token cap** — rejects oversized prompts via `tiktoken`, before any downstream cost is incurred.
- **Rate limiting** — per-minute and per-day request caps, enforced atomically in Redis (Upstash) via `INCR`/`EXPIRE`.
- **Exact-match caching** — normalized-query caching in Redis. Checked *before* PII redaction (so common, non-sensitive questions skip the NLP step entirely) and populated *after* redaction only when no PII was found — PII-containing queries are deliberately never cached, trading a small amount of theoretical cache coverage for a simple, unambiguous privacy story.
- **Prompt injection detection** — keyword/pattern-based first-pass filter (e.g. "ignore previous instructions"). A real, if minimal, first line of defense — see Limitations for what it doesn't catch.
- **PII detection & redaction** — Microsoft Presidio, restricted to high-confidence entity types (email, phone, credit card, SSN, IBAN) to avoid false positives on ordinary text like place names or common first names. Extended with custom regex recognizers for Indian phone numbers and PAN (tax ID) numbers, since Presidio's defaults are US-format-biased.
- **Request logging** — every request writes a row to Postgres (Neon): redacted query, response, tokens used/saved, cost, cache/PII/injection flags, HTTP status, timestamp. Logged asynchronously via FastAPI `BackgroundTasks` on successful paths so logging never adds latency to the response; logged synchronously on rejected/error paths, since background tasks queued right before an exception is raised are silently discarded by Starlette and never actually run — a real bug found and fixed during development (see Limitations/Notes).
- **`/usage` endpoint** — real-time request count against the daily limit, read directly from Redis.

## Tech stack

| Component | Choice | Why |
|---|---|---|
| API framework | FastAPI | Async, auto-docs, standard choice for this kind of service |
| LLM provider | OpenAI (`gpt-4o-mini`) | Single provider for MVP; multi-provider fallback designed but not yet built |
| PII detection | Presidio + spaCy, custom regex recognizers | Real NER-based detection, not plain regex, extended for India-specific formats |
| Cache / rate limiting | Redis (Upstash) | Atomic counters, TTL support, serverless-friendly free tier |
| Database | Postgres (Neon), pooled connection | Structured, queryable request logs that persist across deploys/restarts |
| Hosting | Render (free tier) | Simple deploy; cold-start tradeoff accepted for a demo project |

## Results (measured against `eval/run_eval.py`, 25 automated test cases)

All numbers below are pulled directly from `request_logs` in Neon, scoped to this specific eval run by timestamp — not estimated.

- **25/25 automated test cases passed** (validation, token limits, rate limits, cache hit/miss correctness, PII detection, prompt injection blocking, ordering interactions)
- Total logged requests in this run: **34**
- Cache hits: **5** (14.7% of logged requests in this run)
- Tokens saved via caching: **1,530 tokens**
- PII instances caught and redacted: **12**
- Prompt injection attempts blocked: **5/5** direct pattern-matched attempts (100%); **1** rephrased variant confirmed to bypass regex detection — an expected, documented limitation, not a missed bug
- Total measured cost across this run: **$0.000564**

See `eval/gateway_test_queries.csv` and `eval/results/eval_results.json` for the full test matrix and raw per-case results.

## Project structure

```
.
├── src/app/main.py            # backend entrypoint (FastAPI)
├── frontend/app.py            # frontend entrypoint (Streamlit)
├── requirements.txt           # backend dependencies
├── requirements.frontend.txt  # frontend dependencies (kept separate — Streamlit's
│                               # dependency set doesn't need to ship with the API,
│                               # and vice versa)
├── eval/                      # test cases, queries CSV, run_eval.py, migration SQL
└── ...
```

## Setup (local development)

```bash
git clone https://github.com/Sunny-sketchs/LLM-Gateway
cd llm-gateway
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

Backend:

```bash
pip install -r requirements.txt
```

Frontend (separate environment or same venv, your call):

```bash
pip install -r requirements.frontend.txt
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-key
REDIS_URL=rediss://default:xxx@your-db.upstash.io:6379
NEON_DATABASE_URL=postgresql://...   # use the POOLED connection string
DAILY_REQUEST_LIMIT=50
MAX_TOKENS_PER_REQUEST=500
LLM_MAX_OUTPUT_TOKENS=500
```

Run the migration once (via Neon's SQL editor, or `psql -f eval/migration_request_logs.sql "<connection-string>"`) to create `request_logs`.

Run the backend:

```bash
uvicorn src.app.main:app --reload
```

Run the frontend (in a separate terminal, backend must already be running):

```bash
streamlit run frontend/app.py
```

Run the eval suite against a running backend instance:

```bash
python -m eval.run_eval
```

## API

**`POST /ask`**

```json
// Request
{ "query": "What's the capital of France?", "user_id": "guest", "provider": "openai" }

// Response (200) — CacheEntry wrapping AskResponse
{
  "response": {
    "response": "The capital of France is Paris.",
    "tokens_used": 42,
    "provider": "openai",
    "cache_hit": false,
    "pii_detected": false
  },
  "cached_at": null
}

// Rejected (403 injection / 400 token limit / 422 validation / 429 rate limit)
{ "detail": "Request logged as potential prompt injection attempt." }
```

**`GET /usage`** — returns `{ "used": N, "limit": N, "remaining": N }`.

## Auth (current state)

Single guest-user mode — no API keys, no signup. This is a deliberate MVP scoping decision, not an oversight: the schema for admin-issued, hashed API keys (`users` + `api_keys` tables in Neon) is designed but not yet wired up. Real deployment would issue keys the same way most internal company AI gateways actually work — admin-provisioned, not self-service signup — so a full login/signup system was intentionally out of scope.

## Limitations (known, not hidden)

- **Prompt injection detection is keyword/pattern-based.** Catches obvious, literal phrasings but is bypassed by rephrasing — confirmed empirically in testing (`"Disregard what you were told earlier"` slips through while `"Disregard the above..."` is caught). A production system would add an LLM-based classifier as a second layer to catch intent rather than exact phrasing.
- **Caching is exact-match, not semantic.** "What's the capital of France?" and "capital city of France?" are treated as different queries. Deliberate tradeoff — a semantic cache using embeddings would catch these but adds real cost (an embedding call per request) and complexity not justified at this scale.
- **PII-containing queries are never cached**, even when the underlying question is generic — a simplicity/privacy tradeoff over redact-then-cache. In practice this loses little real cache coverage, since PII-adjacent phrasing rarely repeats verbatim across different requests anyway.
- **Indian phone number and PAN detection are custom regex recognizers**, not NLP-assisted like Presidio's built-in types — pure pattern matching, no contextual disambiguation or checksum validation.
- **Single LLM provider currently.** Multi-provider fallback (OpenAI/Gemini/Claude/Grok) via a unified input/output adapter layer is designed but not implemented.
- **Rate limiting uses a fixed time-window counter**, with the known boundary edge case where requests spanning two adjacent windows can briefly exceed the intended rate. A sliding-window or token-bucket algorithm would close this; not necessary at current traffic scale.
- **Background tasks queued immediately before raising an `HTTPException` are silently dropped** — Starlette builds a fresh response for the exception path that never carries the original task queue forward. Found via a real debugging session (blocked-request logs were silently missing from Neon despite correct HTTP behavior); fixed by logging synchronously on all rejected/error paths instead of via `BackgroundTasks`.
- **Free-tier hosting means cold starts.** First request after ~15 min of inactivity is slow (Render sleep/wake, Neon compute suspend).

## Future Scope

- [ ] Admin-issued, hashed API key auth (schema designed, not wired up)
- [ ] Multi-provider support (Gemini, Claude, Grok) with fallback routing
- [ ] Daily *token-sum* limit (currently only request-count limits exist)
- [ ] LLM-based injection classifier as a second detection layer
- [ ] Simple usage dashboard visualizing requests, cost, and cache savings over time

---

Built as a learning project to explore the systems side of deploying LLMs safely — auth, cost control, and auditability — rather than just calling an API and printing the response.
