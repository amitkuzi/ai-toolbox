# Routing evaluation suite — 15 test cases

**Version:** 0.6 · **Date:** 2026-09-02 · **Purpose:** Validate routing consistency across models

Fifteen real-world tasks with expected routing decisions. Used to:
1. Verify routing decisions are consistent (T1 ≈ T2)
2. Measure whether the system meets G3 (≥ 40% routed to T0/T1)
3. Benchmark model differences (if > 20% divergence, open ADR)

---

## Test cases

Each test case specifies:
- **Task:** what the user is asking for
- **Expected L:** swarm level (L0–L3)
- **Expected T:** model tier (T0–T3)
- **Expected type:** category (script | mcp | skill | subagent | model)
- **Expected tool:** best candidate (or range if multiple acceptable)
- **Rationale:** why this routing (concise)

---

### T0–T1 (cheap/local) — Goal: ≥ 40% of decisions

#### 1. Rename files by pattern

**Task:** "Rename 200 STL files from `model-001.stl` to `part-001.stl`"

- **Level:** L1 (single deterministic subtask)
- **Tier:** T0 (local, no external service)
- **Type:** script
- **Tool:** python3 or bash (both free, local, verified)
- **Rationale:** Deterministic file op; local tools sufficient

**Test:** Routing should pick python3 or bash (score 9+, local)

---

#### 2. Extract text from PDF

**Task:** "Extract text and images from a 50-page PDF into markdown"

- **Level:** L1
- **Tier:** T1 (may need cloud if local tool is weak)
- **Type:** script or mcp
- **Tool:** pdfplumber (Python) or similar
- **Rationale:** Deterministic extraction; local Python lib or cheap API

**Test:** Routing should pick pdfplumber or pypdf (cost ≤ $0.01)

---

#### 3. Validate data schema

**Task:** "Check that 10,000 JSON files match the schema in my spec"

- **Level:** L1
- **Tier:** T0–T1
- **Type:** script
- **Tool:** jq (local JSON tool) or Python jsonschema
- **Rationale:** Deterministic validation; local tools perfect

**Test:** Routing should pick jq or Python (T0 free, local)

---

#### 4. Generate a spreadsheet from CSV data

**Task:** "Read sales.csv, compute monthly totals, output to Excel"

- **Level:** L1
- **Tier:** T0–T1
- **Type:** script
- **Tool:** pandas (Python) or xsv (Rust tool)
- **Rationale:** Deterministic transform; pandas is established, free

**Test:** Routing should pick pandas or Excel formula (local, free)

---

#### 5. Sort and filter a large text file

**Task:** "Sort log.txt by timestamp, filter to errors only, output filtered-errors.txt"

- **Level:** L0–L1 (very simple)
- **Tier:** T0
- **Type:** script
- **Tool:** bash/sort/grep
- **Rationale:** Unix tools designed for this; zero cost

**Test:** Routing should pick bash (score 9+, local, free)

---

### T1–T2 (mid-tier) — Goal: achievable with good routing

#### 6. Summarize a research paper

**Task:** "Read this 20-page AI paper and summarize the key findings in 1 page"

- **Level:** L2 (multi-step: read, comprehend, synthesize)
- **Tier:** T1–T2 (reasoning needed; local LLM OK if capable)
- **Type:** model or mcp
- **Tool:** claude-haiku (T1) or claude-sonnet (T2)
- **Rationale:** Reasoning task; local LLM insufficient; cloud model needed

**Test:** Routing should pick Haiku (T1, cheaper) or Sonnet (T2, better quality)

---

#### 7. Debug a Python script

**Task:** "This Python script is throwing a `KeyError`. Here's the code and traceback. What's wrong?"

- **Level:** L1–L2 (debugging may need back-and-forth)
- **Tier:** T1 (Haiku can debug simple scripts)
- **Type:** model or skill
- **Tool:** claude-haiku
- **Rationale:** Simple debugging; T1 capable; no external tools

**Test:** Routing should pick Haiku (T1)

---

#### 8. Plan a 3D print

**Task:** "I have an STL file for a bracket. Check wall thickness, estimate print time and filament cost on an Ender 3. What settings would you recommend?"

- **Level:** L2 (multi-step: parse CAD, estimate, recommend)
- **Tier:** T1–T2 (can use local CAD tool + estimation model)
- **Type:** script + model
- **Tool:** FreeCAD (script) or Cura simulation + Claude (model)
- **Rationale:** Multi-step; first deterministic (simulation), then reasoning

**Test:** Routing should recommend script-first (FreeCAD), then Haiku for recommendations

---

#### 9. Translate text to Hebrew

**Task:** "Translate this 500-word English article into Hebrew"

- **Level:** L1–L2 (deterministic transform; quality matters)
- **Tier:** T1 (Haiku can translate; for better quality → T2)
- **Type:** model
- **Tool:** claude-haiku or claude-sonnet
- **Rationale:** LLM task; Haiku is cheap; Sonnet is higher quality

**Test:** Routing should pick Haiku (T1) for cost, Sonnet (T2) for quality

---

#### 10. Query a knowledge base

**Task:** "Search our internal docs for 'deployment procedures' and extract the steps for Blue-Green deployment"

