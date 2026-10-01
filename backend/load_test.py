"""Configurable asynchronous HTTP load probe for a deployed Quiz API.

Example:
  python load_test.py https://api.example.com/health --users 20 --seconds 30
  python load_test.py https://api.example.com/api/quizzes/ --users 20 --seconds 30

Use only against an environment you own. For protected routes, provide
QUIZ_LOAD_TEST_TOKEN in the environment. This probe measures a single GET route;
it does not simulate authenticated exam submissions or database writes.
"""
import argparse
import asyncio
import os
import statistics
import time

import httpx


async def run(url: str, concurrency: int, duration: float, token: str | None):
    latencies: list[float] = []
    failures: list[str] = []
    requests = 0
    stop_at = time.monotonic() + duration
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    timeout = httpx.Timeout(20.0)

    async with httpx.AsyncClient(headers=headers, limits=limits, timeout=timeout) as client:
        async def worker():
            nonlocal requests
            while time.monotonic() < stop_at:
                started = time.perf_counter()
                try:
                    response = await client.get(url)
                    latencies.append((time.perf_counter() - started) * 1000)
                    requests += 1
                    if response.status_code >= 400:
                        failures.append(f"HTTP {response.status_code}")
                except httpx.HTTPError as exc:
                    requests += 1
                    failures.append(type(exc).__name__)

        await asyncio.gather(*(worker() for _ in range(concurrency)))

    ordered = sorted(latencies)
    percentile = lambda p: ordered[min(int((len(ordered) - 1) * p), len(ordered) - 1)] if ordered else None
    print(f"URL: {url}")
    print(f"Concurrency: {concurrency}; duration: {duration:.1f}s")
    print(f"Requests: {requests}; failures: {len(failures)}")
    if latencies:
        print(f"Latency ms: mean={statistics.fmean(latencies):.1f}, p50={percentile(.50):.1f}, p95={percentile(.95):.1f}, p99={percentile(.99):.1f}, max={max(latencies):.1f}")
    if failures:
        from collections import Counter
        print(f"Failure types: {dict(Counter(failures))}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if args.users < 1 or args.seconds <= 0:
        parser.error("--users must be positive and --seconds must be greater than zero")
    asyncio.run(run(args.url, args.users, args.seconds, os.getenv("QUIZ_LOAD_TEST_TOKEN")))


if __name__ == "__main__":
    main()
