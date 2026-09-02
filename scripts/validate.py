#!/usr/bin/env python3
"""CI gate for the Catalog Store (PRD NF-1, NF-2, NF-2b, NF-2c).

Checks, in order, and exits non-zero with a clear message on the first
category that fails (each category still runs and reports all its own
violations before validate.py exits):

1. every ledger event matches its `kind`'s envelope + required fields
2. append-only guard: `git diff` of catalog/ledger/* contains no removed
   or modified line, only pure additions
3. catalog/views/* exactly equals a fresh `store project` of the ledger
4. NF-2c: no file under rules/ skills/ agents/ commands/ contains a
   literal 'catalog/' path

Run: python scripts/validate.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import Store, collection_for_kind  # noqa: E402
from backends import FilesBackend  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "catalog"
LEDGER_DIR = CATALOG_DIR / "ledger"
VIEWS_DIR = CATALOG_DIR / "views"

REQUIRED_ENVELOPE = ["event_id", "ts", "kind", "subject_id", "actor", "via", "payload"]
KIND_PAYLOAD_REQUIRED = {
    "tool.added": ["type", "category"],
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


# ---------------------------------------------------------------- 1 -------
def check_schema() -> None:
    if not LEDGER_DIR.exists():
        return
    for jsonl in sorted(LEDGER_DIR.glob("*.jsonl")):
        collection = jsonl.stem
        backend = FilesBackend(CATALOG_DIR)
        for i, ev in enumerate(backend.read_events(collection), start=1):
            where = f"{jsonl.name}:{i}"
            for field in REQUIRED_ENVELOPE:
                if field not in ev:
                    fail(f"{where} missing required field '{field}'")
            kind = ev.get("kind", "")
            try:
                expected_collection = collection_for_kind(kind)
                if expected_collection != collection:
                    fail(f"{where} kind '{kind}' belongs in '{expected_collection}.jsonl', found in '{collection}.jsonl'")
            except ValueError:
                fail(f"{where} unknown kind '{kind}'")
            if not kind.endswith(".added") and not ev.get("reason"):
                fail(f"{where} kind '{kind}' is missing required 'reason'")
            for req_field in KIND_PAYLOAD_REQUIRED.get(kind, []):
                if req_field not in ev.get("payload", {}):
                    fail(f"{where} kind '{kind}' payload missing required field '{req_field}'")


# ---------------------------------------------------------------- 2 -------
def check_append_only() -> None:
    if not LEDGER_DIR.exists():
        return
    try:
        base_ref = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "HEAD", "origin/main"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or "HEAD"
    except Exception:
        base_ref = "HEAD"
    diff = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--unified=0", base_ref, "--", "catalog/ledger"],
        capture_output=True, text=True, check=False,
    ).stdout
    for line in diff.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            fail(f"catalog/ledger diff removes or modifies a line (append-only violation): {line[:120]}")


# ---------------------------------------------------------------- 3 -------
def check_views_match_projection() -> None:
    if not LEDGER_DIR.exists():
        return
    tmp = Path(tempfile.mkdtemp(prefix="validate-project-"))
    try:
        tmp_ledger = tmp / "ledger"
        shutil.copytree(LEDGER_DIR, tmp_ledger)
        store = Store(backend_name="files", base_dir=tmp)
        written = store.project()
        for name, content in written.items():
            actual_path = VIEWS_DIR / name
            actual = actual_path.read_text(encoding="utf-8") if actual_path.exists() else None
            if actual != content:
                fail(f"catalog/views/{name} does not match `store project` output — run `python scripts/store.py project` and commit")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- 4 -------
def check_no_catalog_paths_in_rules() -> None:
    dirs = ["rules", "skills", "agents", "commands"]
    for d in dirs:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".yaml", ".yml", ".json"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(text.splitlines(), start=1):
                    if "catalog/" in line:
                        fail(f"{path.relative_to(REPO_ROOT)}:{i} references 'catalog/' directly (NF-2c: use store.py)")


def main() -> int:
    check_schema()
    check_append_only()
    check_views_match_projection()
    check_no_catalog_paths_in_rules()
    if errors:
        print(f"validate.py: {len(errors)} violation(s)\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("validate.py: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