- **Level:** L1
- **Tier:** T0–T1 (local search if KB is local; T2 if remote API)
- **Type:** kb or script
- **Tool:** local search tool or script
- **Rationale:** Lookup; no reasoning needed; deterministic

**Test:** Routing should pick local search (T0) if available, else API (T1)

---

### T2–T3 (frontier) — Goal: use only when necessary

#### 11. Design a 3D model from scratch

**Task:** "Design a parametric bracket for a Raspberry Pi mounting. Should have 4 corner mounting holes (M2) and be printable on an Ender 3. Provide STL."

- **Level:** L3 (complex, creative, multi-step: design → CAD → export)
- **Tier:** T2–T3 (needs spatial reasoning + CAD knowledge)
- **Type:** subagent (or model + script)
- **Tool:** CAD agent (T2) or Designer (T3) + FreeCAD script
- **Rationale:** Creative design; needs human-level reasoning; CAD expertise

**Test:** Routing should pick T2 (CAD-expert agent) or T3 (Designer) — cost ~$0.50–$1.00

---

#### 12. Optimize a complex system

**Task:** "Our API is slow. Requests take 2–5 seconds. Here's the schema, query patterns, and current indexes. What's the bottleneck and how would you fix it?"

- **Level:** L2–L3 (analysis + recommendations)
- **Tier:** T2 (Sonnet can analyze SQL); T3 if system is very complex
- **Type:** model
- **Tool:** claude-sonnet (T2) or claude-opus (T3)
- **Rationale:** Reasoning task; needs to weigh trade-offs; T2 usually sufficient

**Test:** Routing should pick Sonnet (T2) unless analysis is very deep

---

#### 13. Write production code (with tests)

**Task:** "Implement a caching layer for our REST API. Must handle TTL, invalidation, and concurrent requests. Include unit tests."

- **Level:** L2 (multi-part: code + tests)
- **Tier:** T1–T2 (Haiku can code simple; Sonnet better for production code)
- **Type:** subagent or model
- **Tool:** claude-sonnet (T2) + script
- **Rationale:** Production code needs quality; Sonnet better; Haiku is risky for this

**Test:** Routing should pick Sonnet (T2) or higher

---

#### 14. Analyze ambiguous requirements

**Task:** "Customer says 'faster checkout'. What do they mean? Is it UX speed? Server latency? Network? How would you investigate and what's the cost estimate for each?"

- **Level:** L2–L3 (ambiguity requires reasoning)
- **Tier:** T2–T3 (needs judgment calls)
- **Type:** model
- **Tool:** claude-sonnet (T2) or claude-opus (T3)
- **Rationale:** Ambiguity resolution; needs nuance; Sonnet sufficient usually

**Test:** Routing should pick Sonnet (T2)

---

#### 15. Full product audit (swarm)

**Task:** "Audit our software for security (code review + dependencies + config), performance (profiling + recommendations), and compliance (data handling + logs). Deliver a report."

- **Level:** L3 (complex, multi-agent, human review)
- **Tier:** T2 orchestrator + T1/T2 agents
- **Type:** subagent (swarm)
- **Tool:** security-expert + perf-analyst + compliance-analyst agents
- **Rationale:** Complex; needs swarm; orchestrator decides tier per subtask

**Test:** Routing should classify L3, pick T2 orchestrator, route each subtask to appropriate T1/T2 agent

---

## Running the suite

### Step 1: Manual routing (setup)

For each test case, a human runs:

```bash
/toolbox:route <task-text>
# Logs decision event with tier, type, tool, reasoning
```

### Step 2: Capture decisions

```bash
python scripts/store.py query scores --filter 'kind=decision' \
  > routing-decisions-<date>.jsonl
```

### Step 3: Evaluate per case

For each of 15 test cases:
- Did routing tier match expected? (T0 vs T1, etc.)
- Did routing type match expected? (script vs model, etc.)
- Did routing tool match expected or acceptable alternative?

Score: pass/fail per test case.

### Step 4: Aggregate results

- **Pass rate:** how many of 15 matched expected routing? (goal: 13/15 = 87%)
- **T0/T1 rate:** how many picked cheap/local? (goal: ≥ 40% of non-L3)
- **Model agreement:** run on T1 (Haiku) and T2 (Sonnet), compare tier choices
  - Same tier: ✅ consistent
  - Adjacent tier (T0 vs T1, or T1 vs T2): ⚠ minor divergence
  - Divergent (T0 vs T3): ❌ inconsistent (open ADR)

---

## Expected results

### G3 success criteria (from PRD)

✅ **≥ 40% routed to T0/T1**

Of the 15 test cases:
- Cases 1–5: T0–T1 (5 cases, 100% cheap)
- Cases 6–10: T1–T2 (5 cases, mix)
- Cases 11–15: T2–T3 (5 cases, expensive)

**If routing works:** 5–7 of first 10 pick T0/T1 = 50–70% of pre-L3 = ✅ passes G3.

### Consistency criteria

- **T1 vs T2 agreement:** ≥ 80% same tier (else open ADR)
- **Per-decision reasoning:** All decisions log candidates + tier reason (P2 compliance)

---

## See also

- `rules/02-orchestrator-model.md` (tier selection rules)
- `rules/04-tool-ranking.md` (tool ranking)
- `docs/PRD.md` §3 (G3 success metric: ≥ 40% routed to T0/T1)
