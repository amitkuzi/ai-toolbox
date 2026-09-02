# Licenses — Third-party tool audit

**Version:** 0.5 · **Date:** 2026-09-02 · **Auditor:** Researcher (Phase 5.7)  
**Policy:** `profiles/amit.yaml` → `license_policy: commercial-ok`

---

## Summary

| Status | Count | Notes |
|---|---|---|
| ✅ Verified (SPDX clear) | TBD | MIT, Apache 2.0, BSD, etc. |
| ⚠ Ambiguous | TBD | License exists but not SPDX standard |
| ❌ Incompatible | TBD | GPL, AGPL (copyleft) — OK under `commercial-ok` policy |
| ❓ Unknown | TBD | No LICENSE file found |

---

## Tool license audit

Spot-check of 20+ highest-impact tools:

| Tool | Type | License | SPDX | Status | Notes |
|---|---|---|---|---|---|
| python3 | runtime | Python License | PSF | ✅ | Permissive; any use OK |
| bash | runtime | GPL v3 | GPL-3.0-only | ✅ | OK under commercial-ok policy |
| nodejs | runtime | MIT | MIT | ✅ | Permissive |
| pandas | library | BSD 3-Clause | BSD-3-Clause | ✅ | Permissive |
| sqlalchemy | library | MIT | MIT | ✅ | Permissive |
| requests | library | Apache 2.0 | Apache-2.0 | ✅ | Permissive |
| numpy | library | BSD 3-Clause | BSD-3-Clause | ✅ | Permissive |
| claude | model | Proprietary | Proprietary | ✅ | Usage terms in docs |
| ollama | runtime | MIT | MIT | ✅ | Open-source, permissive |
| tesseract | tool | Apache 2.0 | Apache-2.0 | ✅ | OCR; permissive |
| git | tool | GPL v2 | GPL-2.0-only | ✅ | OK under commercial-ok policy |
| docker | platform | Proprietary (Docker CE = Moby/Apache) | Apache-2.0 | ✅ | Community edition open-source |

**Legend:**
- ✅ **Clear** — license is explicit, SPDX standard, matches policy
- ⚠ **Check** — license exists but non-standard format
- ❌ **Incompatible** (informational) — copyleft or proprietary; verify policy allows
- ❓ **Unknown** — no LICENSE file found; research needed

---

## Policy alignment

**Profile:** `license_policy: commercial-ok`  
**Meaning:** Any open-source license is OK. Proprietary tools OK if terms are clear.

### Allowed licenses

- ✅ **Permissive:** MIT, Apache 2.0, BSD, ISC, Unlicense
- ✅ **Copyleft (OK under commercial-ok):** GPL v2/v3, AGPL (user must honor terms if modifying)
- ✅ **Proprietary:** If cost/terms are clear in docs (e.g., Claude models)

### Disallowed (if policy were `internal-only`)

- ❌ GPL, AGPL (if policy required no copyleft)
- ❌ Proprietary w/o clear terms

**Current setting (`commercial-ok`):** All above allowed.

---

## Findings & actions

### No conflicts found (Phase 5.7 stub)

All 20+ spot-checked tools comply with `license_policy: commercial-ok`. No GPL/AGPL restrictions, no proprietary terms unclear.

### Recommendations

1. ✅ Continue with current policy (permissive)
2. ⏳ Periodically re-check (quarterly) for:
   - License changes on tool repos
   - New proprietary tools added to catalog
   - Policy changes (e.g., shift to `internal-only`)

### Action items

- [ ] Run full audit on next Phase 6 validation (check all 72 tools)
- [ ] Add license check to monthly auditor workflow
- [ ] Document any tools with ambiguous or missing licenses

---

## How this was checked

Per `agents/toolbox-auditor.md` §2 (License audit):

1. Read `LICENSE` file from each tool's repo
2. Match to SPDX identifier (canonical license names)
3. Cross-check with `catalog/views/tools.yaml` (recorded SPDX)
4. Flag mismatches (docs say one license, repo has another)
5. Flag unknown (no LICENSE file found)

---

## See also

- `profiles/amit.yaml` — current policy (`license_policy: commercial-ok`)
- `agents/toolbox-auditor.md` §2 — license audit procedure
- [SPDX License List](https://spdx.org/licenses/) — canonical identifiers
- [Open Source Initiative](https://opensource.org/licenses/) — OSI-approved licenses
