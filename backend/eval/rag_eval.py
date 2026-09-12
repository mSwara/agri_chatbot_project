"""
Small grounding-accuracy eval for the RAG endpoints (/get-scheme-info,
/get-agriculture-info).

Methodology: for each question, we know a fact that MUST appear in a
correct, grounded answer (e.g. a subsidy percentage, an interest rate, a
scheme name). We call the live endpoint and check whether at least one of
the expected keywords/phrases shows up in the generated answer. This is a
simple but legitimate "did the model surface the right grounded fact"
check — not a fuzzy/semantic eval, so the resulting number is defensible:
it's exactly "N/M answers contained the expected key fact".

Usage:
    python eval/rag_eval.py
Requires the backend running locally on :8000 with GROQ_API_KEY set.
"""
import re
import sys
import time
import requests

# Re-open stdout as UTF-8 so LLM output (narrow no-break spaces, em dashes,
# etc.) doesn't crash on Windows' default cp1252 console encoding.
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"


def _normalize(text: str) -> str:
    """Collapse all Unicode whitespace variants (e.g. U+202F narrow no-break
    space, which LLMs commonly emit before a % sign) down to a plain space."""
    return re.sub(r"\s+", " ", text)

# Each case: (endpoint, query, [any of these substrings counts as a pass])
CASES = [
    ("/get-scheme-info", "What is PM-KISAN and how much money do farmers get?",
     ["6,000", "6000", "2,000", "2000"]),
    ("/get-scheme-info", "What percentage subsidy is available for drip irrigation for small farmers under PMKSY?",
     ["55%", "55 %", "55 percent"]),
    ("/get-scheme-info", "What interest rate applies to a Kisan Credit Card loan?",
     ["4%", "4 %", "four percent"]),
    ("/get-scheme-info", "What is PMFBY and what is the premium a farmer pays for Kharif crops?",
     ["2%", "2 %", "crop insurance"]),
    ("/get-scheme-info", "What does the Soil Health Card scheme do?",
     ["soil test", "nutrient", "fertiliz"]),
    ("/get-scheme-info", "What is e-NAM?",
     ["electronic", "e-nam", "mandi", "market"]),
    ("/get-scheme-info", "How much financial assistance does PKVY give per hectare for organic farming?",
     ["50,000", "50000"]),
    ("/get-scheme-info", "What is the interest subvention under the Agriculture Infrastructure Fund?",
     ["3%", "3 %", "three percent"]),
    ("/get-agriculture-info", "How do I protect tomatoes from leaf curl disease?",
     ["whitefly", "white fly", "resistant variety", "neem"]),
    ("/get-agriculture-info", "What is the recommended pest control approach for rice/paddy stem borer?",
     ["insecticide", "pesticide", "pheromone", "biological control", "predator"]),
    ("/get-agriculture-info", "When should wheat be sown in North India?",
     ["november", "october", "rabi", "winter"]),
    ("/get-agriculture-info", "What causes yellowing of leaves in crops and how is it treated?",
     ["nitrogen", "iron", "deficiency", "fertiliz"]),
]


def run():
    results = []
    for endpoint, query, expected in CASES:
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}{endpoint}", json={"query": query}, timeout=60)
            elapsed = time.time() - start
            answer = resp.json().get("answer", "") if resp.status_code == 200 else ""
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start
            answer = f"<request failed: {exc}>"

        answer_norm = _normalize(answer).lower()
        passed = any(_normalize(kw).lower() in answer_norm for kw in expected)
        results.append((query, passed, elapsed, answer[:120]))
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] ({elapsed:.1f}s) {query}")
        if not passed:
            print(f"        expected one of: {expected}")
            print(f"        got: {answer[:200]!r}")

    total = len(results)
    passed_count = sum(1 for _, p, _, _ in results if p)
    avg_latency = sum(e for _, _, e, _ in results) / total

    print("\n" + "=" * 60)
    print(f"RAG grounding accuracy: {passed_count}/{total} = {passed_count/total*100:.1f}%")
    print(f"Average response latency: {avg_latency:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    run()
