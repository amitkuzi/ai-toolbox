# תוכנית עבודה — AI Toolbox Plugin

**גרסה:** 0.1 · **תאריך:** 2026-09-02 · **מבוסס על:** `PRD-ai-toolbox.md` v0.1 · **ענף git:** `ai-toolbox` (ענף פרויקט לפי git-conventions)

---

## TL;DR

- **7 שלבים, ~11 ימי עבודה של סוכנים** (לא ימים קלנדריים — רוב העבודה מקבילית).
- **סדר:** ריפו וסכמה → כללים 1–4 → לולאת המשוב → Curator + Actions → תיעוד ואריזה → ולידציה ופיילוט → פרסום.
- **אבן דרך ראשונה שאפשר להשתמש בה: סוף שלב 2** — `/toolbox:route` עובד על הקטלוג הממוזג.
- **כל שלב מסתיים ב-Validator + commit** לפי הפייפליין `tasks/ → handoffs/ → drafts/ → Validator → inbox/`.

---

## 1. עקרונות ביצוע

| עיקרון | יישום |
|---|---|
| **מודל לפי משימה** (החלטה 2 של ה-PRD, מיושמת על עצמנו) | מיזוג YAML, ולידציה, סקריפטים → T0/T1. כתיבת rules ו-docs → T2. ביקורת ארכיטקטורה → T3 פעם אחת בשלב 0. |
| **סוכן אחד, אחריות אחת** | כל תת-משימה בטבלאות למטה עם בעלים אחד מהצוות |
| **אין רשומה בלי ולידציה** | `scripts/validate.py` רץ לפני כל commit משלב 1 |
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

### שלב 1 — סכמה אחת, קטלוג אחד (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 1.1 | כתיבת `docs/schema.md` — הסכמה המאוחדת מ-PRD §5 עם דוגמה לכל שדה | Implementor | מסמך | Validator: כל שדה משתי הסכמות הישנות ממופה או נדחה בנימוק |
| 1.2 | `scripts/validate.py` — בודק tools/sources/models/scores מול הסכמה; append-only check ל-jsonl | Implementor (T1) | סקריפט + GitHub Action `validate.yml` | נכשל על 5 קבצים שבורים מכוונים, עובר על תקינים |
| 1.3 | מיזוג `AiAgent/ai-toolbox/tools.yaml` (36) + `TaskTriagOrcetrator/ai-toolbox/tools.yaml` (36) → `catalog/tools.yaml` | Explorer (מיפוי) → Implementor (מיזוג, T1) | קטלוג ממוזג | 0 כפילויות `id`; כל רשומה עם `type` **ו-**`category`; ולידציה עוברת |
| 1.4 | `catalog/sources.yaml` — העתקה + ניקוי `pending` | Implementor | | ולידציה |
| 1.5 | `catalog/models.yaml` — מ-`ai-gateway/docs/model-catalog.md` + tiers T0–T3 | Researcher (אימות מחירים עדכניים) → Implementor | | כל מודל עם tier, מחיר, residency |
| 1.6 | העברת `decisions.md`, `gaps.md`, `evals/`, `changelog.jsonl` — ניקוי נתיבים אבסולוטיים (NF-4) | Implementor | | `grep -r "C:\\\\" catalog/` ריק |
| 1.7 | `profiles/_default.yaml` + `profiles/amit.yaml` (משקולות, privacy, license policy, נתיבים) | Implementor | | ולידציה |

**Commit:** `config: unified catalog schema + merged catalog (v0.2.0)`
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
| 2.6 | `skills/toolbox-route/SKILL.md` — קורא rules 00–04 + profile + catalog, מדפיס טבלה, כותב decision ל-`scores.jsonl` | Implementor | skill | `skill-creator` eval: 10 משימות, ≥ 8 ניתובים תואמים לצפוי |
| 2.7 | `commands/route.md`, `commands/gaps.md` | Guide | | פקודות עובדות |
| 2.8 | `hooks/hooks.json` — `SessionStart` בלבד בשלב זה | Guide | | תקציר מוזרק בפתיחה |

**Commit:** `config: decision rules 1-4 + toolbox-route skill (v0.3.0)`
**אבן דרך M1:** `/toolbox:route` שמיש על הקטלוג האמיתי.

---

