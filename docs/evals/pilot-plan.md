# Pilot plan — Week-long real-world test

**Version:** 0.6 · **Date:** 2026-09-02 · **Duration:** 1 week (7 days) · **Measurement:** Cost + routing + gaps

---

## Pilot scope

Run AI Toolbox on real work for 7 days. Measure:
1. **Cost before/after** — total spend this week vs. historical average
2. **Routing distribution** — % routed to T0/T1/T2/T3 (goal: ≥ 40% T0/T1)
3. **Tool performance** — score trends; any regret patterns?
4. **Gaps found** — tools missing, routing mistakes, etc.

---

## Setup (Day 0)

### Install plugin

```bash
/plugin install amitkuzi/ai-toolbox
```

### Configure profile

Edit `profiles/amit.yaml` or create personal profile with your preferences:

```yaml
id: amit
privacy_default: hybrid
license_policy: commercial-ok
budget_usd_per_task: 0.50

weights:
  score: 0.40
  local: 0.20
  agent_ready: 0.15
  cost: 0.15
  fresh: 0.10
```

### Baseline cost

```bash
# Track how much you spent on AI tasks this past week
# (Check LiteLLM, Azure, AWS, or billing records)
# Store as: baseline_cost_usd = <amount>

echo "baseline_cost_usd: 15.50" > pilot-baseline.yaml
```

---

## Daily workflow (Days 1–7)

For each task:

1. **Use `/toolbox:route` before delegating**
   ```
   /toolbox:route <your-task-description>
   ```

2. **Follow recommendation** (don't override unless unusual)

3. **Log outcome after completion**
   ```
   /toolbox:outcome <decision-id>
   # Rate 1–10: how well did this tool work?
   ```

4. **Note any problems** (routing was wrong, tool failed, etc.)

---

## Example: 3D printing task

```
Day 2, 14:30 UTC

Task: "Design a bracket for a Raspberry Pi. Should have 4 M2 mounting holes, 
       be printable on Ender 3, and fit within 50×50×30mm."

Action:
  /toolbox:route Design a bracket for a Raspberry Pi...
  
Response:
  ✅ Routed to: claude-sonnet (T2) + FreeCAD skill
  Reason: Creative design (needs reasoning) + CAD expertise
  
Run:
  [Claude creates STL in FreeCAD skill]
  [User reviews, exports STL]
  
Outcome:
  /toolbox:outcome d-20260902-042
  Result: success
  Duration: 15 min
  Cost: $0.12 (sonnet token use)
  Score: 9/10 (design is excellent, fits constraints)
  
Note: Would have been cheaper with Haiku, but design quality matters here.
```

---

## Daily checklist

At end of each day:

- [ ] Logged outcomes for all routed tasks
- [ ] No tasks with missing decisions (check remind_outcome hook)
- [ ] Any routing that felt wrong? → note it
- [ ] Any tools that failed? → rate them low (< 5)

---

## Measurement: daily tracking

Create a `pilot-log.yaml`:

```yaml
pilot_start: 2026-09-02
baseline_cost_usd: 15.50
tasks_routed: 0
cost_this_week: 0

days:
  1:
    date: 2026-09-02
    tasks: 5
    cost_usd: 2.50
    t0_count: 2
    t1_count: 2
    t2_count: 1
    t3_count: 0
    gaps_found: ["need free OCR tool"]
    
  2:
    date: 2026-09-03
    tasks: 4
    cost_usd: 1.80
    t0_count: 1
    t1_count: 2
    t2_count: 1
    t3_count: 0
    gaps_found: []
```

---

## End-of-week report (Day 7, PM)

### Cost analysis

```bash
# Calculate
total_cost_usd = sum(day.cost_usd for day in days)
cost_reduction = (baseline - total_cost_usd) / baseline * 100
cost_per_task = total_cost_usd / total_tasks

echo "Baseline (historical): $baseline_cost_usd/week"
echo "Pilot week actual:     $total_cost_usd/week"
echo "Savings:               ${cost_reduction}%"
echo "Per task:              $cost_per_task"
```

### Routing distribution

```bash
# Count by tier
t0_pct = t0_count / total_tasks * 100
t1_pct = t1_count / total_tasks * 100
t2_pct = t2_count / total_tasks * 100
t3_pct = t3_count / total_tasks * 100
cheap_pct = (t0_count + t1_count) / total_tasks * 100

echo "T0 (local):     ${t0_pct}%"
echo "T1 (cheap):     ${t1_pct}%"
echo "T2 (mid):       ${t2_pct}%"
echo "T3 (frontier):  ${t3_pct}%"
echo "---"
echo "T0+T1 (cheap):  ${cheap_pct}% (goal: ≥ 40%)"

if [ "$cheap_pct" -ge 40 ]; then
  echo "✅ G3 SUCCESS: ≥ 40% routed to T0/T1"
else
  echo "⚠️ G3 BELOW GOAL: only ${cheap_pct}% cheap"
fi
```

### Gap analysis

```bash
# List all gaps mentioned during the week
gaps=$(grep -h "gaps_found" pilot-log.yaml | grep -o '"[^"]*"' | sort | uniq)

echo "Gaps found:"
for gap in $gaps; do
  echo "  - $gap"
done

# Append to catalog
for gap in $gaps; do
  python scripts/store.py append --kind gap.opened \
    --subject-id "gap-pilot-$(date +%s)" \
    --actor human:amit \
    --via pilot \
    --reason "Pilot week: $gap" \
    --payload '{"description": "'$gap'"}'
done
```

### Tool performance review

```bash
# Query scores from the pilot
python scripts/store.py query scores --filter 'via=outcome,ts>2026-09-02' \
  > pilot-outcomes.jsonl

# Summarize per tool
jq -r '.payload | "\(.tool_id): \(.score)/10 (\(.result))"' pilot-outcomes.jsonl | \
  sort | uniq -c | sort -rn
```

### Success criteria

| Metric | Goal | Pilot result |
|---|---|---|
| **Cost reduction** | 20–30% | ? |
| **T0/T1 routing** | ≥ 40% | ? |
| **Avg tool score** | ≥ 7/10 | ? |
| **No crashes** | 100% uptime | ? |
| **Clean install** | passes in 5 min | ? (tested separately) |

---

## Failure modes

| Problem | Action |
|---|---|
| Routing picks expensive tool for simple task | Review rules 02–04; may need weight tuning |
| Tool scores go down (< 5/10) | Flag for auditor; consider retiring tool |
| Plugin crashes or validation fails | Debug, file issue, may need hotfix before release |
| Cost doesn't improve | Weights may need adjustment; review rules |
| Gaps are numerous | May need discovery improvements in curator |

---

## See also

- `docs/customer-guide.md` (user perspective on `/toolbox:route` + `/toolbox:outcome`)
- `docs/evals/routing-suite.md` (test cases)
- `docs/PRD.md` §3 (G3 metric: ≥ 40% T0/T1)
- `.github/workflows/daily-refresh.yml` (automated curator runs during pilot)
