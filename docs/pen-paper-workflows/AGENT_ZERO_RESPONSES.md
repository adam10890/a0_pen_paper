# # סיכום קצר — שלב 1 אפיון P&P + Workflow Dashboard

**סטטוס:** לא שיניתי קוד. ביצעתי איסוף evidence בלבד ויצרתי artifacts תחת:

`/a0/usr/workdir/pen_paper_phase1_artifacts/`

השורה התחתונה: **P&P עובד כמחברת/Workspace**, אבל **Workflow Dashboard עדיין לא מתפקד כ־Policy/State Machine אמיתי**. כרגע הוא יותר עורך templates מאשר מנגנון deterministic.

---

# חוויית שימוש

## 1. מתי לפתוח `pen_paper` לעומת רק `skills_tool:load`?

| מצב | פעולה נכונה |

|---|---|

| רק צריך לדעת איך לעבוד / methodology | `skills_tool:load` בלבד |

| משימה מעל 3–4 צעדים, audit, debugging, planning, research | לפתוח `pen_paper` |

| workflow שרוצים לבדוק ולשמר state | לפתוח `pen_paper` עם template |

| skill יציב שכבר הוכח | `skills_tool:load`, בלי P&P אלא אם יש state חדש |

**כלל אפיון:** Skill = הוראות התנהגות. P&P = state runtime.

---

## 2. כשלי P&P — תדירות, recovery, state drift?

ממצאים:

- יש **2 סשנים active פתוחים** מול **6 archived**.

- אין enforcement לסגירה `close`) בסוף משימה.

- אם מודל שוכח `close`, נוצר **state drift**.

- כשלי section לא חוקיים נדחים ב־public tool, אבל המודל צריך לדעת להתאושש.

Recovery היום:

- ידני: לקרוא `pen_paper list/read`, להבין מה פתוח, ואז `close`.

- אין auto-recovery / validator.

---

## 3. Canvas Workflows vs `create_template` — מה חסר למדיניות?

חסר:

1. **Locking / versioning** — אם אתה עורך ב־Canvas ואני כותב ל־registry במקביל, אין מנגנון conflict resolution ברור.

2. **Policy metadata** — אין fields כמו `required_steps`, `success_criteria`, `failure_policy`, `model_min_capability`.

3. **Execution state** — registry שומר template, לא run state.

4. **Validation layer** — אין בדיקה שה־template ניתן להרצה deterministic.

כרגע Canvas + `create_template` הם **editor**, לא policy engine.

---

## 4. `pen_paper_wiki_template` + `/data/SharedBrain` — עובד?

כן, ברמת availability: הכלי קיים וה־SharedBrain זמין במערכת.

אבל החיבור הוא **חלקי**:

- `list_templates` / `load_template` מחזירים payload.

- `pen_paper.create` לא מפרש payload כסכמה.

- בפועל payload נכנס כ־text לתוך `notes`.

כלומר: **עובד כ־source/import**, לא כ־contract enforced.

---

## 5. ניסית base_workflows hooks?

בדיקה מצאה:

| Hook target | מצב |

|---|---|

| `research.md` | חסר |

| `debugging.md` | חסר |

| `validation.md` | חסר |

לכן `on_stuck→debugging` לא יכול להיות אמין. אם hook מופעל, הוא כנראה ייכשל / יחזיר template missing / ידרוש improvisation.

---

# דטרמיניזם

## 6. אותה תבנית + משתנים על שני מודלים — מה השתנה?

אין עדיין diff כמותי נקי בין מודלים. אבל לפי המבנה הקיים, צפויים הבדלים ב:

| אזור | למה יש drift |

|---|---|

| האם לפתוח P&P | תלוי מודל/skill recognition |

| האם לקרוא wiki templates | לא enforced |

| שמות sections | public tool דוחה חריגים, אבל מודל קטן עלול להיתקע |

| סגירת session | אין חובה בקוד |

| שימוש ב־base_hooks | targets חסרים |