### שלב 3 — כלל 5: לולאת המשוב (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 3.1 | `rules/05-outcome-scoring.md` — איסוף, EMA, decay, min-samples, retraction, ניתוח חרטה | Architect → Implementor | | דוגמה מספרית לעדכון ציון |
| 3.2 | `skills/toolbox-outcome/SKILL.md` + `commands/outcome.md` | Implementor | | 3 outcome נרשמים ל-decision אחד בלי לדרוס |
| 3.3 | `scripts/rescore.py` — קורא `scores.jsonl`, מעדכן `my_score`/`score_samples` ב-`tools.yaml` ו-`models.yaml` (רץ רק ב-daily) | Implementor (T1) | סקריפט | בדיקת יחידה: 5 דגימות → עדכון; 4 → אין |
| 3.4 | hooks `SubagentStop` + `Stop` — תזכורת לסגירת decision פתוח | Guide | | decision בלי outcome מציף תזכורת פעם אחת |
| 3.5 | Validator ל-L3 רושם outcome `auto:validator` אוטומטית | Implementor | הרחבה ל-skill | בדיקה על משימת L3 |

**Commit:** `config: outcome scoring loop + hooks (v0.4.0)`
**אבן דרך M2:** לולאה סגורה — decision → outcome → my_score.

---

### שלב 4 — Curator: איסוף והערכה ראשונית (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 4.1 | `skills/toolbox-curate/SKILL.md` — רוטינות daily/weekly/monthly מ-CLAUDE.md §2 הקיים + `rescore.py` | Implementor | skill | ריצה ידנית מקומית מייצרת commit תקין |
| 4.2 | `agents/toolbox-curator.md`, `agents/toolbox-assessor.md`, `agents/toolbox-auditor.md` — role prompts, allowlist כלים, max-turns | Implementor (T2) | 3 סוכנים | כל סוכן רץ headless |
| 4.3 | הערכה ראשונית: assessor כותב ציון מבני + `evals/<id>.md` + הצעת ניסוי תחום, **בלי להריץ** | Implementor | | על 3 כלים חדשים: פלט תואם לסכמה, `seed-unverified` |
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
| 5.4 | `catalog/` → `catalog-example/` בגרסה הציבורית; הקטלוג האמיתי של עמית לריפו פרטי `ai-toolbox-catalog` (או ענף מוגן) | Orchestrator + Implementor | הפרדה | plugin ציבורי ללא `scores.jsonl` של עמית |
| 5.5 | `Skills/ai-toolbox/SKILL.md` — skill דק בריפו `Skills` שמפנה ל-plugin | Implementor | | README של Skills מעודכן |
| 5.6 | `CHANGELOG.md`, `docs/lecture-kit.md` (איזה קובץ מוכיח איזה שקף) | Implementor | | |
| 5.7 | בדיקת רישיונות צד-ג' בקטלוג + disclaimer | Researcher | רשימה ב-`docs/licenses.md` | אין רשומה `license: unknown` |

**Commit:** `inbox: full documentation + packaging (v0.6.0)`

---

### שלב 6 — ולידציה ופיילוט (1.5 יום)

| # | משימה | בעלים | פלט | קבלה |
|---|---|---|---|---|
| 6.1 | `docs/evals/routing-suite.md` — 15 משימות ידועות עם ניתוב צפוי (כולל 3 הדוגמאות מ-selection-rules) | Architect | | |
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
| 1 | 1.5 | — | 0 |
| 2 | 2.0 | 5 (חלקית) | 1 |
| 3 | 1.5 | 4 | 2 |
| 4 | 1.5 | 3 | 1 (סכמה), 1.5 (models) |
| 5 | 1.5 | 2–4 | טיוטות; סופי אחרי 4 |
| 6 | 1.5 | — | 3, 4, 5 |
| 7 | 0.5 | — | 6 |
| **סה"כ** | **~10.5** | | **קריטי: 0→1→2→3→6→7 ≈ 7.5 ימים** |

---

## 4. הקצאת מודלים לעבודה (החלטה 2 מיושמת על התוכנית)

| סוג עבודה | Tier | מודל מוצע | הערכת עלות |
|---|---|---|---|
| מיזוג YAML, ולידציה, סקריפטים, hooks | T1 | Haiku 4.5 / kimi-coder | ~$2 |
| כתיבת rules, skills, docs | T2 | Sonnet 5 | ~$8 |
| ביקורת ארכיטקטורה (0.3), eval-suite (6.1) | T3 | Opus 5 — פעמיים בלבד | ~$3 |
| Curator בפיילוט (7 ימים × daily) | T1 | Haiku / Sonnet עם max-turns | ~$2 |
| **סה"כ משוער** | | | **~$15** (או $0 עם OAuth של המנוי) |

---

## 5. סיכונים ומיטיגציה לפי שלב

| שלב | סיכון | מיטיגציה |
|---|---|---|
| 1 | מיזוג ידני של 70 רשומות מייצר שגיאות | Explorer מייצר טבלת מיפוי `id → id` קודם; Implementor ממזג לפי הטבלה; ולידציה אוטומטית |
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
