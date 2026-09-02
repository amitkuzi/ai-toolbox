# תוכנית עבודה — AI Toolbox Plugin

**גרסה:** 0.2 · **תאריך:** 2026-09-02 · **מבוסס על:** `PRD-ai-toolbox.md` v0.2 (עקרונות נתונים P1–P4) · **ענף git:** `ai-toolbox` (ענף פרויקט לפי git-conventions)

---

## TL;DR

- **7 שלבים, ~12 ימי עבודה של סוכנים** (לא ימים קלנדריים — רוב העבודה מקבילית). 0.2 מוסיף ~1.5 יום ל-Catalog Store + ledger (P1–P4).
- **סדר:** ריפו וסכמה → כללים 1–4 → לולאת המשוב → Curator + Actions → תיעוד ואריזה → ולידציה ופיילוט → פרסום.
- **אבן דרך ראשונה שאפשר להשתמש בה: סוף שלב 2** — `/toolbox:route` עובד על הקטלוג הממוזג.
- **כל שלב מסתיים ב-Validator + commit** לפי הפייפליין `tasks/ → handoffs/ → drafts/ → Validator → inbox/`.

---

## 1. עקרונות ביצוע

| עיקרון | יישום |
|---|---|
| **מודל לפי משימה** (החלטה 2 של ה-PRD, מיושמת על עצמנו) | מיזוג YAML, ולידציה, סקריפטים → T0/T1. כתיבת rules ו-docs → T2. ביקורת ארכיטקטורה → T3 פעם אחת בשלב 0. |
| **סוכן אחד, אחריות אחת** | כל תת-משימה בטבלאות למטה עם בעלים אחד מהצוות |
| **אין רשומה בלי ולידציה** | `scripts/validate.py` רץ לפני כל commit משלב 1 — כולל append-only guard ו-`views == project(ledger)` |
| **P1–P4 מיום אחד** | אף skill/agent לא ניגש לקובץ ב-`catalog/` ישירות; רק `store`. הסוכנים מוסיפים אירועים, לא עורכים. הפרה = כשל Validator. |
| **אנגלית בריפו, עברית ב-inbox** | סיכומי שלבים → `inbox/ai-toolbox/` דרך skill `report` |
| **commit לכל שלב** | prefix לפי git-conventions + גרסת plugin בהודעה (`v0.1.0` → `v0.7.0`) |

---

## 2. השלבים

### שלב 0 — בסיס: ריפו, ענף, סקלטון (0.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 0.1 | יצירת `github.com/amitkuzi/ai-toolbox`, ענף `development`, README ראשוני, LICENSE MIT | Implementor | ריפו ריק עם מבנה §4.1 מה-PRD | `tree` תואם ל-PRD |
| 0.2 | `.claude-plugin/plugin.json` + `marketplace.json` | Guide (claude-code-guide) | plugin ניתן להתקנה (ריק) | `claude plugin install` מצליח |
| 0.3 | סקירת ארכיטקטורה של ה-PRD — "grill me" על החלטות 1–5 | Architect (T3, פעם אחת) | `catalog/decisions.md` D-008..D-0xx | אין סתירה פתוחה בין rules |
| 0.4 | רישום הפרויקט: `projects/ai-toolbox.md` + `projects/README.md` בסביבת העבודה | Orchestrator | קובץ פרויקט | commit `project:` |

**Commit:** `init: ai-toolbox plugin skeleton (v0.1.0)`

---

