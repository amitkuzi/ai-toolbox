# PRD — AI Toolbox Plugin

**גרסה:** 0.1 · **תאריך:** 2026-09-02 · **בעלים:** עמית קוזי · **סטטוס:** טיוטה לאישור

---

## TL;DR

- **מה בונים:** ריפו חדש `amitkuzi/ai-toolbox` — Claude Code plugin שמאחד את שלושת השברים הקיימים (קטלוג ההיצע ב-`AiAgent`, שער הבחירה ב-`TaskTriagOrcetrator`, ו-Mission Router מה-`ai-gateway`) למוצר אחד שניתן להתקין, לייצא ולמכור.
- **הלב:** חמש החלטות מסודרות, כתובות כ-Markdown שה-LLM מפרש: (1) האם צריך Toolbox ונחיל סוכנים, (2) איזה מודל ינהל, (3) איזו קטגוריית כלי לכל תת-משימה, (4) איזה כלי בקטגוריה — משוקלל לפי מי משתמש ואיזה סוג משימה, (5) הערכת הצלחה ועדכון ציונים.
- **הזיכרון:** `tools.yaml` (קטלוג) + `scores.jsonl` (יומן תוצאות, append-only) + סוכן מתוזמן (GitHub Actions כברירת מחדל, Docker כאופציה) שאוסף כלים חדשים ומבצע הערכה ראשונית.
- **לא בונים ב-V1:** שירות HTTP, CLI דטרמיניסטי, UI. רק קבצים + skills + agents + hooks.

---

## 1. רקע — מה קיים היום

| שבר | מיקום | מה יש בו | מצב |
|---|---|---|---|
| **היצע (Supply)** | `AiAgent/ai-toolbox` | `tools.yaml` (36 כלים, 9 קטגוריות), `sources.yaml` (32 מקורות), `changelog.jsonl`, `CLAUDE.md` עם רוטינות יומי/שבועי, `ops/` (Docker + cron), `toolbox-api` (Node, סיווג URL) | פעיל, מתוחזק, יש audit trail |
| **ביקוש (Demand)** | `Luctures/TaskTriagOrcetrator/ai-toolbox` | `tools.yaml` (36 כלים, 8 סוגים), `selection-rules.md` (שער 5 שאלות + שוברי שוויון + cold-start), `decisions.md` (7 ADR), `gaps.md` (5 פערים), `evals/` | מבוסס רעיונית, לא מחובר להיצע |
| **ניתוב מודלים** | `ai-gateway/docs/PRD.md` §4.3–4.4 | דרישות Mission Router (`/route`, `/outcome`), יומן ציונים `scores.jsonl` עם decay ו-min-samples, `model-catalog.md` עם מחירים | PRD בלבד, לא מומש |
| **עותק ישן** | `Amit Kuzi Google Dominance Plan/ai-toolbox` | `tools.yaml` מקוצר (88 שורות) | להשליך אחרי מיזוג |

### הבעיות שהאיחוד פותר

- **שתי סכמות שונות ל-`tools.yaml`** (`category` מול `type`, `my_score` 1-10 עם משמעויות שונות, `verified` מול `last_reviewed`). סוכן שקורא אחת לא מבין את השנייה.
- **אין חיבור בין היצע לביקוש:** כלי שנוסף בקטלוג היומי לא נכנס לשער הבחירה; ציון שנפגע בשימוש לא חוזר לקטלוג.
- **אין החלטה על המודל המנהל:** כל משימה רצה על המודל הכי יקר כברירת מחדל.
- **אין לולאת משוב סגורה:** `my_score` מתעדכן ידנית, אם בכלל.
- **לא ניתן להפצה:** הכל כרוך ב-status-app, ב-Caddy ובנתיבים של המחשב של עמית.

---

## 2. חזון ומטרות

**חזון:** "מערכת הפעלה לבחירת כלים" — כל סוכן, בכל פרויקט, מקבל קטלוג, כלל החלטה וזיכרון, ומשאיר אחריו שובל ביקורת שמשפר את ההחלטה הבאה.

### מטרות V1

