# UAT — Cross-Model Determinism

**What this tests:** the plugin's founding claim — that a small/local model and a
flagship model, given the same task, produce the **same shape** of Pen & Paper
session. Wording and timing will differ; structure must not.

**Why it matters now:** the deterministic sequence used to live only in
`skills/pen-and-paper-workflow/SKILL.md`, which loads only when the model notices
a trigger. It now also lives in `prompts/agent.system.tool.pen_paper.md`, which is
injected into **every** system prompt regardless of model. This UAT is what tells
you whether that change actually closed the gap.

**Status:** not yet executed. Record results in §6.

---

## 1. Prerequisites

- A running Agent Zero with `a0_pen_paper` installed at `/a0/usr/plugins/a0_pen_paper/`.
- Two configured models: one small/local (e.g. a 7–8B local model, or Haiku), one
  flagship (e.g. Opus/Sonnet). Referred to below as **SMALL** and **FLAGSHIP**.
- `python scripts/verify_pen_paper_setup.py` passing (12/12) before you start.

Record the exact model IDs in §6 — "a small model" is not a result.

---

## 2. The task prompt (use verbatim, both runs)

Give each model the **same** message, in a fresh chat, with no other context:

```
Investigate how session state is persisted in this plugin and write up what you
find. Track your steps as you go.
```

Deliberate properties of this prompt:

- It needs ≥3 steps → the plugin's own activation rule says P&P is mandatory.
- It says "write up what you find" → should produce `findings`.
- It says "track your steps" → should produce `execution_log`.
- It does **not** name the tool, the sections, or the sequence. Naming them would
  test compliance-when-told, not determinism. The whole question is whether the
  model reaches the right behavior from the guidance it is given.

Do not coach, correct, or re-prompt mid-run. If the model goes off-script, that
**is** the result.

---

## 3. Collect the artifacts

After each run, copy the workspace out of the runtime:

```bash
# on the A0 host
cp /a0/usr/pen_and_paper/sessions/active/<name>/workspace.json  ./run_flagship.json
# if the model closed the session it will be under sessions/archive/ instead
cp /a0/usr/pen_and_paper/sessions/archive/<name>/workspace.json ./run_flagship.json
```

Repeat for the small model as `run_small.json`.

If a run produced **no workspace at all**, that is the strongest possible failure
— record it in §6 and skip the comparison for that pair.

---

## 4. Compare (automated)

```bash
python scripts/compare_cross_model_runs.py run_flagship.json run_small.json
```

Exit codes: `0` structurally equivalent · `1` divergence · `2` bad input.

The comparator ignores what legitimately varies — timestamps, free text, agent
name, chat id, workspace name — and reports only structural divergence:

| Check | Fails when |
|---|---|
| top-level keys | one run has keys the other lacks |
| section vocabulary | a run drops a `VALID_SECTIONS` entry or **invents** a key |
| metadata keys / values | key sets differ, or a non-volatile value differs |
| sections used | one run populated a section the other left empty |
| entry shape | entries in the same section have different key sets |
| execution_log status | a status outside `pending/running/done/failed/skipped`, or prose instead of JSON |
| execution_log steps | the `step_id` sequence differs |
| required section | `findings` or `execution_log` left empty (configurable) |

Tune with `--require-sections findings,execution_log` (default) or
`--require-sections ''` to disable that last check.

---

## 5. Reading the result

**PASS** — the externalized guidance is sufficient. The prompt-level sequence is
carrying the small model. Note it in §6 and in `IMPLEMENTATION_STATUS.md`.

**FAIL** — read *which* check fired; the fix differs by failure mode:

| Divergence | Likely cause | Where to fix |
|---|---|---|
| No workspace created at all | model never reached for the tool | tool description in `prompts/agent.system.tool.pen_paper.md`; consider a harness-level nudge |
| Invented section name | section list not salient enough | `prompts/…pen_paper.md` — the `section` bullet |
| `COMPLETED` or other bad status | status vocabulary not reaching the model | same prompt, "Hard rules" |
| Prose in `execution_log` | JSON shape not explicit enough | same prompt, "Required sequence" step 3 |
| `findings` empty | model treated P&P as a log, not a workspace | skill + prompt guidance on when to write |
| step_id sequence differs | genuinely different decomposition | **may be acceptable** — see below |

**Important:** a differing `step_id` sequence is not automatically a bug. Two
models may legitimately decompose the same task differently. What must not differ
is the *contract*: valid statuses, JSON shape, no invented sections. Judge that
row on its merits rather than treating exit 1 as a verdict.

**The fix is never** to move methodology back into `tools/pen_paper.py`. That is
the regression the `AGENTS.md` tree explicitly forbids (see `tools/AGENTS.md`).
Strengthen the always-injected prompt, or enforce in code via
`helpers/workflow_executor.py`.

---

## 6. Results

Fill in on execution. Keep every run — a later regression is only visible against
a recorded baseline.

| Date | FLAGSHIP model | SMALL model | Exit | Divergences | Action taken |
|---|---|---|---|---|---|
| _(pending)_ | | | | | |

Store the raw artifacts under `docs/pen-paper-workflows/uat-runs/<date>/`.

---

## 7. Re-run triggers

Re-run this UAT whenever:

- `prompts/agent.system.tool.pen_paper.md` changes (it is the determinism channel).
- `VALID_SECTIONS` or the execution contract changes.
- A skill's `trigger_patterns` or `priority` changes.
- A new model tier is added to the deployment.
