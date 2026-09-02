#!/usr/bin/env python3
"""One-time migration (PRD Phase 1.7): ai-gateway/docs/model-catalog.md into
ledger/models.jsonl. The source is a hand-written Hebrew markdown snapshot
(prices drift — see the file's own disclaimer), so this is transcribed by
hand into a table below rather than table-scraped from the markdown; re-run
after updating MODELS if the source doc changes.

Tiers per PRD §6.2/§7.2: T0 local free · T1 cheap cloud · T2 mid · T3 frontier.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import Store  # noqa: E402

SOURCE = "ai-gateway/docs/model-catalog.md (collected 2026-08-23)"

# id, provider, model, tier, input, cache_hit, output, context_k, data_residency, strengths
MODELS = [
    ("kimi-coder", "Moonshot/Kimi", "kimi-k2.7-code", "T1", 0.95, 0.19, 4.00, 262, "cloud", ["coding"]),
    ("kimi-fast", "Moonshot/Kimi", "kimi-k2.7-code-highspeed", "T1", 1.90, 0.38, 8.00, 262, "cloud", ["coding"]),
    ("kimi", "Moonshot/Kimi", "kimi-k3", "T2", 3.00, 0.30, 15.00, 1000, "cloud", ["long-context", "reasoning"]),
    ("local-coder", "local/Ollama", "qwen2.5-coder:14b", "T0", 0, 0, 0, 32, "local", ["coding"]),
    ("local-fast", "local/Ollama", "gemma4:12b", "T0", 0, 0, 0, 32, "local", ["classification", "summarize"]),
    ("local-tiny", "local/Ollama", "mistral:latest", "T0", 0, 0, 0, 32, "local", ["classification"]),
    ("claude-fable-5", "Anthropic", "Claude Fable 5", "T3", 10.00, 1.00, 50.00, 200, "cloud", ["reasoning", "coding"]),
    ("claude-opus-5", "Anthropic", "Claude Opus 5", "T3", 5.00, 0.50, 25.00, 200, "cloud", ["reasoning", "coding"]),
    ("claude-sonnet-5", "Anthropic", "Claude Sonnet 5", "T2", 2.00, 0.20, 10.00, 200, "cloud", ["coding", "reasoning"]),
    ("claude-sonnet-4.6", "Anthropic", "Claude Sonnet 4.6 / 4.5", "T2", 3.00, 0.30, 15.00, 200, "cloud", ["coding"]),
    ("claude-haiku-4.5", "Anthropic", "Claude Haiku 4.5", "T1", 1.00, 0.10, 5.00, 200, "cloud", ["classification", "summarize"]),
    ("gemini-3.7-flash", "Google", "gemini-3.7-flash", "T1", 0.75, None, 3.75, 1000, "cloud", ["long-context"]),
    ("gemini-3.5-flash-lite", "Google", "gemini-3.5-flash-lite", "T1", 0.30, None, 2.50, 1000, "cloud", ["classification"]),
    ("gemini-3.1-flash-lite", "Google", "gemini-3.1-flash-lite", "T1", 0.25, None, 1.50, 1000, "cloud", ["classification"]),
    ("gemini-2.5-pro", "Google", "gemini-2.5-pro", "T2", 1.25, None, 10.00, 1000, "cloud", ["reasoning", "vision"]),
    ("gemini-2.5-flash", "Google", "gemini-2.5-flash", "T1", 0.30, None, 2.50, 1000, "cloud", ["classification"]),
    ("gemini-2.5-flash-lite", "Google", "gemini-2.5-flash-lite", "T1", 0.10, None, 0.40, 1000, "cloud", ["classification", "summarize"]),
    ("gpt-5.6-sol", "OpenAI", "gpt-5.6-sol", "T2", 4.00, 0.40, 20.00, 200, "cloud", ["coding"]),
    ("gpt-5.6-terra", "OpenAI", "gpt-5.6-terra", "T2", 2.00, 0.20, 12.00, 200, "cloud", ["coding"]),
    ("gpt-5.6-luna", "OpenAI", "gpt-5.6-luna", "T1", 0.20, 0.02, 1.20, 200, "cloud", ["classification"]),
    ("gpt-5.4", "OpenAI", "gpt-5.4", "T2", 2.50, 0.25, 15.00, 200, "cloud", ["coding", "reasoning"]),
    ("gpt-5.4-mini", "OpenAI", "gpt-5.4-mini", "T1", 0.75, 0.075, 4.50, 200, "cloud", ["classification"]),
    ("gpt-5.3-codex", "OpenAI", "gpt-5.3-codex", "T2", 1.75, 0.175, 14.00, 200, "cloud", ["coding"]),
    ("gpt-5", "OpenAI", "gpt-5", "T2", 1.25, 0.125, 10.00, 200, "cloud", ["reasoning"]),
    ("gpt-5-mini", "OpenAI", "gpt-5-mini", "T1", 0.25, 0.025, 2.00, 200, "cloud", ["classification"]),
    ("gpt-5-nano", "OpenAI", "gpt-5-nano", "T1", 0.05, 0.005, 0.40, 200, "cloud", ["classification"]),
    ("deepseek-v4-flash", "DeepSeek", "deepseek-v4-flash", "T1", 0.33, 0.0105, 0.99, 128, "cloud", ["coding", "reasoning"]),
    ("deepseek-v4-pro", "DeepSeek", "deepseek-v4-pro", "T2", 0.99, 0.033, 2.97, 128, "cloud", ["reasoning"]),
    ("glm-4.7-flash", "Z.ai/GLM", "GLM-4.7-Flash", "T1", 0, 0, 0, 128, "cloud", ["classification"]),
    ("glm-4.5-flash", "Z.ai/GLM", "GLM-4.5-Flash", "T1", 0, 0, 0, 128, "cloud", ["classification"]),
    ("glm-4.7-flashx", "Z.ai/GLM", "GLM-4.7-FlashX", "T1", 0.07, None, 0.40, 128, "cloud", ["classification"]),
    ("glm-4.7", "Z.ai/GLM", "GLM-4.7 / 4.6 / 4.5", "T2", 0.60, None, 2.20, 128, "cloud", ["coding"]),
    ("glm-5", "Z.ai/GLM", "GLM-5", "T2", 1.00, None, 3.20, 128, "cloud", ["coding", "reasoning"]),
    ("glm-5.3", "Z.ai/GLM", "GLM-5.3 / 5.2 / 5.1", "T2", 1.40, None, 4.40, 128, "cloud", ["coding", "reasoning"]),
    ("grok-4.3", "xAI/Grok", "grok-4.3", "T2", 1.88, 0.30, 3.75, 1000, "cloud", ["long-context"]),
    ("grok-4.6", "xAI/Grok", "grok-4.6", "T2", 3.00, 0.75, 9.00, 500, "cloud", ["long-context"]),
    ("grok-build-0.1", "xAI/Grok", "grok-build-0.1", "T1", 1.50, 0.30, 3.00, 256, "cloud", ["coding"]),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=None)
    args = parser.parse_args()
    store = Store(backend_name="files", base_dir=args.base_dir)

    n = 0
    for mid, provider, model, tier, inp, cache, out, ctx, residency, strengths in MODELS:
        payload = {
            "provider": provider,
            "model": model,
            "tier": tier,
            "input_usd_mtok": inp,
            "output_usd_mtok": out,
            "context_k": ctx,
            "data_residency": residency,
            "strengths": strengths,
        }
        if cache is not None:
            payload["cache_hit_usd_mtok"] = cache
        store.append(
            kind="model.added",
            subject_id=mid,
            actor="system:migration",
            via="migration",
            reason=f"imported from {SOURCE}",
            payload=payload,
        )
        n += 1
    print(f"migrated {n} models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