| # | מטרה | מדד הצלחה |
|---|---|---|
| G1 | קטלוג אחד, סכמה אחת | 100% מהרשומות משני הקבצים ממוזגות ועוברות ולידציה |
| G2 | חמש ההחלטות מתועדות ופועלות | כל משימה מייצרת רשומת `decision` עם 5 השדות |
| G3 | הוזלה מדידה | ≥ 40% מהמשימות מנותבות ל-T0/T1 (מקומי/זול) במקום למודל frontier |
| G4 | לולאת משוב | כל משימה מסתיימת ברשומת `outcome`; `my_score` מתעדכן אוטומטית אחרי ≥ 5 דגימות |
| G5 | קטלוג חי | ריצה יומית מוסיפה/מאמתת כלים ללא מגע יד; ריצה שבועית סוקרת מקורות |
| G6 | ניתן להפצה | התקנה ב-3 פקודות, ללא תלות במחשב של עמית; רישיון ברור |

### Non-goals (V1)

- שירות HTTP / Mission Router כ-API — נשאר ב-PRD של `ai-gateway` לשלב מאוחר.
- CLI דטרמיניסטי לניתוב — הוחלט: כללי Markdown בלבד. (ניתן להוסיף ב-V2 בלי לשנות את הנתונים.)
- ממשק משתמש. `toolbox-api` + `public/index.html` נשארים ב-`AiAgent` כ-optional.
- fine-tuning של מודלים.

---

## 3. משתמשים ותרחישים

| משתמש | צורך | תרחיש מייצג |
|---|---|---|
| **עמית (מפעיל)** | לתת משימה ולדעת שנבחר הכלי הזול-נכון | "שנה שם ל-200 קבצי STL" → `python3`, לא סוכן |
| **סוכן מתזמר (Claude Code)** | לפני כל האצלה: קטלוג + כלל | קורא `rules/`, בוחר, רושם `decision` |
| **סוכן מתוזמן (Curator)** | לאסוף, לאמת, לתת ציון ראשוני | ריצה יומית ב-Actions, commit אוטומטי |
| **לקוח חיצוני** | להתקין את ה-plugin על הקטלוג שלו | `claude plugin install ai-toolbox`, ממלא `profiles/` משלו |
| **מרצה (עמית)** | חומר הדגמה להרצאה | `decisions.md` + `scores.jsonl` = הוכחה חיה |

---

## 4. ארכיטקטורה

### 4.1 מבנה הריפו החדש

```
ai-toolbox/
├── .claude-plugin/
│   ├── plugin.json              # מטא-דאטה של ה-plugin
│   └── marketplace.json         # כדי שאפשר יהיה להתקין מ-GitHub ישירות
├── skills/
│   ├── toolbox-route/SKILL.md   # החלטות 1–4 (לפני האצלה)
│   ├── toolbox-outcome/SKILL.md # החלטה 5 (אחרי סיום)
│   └── toolbox-curate/SKILL.md  # רוטינות יומי/שבועי/חודשי (לסוכן המתוזמן)
├── agents/
│   ├── toolbox-curator.md       # אוסף ומאמת כלים ממקורות
│   ├── toolbox-assessor.md      # הערכה ראשונית + ניסוי תחום (bounded trial)
│   └── toolbox-auditor.md       # ביקורת חודשית: stale / dead / license
├── commands/
│   ├── route.md                 # /toolbox:route <task>
│   ├── outcome.md               # /toolbox:outcome <decision_id> <result>
│   ├── add.md                   # /toolbox:add <url>
│   ├── gaps.md                  # /toolbox:gaps
│   └── audit.md                 # /toolbox:audit
├── hooks/hooks.json             # SessionStart / SubagentStop / Stop
├── rules/                       # הלוגיקה — Markdown, אנגלית, ממוספר לפי סדר קריאה
│   ├── 00-glossary.md
│   ├── 01-swarm-gate.md         # החלטה 1
│   ├── 02-orchestrator-model.md # החלטה 2
│   ├── 03-category-gate.md      # החלטה 3
│   ├── 04-tool-ranking.md       # החלטה 4
│   ├── 05-outcome-scoring.md    # החלטה 5
│   └── 06-safety.md
├── catalog/                     # הנתונים — מקור האמת
│   ├── tools.yaml               # סכמה מאוחדת (§5)
│   ├── sources.yaml
│   ├── models.yaml              # מודלי LLM: מחיר, tier, context, residency
│   ├── scores.jsonl             # append-only, לולאת המשוב
│   ├── decisions.md             # ADR
│   ├── gaps.md
│   ├── changelog.jsonl
│   └── evals/<tool-id>.md
├── profiles/                    # "מי משתמש" — משקולות לפי פרסונה (§6.4)
│   ├── _default.yaml
│   └── amit.yaml
├── ops/                         # Docker + cron (אופציה ל-self-host)
├── .github/workflows/
│   ├── daily-refresh.yml
│   ├── weekly-sources.yml
│   └── monthly-audit.yml
├── docs/                        # תיעוד מלא באנגלית (§9)
├── CLAUDE.md                    # הוראות לסוכן שעובד בתוך הריפו
├── README.md
└── LICENSE
```

