# AgriBot benchmarks

Two small scripts to measure real numbers instead of guessing them.

## RAG grounding accuracy — `rag_eval.py`

A 12-question set against `/get-scheme-info` and `/get-agriculture-info`,
each with a known fact that must appear in a correct answer (a subsidy %,
an interest rate, a scheme name, etc.). Checks whether the generated answer
contains at least one of the expected keywords/phrases.

```bash
python eval/rag_eval.py
```

**Result (2026-09-11, 12 questions):** 12/12 = 100% grounding accuracy,
9.2s average response latency (includes the Groq LLM call + retrieval).

This is a small sample — good enough to demonstrate the eval methodology
and catch regressions, not a statistically rigorous benchmark. Extend
`CASES` in the script with more Q&A pairs for a stronger number.

## Load test — `load_test.py`

Async concurrent load test against any endpoint, reporting throughput and
P50/P95/P99 latency.

```bash
python eval/load_test.py --endpoint /health --method GET --concurrency 50 --total 500
python eval/load_test.py --endpoint /detect-language --method POST \
    --payload '{"text": "hello"}' --concurrency 20 --total 200
python eval/load_test.py --endpoint /chat --method POST \
    --payload '{"message": "hello"}' --concurrency 5 --total 20
```

**Results (2026-09-11, single-process `uvicorn --reload` dev server, local machine):**

| Endpoint | Concurrency | Total | Success | Throughput | P50 | P95 |
|---|---|---|---|---|---|---|
| `GET /health` | 50 | 500 | 100% | 167 req/s | 280 ms | 348 ms |
| `POST /detect-language` | 20 | 200 | 100% | 275 req/s | 37 ms | 356 ms |
| `POST /chat` (full pipeline: LLM + translation + TTS) | 5 | 20 | 100% | 0.6 req/s | 8.2 s | 9.4 s |

Notes:
- These are dev-server numbers on a single machine/process — a production
  deployment (multiple `uvicorn` workers behind a load balancer, or serving
  from a paid/higher-tier LLM API) would improve on this, especially for
  `/chat`, but this repo has not been tested that way.
- `/chat` concurrency was kept modest deliberately: the Groq free tier has
  real rate limits, so pushing higher concurrency here mostly tests Groq's
  rate limiter, not this app's own performance.