### שלב 1 — Catalog Store, ledger אחד, קטלוג אחד (3 ימים)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 1.1 | `docs/schema.md` — מעטפת האירוע (PRD §5.0) + payloads לכל `kind` + השדות המחושבים של ה-views | Implementor | מסמך | Validator: כל שדה משתי הסכמות הישנות ממופה לאירוע/view או נדחה בנימוק |
| 1.2 | **`scripts/store.py` + `backends/files.py`** — `append` / `query` / `project` / `trace` (P1); `event_id` ULID, `ts`, חובת `reason` | Implementor (T2) | adapter | contract test: 12 תרחישים עוברים |
| 1.3 | `backends/sqlite.py` — אותו contract test | Implementor (T1) | backend שני | `project` מייצר views זהים ביט-לביט ל-`files` על אותו ledger |
| 1.4 | `scripts/validate.py` — סכמה + **append-only guard** (diff של ledger מכיל רק `+`) + `views == project(ledger)` + NF-2c (אין נתיבי catalog ב-rules/skills) | Implementor (T1) | סקריפט + Action `validate.yml` | נכשל על 6 הפרות מכוונות (מחיקה, עריכה, אירוע בלי reason, view ידני, נתיב ב-skill, id כפול) |
| 1.5 | **מיגרציה:** `AiAgent/ai-toolbox/tools.yaml` (36) + `TaskTriagOrcetrator/ai-toolbox/tools.yaml` (36) → אירועי `tool.added` + `score.seed` ב-`ledger/tools.jsonl`/`scores.jsonl`, `via: migration`, `reason` מצטט קובץ מקור ו-`last_reviewed` | Explorer (טבלת מיפוי id→id) → Implementor (סקריפט מיגרציה חד-פעמי, T1) | ledger | 0 כפילויות `id`; כל אירוע עם `type` **ו-**`category`; `store project` מייצר `views/tools.yaml` שמכיל את כל 72 הרשומות (אחרי איחוד כפולים) |
| 1.6 | מיגרציה של `sources.yaml` (32), `changelog.jsonl` (→ אירועים היסטוריים עם ה-`ts` המקורי), `decisions.md` (7 ADR → `adr.added`), `gaps.md` (5 → `gap.opened`) | Implementor (T1) | | ה-changelog ההיסטורי נשמר כאירועים — לא נזרק |
| 1.7 | `ledger/models.jsonl` — מ-`ai-gateway/docs/model-catalog.md` + tiers T0–T3 | Researcher (אימות מחירים עדכניים) → Implementor | | כל מודל עם tier, מחיר, residency |
| 1.8 | ניקוי נתיבים אבסולוטיים (NF-4) → `profiles/amit.yaml`; `profiles/_default.yaml` | Implementor | | `grep -r "C:\\\\" catalog/` ריק |
| 1.9 | `rules/07-data-contract.md` — P1–P4 בניסוח לסוכן (מה מותר: `store append`; מה אסור: Edit על catalog/) | Architect → Implementor | | Validator: סוכן T1 שקורא רק את הקובץ הזה מסרב לערוך view |

**Commit:** `config: catalog store + append-only ledger + migrated catalog (v0.2.0)`
**סיכום לאינבוקס:** "מה מוזג, מה נזרק, מה נשאר פתוח" (עברית).

---

### שלב 2 — כללים 1–4 + skill הניתוב (2 ימים)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 2.1 | `rules/00-glossary.md` + `rules/06-safety.md` (מ-CLAUDE.md §6 הקיים) | Implementor (T2) | | Validator |
| 2.2 | `rules/01-swarm-gate.md` — L0–L3, סימני נחיל, כלל אנטי-דיפולט, 6 דוגמאות | Architect (טיוטה) → Implementor | | 6 הדוגמאות מסווגות נכון ע"י T1 ו-T2 בנפרד |
| 2.3 | `rules/02-orchestrator-model.md` — tiers, 6 כללי בחירה, escalation | Architect → Implementor | | 6 דוגמאות עקביות בין מודלים |
| 2.4 | `rules/03-category-gate.md` — העברת §1 + §3 מ-`selection-rules.md`, הוספת `kb`/`schedule` | Implementor | | 3 הדוגמאות המקוריות עדיין עוברות |
| 2.5 | `rules/04-tool-ranking.md` — מסננים קשיחים, נוסחת effective, `my_score_ctx`, cold-start, פלט | Architect → Implementor | | דוגמה מחושבת ידנית לכל מסלול |
| 2.6 | `skills/toolbox-route/SKILL.md` — קורא rules 00–04 + 07, profile, `store query --routable`; מדפיס טבלה; `store append` של decision **עם כל המועמדים והנימוקים** (P2) | Implementor | skill | `skill-creator` eval: 10 משימות, ≥ 8 ניתובים תואמים לצפוי; כל decision מכיל `candidates[]`, `reason`, `rules_version` |
| 2.7 | `commands/route.md`, `commands/gaps.md`, **`commands/trace.md`** (P2) | Guide | | `/toolbox:trace` על decision מהעבר מציג את השרשרת המלאה |
| 2.8 | `hooks/hooks.json` — `SessionStart` בלבד בשלב זה | Guide | | תקציר מוזרק בפתיחה |