### 4.2 זרימת עבודה בזמן ריצה

```
משימה מהמשתמש
   │
   ▼
[hook: SessionStart] טוען תקציר קטלוג + פרופיל
   │
   ▼
skill: toolbox-route
   ├─ 1. Swarm gate   → L0 / L1 / L2 / L3
   ├─ 2. Model tier   → T0 / T1 / T2 / T3 למתזמר ולכל סוכן
   ├─ 3. Category     → לכל תת-משימה: script/mcp/skill/model/subagent/kb/plugin/schedule
   ├─ 4. Tool ranking → הכלי הזוכה + חלופה + install/auth
   └─ רושם decision ל-scores.jsonl (status: open)
   │
   ▼
ביצוע (סוכנים / כלים)
   │
   ▼
[hook: SubagentStop / Stop] מזכיר לסגור
   │
   ▼
skill: toolbox-outcome
   ├─ 5. Outcome: success/partial/fail, rework, cost, duration, human_rating
   ├─ append ל-scores.jsonl
   └─ אם n ≥ 5 → מעדכן my_score ב-tools.yaml (EMA + decay)
```

### 4.3 זרימה מתוזמנת (Curator)

```
daily   → discover מ-sources (value_score ≥ 3) → רשומות seed-unverified
        → validate slice (oldest first) → verified/stale/dead
        → קורא scores.jsonl → מעדכן my_score למי שהגיע ל-5 דגימות
        → מנסה לסגור gaps
        → changelog + commit + push
weekly  → סקירת sources: value_score, needs_user_action, מקורות חדשים
monthly → audit: stale > 90 יום, רישיונות, eval לכל כלי routable
```

---

## 5. סכמת הקטלוג המאוחדת (`tools.yaml`)

מיזוג שתי הסכמות. שדות חובה מסומנים ב-★.

| שדה | סוג | מקור | הערה |
|---|---|---|---|
| ★ `id` | slug | שניהם | |
| ★ `name` | string | supply | |
| ★ `type` | enum: `script` \| `mcp` \| `skill` \| `subagent` \| `model` \| `plugin` \| `schedule` \| `kb` | demand | **סוג ההפעלה** — משמש בהחלטה 3 |
| ★ `category` | enum: `runtime` \| `model` \| `agent-framework` \| `agent-infra` \| `coding-agent` \| `api` \| `gateway` \| `mcp` \| `skill` \| `tool` | supply | **תחום** — משמש לשורטליסט בלבד |
| ★ `purpose` | string | demand | שורה אחת |
| `abilities` / `pros` / `cons` | list | supply | |
| ★ `domains` | list | demand | תגיות לשורטליסט |
| ★ `task_types` | list | חדש | אילו `task_type` הכלי מתאים להם (§6.4) |
| ★ `cost` | enum: `free` \| `included` \| `metered` \| `paid` | demand | + `cost_notes` |
| `cost_per_use_usd` | number | חדש | הערכה, למדד G3 |
| ★ `local_capable` / ★ `agent_ready` | bool | שניהם | |
| ★ `data_residency` | `local` \| `cloud` \| `hybrid` | supply | אילוץ קשיח לפרטיות |
| ★ `autonomy` | 1–5 | supply | |
| ★ `license` | SPDX | שניהם | + `license_notes` |
| ★ `install` / ★ `auth` / `entrypoint` | string | שניהם | `auth`: `none` \| `account` \| `api-key` \| `oauth` \| `local-path` |
| `published_score` | string+source | supply | **רק** לדירוג תור הניסויים |
| ★ `my_score` | 1–10 | שניהם | אמפירי כשיש ≥ 5 דגימות; אחרת הערכה מסומנת |
| `score_rationale` | string | supply | |
| `score_samples` | int | חדש | כמה רשומות outcome תרמו ל-`my_score` |
| ★ `review_status` | `seed-unverified` \| `verified` \| `stale` \| `dead` | supply | |
| ★ `verified` | date | demand | שימוש מוצלח אחרון; פג אחרי 90 יום |
| `last_reviewed` | date | supply | בדיקת מטא-דאטה אחרונה |
| `maturity` / `tags` / `homepage` / `repo` / `notes` | | supply | |

