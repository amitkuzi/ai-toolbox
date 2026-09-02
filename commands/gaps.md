---
description: List open tool/model gaps and propose building a fix for any gap with 3+ hits.
---

Run `python scripts/store.py project --collection gaps`, then read the
resulting `gaps.md` view (`python scripts/store.py query gaps` if you need
the raw events) and print the open-gaps table.

For any gap with `hits >= 3`, propose a concrete next step per
`selection-rules.md`'s escalation table (carried into `rules/03-category-gate.md`):
a repeated MCP gap → build the connector; a repeated procedure → package a
skill. State the proposal, do not act on it without confirmation.
