---
description: Print the full traceable chain for a decision or a tool's complete event history (PRD P2).
argument-hint: <decision_id | tool_id>
---

Run `python scripts/store.py trace $ARGUMENTS` and present the result as:

- If it's a `decision_id`: task → swarm level/reason → orchestrator tier/reason
  → per subtask, every candidate considered with its `effective` score and
  flags → the winner and runner-up → every `score.outcome`/`score.human`
  event that followed → how much `my_score_current` moved as a result
  (compare `views/scores-summary.yaml` before/after if both are available).
- If it's a `tool_id`: full history — `tool.added` → every `tool.revised`/
  `tool.status`/`tool.retired` event → every `score.*` event referencing it,
  in chronological order.

Never read a ledger file directly to answer this — `store trace` is the only
path (`rules/07-data-contract.md`).