**כללי מיזוג:** `type` + `category` שניהם חובה (הם עונים על שאלות שונות). `verified` = שימוש; `last_reviewed` = בדיקת מטא-דאטה. רשומה בלי `verified` היא **מועמד** (candidate), לא **ניתן לניתוב** (routable).

### `models.yaml` (חדש)

| שדה | הערה |
|---|---|
| `id`, `provider`, `model` | alias שמוכר ל-gateway / ל-Claude Code |
| `tier` | `T0` מקומי חינם · `T1` ענן זול · `T2` ביניים · `T3` frontier |
| `input_usd_mtok`, `output_usd_mtok`, `cache_hit_usd_mtok` | מ-`model-catalog.md` |
| `context_k`, `tokens_per_sec` | |
| `data_residency` | `local` / `cloud` |
| `strengths` | `[coding, reasoning, classification, hebrew, vision, long-context]` |
| `my_score`, `score_samples`, `verified` | כמו ב-tools |

### `scores.jsonl` (חדש — לפי F-401–F-410)

רשומת `decision` ורשומת `outcome` חולקות `decision_id`:

```json
{"ts":"...","kind":"decision","decision_id":"d-20260902-001","task":"...","task_type":"file-batch","actor":"human:amit","swarm_level":"L1","orchestrator_model":"T0:local-fast","subtasks":[{"id":"s1","type":"script","tool_id":"python3","alt":"agent-implementor","reason":"Q1 reproducible"}]}
{"ts":"...","kind":"outcome","decision_id":"d-20260902-001","tool_id":"python3","success":true,"partial":false,"rework":false,"duration_s":4,"cost_usd":0,"score":9,"scored_by":"auto:validator","reason":"..."}
{"ts":"...","kind":"outcome","decision_id":"d-20260902-001","tool_id":"python3","score":10,"scored_by":"human:amit","reason":"exactly what I wanted"}
```

---

## 6. חמש ההחלטות — מפרט הלוגיקה

כל החלטה = קובץ אחד ב-`rules/`, נקרא בסדר. כל קובץ בנוי: **קלט → שאלות → פלט → דוגמאות → מה לא לעשות.** להלן התמצית; הניסוח המלא (אנגלית) ייכתב בשלב 2 בתוכנית העבודה.

### החלטה 1 — האם צריך Toolbox ונחיל סוכנים? (`01-swarm-gate.md`)

**קלט:** תיאור המשימה. **פלט:** רמה L0–L3.

| רמה | תנאי | מה קורה |
|---|---|---|
| **L0 — inline** | תשובה מהידע, אין פלט קובץ, אין שירות חיצוני, < ~500 מילים | המתזמר עונה ישירות. **לא** קוראים ל-Toolbox. |
| **L1 — כלי יחיד** | תת-משימה אחת, דטרמיניסטית או שירות אחד | Toolbox כן, סוכן לא. script/mcp/skill. |
| **L2 — סוכן יחיד** | דורש שיפוט/כתיבה, תחום אחד, אין צורך בבדיקה עצמאית | סוכן אחד + כלים שלו |
| **L3 — נחיל** | ≥ 3 תת-משימות **ב-≥ 2 קטגוריות**, או ניתן למקבל, או דורש Validator עצמאי, או deliverable ל-inbox | פירוק → האצלה מקבילה → Validator |