**Commit:** `config: decision rules 1-4 + toolbox-route skill (v0.3.0)`
**אבן דרך M1:** `/toolbox:route` שמיש על הקטלוג האמיתי.

---

### שלב 3 — כלל 5: לולאת המשוב (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 3.1 | `rules/05-outcome-scoring.md` — איסוף, EMA, decay, min-samples, retraction, ניתוח חרטה | Architect → Implementor | | דוגמה מספרית לעדכון ציון |
| 3.2 | `skills/toolbox-outcome/SKILL.md` + `commands/outcome.md` — רק `store append score.outcome / score.human` (P3/P4) | Implementor | | 3 outcome נרשמים ל-decision אחד; ה-diff של ה-ledger = 3 שורות `+` בלבד |
| 3.3 | `scripts/rescore.py` = ה-projection של ציונים בתוך `store project` — מחשב `my_score_current`, `score_samples`, `score_trend`, `by_task_type`, `by_actor` ל-`views/scores-summary.yaml` ו-`views/tools.yaml`; **לא כותב ל-ledger** | Implementor (T1) | projection | בדיקת יחידה: 5 דגימות → ערך מחושב; 4 → `estimate: true`; retract מוריד דגימה; ledger ללא שינוי (hash) |
| 3.3b | `commands/project.md` — `store project` + diff של views לפני commit | Guide | | |
| 3.4 | hooks `SubagentStop` + `Stop` — תזכורת לסגירת decision פתוח | Guide | | decision בלי outcome מציף תזכורת פעם אחת |
| 3.5 | Validator ל-L3 רושם outcome `auto:validator` אוטומטית | Implementor | הרחבה ל-skill | בדיקה על משימת L3 |

**Commit:** `config: outcome scoring loop + hooks (v0.4.0)`
**אבן דרך M2:** לולאה סגורה — decision → outcome → my_score.

---

### שלב 4 — Curator: איסוף והערכה ראשונית (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 4.1 | `skills/toolbox-curate/SKILL.md` — רוטינות daily/weekly/monthly מ-CLAUDE.md §2 הקיים, מנוסחות מחדש כ-**append בלבד** (`tool.added`, `score.seed`, `tool.status`, `gap.closed`) + `store project` בסוף | Implementor | skill | ריצה ידנית מקומית: ledger diff הוא `+` בלבד, views מתעדכנות, validate עובר |
| 4.2 | `agents/toolbox-curator.md`, `agents/toolbox-assessor.md`, `agents/toolbox-auditor.md` — role prompts, allowlist כלים (**ללא `Edit` על `catalog/`** — רק `Bash(store append …)`), max-turns | Implementor (T2) | 3 סוכנים | כל סוכן רץ headless; ניסיון Edit על catalog/ נחסם |
| 4.3 | הערכה ראשונית: assessor מוסיף `score.seed` עם `reason` מפורט (rubric) + `evals/<id>.md` + הצעת ניסוי תחום, **בלי להריץ** | Implementor | | על 3 כלים חדשים: אירועים תואמים לסכמה, `reason` מצטט את הרובריקה |
| 4.4 | `.github/workflows/daily-refresh.yml`, `weekly-sources.yml`, `monthly-audit.yml` — secrets, שער YAML, commit bot | Guide → Implementor | 3 workflows | `workflow_dispatch` ידני מצליח ומבצע commit |
| 4.5 | `ops/` — העברת Docker + `run-task.sh` הקיימים, עדכון ל-skill החדש | Implementor | | `docker compose run --rm runner daily` עובד |
| 4.6 | `commands/add.md`, `commands/audit.md` | Guide | | |
| 4.7 | התראה על כשל ריצה — ntfy / Slack `AgentClaude` | Implementor | | ריצה כושלת מכוונת שולחת הודעה |

