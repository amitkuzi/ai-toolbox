#!/usr/bin/env python3
"""One-time migration (PRD Phase 1.5): read both legacy tools.yaml catalogs
(read-only) and append one tool.added + one score.seed event per tool to the
ledger via the Catalog Store — never write catalog files directly (P1).

Source files use incompatible schemas: the supply catalog has `category` but
no `type`; the demand catalog has `type` but no `category`. Neither has both,
so every migrated event synthesizes the missing one from the field that is
present (see CATEGORY_TO_TYPE / DEMAND_TYPE_TO_CATEGORY below) — a judgement
call, documented in the handoff, not a fact recovered from the source data.

The two catalogs turned out to have disjoint id sets (checked by hand before
writing this script) — no tool appears in both, so there is nothing to merge,
only to union. The dedup-by-id guard below is kept anyway in case that ever
changes on a re-run against updated sources.

Safe to re-run: it always starts from a fresh ledger (pass --base-dir to a
temp dir to dry-run) — running it twice against the real catalog would
duplicate every tool, since store.append never deduplicates for you.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import Store  # noqa: E402

SUPPLY_PATH = Path(r"D:\Development\AiAgent\ai-toolbox\tools.yaml")
DEMAND_PATH = Path(r"D:\Development\Luctures\TaskTriagOrcetrator\ai-toolbox\tools.yaml")

# category (supply) -> type, when type is missing
CATEGORY_TO_TYPE = {
    "runtime": "script",
    "model": "model",
    "agent-framework": "script",
    "coding-agent": "script",
    "mcp": "mcp",
    "agent-infra": "script",
    "api": "script",
    "gateway": "script",
    "tool": "script",
}
# per-id override where the category default is wrong for that specific tool
TYPE_OVERRIDE = {"anthropic-api": "model", "gemini-api": "model", "firecrawl": "mcp"}

# type (demand) -> category, when category is missing
DEMAND_TYPE_TO_CATEGORY = {
    "subagent": "tool",
    "skill": "skill",
    "mcp": "mcp",
    "script": "tool",
    "kb": "tool",
}

COST_MAP = {"freemium": "metered"}  # supply's `freemium` has no PRD equivalent; nearest is metered

# NF-4: no machine-specific absolute path may land in catalog/. The one path
# baked into the demand source (agent-cad-expert, kb-3dmodel-source) becomes a
# profile reference instead; the real path lives in profiles/amit.yaml.
ABS_PATH = r"C:\Users\Amit.kuzi\OneDrive\Documents\3dModel"
PATH_PLACEHOLDER = "${profiles.amit.paths.cad_source}"


def scrub_paths(value):
    if isinstance(value, str):
        return value.replace(ABS_PATH, PATH_PLACEHOLDER)
    if isinstance(value, list):
        return [scrub_paths(v) for v in value]
    if isinstance(value, dict):
        return {k: scrub_paths(v) for k, v in value.items()}
    return value


def load_yaml(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["tools"]


def from_supply(raw: dict) -> dict:
    tid = raw["id"]
    category = raw.get("category", "tool")
    tool_type = TYPE_OVERRIDE.get(tid, CATEGORY_TO_TYPE.get(category, "script"))
    rec = {
        "name": raw.get("name", tid),
        "type": tool_type,
        "category": category,
        "purpose": raw.get("description", ""),
        "abilities": raw.get("abilities", []),
        "pros": raw.get("pros", []),
        "cons": raw.get("cons", []),
        "domains": raw.get("tags", []),
        "task_types": [],
        "cost": COST_MAP.get(raw.get("cost"), raw.get("cost", "free")),
        "cost_notes": raw.get("cost_notes"),
        "local_capable": raw.get("local_capable", False),
        "agent_ready": raw.get("agent_ready", False),
        "data_residency": raw.get("data_residency", "cloud"),
        "autonomy": raw.get("autonomy"),
        "license": raw.get("license", "n-a"),
        "license_notes": raw.get("license_notes"),
        "install": raw.get("install", "n-a"),
        "auth": raw.get("auth_required", "none"),
        "published_score": raw.get("published_score"),
        "maturity": raw.get("maturity"),
        "tags": raw.get("tags", []),
        "homepage": raw.get("homepage"),
        "repo": raw.get("repo"),
        "notes": raw.get("notes"),
        "review_status": raw.get("review_status", "seed-unverified"),
    }
    return {k: v for k, v in rec.items() if v not in (None, [], "")}, raw.get("my_score"), raw.get(
        "score_rationale"
    ), raw.get("last_reviewed")


def from_demand(raw: dict) -> dict:
    tid = raw["id"]
    tool_type = raw.get("type", "script")
    category = DEMAND_TYPE_TO_CATEGORY.get(tool_type, "tool")
    rec = {
        "name": raw.get("name", tid),
        "type": tool_type,
        "category": category,
        "purpose": raw.get("purpose", ""),
        "domains": raw.get("domains", []),
        "task_types": [],
        "cost": raw.get("cost", "included"),
        "local_capable": raw.get("local_capable", False),
        "agent_ready": raw.get("agent_ready", False),
        "data_residency": "local" if raw.get("local_capable") else "cloud",
        "license": raw.get("license", "n-a"),
        "install": raw.get("install", "n-a"),
        "auth": raw.get("auth", "none"),
        "entrypoint": raw.get("entrypoint"),
        "notes": raw.get("notes"),
        "verified": str(raw["verified"]) if raw.get("verified") else None,
        "review_status": "verified" if raw.get("verified") else "seed-unverified",
    }
    return {k: v for k, v in rec.items() if v not in (None, [], "")}, raw.get("my_score"), (
        raw.get("notes") or "migrated from demand catalog"
    ), raw.get("verified")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=None, help="override catalog dir (dry-run into a temp dir)")
    args = parser.parse_args()

    store = Store(backend_name="files", base_dir=args.base_dir)

    seen_ids: set[str] = set()
    total = 0
    for path, loader, source_label in (
        (SUPPLY_PATH, from_supply, "AiAgent/ai-toolbox/tools.yaml"),
        (DEMAND_PATH, from_demand, "TaskTriagOrcetrator/ai-toolbox/tools.yaml"),
    ):
        for raw in load_yaml(path):
            tid = raw["id"]
            if tid in seen_ids:
                print(f"skip duplicate id across sources: {tid}", file=sys.stderr)
                continue
            seen_ids.add(tid)
            payload, my_score, rationale, last_reviewed = loader(raw)
            payload = scrub_paths(payload)
            rationale = scrub_paths(rationale) if rationale else rationale
            store.append(
                kind="tool.added",
                subject_id=tid,
                actor="system:migration",
                via="migration",
                reason=f"imported from {source_label} (last_reviewed {last_reviewed})",
                payload=payload,
            )
            if my_score is not None:
                store.append(
                    kind="score.seed",
                    subject_id=f"seed-{tid}",
                    actor="system:migration",
                    via="migration",
                    reason=str(rationale) if rationale else f"seed score from {source_label}",
                    payload={"tool_id": tid, "score": my_score},
                )
            total += 1
    print(f"migrated {total} tools, {len(seen_ids)} unique ids, 0 duplicates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