**סימני נחיל (מספיק 2):** מספר תוצרים שונים · תחומים שונים (CAD + חומרים + תיעוד) · תלות בשירותים חיצוניים מרובים · דרישה לעצמאות בין כותב לבודק · סיכון גבוה (בלתי הפיך / ללקוח).

**כלל אנטי-דיפולט:** אם יש ספק בין L1 ל-L2 — L1. אם יש ספק בין L2 ל-L3 — L2. עלות הטעות כלפי מטה קטנה מעלות הטעות כלפי מעלה.

### החלטה 2 — איזה מודל ינהל? (`02-orchestrator-model.md`)

**קלט:** רמה מהחלטה 1 + אילוצים. **פלט:** tier למתזמר ו-tier לכל סוכן.

| Tier | דוגמאות (מ-`models.yaml`) | מתי |
|---|---|---|
| **T0** מקומי, $0 | `local-fast` (gemma4:12b), `local-coder` (qwen2.5-coder:14b) | סיווג, סיכום, extraction, ניתוב, טיוטה ראשונה, כל דבר עם `privacy: local` |
| **T1** ענן זול | Haiku 4.5, gemini-2.5-flash-lite, gpt-5-nano, GLM-4.7-Flash, deepseek-v4-flash | תת-משימות מוגדרות היטב, ולידציה סכמתית, סוכנים 24/7 |
| **T2** ביניים | Sonnet 5, kimi-coder, gemini-2.5-pro | קוד, מחקר, כתיבה לאינבוקס, מתזמר ל-L3 |
| **T3** frontier | Opus 5 / Fable 5 | ארכיטקטורה, החלטות בלתי הפיכות, Validator ל-deliverable ללקוח, כשל ב-T2 |

**כללי בחירה (בסדר):**

1. `privacy: local` → T0 בלבד. אילוץ קשיח.
2. **המתזמר** = tier של תת-המשימה הקשה ביותר **מינוס אחד**, מינימום T1 ל-L3. המתזמר מפרק ומאציל — לא צריך להיות החכם ביותר.
3. **סוכן** = tier לפי סוג העבודה: script/mcp → T0–T1; כתיבה/קוד → T2; שיפוט/אימות סופי → T2–T3.
4. **Escalation:** כשל או `partial` בניסיון ראשון → tier+1, פעם אחת בלבד, ונרשם ב-outcome.
5. **תקציב:** אם `budget_usd` ניתן — לא לחרוג; Batch API (50% הנחה) לכל דבר שלא דחוף.
6. **Cache-first:** אם context משותף גדול → להעדיף ספק עם cache hit זול (Anthropic 10%, OpenAI 10%).

### החלטה 3 — איזו קטגוריה לכל תת-משימה? (`03-category-gate.md`)

זהו השער הקיים מ-`selection-rules.md` §1, ללא שינוי מהותי — הוא כבר נכון (ADR D-002):

| # | שאלה | סוג |
|---|---|---|
| 1 | חייב להיות reproducible ביט-לביט? | `script` |
| 2 | צריך נתונים/פעולה בשירות חיצוני? | `mcp` |
| 3 | עשיתי את זה 3+ פעמים? | `skill` |
| 4 | צריך modality שאין ל-LLM טקסטואלי (תמונה/קול/embeddings) או **עצמאות ממודל אחר** (D-007)? | `model` |
| 5 | אחרת | `subagent` |

**תוספות V1:** לפני 1 — "האם זו קריאה לידע קיים?" → `kb`. "האם זה צריך לרוץ שוב ושוב בזמן קבוע?" → `schedule`. הסדר נשאר לפי דטרמיניזם ועלות.

### החלטה 4 — איזה כלי בקטגוריה? (`04-tool-ranking.md`)

**שלב א — מסננים קשיחים** (כלי שנכשל באחד מהם לא נכנס לדירוג):

