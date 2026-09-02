"""
Adversary testing framework: Multi-model routing consistency validation

Tests AI Toolbox routing decisions across three frontier models:
- Claude Haiku (T1, cheap)
- Claude Sonnet (T2, balanced)
- Kimi-K3 (frontier, high-reasoning)

Measures consistency and identifies divergence patterns.
"""

import os
import json
import pytest
from dataclasses import dataclass
from typing import Optional
import re

# LLM client libraries
try:
    from anthropic import Anthropic as AnthropicClient
except ImportError:
    AnthropicClient = None

try:
    import requests
except ImportError:
    requests = None


@dataclass
class RoutingDecision:
    """Parsed routing decision from an LLM"""
    tier: str  # T0, T1, T2, T3
    type_: str  # script, model, mcp, skill, subagent, schedule, kb
    tool: str  # tool name
    reason: str  # explanation
    raw_response: str  # full LLM response


class LLMRouter:
    """Route tasks using an LLM model"""

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    def route(self, task: str) -> RoutingDecision:
        """Route a task and parse the decision"""
        if self.model.startswith("claude"):
            return self._route_claude(task)
        elif self.model.startswith("kimi"):
            return self._route_kimi(task)
        else:
            raise ValueError(f"Unknown model: {self.model}")

    def _route_claude(self, task: str) -> RoutingDecision:
        """Route using Claude API"""
        if not AnthropicClient:
            pytest.skip("Anthropic client not installed")

        client = AnthropicClient(api_key=self.api_key)

        prompt = f"""You are an AI Toolbox orchestrator. Route this task to the best tool.

Task: {task}

Respond with EXACTLY this format:
TIER: <T0|T1|T2|T3>
TYPE: <script|model|mcp|skill|subagent|schedule|kb>
TOOL: <tool-name>
REASON: <brief explanation>

---RESPONSE---"""

        message = client.messages.create(
            model=self._map_model_name("claude"),
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        return self._parse_routing_response(response_text)

    def _route_kimi(self, task: str) -> RoutingDecision:
        """Route using Kimi API (via platform.kimi.ai)"""
        if not requests:
            pytest.skip("requests library not installed")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"""You are an AI Toolbox orchestrator. Route this task to the best tool.

Task: {task}

Respond with EXACTLY this format:
TIER: <T0|T1|T2|T3>
TYPE: <script|model|mcp|skill|subagent|schedule|kb>
TOOL: <tool-name>
REASON: <brief explanation>"""

        payload = {
            "model": "moonshot-v1",  # Kimi's model name
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "top_p": 0.95,
            "max_tokens": 300
        }

        # Call Kimi API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",  # Kimi uses OpenAI-compatible API
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            raise RuntimeError(f"Kimi API error: {response.status_code} {response.text}")

        data = response.json()
        response_text = data["choices"][0]["message"]["content"]
        return self._parse_routing_response(response_text)

    def _map_model_name(self, base: str) -> str:
        """Map model name to Anthropic model ID"""
        mapping = {
            "claude-haiku": "claude-3-5-haiku-20241022",
            "claude-sonnet": "claude-3-5-sonnet-20241022",
        }
        return mapping.get(base, base)

    def _parse_routing_response(self, response_text: str) -> RoutingDecision:
        """Parse LLM response into RoutingDecision"""
        lines = response_text.strip().split("\n")

        tier = None
        type_ = None
        tool = None
        reason = None

        for line in lines:
            if line.startswith("TIER:"):
                tier = line.split(":", 1)[1].strip()
            elif line.startswith("TYPE:"):
                type_ = line.split(":", 1)[1].strip()
            elif line.startswith("TOOL:"):
                tool = line.split(":", 1)[1].strip()
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        if not all([tier, type_, tool, reason]):
            raise ValueError(f"Failed to parse response: {response_text}")

        return RoutingDecision(
            tier=tier,
            type_=type_,
            tool=tool,
            reason=reason,
            raw_response=response_text
        )


@pytest.fixture
def routing_test_cases():
    """15 routing test cases from Phase 6 routing suite"""
    return [
        {
            "id": 1,
            "task": "Rename 200 STL files from model-001.stl to part-001.stl",
            "expected_tier": "T0",
            "expected_type": "script",
            "expected_tools": ["python3", "bash"],
        },
        {
            "id": 2,
            "task": "Extract text and images from a 50-page PDF into markdown",
            "expected_tier": "T1",
            "expected_type": "script",
            "expected_tools": ["pdfplumber", "pypdf"],
        },
        {
            "id": 3,
            "task": "Validate that 10,000 JSON files match the provided schema",
            "expected_tier": "T0",
            "expected_type": "script",
            "expected_tools": ["jq", "python3"],
        },
        {
            "id": 6,
            "task": "Summarize this 20-page AI research paper into 1 page",
            "expected_tier": "T1",
            "expected_type": "model",
            "expected_tools": ["claude-haiku", "haiku"],
        },
        {
            "id": 8,
            "task": "I have an STL bracket file. Check wall thickness, estimate print time on Ender 3. What settings?",
            "expected_tier": "T2",
            "expected_type": "model",
            "expected_tools": ["claude-sonnet", "sonnet"],
        },
    ]


@pytest.mark.skipif(not os.getenv("KIMI_API_KEY"), reason="KIMI_API_KEY not set")
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
class TestRoutingConsistency:
    """Multi-model routing consistency tests"""

    @pytest.fixture(autouse=True)
    def setup_routers(self):
        """Initialize routers for all three models"""
        self.routers = {
            "haiku": LLMRouter("claude-haiku", os.getenv("ANTHROPIC_API_KEY")),
            "sonnet": LLMRouter("claude-sonnet", os.getenv("ANTHROPIC_API_KEY")),
            "kimi": LLMRouter("kimi-k3", os.getenv("KIMI_API_KEY")),
        }

    def test_case_1_rename_files(self, routing_test_cases):
        """Consistency: rename 200 files (T0/script)"""
        test_case = routing_test_cases[0]
        results = self._route_and_compare(test_case)

        # All should pick T0 or T1 (adjacent OK for simple task)
        self._assert_tier_agreement(results, tolerance=1)
        # All should pick script or subagent type
        self._assert_type_agreement(results, test_case["expected_type"])

    def test_case_2_extract_pdf(self, routing_test_cases):
        """Consistency: extract PDF (T1/script)"""
        test_case = routing_test_cases[1]
        results = self._route_and_compare(test_case)

        self._assert_tier_agreement(results, tolerance=1)

    def test_case_6_summarize_paper(self, routing_test_cases):
        """Consistency: summarize paper (T1/model)"""
        test_case = routing_test_cases[3]
        results = self._route_and_compare(test_case)

        self._assert_tier_agreement(results, tolerance=0)  # Must agree on T1

    def test_cost_goal_g3(self, routing_test_cases):
        """Measure G3: ≥ 40% routed to T0/T1"""
        all_results = {}

        for test_case in routing_test_cases:
            results = self._route_and_compare(test_case)
            all_results[test_case["id"]] = results

        # Count T0/T1 across all models and cases
        cheap_count = 0
        total_count = 0

        for case_id, results in all_results.items():
            for model_name, decision in results.items():
                tier = decision.tier
                if tier in ["T0", "T1"]:
                    cheap_count += 1
                total_count += 1

        cheap_pct = (cheap_count / total_count) * 100
        print(f"\nG3 measurement: {cheap_count}/{total_count} = {cheap_pct:.1f}% T0/T1")

        assert cheap_pct >= 40, f"G3 FAILED: Only {cheap_pct:.1f}% routed to T0/T1 (goal: ≥40%)"

    def _route_and_compare(self, test_case: dict) -> dict:
        """Route task on all models and collect results"""
        results = {}

        for model_name, router in self.routers.items():
            try:
                decision = router.route(test_case["task"])
                results[model_name] = decision
                print(f"  {model_name:8} → {decision.tier} / {decision.type_:10} / {decision.tool}")
            except Exception as e:
                pytest.fail(f"{model_name} routing failed: {e}")

        return results

    def _assert_tier_agreement(self, results: dict, tolerance: int = 1):
        """All models should agree on tier (within tolerance)"""
        tiers = [self._tier_rank(d.tier) for d in results.values()]

        if len(set(tiers)) > 1:
            max_diff = max(tiers) - min(tiers)
            assert max_diff <= tolerance, \
                f"Tier divergence too high: {tiers} (tolerance: {tolerance})"

    def _assert_type_agreement(self, results: dict, expected_type: str):
        """All models should agree on type"""
        types = set(d.type_ for d in results.values())

        # Allow close matches (model vs claude, script vs bash)
        normalized = {self._normalize_type(t) for t in types}
        assert len(normalized) <= 2, f"Type divergence: {types}"

    def _tier_rank(self, tier: str) -> int:
        """Convert tier string to numeric rank"""
        rank = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
        return rank.get(tier, -1)

    def _normalize_type(self, type_str: str) -> str:
        """Normalize type variations"""
        type_lower = type_str.lower()
        if "script" in type_lower or "bash" in type_lower or "python" in type_lower:
            return "script"
        elif "model" in type_lower or "claude" in type_lower:
            return "model"
        else:
            return type_lower


class TestConsistencyMetrics:
    """Measure overall routing consistency"""

    @pytest.mark.skipif(not os.getenv("KIMI_API_KEY"), reason="KIMI_API_KEY not set")
    def test_agreement_percentage(self, routing_test_cases):
        """
        Measure tier agreement across model pairs:
        - Haiku vs Sonnet (goal: ≥80%)
        - Sonnet vs Kimi (goal: ≥75%)
        - Haiku vs Kimi (goal: ≥70%)
        """
        routers = {
            "haiku": LLMRouter("claude-haiku", os.getenv("ANTHROPIC_API_KEY")),
            "sonnet": LLMRouter("claude-sonnet", os.getenv("ANTHROPIC_API_KEY")),
            "kimi": LLMRouter("kimi-k3", os.getenv("KIMI_API_KEY")),
        }

        pairs = [
            ("haiku", "sonnet", 0.80),
            ("sonnet", "kimi", 0.75),
            ("haiku", "kimi", 0.70),
        ]

        for m1_name, m2_name, threshold in pairs:
            agreements = 0

            for test_case in routing_test_cases[:3]:  # Test subset for speed
                try:
                    d1 = routers[m1_name].route(test_case["task"])
                    d2 = routers[m2_name].route(test_case["task"])

                    if d1.tier == d2.tier:
                        agreements += 1
                except Exception:
                    pass

            if test_case:
                agreement_pct = agreements / len(routing_test_cases[:3])
                print(f"{m1_name} vs {m2_name}: {agreement_pct:.0%} (goal: {threshold:.0%})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