**Commit:** `team: curator/assessor/auditor agents + scheduled runs (v0.5.0)`
**אבן דרך M3:** Actions רץ לבד, מוסיף כלים.

---

### שלב 5 — תיעוד ואריזה (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 5.1 | `docs/PRD.md` (אנגלית — מהטיוטה שנמסרה עם מסמך זה), `docs/architecture.md`, `docs/rules.md` | Implementor (T2) | | Validator: תואם ל-rules/ בפועל |
| 5.2 | `docs/curator.md`, `docs/profiles.md`, `docs/customer-guide.md` | Implementor | | לקוח מדומה (סוכן ללא context) מצליח להתקין לפי המדריך |
| 5.3 | `README.md` — 3 פקודות התקנה, GIF של `/toolbox:route` (`gif_creator`) | Implementor + Guide | | |
| 5.4 | `catalog/` → `catalog-example/` (ledger קטן + views) בגרסה הציבורית; הקטלוג האמיתי של עמית לריפו פרטי `ai-toolbox-catalog` | Orchestrator + Implementor | הפרדה | plugin ציבורי ללא `ledger/scores.jsonl` של עמית |
| 5.4b | `docs/storage.md` — חוזה ה-Store, איך כותבים backend חדש (postgres/ארגוני), contract test | Implementor | | לקוח מדומה מוסיף backend דמה לפי המסמך |
| 5.5 | `Skills/ai-toolbox/SKILL.md` — skill דק בריפו `Skills` שמפנה ל-plugin | Implementor | | README של Skills מעודכן |
| 5.6 | `CHANGELOG.md`, `docs/lecture-kit.md` (איזה קובץ מוכיח איזה שקף) | Implementor | | |
| 5.7 | בדיקת רישיונות צד-ג' בקטלוג + disclaimer | Researcher | רשימה ב-`docs/licenses.md` | אין רשומה `license: unknown` |

**Commit:** `inbox: full documentation + packaging (v0.6.0)`

---

### שלב 6 — ולידציה ופיילוט (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 6.1 | `docs/evals/routing-suite.md` — 15 משימות ידועות עם ניתוב צפוי (כולל 3 הדוגמאות מ-selection-rules) | Architect | | |
| 6.1b | **בדיקת אי-שינוי:** ריצה מלאה של daily + 10 route/outcome → hash של כל שורה קיימת ב-ledger זהה; רק תוספות | Validator | | P4 מוכח |
| 6.2 | הרצת ה-suite על T1 ו-T2 — מדידת עקביות בין ריצות | Validator | טבלת תוצאות | ≥ 80% תואם; סטייה בין מודלים < 20% (אחרת → נפתח ADR ל-CLI ב-V2) |
| 6.3 | פיילוט: שבוע של משימות אמיתיות של עמית דרך ה-plugin (3D printing, report, code) | Orchestrator | `scores.jsonl` עם ≥ 20 רשומות | ≥ 40% מהמשימות ב-T0/T1 (G3) |
| 6.4 | התקנה נקייה על מחשב שני / container ריק לפי `customer-guide.md` | Validator | | עובד בלי שאלות לעמית |
| 6.5 | דוח פיילוט לאינבוקס (עברית): עלות לפני/אחרי, ניתובים, פערים | Validator → skill `report` | `inbox/ai-toolbox/דוח-פיילוט.md` | |

**Commit:** `task: pilot results + routing eval suite (v0.7.0-rc)`
**אבן דרך M4:** הגדרת "גמור" מ-PRD §13 מסומנת כולה.

---

### שלב 7 — פרסום (0.5 יום)

| # | משימה | בעלים |
|---|---|---|
| 7.1 | tag `v1.0.0`, release notes, marketplace entry | Implementor |
| 7.2 | הגשה ל-`awesome-claude-code` / `claude-plugins-community` (שני מקורות שכבר בקטלוג) | Researcher |
| 7.3 | עדכון ההרצאה: שקפים 9–12 מפנים לריפו החדש | Orchestrator |
| 7.4 | פוסט השקה (LinkedIn/אתר) — דרך brand-kit הקיים | Implementor |

**Commit:** `project: ai-toolbox v1.0.0 release`

---

## 3. לוח זמנים ותלויות