- `license` תואם למטרה (מסחרי / פנימי) לפי הפרופיל
- `data_residency` תואם ל-`privacy` של המשימה
- `auth` זמין בסביבה (אין api-key → הכלי מסומן "דורש התערבות", לא נבחר בשקט)
- `review_status != dead`

**שלב ב — ציון אפקטיבי:**

```
effective = w_score · my_score_ctx
          + w_local · local_capable
          + w_agent · agent_ready
          + w_cost  · (1 − cost_rank/3)
          + w_fresh · fresh(verified)
```

- **`my_score_ctx`** = `my_score` **בהקשר** — ממוצע משוקלל של רשומות `outcome` עם אותו `task_type` (משקל 1.0), `task_type` קרוב (0.5), כללי (0.25); רשומות `human:*` × 1.5; decay אחרי 90 יום; מתחת ל-5 דגימות → משתמשים ב-`my_score` הכללי המסומן כהערכה.
- **המשקולות `w_*` מגיעות מ-`profiles/<actor>.yaml`** — זה "מי משתמש": פרופיל של עמית מעדיף local ו-cost; פרופיל לקוח ארגוני יכול להעדיף `verified` ו-license.
- **ברירת מחדל (`_default.yaml`):** `w_score 0.40, w_local 0.20, w_agent 0.15, w_cost 0.15, w_fresh 0.10`.

**שלב ג — cold start** (מ-`selection-rules.md` §2a, ללא שינוי): הערכה לעולם לא גוברת על מדידה; מועמד `seed-unverified` נכנס רק דרך **ניסוי תחום** (subtask אחד בסיכון נמוך מול הכלי הקיים); `published_score` מדרג את תור הניסויים בלבד.

**פלט:** הכלי הזוכה + החלופה השנייה + install/auth בשורה אחת + `reason`. אם אין מועמד → `gaps.md` (+ `hits`) וממשיכים עם הקרוב ביותר, בציון ההתפשרות.

### החלטה 5 — הערכה ועדכון ציונים (`05-outcome-scoring.md`)

**מתי:** בסיום כל משימה (hook `Stop` מזכיר; `/toolbox:outcome` מבצע).

**מה נאסף לכל `tool_id` שהשתתף:**

| שדה | מקור | הערה |
|---|---|---|
| `success` / `partial` / `fail` | הסוכן / Validator | |
| `rework` | האם היה צורך לחזור על תת-המשימה | העלות השלישית מהמצגת |
| `duration_s`, `cost_usd` | מדידה (LiteLLM אם קיים, אחרת הערכת הסוכן מסומנת `est:`) | |
| `score` 1–10 + `reason` | `auto:validator` / `agent:<name>` / `human:amit` | ריבוי ציונים תקין (F-405) |
| `escalated_from` | tier קודם אם הייתה escalation | מזין את החלטה 2 |

**עדכון `my_score` (בריצה היומית, לא בזמן המשימה — F-410):**

```
if score_samples(tool) >= 5:
    my_score = EMA(α=0.3) על outcome.score עם decay 90 יום, human × 1.5
    score_samples += n_new
    אם ירד ≥ 2 נקודות → הערה ב-notes + שורה ב-changelog
```

**עדכון משקולות `w_*` (חודשי, ב-audit):** ניתוח "חרטה" — לכל decision שנכשל, האם החלופה השנייה הייתה מצליחה לפי ההיסטוריה? אם דפוס חוזר (≥ 3) לאותה משקולת → הצעה לשינוי ב-`profiles/` **כ-PR, לא commit אוטומטי**. אדם מאשר.

**Retraction:** ציון שגוי = רשומה חדשה `{"retracts": "<record_id>"}`. אין עריכה.

---

## 7. הסוכן המתוזמן (Curator)

| ריצה | תדירות | סוכן | פלט | תקציב |
|---|---|---|---|---|
| `daily-refresh` | 07:00 | `toolbox-curator` (T1: Haiku/Sonnet, `--max-turns 40`) | רשומות חדשות `seed-unverified`, validation slice, `my_score` מ-scores.jsonl, commit | ~$0.05–0.30 |
| `weekly-sources` | ב' 08:00 | `toolbox-curator` | `sources.yaml` מעודכן, רשימת `needs_user_action` בהודעת ה-commit | ~$0.10 |
| `monthly-audit` | 1 לחודש | `toolbox-auditor` | stale/dead, רישיונות, eval לכל routable, הצעת משקולות כ-PR | ~$0.50 |
| `first-assessment` | on-demand / אחרי discover | `toolbox-assessor` | ציון מבני מהתיעוד + הצעת ניסוי תחום | |