צריך test matrix: אותה תבנית × אותם variables × שני מודלים × להשוות `workspace.json`.

---

## 7. `skills_tool:load` לפני workflow כמו BMAD או רק trigger?

לא לסמוך רק על trigger.

**המלצה לאפיון:**

1. Dashboard מזהה workflow type.

2. Dashboard מגדיר required skill.

3. המודל חייב לבצע `skills_tool:load` לפני P&P.

4. רק אז `pen_paper.create`.

כלומר: **skill קודם, P&P אחר כך**.

---

## 8. מינימום ב־SKILL לצפיות cross-model

מינימום חובה:

1. מתי להפעיל.

2. מתי לא להפעיל.

3. רצף צעדים קשיח.

4. שמות sections מותרים בלבד.

5. תנאי close.

6. fallback לכשל כלי.

7. output schema.

8. “Do not invent sections/templates”.

9. “If template missing, write `backtrack` and continue with generic plan”.

---

# Router / config / חוזה

## 9. SmartRouter היה פעיל? כפילות שלבים אחרי השבתה?

לא נראה פעיל. נמצא ב:

`/a0/usr/plugins/a0_lmm_router/extensions/python/message_loop_start/_20_smart_router.py`

והתיעוד אומר שהוא **disabled/no-op**.

כפילות שלבים כרגע לא מגיעה מ־SmartRouter פעיל, אלא מ־model behavior / repeated prompts / חוסר state guard.

---

## 10. `execution_contract` — מתעלם / מפרש / `execution_log`?

בפועל: **מתעלמים ממנו**.

`rules.yaml` מזכיר:

- workflow session state

- `pen_paper execution_log`

- `SmartRouterExtension._execute_workflow_steps`

אבל `workspace.json` בפועל לא כולל `execution_log`, ו־SmartRouter מושבת.

---

## 11. `COMPLETED` vs `DONE` — במה להשתמש?

כרגע בקוד `WorkflowStepStatus` משתמש ב`DONE`, לא `COMPLETED`.

לכן באפיון החדש צריך לבחור אחד. אני ממליץ:

```json

"status": "pending | running | done | failed | skipped"

```

ולא `COMPLETED`, כדי להתיישר עם הקוד הקיים.

---

## 12. הגדרות `config.html` משפיעות?

על חוויית UI — כן כנראה.

על `pen_paper.py` עצמו — **לא מספיק / לא מחובר כמו שצריך**.

הבעיה: `pen_paper.py` משתמש בברירות מחדל hardcoded:

- `retrieve_context=True`

- `vectorize=True`

בעוד `config.json` אומר false.

---

# Promotion

## 13. `workflow_to_skill` end-to-end — מה נשאר ב־P&P?

ב־P&P צריך להישאר:

- ניסויים

- session logs

- variants

- raw notes

- decisions/backtrack

- test run evidence

