"""
Honest load test for the FastAPI backend.

Measures real throughput and P50/P95/P99 latency for a given endpoint under
concurrent load, using asyncio + httpx. Two separate runs are meant to be
reported separately and NOT conflated:

  1. A lightweight, non-LLM endpoint (e.g. /detect-language) — this reflects
     the raw FastAPI/API-layer throughput.
  2. The /chat endpoint — this reflects real end-to-end latency including the
     Groq LLM call, translation, and TTS generation. Free-tier Groq accounts
     have real rate limits, so concurrency here is intentionally modest
     (matches what the app can actually sustain) rather than an arbitrary
     "1000 concurrent users" claim that was never tested.

Usage:
    python eval/load_test.py --endpoint /health --method GET --concurrency 50 --total 300
    python eval/load_test.py --endpoint /detect-language --method POST \
        --payload '{"text": "hello, how are you"}' --concurrency 50 --total 300
    python eval/load_test.py --endpoint /chat --method POST \
        --payload '{"message": "hello"}' --concurrency 5 --total 20
"""
import argparse
import asyncio
import json
import time

import httpx

BASE_URL = "http://localhost:8000"


async def _one_request(client: httpx.AsyncClient, method: str, endpoint: str, payload: dict | None):
    start = time.perf_counter()
    try:
        if method == "GET":
            resp = await client.get(endpoint)
        else:
            resp = await client.post(endpoint, json=payload)
        ok = resp.status_code == 200
    except Exception:  # noqa: BLE001
        ok = False
    return time.perf_counter() - start, ok


async def run(endpoint: str, method: str, payload: dict | None, concurrency: int, total: int):
    latencies: list[float] = []
    successes = 0

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        sem = asyncio.Semaphore(concurrency)

        async def bound_request():
            nonlocal successes
            async with sem:
                elapsed, ok = await _one_request(client, method, endpoint, payload)
                latencies.append(elapsed)
                if ok:
                    successes += 1

        wall_start = time.perf_counter()
        await asyncio.gather(*[bound_request() for _ in range(total)])
        wall_elapsed = time.perf_counter() - wall_start

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50) - 1] if n else 0
    p95 = latencies[int(n * 0.95) - 1] if n else 0
    p99 = latencies[int(n * 0.99) - 1] if n else 0
    throughput = total / wall_elapsed if wall_elapsed else 0

    print("=" * 60)
    print(f"Endpoint:        {method} {endpoint}")
    print(f"Total requests:  {total}")
    print(f"Concurrency:     {concurrency}")
    print(f"Successful:      {successes}/{total} ({successes/total*100:.1f}%)")
    print(f"Wall time:       {wall_elapsed:.2f}s")
    print(f"Throughput:      {throughput:.1f} req/s")
    print(f"Latency P50:     {p50*1000:.0f} ms")
    print(f"Latency P95:     {p95*1000:.0f} ms")
    print(f"Latency P99:     {p99*1000:.0f} ms")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--payload", default=None, help="JSON string body for POST")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--total", type=int, default=100)
    args = parser.parse_args()

    payload = json.loads(args.payload) if args.payload else None
    asyncio.run(run(args.endpoint, args.method, payload, args.concurrency, args.total))