**הערכה ראשונית = ציון מבני בלבד:** license, autonomy, local_capable, cost, maturity, agent_ready — כולם קריאים מהתיעוד. הסוכן **לא** מריץ את הכלי. הוא כותב `evals/<id>.md` עם הפקודה הקטנה ביותר שתוכיח שהכלי עובד, ומסמן `review_status: seed-unverified`. הריצה הראשונה אצל המשתמש היא הניסוי.

**היכן רץ:**

- **ברירת מחדל: GitHub Actions** — `ANTHROPIC_API_KEY` או `CLAUDE_CODE_OAUTH_TOKEN` כ-secret; commit עם `github-actions[bot]`; שער בטיחות YAML לפני commit (מ-`ops/run-task.sh` הקיים).
- **אופציה: Docker + cron** — `ops/` הקיים, מתועד ל-self-host ופרטיות.
- **שניהם משתמשים באותו skill `toolbox-curate`** — ההבדל הוא רק ה-runner.

---

## 8. Hooks ופקודות

| Hook | אירוע | פעולה |
|---|---|---|
| `SessionStart` | פתיחת סשן | מזריק תקציר: N כלים routable, gaps פתוחים, פרופיל פעיל, תזכורת ל-`/toolbox:route` |
| `UserPromptSubmit` | כל prompt | (קל) מזכיר את שער L0–L3 אם הפרומפט ארוך מ-N מילים או מזכיר קובץ/שירות |
| `SubagentStop` | סיום סוכן | מזכיר לרשום outcome לכלי שהסוכן השתמש בו |
| `Stop` | סיום תשובה | אם יש `decision` פתוח בלי `outcome` — מבקש לסגור |

| פקודה | מה עושה |
|---|---|
| `/toolbox:route <task>` | מריץ החלטות 1–4, מדפיס טבלת בחירה, רושם decision |
| `/toolbox:outcome <decision_id> <success\|partial\|fail> [score] [reason]` | החלטה 5 |
| `/toolbox:add <url>` | סיווג (tool/source), רשומה `pending`, changelog |
| `/toolbox:gaps` | מציג פערים פתוחים, מציע build אם `hits ≥ 3` |
| `/toolbox:audit` | מריץ את בדיקת ה-stale מקומית |

---

## 9. תיעוד (docs/, אנגלית)

| קובץ | קהל |
|---|---|
| `README.md` | 3 פקודות התקנה, GIF של `/toolbox:route`, מה זה נותן |
| `docs/PRD.md` | הגרסה האנגלית של מסמך זה |
| `docs/architecture.md` | הדיאגרמות מ-§4, זרימות, hooks |
| `docs/rules.md` | חמש ההחלטות — הסבר לבני אדם (ה-`rules/` עצמם הם לסוכן) |
| `docs/schema.md` | כל שדה ב-tools/sources/models/scores + דוגמאות |
| `docs/curator.md` | הפעלת Actions / Docker, secrets, עלויות, בטיחות |
| `docs/profiles.md` | איך להגדיר "מי משתמש" ומשקולות |
| `docs/customer-guide.md` | ללקוח: התקנה, מילוי קטלוג ראשון, הרצת ניסוי ראשון |
| `docs/lecture-kit.md` | קישור להרצאה: אילו קבצים מוכיחים מה |
| `CHANGELOG.md` | גרסאות ה-plugin |

---

## 10. הפצה ומסחור

