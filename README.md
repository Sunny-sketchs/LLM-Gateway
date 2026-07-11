# LLM Gateway

A FastAPI proxy that sits between client apps and an LLM API, adding 
PII redaction, prompt-injection detection, rate limiting, caching, 
and request-level cost/audit logging.

## Status: 🚧 In progress

## Architecture
Client → Gateway (FastAPI) → LLM API
              ↓
      [middleware: redact PII → check injection → rate limit → cache check]
              ↓
         log request/cost

## Progress
- [ ] Part 1: Bare proxy
- [ ] Part 2: Middleware
- [ ] Part 3: PII redaction (Presidio)
- [ ] Part 4: Prompt-injection check
- [ ] Part 5: Rate limiting (Redis)
- [ ] Part 6: Logging + cost tracking
- [ ] Part 7: Caching
- [ ] Part 8: Dashboard