```
שלב 0 ─┬─ שלב 1 ─┬─ שלב 2 ──┬─ שלב 3 ──┬─ שלב 6 ── שלב 7
       │         │          │          │
       │         └─ 1.5 ────┼─ שלב 4 ──┤
       │                    │          │
       └────────────────────┴─ שלב 5 ──┘
```

| שלב | ימי סוכן | מקביל ל- | תלוי ב- |
|---|---|---|---|
| 0 | 0.5 | — | — |
| 1 | 3.0 | — | 0 |
| 2 | 2.0 | 5 (חלקית) | 1 |
| 3 | 1.5 | 4 | 2 |
| 4 | 1.5 | 3 | 1 (סכמה), 1.5 (models) |
| 5 | 1.5 | 2–4 | טיוטות; סופי אחרי 4 |
| 6 | 1.5 | — | 3, 4, 5 |
| 7 | 0.5 | — | 6 |
| **סה"כ** | **~12** | | **קריטי: 0→1→2→3→6→7 ≈ 9 ימים** |

---

## 4. הקצאת מודלים לעבודה (החלטה 2 מיושמת על התוכנית)

| סוג עבודה | Tier | מודל מוצע | הערכת עלות |
|---|---|---|---|
| מיגרציה, ולידציה, backends, hooks | T1 | Haiku 4.5 / kimi-coder | ~$3 |
| `store.py` + contract test | T2 | Sonnet 5 / kimi-coder | ~$2 |
| כתיבת rules, skills, docs | T2 | Sonnet 5 | ~$8 |
| ביקורת ארכיטקטורה (0.3), eval-suite (6.1) | T3 | Opus 5 — פעמיים בלבד | ~$3 |
| Curator בפיילוט (7 ימים × daily) | T1 | Haiku / Sonnet עם max-turns | ~$2 |
| **סה"כ משוער** | | | **~$18** (או $0 עם OAuth של המנוי) |

---

## 5. סיכונים ומיטיגציה לפי שלב

| שלב | סיכון | מיטיגציה |
|---|---|---|
| 1 | מיזוג של 72 רשומות מייצר שגיאות | Explorer מייצר טבלת מיפוי `id → id` קודם; סקריפט מיגרציה (לא ידני); ולידציה אוטומטית |
| 1 | סוכנים "מתקנים" views ידנית מתוך הרגל | `07-data-contract.md` נטען בכל סשן; CI מפיל; allowlist ללא Edit על catalog/ |
| 2 | rules ארוכים מדי → הסוכן מדלג | כל rule ≤ 150 שורות; טבלת החלטה בראש, דוגמאות בסוף |
| 3 | אף אחד לא סוגר outcome | hook `Stop` + `auto:validator` ב-L3 — הלולאה לא תלויה באדם |
| 4 | Actions נתקע על permissions | allowlist מפורש + `--max-turns`; fallback מתועד ל-Docker |
| 5 | הקטלוג הפרטי דולף לציבורי | `catalog/` ב-`.gitignore` של הגרסה הציבורית; CI בודק שאין `scores.jsonl` בריפו |
| 6 | עקביות < 80% | ADR מיידי ל-CLI (V2) — הנתונים לא משתנים, רק המנוע |

---

## 6. מה נדרש מעמית

| מתי | מה |
|---|---|
| שלב 0 | ליצור את הריפו ב-GitHub (או לאשר יצירה עם PAT); להחליט על 3 הפתוחים ב-PRD §12 |
| שלב 1 | לאשר את טבלת המיפוי של המיזוג (5 דקות) |
| שלב 4 | להזין `ANTHROPIC_API_KEY` / `CLAUDE_CODE_OAUTH_TOKEN` + `GITHUB_TOKEN` כ-secrets |
| שלב 6 | שבוע של עבודה רגילה דרך ה-plugin + דירוג `human:amit` על ~10 משימות |
| שלב 7 | לאשר פרסום ורישיון |

---

## 7. הצעד הבא

1. אישור PRD + תוכנית זו (או הערות).
2. תשובה ל-3 הפתוחים ב-PRD §12.
3. יצירת הריפו → פתיחת ענף `ai-toolbox` → שלב 0.