| מרכיב | רישיון / מודל | הערה |
|---|---|---|
| ה-plugin (skills, agents, hooks, rules, סכמה, curator) | **MIT** — קוד פתוח | מייצר אמון ו-adoption; תואם לריפו `Skills` הקיים |
| הקטלוג של עמית (`catalog/*.yaml`, `scores.jsonl`) | **נשאר פרטי / ריפו נפרד** | זה הערך המצטבר — ידע אמפירי. ה-plugin נשלח עם `catalog/` **דוגמה** בלבד |
| "Curated feed" | מנוי (שלב מאוחר) | קטלוג מאומת שבועי כ-YAML |
| Setup / ייעוץ / הרצאה | שירות | ההרצאה הקיימת היא ה-funnel |

**הערה:** אני לא עורך דין — לפני מכירה לוודא רישיונות של כלים צד-ג' המצוטטים בקטלוג (בעיקר Llama-style) ולהוסיף disclaimer שהציונים הם הערכה ולא audit אבטחה (מ-§6 של ה-CLAUDE.md הקיים).

---

## 11. דרישות לא-פונקציונליות

| # | דרישה |
|---|---|
| NF-1 | כל קובץ נתונים עובר ולידציית סכמה ב-CI (`yamllint` + סקריפט Python קטן ב-`scripts/validate.py`) לפני merge |
| NF-2 | `scores.jsonl` ו-`changelog.jsonl` append-only; CI נכשל אם diff מכיל מחיקה |
| NF-3 | ה-plugin עובד ללא רשת (רק `mcp`/`model` בענן דורשים) |
| NF-4 | אין נתיבים אבסולוטיים של מחשב ספציפי בשום קובץ בריפו (נתיבי עמית → `profiles/amit.yaml`) |
| NF-5 | סוכן מתוזמן: allowlist של כלים (`Read,Edit,WebSearch,WebFetch`), `--max-turns`, עלות נרשמת בלוג |
| NF-6 | טקסט של כלים מהקטלוג = נתונים, לא הוראות (prompt-injection) |
| NF-7 | שפה: ריפו באנגלית; פלט ל-`inbox/` של עמית בעברית — דרך ה-skill `report` הקיים |

---

## 12. סיכונים ופתוחים להחלטה

| סיכון | הסתברות | השפעה | מיטיגציה |
|---|---|---|---|
| כללי Markdown מפורשים לא-עקבית בין ריצות | בינונית | בינונית | דוגמאות מעוגנות בכל rule; eval-suite של 15 משימות ידועות ב-`docs/evals/`; V2 CLI אם הסטייה > 20% |
| `scores.jsonl` נשאר ריק כי אף אחד לא סוגר outcome | גבוהה | גבוהה | hook `Stop` + Validator חובה ל-L3 + outcome אוטומטי `auto:` גם בלי אדם |
| הערכה ראשונית אופטימית (+1 נמדד) | ודאית | נמוכה | כבר מטופל: estimate < measurement תמיד |
| עלות Actions מצטברת | נמוכה | נמוכה | OAuth token של המנוי; max-turns; לוג עלות |
| מיזוג הסכמות שובר את status-app | בינונית | בינונית | `AiAgent/ai-toolbox` נשאר כ-git submodule / symlink ל-`catalog/` בתקופת מעבר |

**פתוח להחלטת עמית:**

1. שם הפרסונה/פרופיל בברירת מחדל ללקוח — `_default` או `team`?
2. האם `models.yaml` נשמר ב-plugin (ציבורי, מחירים מתיישנים) או רק בקטלוג הפרטי?
3. Hebrew מובנה ב-plugin (skill `report`) או תלות חיצונית?

---

## 13. הגדרת "גמור" ל-V1

- [ ] `claude plugin install` מ-GitHub עובד על מחשב נקי
- [ ] `/toolbox:route "rename 200 STL files"` → `python3`, L1, T0, בלי סוכן
- [ ] `/toolbox:route "design a bracket, pick filament, document in Hebrew"` → L3, 3 תת-משימות, 3 קטגוריות, Validator
- [ ] 5 outcome לכלי אחד → `my_score` מתעדכן בריצה היומית
- [ ] Actions רץ 7 ימים רצוף ללא כשל, מוסיף ≥ 1 כלי חדש
- [ ] כל docs/ קיימים; README מאפשר ללקוח להתחיל בלי לשאול את עמית
- [ ] ההרצאה מפנה ל-`decisions.md` + `scores.jsonl` בריפו החדש