ב־[SKILL.md](http://SKILL.md) צריך לעבור רק:

- behavior יציב

- trigger rules

- deterministic steps

- failure handling

- output contract

**כלל:** P&P = prototype/run history. Skill = production behavior.

---

## 14. השתמשת ב`a0_skill_creator`?

לא בשלב הזה. אנחנו עדיין באפיון, ללא שינוי קוד.

המלצה: להשתמש בו רק אחרי שיש:

1. workflow יציב.

2. שני runs מוצלחים.

3. test matrix בסיסי.

4. SKILL draft קנוני.

---

## 15. [SKILL.md](http://SKILL.md) קנוני להעתקה ל־Cursor

```markdown

---

name: pen-and-paper-workflow

version: 1.0

description: Deterministic workflow execution using Pen & Paper as runtime state and Workflow Dashboard as policy controller.

trigger_patterns:

  - "plan"

  - "analyze"

  - "audit"

  - "debug"

  - "research"

  - "תכנן"

  - "נתח"

  - "בדוק"

  - "חקור"

---

# Pen & Paper Workflow Skill

## Purpose

Use Pen & Paper only as a runtime workspace for multi-step work. Do not treat it as the policy engine.

## Activation Rules

Use this skill when the task requires more than 3 steps, multiple tools, planning, debugging, audit, research, or state tracking.

Do not use this skill for simple one-shot answers.

## Required Sequence

1. Identify task type: planning, research, debugging, audit, implementation, validation.

2. Load the required domain skill before creating a Pen & Paper session.

3. Create one Pen & Paper session with a deterministic name.

4. Use only these sections:

   - findings

   - results

   - insights

   - notes

   - decisions

   - backtrack

5. If a workflow template is required, load it before the first update.

6. If the template is missing, record the failure in `backtrack` and continue with a generic template.

7. Update P&P after each major step.

8. Before final response, read the session summary.

9. Close the session unless the task explicitly remains open.

## Failure Handling

- If a tool call fails, write the failure to `backtrack`.

- Do not invent section names.

- Do not invent missing templates.

- If config and code disagree, prefer runtime code behavior and record the contradiction.

## Output Contract

Final response must include:

- What was done

- What evidence was collected

- What remains open

- Recommended next step

## Promotion Rule

A workflow can be promoted to a dedicated [SKILL.md](http://SKILL.md) only after at least two successful runs and one documented test matrix.

```

---

## 16. `plugin_debugger` — ממצאי audit אחרון על `a0_pen_paper`

| אזור | מצב | ממצא |

|---|---|---|

| plugin manifest | עובד | `plugin.yaml` קיים |

| tools | עובד | `pen_paper.py`, `pen_paper_wiki_template.py` קיימים |

| config alignment | שבור | `config.json` false, `default_config.yaml` true, tool hardcoded true |

| config UI wiring | שבור | UI לא מחובר מספיק ל־runtime defaults |

| base workflow hooks | שבור | `research/debugging/validation.md` חסרים |

| execution contract | שבור | מצביע ל־SmartRouter מושבת |

| status enum | שבור | `COMPLETED` מול `DONE` |

| wiki template payload | חלקי | payload כטקסט, לא schema enforced |

| section validation | עובד חלקית | public tool דוחה sections לא חוקיים |

---

# Artifacts

נוצרו artifacts כאן:

`/a0/usr/workdir/pen_paper_phase1_artifacts/`

| Artifact | Path |

|---|---|

| inventory של sessions | `/a0/usr/workdir/pen_paper_phase1_artifacts/00_inventory.txt` |

| workspace מסשן מוצלח | `/a0/usr/workdir/pen_paper_phase1_artifacts/workspace_success.json` |

| workspace active/unclosed | `/a0/usr/workdir/pen_paper_phase1_artifacts/workspace_active_unclosed.json` |

| template registry | `/a0/usr/workdir/pen_paper_phase1_artifacts/template_registry.json` |

| production templates summary | `/a0/usr/workdir/pen_paper_phase1_artifacts/production_templates.txt` |

| config runtime | `/a0/usr/workdir/pen_paper_phase1_artifacts/config.json` |

| default config | `/a0/usr/workdir/pen_paper_phase1_artifacts/default_config.yaml` |

| config UI raw | `/a0/usr/workdir/pen_paper_phase1_artifacts/config_ui.html` |

| config UI fields | `/a0/usr/workdir/pen_paper_phase1_artifacts/config_ui_fields.txt` |

| base workflow hook check | `/a0/usr/workdir/pen_paper_phase1_artifacts/base_workflows_hooks_check.txt` |

| tool calls log snippets | `/a0/usr/workdir/pen_paper_phase1_artifacts/tool_calls_template_run.log` |

| plugin debugger table | `/a0/usr/workdir/pen_paper_phase1_artifacts/plugin_debugger_table.md` |

הערה: לא נמצא artifact נקי בשם `workspace_failed_or_error.json`, לכן שמרתי במקום זה `workspace_active_unclosed.json` כאינדיקציה ל־state drift.  
## Follow-up (completed in repo)

- [x] Updated [`CONTRACT.md`](CONTRACT.md) section 7
- [x] Waves 0–3 implemented — see [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md)

