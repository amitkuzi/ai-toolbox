---
description: Re-fold the ledger into the generated views and show what changed before committing.
argument-hint: "[--collection tools|sources|models|decisions|gaps]"
---

Run `python scripts/store.py project $ARGUMENTS`, note which view files it
reports writing, then `git diff --stat` and `git diff` on just those files
so the caller sees exactly what the fold changed before staging it.

This never touches the ledger — it only ever writes the generated views, and
the output is deterministic from the ledger (P3/P4, `rules/07-data-contract.md`).
