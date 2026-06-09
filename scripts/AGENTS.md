# DOX contract - a0_pen_paper-repo/scripts

## Purpose

Operator and verification scripts.

## Ownership

- Scripts may inspect plugin layout and runtime assumptions.
- They must not mutate live user sessions unless explicitly documented.

## Local Contracts

- `verify_pen_paper_setup.py` should stay aligned with current shipped layout.

## Work Guidance

- Keep script output actionable for Agent Zero operators.

## Verification

- Run `python scripts/verify_pen_paper_setup.py` after layout/script changes.

## Child DOX Index

No child AGENTS.md files yet.
