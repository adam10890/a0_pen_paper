# DOX contract - a0_pen_paper/scripts

## Purpose

Operator and verification scripts.

## Ownership

- Scripts may inspect plugin layout and runtime assumptions.
- They must not mutate live user sessions unless explicitly documented.

## Local Contracts

- `verify_pen_paper_setup.py` should stay aligned with current shipped layout.
- `compare_cross_model_runs.py` must stay runnable **standalone** — outside an
  Agent Zero checkout, with no plugin imports. Its `VALID_SECTIONS` is therefore a
  deliberate literal copy; update it when `tools/pen_paper.py` changes.

## Work Guidance

- Keep script output actionable for Agent Zero operators.
- A verification check that cannot fail is worse than no check. When adding one to
  `verify_pen_paper_setup.py`, negative-test it: break the thing it guards, confirm
  it reports FAIL, then restore. Scope string searches to the specific region that
  is authoritative — an incidental mention elsewhere in the file will otherwise
  mask a real omission.

## Verification

- Run `python scripts/verify_pen_paper_setup.py` after layout/script changes.
- `compare_cross_model_runs.py` exit codes: `0` equivalent, `1` divergence,
  `2` bad input. See [`docs/pen-paper-workflows/UAT_CROSS_MODEL.md`](../docs/pen-paper-workflows/UAT_CROSS_MODEL.md).

## Child DOX Index

No child AGENTS.md files yet.
