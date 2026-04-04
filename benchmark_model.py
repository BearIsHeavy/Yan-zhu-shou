#!/usr/bin/env python
"""
Benchmark script for evaluating LLM models against project requirements.

Usage:
    python benchmark_model.py                           # Use model from .env
    python benchmark_model.py qwen2.5:7b                  # Test specific model
    python benchmark_model.py qwen2.5:7b http://host:port # Custom endpoint

Requirements:
    - Ollama running and accessible
    - Target model pulled via: ollama pull <model>
"""

import asyncio
import json
import sys
import time
from typing import Any

# Ensure .env is loaded before importing config
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from ai_analysis.llm_client import LLMClient
from ai_analysis.config import AIAnalysisConfig


class BenchmarkResult:
    """Stores benchmark results."""

    def __init__(self):
        self.results = []
        self.total = 0
        self.success = 0
        self.failed = 0
        self.empty_response = 0
        self.json_parse_fail = 0
        self.total_time = 0.0

    def add(self, name: str, success: bool, elapsed: float, detail: str = ""):
        self.total += 1
        if success:
            self.success += 1
        else:
            self.failed += 1
        self.total_time += elapsed
        self.results.append({
            "name": name,
            "success": success,
            "time": round(elapsed, 2),
            "detail": detail[:100] if detail else "",
        })

    def summary(self) -> str:
        avg_time = self.total_time / max(self.total, 1)
        success_rate = (self.success / max(self.total, 1)) * 100
        lines = [
            "=" * 60,
            f"  Model: {AIAnalysisConfig.OPENAI_MODEL}",
            f"  Base URL: {AIAnalysisConfig.OPENAI_BASE_URL}",
            "=" * 60,
            "",
            f"  Total tests:     {self.total}",
            f"  Passed:          {self.success} ({success_rate:.0f}%)",
            f"  Failed:          {self.failed}",
            f"  Avg response:    {avg_time:.1f}s",
            "",
            "-" * 60,
            f"  {'Test':<35} {'Time':>6} {'Status':>8}",
            "-" * 60,
        ]
        for r in self.results:
            status = "✅ OK" if r["success"] else "❌ FAIL"
            lines.append(f"  {r['name']:<35} {r['time']:>5.1f}s  {status:>7}")
            if r["detail"] and not r["success"]:
                lines.append(f"    → {r['detail']}")
        lines.append("-" * 60)
        lines.append("")

        # Capability assessment
        lines.append("  Capability Assessment:")
        if success_rate >= 90 and avg_time < 30:
            lines.append("  ✅ EXCELLENT — Model is ready for production")
        elif success_rate >= 70 and avg_time < 60:
            lines.append("  ⚠️  ACCEPTABLE — Model works, may need prompt tuning")
        elif success_rate >= 50:
            lines.append("  ⚠️  MARGINAL — Model barely meets requirements")
        else:
            lines.append("  ❌ INSUFFICIENT — Model too small for these tasks")

        if avg_time > 30:
            lines.append(f"  ⚠️  Warning: Average response time is {avg_time:.0f}s (target: <30s)")

        lines.append("")
        return "\n".join(lines)


