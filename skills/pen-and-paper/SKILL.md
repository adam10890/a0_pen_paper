---
name: pen-and-paper
description: Structured thinking workflow using virtual pen & paper sessions. Helps agent think step-by-step with persistent, searchable sessions. Use for complex reasoning, planning, or problem decomposition.
version: 1.0.0
author: Adam
tags: [thinking, methodology, workflow, planning, reasoning, sessions]
trigger_patterns: ["pen and paper", "pen paper", "think step by step", "structured thinking", "session", "×¢×˜ ×•× ×™×™×¨", "×—×©×™×‘×” ×ž×•×‘× ×™×ª"]
priority: 2
---

# Pen & Paper (Pure Skill)

The Pen & Paper system is a fundamental methodology for structured thinking. Rather than attempting to process complex multi-step reasoning solely in the immediate context, this skill instructs the agent to persist, organize, and track its thoughts across workspaces.

## Pure Skill Architecture

This is a **Pure Skill**, meaning it acts as a methodology and behavioral guide. This plugin provides the `pen_paper` tool, optional vector helper, prompts, templates, and references. This `SKILL.md` teaches the agent when and how to use the installed plugin.

## When to use Pen & Paper

- **Mandatory**: Tasks with $\ge3$ tools, taking >90s, or involving multi-step planning.
- **Optional**: 2 tool operations.
- **Skip**: Simple direct queries requiring $<2$ tools.
Also use it when you need to make critical decisions, process complex logic, or structure a long-term plan.

## How it works

1. **Open a workspace**: Use the `pen_paper` tool with `action: create`.
2. **Log findings**: Record your intermediate insights logically.
3. **Decisions**: Explicitly document *why* you chose a specific path.
4. **Backtrack**: Keep a list of things to return to.
5. **Close & Vectorize**: Complete the session with `action: close`, allowing the system to summarize and vectorize your thoughts for future retrieval.

### References

- [Philosophy & Core Principles](references/philosophy.md)
- [Session Management](references/session-management.md)
- [Vectorizer Details](references/vectorizer.md)
- [Plugin Packaging](references/plugin-packaging.md)

