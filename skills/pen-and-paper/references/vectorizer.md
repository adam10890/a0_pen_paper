# Vectorizer — what `vectorize=true` actually saves

This page tells you what happens when you close a Pen & Paper session with
`vectorize=true`, so you can decide whether to set the flag.

## Default

`vectorize` defaults to whatever the plugin config says (`features.vectorize_on_close`).
You can override per-call:

```json
{"tool_name": "pen_paper", "tool_args": {"action": "close", "name": "...", "vectorize": true}}
```

## What gets vectorized

When `vectorize=true` and the optional `pen_paper_vectorizer` helper is installed,
only these three sections of the workspace are chunked into the vector DB:

- `decisions`
- `insights`
- `findings`

`notes`, `results`, `backtrack`, and `execution_log` are **not** vectorized.
That keeps the index focused on long-term-useful reasoning instead of noisy
intermediate state.

## When to set `vectorize=true`

Set it when the session produced *recallable* knowledge — decisions you might
revisit, insights worth surfacing in future tasks, findings that change how the
codebase or domain is understood.

Skip it (`vectorize=false`) for throwaway scratch sessions, debug fish-finds that
got resolved in the same session, or anything whose value ends with this task.
For a one-shot scratchpad use `ephemeral=true` together with `vectorize=false` to
delete the session entirely on close.

## What happens with no vectorizer installed

`pen_paper_vectorizer` is an optional sibling helper. If it is not installed, the
close still succeeds and the response carries a single line:
`**Vectorization:** Failed - ...` (followed by the import error). The session is
still archived normally; no data is lost.

## How it interacts with `ephemeral=true`

- `vectorize=true` + `ephemeral=true` — session is vectorized and the source
  file is deleted in the same step. Use when you want the recallable nuggets but
  not the raw scratch.
- `vectorize=false` + `ephemeral=true` — session is deleted with no vector copy.
  Pure throwaway.
- `vectorize=true` + `ephemeral=false` — session is vectorized and the source
  file is archived under `sessions/archive/`. Default-ish persistent path.
- `vectorize=false` + `ephemeral=false` — session is archived but not vectorized.

## Promoting to long-term memory (`llm_wiki`)

The vectorizer is short-to-medium-term recall (still inside the P&P system). For
anything that should survive across many sessions as canonical knowledge, promote
the synthesised conclusion to `llm_wiki` via `wiki_ingest` instead — see the
bridge section in [`_start_here.md`](../../../data/templates/_start_here.md).
Never duplicate the same fact in both stores.