async def run_benchmark(model_name: str | None = None) -> BenchmarkResult:
    """Run all benchmark tests against the specified model."""
    client = LLMClient(model=model_name)
    result = BenchmarkResult()

    print(f"Testing model: {client.model}")
    print(f"Base URL: {client.base_url}")
    print()

    def _print_answer(question: str, answer: str, elapsed: float):
        """Helper: print question, answer, and timing."""
        print(f"  耗时: {elapsed:.1f}s")
        print(f"  问题: {question}")
        print(f"  回答: {answer[:300]}{'...' if len(answer) > 300 else ''}")
        print()

    def _print_parsed(question: str, raw: str, parsed: Any, elapsed: float):
        """Helper: print question, raw answer, and parsed result."""
        print(f"  耗时: {elapsed:.1f}s")
        print(f"  问题: {question}")
        print(f"  原始回答: {raw[:300]}{'...' if len(raw) > 300 else ''}")
        if parsed is not None:
            import pprint
            pretty = pprint.pformat(parsed, width=80)
            print(f"  解析结果: {pretty[:300]}{'...' if len(pretty) > 300 else ''}")
        else:
            print(f"  解析结果: (解析失败)")
        print()

    # ----- Test 1: Basic Chat -----
    print("[1/10] Basic chat")
    start = time.time()
    try:
        question = "What is 2+2? One word."
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        ok = bool(resp) and len(resp.strip()) > 0
        result.add("Basic chat", ok, elapsed, resp[:100] if not ok else "")
        _print_answer(question, resp or "(empty)", elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Basic chat", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 2: JSON Format — Simple -----
    print("[2/10] JSON format — simple")
    start = time.time()
    try:
        question = 'Return ONLY this JSON: {"name":"test","count":3}'
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        data = client.parse_json_response(resp)
        ok = isinstance(data, dict) and data.get("name") == "test" and data.get("count") == 3
        result.add("JSON format — simple", ok, elapsed, resp[:100] if not ok else "")
        _print_parsed(question, resp, data, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("JSON format — simple", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 3: JSON Array format -----
    print("[3/10] JSON format — array")
    start = time.time()
    try:
        question = 'Return a JSON array of 3 fruits: [{"name":"Apple"},{"name":"Banana"},{"name":"Cherry"}]'
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        data = client.parse_json_response(resp)
        ok = isinstance(data, list) and len(data) == 3 and all("name" in item for item in data)
        result.add("JSON format — array", ok, elapsed, resp[:100] if not ok else "")
        _print_parsed(question, resp, data, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("JSON format — array", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 4: JSON with nested objects -----
    print("[4/10] JSON format — nested")
    start = time.time()
    try:
        question = """Return ONLY valid JSON (no markdown, no extra text):
{
    "student": {
        "name": "Alice",
        "scores": {"math": 95, "english": 88}
    },
    "passed": true
}"""
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        data = client.parse_json_response(resp)
        ok = (
            isinstance(data, dict)
            and data.get("student", {}).get("name") == "Alice"
            and data.get("student", {}).get("scores", {}).get("math") == 95
            and data.get("passed") is True
        )
        result.add("JSON format — nested", ok, elapsed, resp[:150] if not ok else "")
        _print_parsed(question, resp, data, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("JSON format — nested", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 5: JSON list of objects (project use case) -----
    print("[5/10] JSON format — knowledge points")
    start = time.time()
    try:
        question = """Extract knowledge points from this text and return ONLY a JSON array:

"Linear equations have the form ax + b = c. To solve, isolate x. The quadratic formula is x = (-b ± √(b²-4ac)) / 2a."

Return format:
[{"name": "...", "description": "...", "difficulty": 1-5}]

No explanation, just the JSON array."""
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        data = client.parse_json_response(resp)
        has_fields = isinstance(data, list) and all("name" in item for item in data)
        result.add("JSON format — knowledge points", has_fields, elapsed, resp[:150] if not has_fields else "")
        _print_parsed(question, resp, data, elapsed)
        print(f"  状态: {'✅ OK' if has_fields else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("JSON format — knowledge points", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 6: Weak Point Analysis -----
    print("[6/10] Weak point analysis")
    start = time.time()
    try:
        wrong_questions = [
            {"question_no": "Q001", "category": "Algebra", "stem": "Solve: 2x+3=7", "user_answer": "x=5", "correct_ans_summary": "x=2"},
            {"question_no": "Q002", "category": "Algebra", "stem": "Solve: 3x-1=8", "user_answer": "x=1", "correct_ans_summary": "x=3"},
        ]
        question = f"分析 {len(wrong_questions)} 道错题的薄弱点"
        analysis = await client.analyze_weak_points(wrong_questions)
        elapsed = time.time() - start
        ok = analysis.get("summary", "") != "Analysis failed"
        if not ok:
            result.empty_response += 1
            result.json_parse_fail += 1
        result.add("Weak point analysis", ok, elapsed)
        _print_parsed(question, json.dumps(analysis, indent=2, ensure_ascii=False), analysis, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Weak point analysis", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 7: Knowledge Point Extraction -----
    print("[7/10] Knowledge extraction")
    start = time.time()
    try:
        text = "Linear equations describe straight lines. They have the form ax + b = c. To solve, isolate the variable."
        question = f"从文本中提取知识点 (subject=Math):\n\n{text}"
        kps = await client.extract_knowledge_points(text, subject="Math")
        elapsed = time.time() - start
        ok = len(kps) > 0
        if not ok:
            result.empty_response += 1
        result.add("Knowledge extraction", ok, elapsed)
        _print_parsed(question, json.dumps(kps, indent=2, ensure_ascii=False), kps, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Knowledge extraction", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 8: Recommendation Generation -----
    print("[8/10] Recommendation generation")
    start = time.time()
    try:
        weak_points = [
            {"knowledge": "Algebra", "error_count": 5, "confidence": 0.3},
            {"knowledge": "Geometry", "error_count": 3, "confidence": 0.5},
        ]
        question = f"基于 {len(weak_points)} 个薄弱点生成推荐 (user_level=beginner)"
        recs = await client.generate_recommendations(weak_points, user_level="beginner")
        elapsed = time.time() - start
        ok = len(recs) > 0
        if not ok:
            result.empty_response += 1
        result.add("Recommendation generation", ok, elapsed)
        _print_parsed(question, json.dumps(recs, indent=2, ensure_ascii=False), recs, elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Recommendation generation", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 9: Long Context Understanding -----
    print("[9/10] Long context understanding")
    start = time.time()
    try:
        long_text = "二次函数是形如y=ax²+bx+c的函数，其中a≠0。它的图像是一条抛物线。当a>0时，抛物线开口向上；当a<0时，抛物线开口向下。二次函数的顶点坐标为(-b/2a, (4ac-b²)/4a)。对称轴是x=-b/2a。二次函数在实际中有广泛应用，如物理中的抛体运动、经济中的利润最大化等。"
        question = f"Read this and summarize in one sentence:\n\n{long_text}"
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        ok = bool(resp) and len(resp.strip()) > 5
        result.add("Long context understanding", ok, elapsed, resp[:100] if not ok else "")
        _print_answer(question, resp or "(empty)", elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Long context understanding", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    # ----- Test 10: Chinese Language Capability -----
    print("[10/10] Chinese language capability")
    start = time.time()
    try:
        question = "用中文解释什么是勾股定理，两句话以内。"
        resp = await client.chat([{"role": "user", "content": question}])
        elapsed = time.time() - start
        ok = bool(resp) and ("勾股" in resp or "直角" in resp or "三角形" in resp or "a²" in resp)
        result.add("Chinese language capability", ok, elapsed, resp[:100] if not ok else "")
        _print_answer(question, resp or "(empty)", elapsed)
        print(f"  状态: {'✅ OK' if ok else '❌ FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        result.add("Chinese language capability", False, elapsed, str(e))
        print(f"  ❌ Exception: {e}\n")

    return result


def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else None
    base_url = sys.argv[2] if len(sys.argv) > 2 else None

    if model_name:
        AIAnalysisConfig.OPENAI_MODEL = model_name
    if base_url:
        AIAnalysisConfig.OPENAI_BASE_URL = base_url.rstrip("/")

    print("=" * 60)
    print("  LLM Model Benchmark for YanZhuShou Project")
    print("=" * 60)
    print()

    result = asyncio.run(run_benchmark(model_name))
    print()
    print(result.summary())


if __name__ == "__main__":
    main()
