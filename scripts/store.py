#!/usr/bin/env python3
"""Catalog Store adapter (PRD §1a P1). The ONLY way anything reads or writes
catalog data. Exposes append / query / project / trace as both a Python API
and a CLI. Backend-agnostic: pass --backend files|sqlite (files is default).

    python scripts/store.py append --kind tool.added --subject-id ollama \
        --actor system:migration --via migration --reason "..." \
        --payload '{"name": "Ollama", ...}'
    python scripts/store.py query tools --kind tool.added
    python scripts/store.py project
    python scripts/store.py trace d-20260902-001
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backends import get_backend  # noqa: E402
import yaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_DIR = REPO_ROOT / "catalog"

# kind prefix -> ledger collection
KIND_COLLECTION = {
    "tool": "tools",
    "source": "sources",
    "model": "models",
    "decision": "scores",
    "score": "scores",
    "adr": "decisions",
    "gap": "gaps",
}


# batch runs (daily-run/weekly-run) stamp historical events with a rounded
# midnight ts for the whole day's work, which can sort *before* same-day
# intraday events (e.g. a UI-added tool later "removed" by that day's batch).
# Folding by literal ts alone would then apply the removal before the add.
# Break same-day ties by event-type intent instead: added, then revised/status,
# then retired — so a same-day add-then-remove folds in the right order while
# the literal `ts` on each event is still preserved exactly as recorded (P4).
_KIND_DAY_PRIORITY = {"added": 0, "revised": 1, "status": 1, "retired": 2}


def _fold_sort_key(ev: dict):
    ts = ev["ts"]
    suffix = ev["kind"].rsplit(".", 1)[-1]
    return (ts[:10], _KIND_DAY_PRIORITY.get(suffix, 1), ts)


def collection_for_kind(kind: str) -> str:
    prefix = kind.split(".", 1)[0]
    if prefix not in KIND_COLLECTION:
        raise ValueError(f"unknown kind '{kind}' — no collection mapping")
    return KIND_COLLECTION[prefix]


# ---------------------------------------------------------------- ULID ----
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_last_ulid_ms = 0
_last_ulid_seq = 0


def new_ulid() -> str:
    """Time-sortable unique id. Not a byte-exact ULID spec implementation,
    but satisfies the envelope's requirement: unique, time-sortable, 26 chars.
    ponytail: stdlib-only instead of pulling a ulid package for one function.
    """
    global _last_ulid_ms, _last_ulid_seq
    ms = time.time_ns() // 1_000_000
    if ms == _last_ulid_ms:
        _last_ulid_seq += 1
    else:
        _last_ulid_ms = ms
        _last_ulid_seq = 0
    # 48 bits timestamp + 16 bits seq (monotonic tiebreak) + 40 bits random
    ts_part = ms & ((1 << 48) - 1)
    seq_part = _last_ulid_seq & ((1 << 16) - 1)
    rand_part = int.from_bytes(os.urandom(5), "big")
    value = (ts_part << 56) | (seq_part << 40) | rand_part
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# --------------------------------------------------------- rules_version --
def compute_rules_version(override: str | None = None) -> str:
    """PRD §5.1/§6.0 (D-012 resolution): `<rules/VERSION contents>+<short git
    hash of the rules/ tree>`. Accepts an explicit override for testing;
    otherwise reads rules/VERSION and `git rev-parse --short HEAD -- rules/`,
    falling back to 'dev' if not in a git repo or rules/VERSION is missing.
    """
    if override:
        return override
    version_file = REPO_ROOT / "rules" / "VERSION"
    if not version_file.exists():
        return "dev"
    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        return "dev"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD", "--", "rules/"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=5,
        )
        git_hash = result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        git_hash = ""
    return f"{version}+{git_hash}" if git_hash else version


# ------------------------------------------------------------- YAML I/O ---
def dump_yaml(data) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ------------------------------------------------------------- Store -----
class Store:
    def __init__(self, backend_name: str = "files", base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_BASE_DIR
        self.backend = get_backend(backend_name, self.base_dir)

    # -- P4: append is the only write path -------------------------------
    def append(
        self,
        kind: str,
        subject_id: str,
        actor: str,
        via: str,
        reason: str | None = None,
        payload: dict | None = None,
        supersedes: str | None = None,
        rules_version: str | None = None,
        ts: str | None = None,
    ) -> dict:
        collection = collection_for_kind(kind)
        if not reason:
            # D-011: reason is required on every event, unconditionally —
            # no exception for an initial *.added.
            raise ValueError(f"reason is required for kind '{kind}'")
        if kind == "decision" and not rules_version:
            # D-012: default rules_version from rules/VERSION + git hash.
            rules_version = compute_rules_version()
        event = {
            "event_id": new_ulid(),
            "ts": ts or now_iso(),
            "kind": kind,
            "subject_id": subject_id,
            "actor": actor,
            "via": via,
        }
        if reason:
            event["reason"] = reason
        if supersedes:
            event["supersedes"] = supersedes
        if rules_version:
            event["rules_version"] = rules_version
        event["payload"] = payload or {}
        self.backend.append(collection, event)
        return event

    # -- read path ---------------------------------------------------------
    def query(self, collection: str, **filters) -> list[dict]:
        events = self.backend.read_events(collection)
        if not filters:
            return events
        out = []
        for ev in events:
            if _matches(ev, filters):
                out.append(ev)
        return out

    # -- projection (never writes the ledger) ------------------------------
    def project(self, collection: str | None = None) -> dict:
        """Fold ledger events into catalog/views/*. Returns {view_name: content}."""
        written = {}
        collections = [collection] if collection else ["tools", "sources", "models", "decisions", "gaps"]
        scores_by_tool = self._fold_scores()
        for c in collections:
            if c == "tools":
                content = self._project_tools(scores_by_tool)
                self.backend.write_view("tools.yaml", content)
                written["tools.yaml"] = content
                summary = self._project_scores_summary(scores_by_tool)
                self.backend.write_view("scores-summary.yaml", summary)
                written["scores-summary.yaml"] = summary
            elif c == "sources":
                content = self._project_sources()
                self.backend.write_view("sources.yaml", content)
                written["sources.yaml"] = content
            elif c == "models":
                content = self._project_models(scores_by_tool)
                self.backend.write_view("models.yaml", content)
                written["models.yaml"] = content
            elif c == "decisions":
                content = self._project_decisions()
                self.backend.write_view("decisions.md", content)
                written["decisions.md"] = content
            elif c == "gaps":
                content = self._project_gaps()
                self.backend.write_view("gaps.md", content)
                written["gaps.md"] = content
        return written

    def _fold_scores(self) -> dict:
        """tool_id -> {samples, my_score_current, estimate, trend, by_task_type, by_actor}."""
        events = self.backend.read_events("scores")
        retracted_ids = {
            ev["supersedes"] for ev in events if ev["kind"] == "score.retract" and ev.get("supersedes")
        }
        by_tool: dict[str, list[dict]] = {}
        for ev in events:
            if ev["kind"] not in ("score.seed", "score.outcome", "score.human"):
                continue
            if ev["event_id"] in retracted_ids:
                continue
            tool_id = ev["payload"].get("tool_id")
            if not tool_id:
                continue
            by_tool.setdefault(tool_id, []).append(ev)

        result = {}
        for tool_id, evs in by_tool.items():
            evs.sort(key=_fold_sort_key)
            scores = [e["payload"].get("score") for e in evs if e["payload"].get("score") is not None]
            samples = len(scores)
            if samples < 5:
                seed = next((e for e in evs if e["kind"] == "score.seed"), evs[0])
                current = seed["payload"].get("score")
                estimate = True
            else:
                # EMA with human events weighted 1.5x by repeating their contribution.
                # ponytail: linear 90-day decay via simple recency weight, not a full
                # time-series model — good enough until real outcome volume demands more.
                weighted = []
                now = datetime.now(timezone.utc)
                for e in evs:
                    w = 1.5 if e["kind"] == "score.human" else 1.0
                    try:
                        age_days = (now - datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))).days
                    except ValueError:
                        age_days = 0
                    w *= max(0.0, 1 - age_days / 90) if age_days > 0 else 1.0
                    weighted.append((e["payload"]["score"], max(w, 0.05)))
                ema = weighted[0][0]
                alpha = 0.3
                for score, w in weighted[1:]:
                    ema = alpha * w * score + (1 - alpha * w) * ema
                current = round(ema, 2)
                estimate = False
            trend = "flat"
            if samples >= 2:
                mid = max(1, samples // 2)
                prev_mean = sum(scores[:mid]) / mid
                last_mean = sum(scores[mid:]) / (samples - mid)
                trend = "up" if last_mean > prev_mean else ("down" if last_mean < prev_mean else "flat")
            by_task_type: dict[str, list] = {}
            by_actor: dict[str, list] = {}
            for e in evs:
                tt = e["payload"].get("task_type")
                if tt:
                    by_task_type.setdefault(tt, []).append(e["payload"].get("score"))
                by_actor.setdefault(e["actor"], []).append(e["payload"].get("score"))
            verified_dates = [
                e["ts"][:10] for e in evs
                if e["kind"] == "score.outcome" and e["payload"].get("result") == "success"
            ]
            result[tool_id] = {
                "my_score_current": current,
                "score_samples": samples,
                "score_trend": trend,
                "estimate": estimate,
                "last_outcome_ts": evs[-1]["ts"],
                "by_task_type": {k: round(sum(v) / len(v), 2) for k, v in by_task_type.items()},
                "by_actor": {k: round(sum(v) / len(v), 2) for k, v in by_actor.items()},
                "verified": max(verified_dates) if verified_dates else None,
            }
        return result

    def _project_tools(self, scores_by_tool: dict) -> str:
        events = sorted(self.backend.read_events("tools"), key=_fold_sort_key)
        by_id: dict[str, dict] = {}
        history: dict[str, list[str]] = {}
        for ev in events:
            tid = ev["subject_id"]
            history.setdefault(tid, []).append(ev["event_id"])
            if ev["kind"] == "tool.added":
                rec = dict(ev["payload"])
                rec["id"] = tid
                rec["review_status"] = rec.get("review_status", "seed-unverified")
                rec["last_reviewed"] = ev["ts"][:10]
                by_id[tid] = rec
            elif ev["kind"] == "tool.revised":
                if tid in by_id:
                    by_id[tid].update(ev["payload"])
                    by_id[tid]["last_reviewed"] = ev["ts"][:10]
            elif ev["kind"] == "tool.status":
                if tid in by_id:
                    if "review_status" in ev["payload"]:
                        by_id[tid]["review_status"] = ev["payload"]["review_status"]
                    if ev["payload"].get("verified"):
                        by_id[tid]["verified"] = ev["payload"]["verified"]
                    by_id[tid]["last_reviewed"] = ev["ts"][:10]
            elif ev["kind"] == "tool.retired":
                if tid in by_id:
                    by_id[tid]["review_status"] = "dead"
                    by_id[tid]["retired"] = True
                    by_id[tid]["last_reviewed"] = ev["ts"][:10]

        tools = []
        for tid, rec in by_id.items():
            sc = scores_by_tool.get(tid)
            if sc:
                rec["my_score_current"] = sc["my_score_current"]
                rec["score_samples"] = sc["score_samples"]
                rec["score_trend"] = sc["score_trend"]
                if sc["estimate"]:
                    rec["estimate"] = True
                if sc["verified"]:
                    rec["verified"] = max(rec.get("verified", ""), sc["verified"])
            elif "my_score" in rec:
                rec["my_score_current"] = rec["my_score"]
                rec["score_samples"] = 0
                rec["estimate"] = True
            rec["history"] = history.get(tid, [])
            tools.append(rec)
        tools.sort(key=lambda r: r["id"])
        return dump_yaml({"tools": tools})

    def _project_scores_summary(self, scores_by_tool: dict) -> str:
        out = {tid: data for tid, data in sorted(scores_by_tool.items())}
        return dump_yaml(out)

    def _project_sources(self) -> str:
        events = sorted(self.backend.read_events("sources"), key=_fold_sort_key)
        by_id: dict[str, dict] = {}
        for ev in events:
            sid = ev["subject_id"]
            if ev["kind"] == "source.added":
                rec = dict(ev["payload"])
                rec["id"] = sid
                by_id[sid] = rec
            elif ev["kind"] == "source.revised":
                if sid in by_id:
                    by_id[sid].update(ev["payload"])
            elif ev["kind"] == "source.retired":
                if sid in by_id:
                    by_id[sid]["review_status"] = "retired"
        sources = sorted(by_id.values(), key=lambda r: r["id"])
        return dump_yaml({"sources": sources})

    def _project_models(self, scores_by_tool: dict) -> str:
        # D-010: models fold score.* events exactly like tools — same scores.jsonl
        # ledger, subject_id = model id — so my_score_current is ⚙ computed here too.
        events = sorted(self.backend.read_events("models"), key=_fold_sort_key)
        by_id: dict[str, dict] = {}
        for ev in events:
            mid = ev["subject_id"]
            if ev["kind"] == "model.added":
                rec = dict(ev["payload"])
                rec["id"] = mid
                by_id[mid] = rec
            elif ev["kind"] == "model.revised":
                if mid in by_id:
                    by_id[mid].update(ev["payload"])
        for mid, rec in by_id.items():
            sc = scores_by_tool.get(mid)
            if sc:
                rec["my_score_current"] = sc["my_score_current"]
                rec["score_samples"] = sc["score_samples"]
                rec["score_trend"] = sc["score_trend"]
                if sc["estimate"]:
                    rec["estimate"] = True
            elif "my_score" in rec:
                rec["my_score_current"] = rec["my_score"]
                rec["score_samples"] = 0
                rec["estimate"] = True
        models = sorted(by_id.values(), key=lambda r: r["id"])
        return dump_yaml({"models": models})

    def _project_decisions(self) -> str:
        events = self.backend.read_events("decisions")
        by_id: dict[str, dict] = {}
        for ev in events:
            did = ev["subject_id"]
            if ev["kind"] == "adr.added":
                by_id[did] = {"id": did, **ev["payload"], "status": "accepted"}
            elif ev["kind"] == "adr.superseded":
                if did in by_id:
                    by_id[did]["status"] = "superseded"
                    by_id[did]["superseded_by"] = ev["payload"].get("superseded_by")
                    if ev["payload"].get("resolution"):
                        by_id[did]["resolution"] = ev["payload"]["resolution"]
        lines = ["# Decisions (ADRs)", "", "Generated by `store project` — do not hand-edit.", ""]
        for did in sorted(by_id):
            d = by_id[did]
            lines.append(f"## {did} — {d.get('title', '')}")
            lines.append(f"Status: {d['status']}")
            if d.get("body"):
                lines.append("")
                lines.append(d["body"])
            if d.get("resolution"):
                lines.append("")
                lines.append(f"**Resolution:** {d['resolution']}")
            lines.append("")
        return "\n".join(lines)

    def _project_gaps(self) -> str:
        events = self.backend.read_events("gaps")
        by_id: dict[str, dict] = {}
        for ev in events:
            gid = ev["subject_id"]
            if ev["kind"] == "gap.opened":
                rec = dict(ev["payload"])
                rec["id"] = gid
                rec["hits"] = 1
                rec["status"] = "open"
                by_id[gid] = rec
            elif ev["kind"] == "gap.hit":
                if gid in by_id:
                    by_id[gid]["hits"] = by_id[gid].get("hits", 1) + 1
            elif ev["kind"] == "gap.closed":
                if gid in by_id:
                    by_id[gid]["status"] = "closed"
        lines = ["# Tool Gaps", "", "Generated by `store project` — do not hand-edit.", "", "## Open", "",
                  "| ID | Gap | Type needed | Hits | Status |", "|---|---|---|---|---|"]
        for gid in sorted(k for k, v in by_id.items() if v["status"] == "open"):
            g = by_id[gid]
            lines.append(f"| {gid} | {g.get('gap', '')} | {g.get('type_needed', '')} | {g.get('hits', 1)} | open |")
        lines.append("")
        lines.append("## Closed")
        lines.append("")
        for gid in sorted(k for k, v in by_id.items() if v["status"] == "closed"):
            g = by_id[gid]
            lines.append(f"- {gid} — {g.get('gap', '')}")
        lines.append("")
        return "\n".join(lines)

    # -- trace (P2) ----------------------------------------------------------
    def trace(self, subject_id: str) -> list[dict]:
        chain = []
        for collection in self.backend.list_collections():
            for ev in self.backend.read_events(collection):
                if ev["subject_id"] == subject_id or ev.get("payload", {}).get("tool_id") == subject_id:
                    chain.append(ev)
        chain.sort(key=lambda e: e["ts"])
        return chain


def _matches(event: dict, filters: dict) -> bool:
    for key, want in filters.items():
        val = _get_nested(event, key)
        if val != want:
            return False
    return True


def _get_nested(obj: dict, dotted_key: str):
    cur = obj
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


# ------------------------------------------------------------------ CLI ---
def main(argv=None):
    parser = argparse.ArgumentParser(description="Catalog Store CLI")
    parser.add_argument("--backend", default="files", choices=["files", "sqlite"])
    parser.add_argument("--base-dir", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append")
    p_append.add_argument("--kind", required=True)
    p_append.add_argument("--subject-id", required=True)
    p_append.add_argument("--actor", required=True)
    p_append.add_argument("--via", required=True)
    p_append.add_argument("--reason", default=None)
    p_append.add_argument("--payload", default="{}")
    p_append.add_argument("--supersedes", default=None)
    p_append.add_argument("--rules-version", default=None)

    p_query = sub.add_parser("query")
    p_query.add_argument("collection")
    p_query.add_argument("--filter", action="append", default=[], help="key=value, repeatable")

    p_project = sub.add_parser("project")
    p_project.add_argument("--collection", default=None)

    p_trace = sub.add_parser("trace")
    p_trace.add_argument("subject_id")

    args = parser.parse_args(argv)
    store = Store(backend_name=args.backend, base_dir=args.base_dir)

    if args.cmd == "append":
        event = store.append(
            kind=args.kind,
            subject_id=args.subject_id,
            actor=args.actor,
            via=args.via,
            reason=args.reason,
            payload=json.loads(args.payload),
            supersedes=args.supersedes,
            rules_version=args.rules_version,
        )
        print(json.dumps(event, ensure_ascii=False, indent=2))
    elif args.cmd == "query":
        filters = dict(f.split("=", 1) for f in args.filter)
        results = store.query(args.collection, **filters)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.cmd == "project":
        written = store.project(collection=args.collection)
        for name in written:
            print(f"wrote {name}")
    elif args.cmd == "trace":
        chain = store.trace(args.subject_id)
        for ev in chain:
            print(f"{ev['ts']}  {ev['kind']:<16} {ev['actor']:<24} {ev.get('reason', '')}")
            print(f"    payload: {json.dumps(ev['payload'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
