---
name: ai-docs
description: >
  Generate, audit, and compress AI-optimized documentation for codebases. This skill applies
  research-backed principles from three peer-reviewed papers to create documentation that
  maximizes AI agent performance instead of degrading it. Use this skill whenever the user asks
  to "write docs", "create a CLAUDE.md", "document a module", "audit documentation", "compress
  docs", "optimize docs for AI", "write module docs", "create domain documentation",
  "review doc quality", or mentions documentation bloat, token waste, or AI context efficiency.
  Also trigger when the user references "ai-docs principles", "telegram style docs", or
  wants to apply the "Lost in the Middle", "Less is More", or "AGENTS.md" research findings.
---

# AI-Optimized Documentation Generator

You write documentation that makes AI agents smarter, not dumber.

Three peer-reviewed studies prove that most project documentation **actively harms** AI performance. This skill applies their findings to produce docs that are short, dense, and structurally optimized for how LLMs actually process context.

## The Three Laws

Before writing or auditing any documentation, internalize these research-backed principles:

**Law 1 — Minimal Context (ETH Zurich, 2026)**
Extensive context files reduce AI success by 3% and increase costs 20%+. Write only what cannot be inferred from the code. If the code's types, signatures, and structure already convey it, the doc is noise.

**Law 2 — Zero Redundancy (Yang et al., 2024)**
25-40% of documentation is redundant. Removing it maintains or improves code quality. Every sentence must pass: *"Does this tell the agent something it cannot infer from function names, types, and code structure?"* If no, delete it.

**Law 3 — Position-Aware Structure (Stanford/Berkeley, 2024)**
LLMs exhibit U-shaped attention: strong recall at start and end, catastrophic loss in the middle. Place critical constraints at the END of documents. Keep docs short enough that there is no "middle."

For the full research details, read `references/research-foundations.md`.

---

## Modes of Operation

This skill operates in four modes. Determine which one the user needs:

### Mode 1: Generate New Documentation

When the user asks to create docs for a module, feature, or the project root:

1. **Read the actual code first.** List the module directory, read key files (models, services, routers). Understand the domain from the source code, not from existing docs.

2. **Identify what's non-inferable.** As you read, note only:
   - Build/deploy commands that aren't standard
   - Business rules that contradict common patterns
   - Edge cases that have caused or could cause bugs
   - Integration points between modules that aren't obvious from imports
   - Invariants that, if broken, cause data corruption or security issues

3. **Apply the templates.** Read `references/templates.md` and use the appropriate template:
   - **Project root (CLAUDE.md):** < 80 lines. Stack, commands, module map, critical rules.
   - **Module doc:** < 100 lines. Domain concepts, data flow, business rules, gotchas.
   - **Feature/domain doc:** < 150 lines. Architecture decisions (why, not what), integration points, invariants.

4. **Structure for attention.** In every document:
   - **First lines:** Identity and scope (what module, what domain)
   - **Middle:** Reference material (data flows, integration points)
   - **Last section:** CRITICAL constraints, invariants, "do not violate" rules

5. **Self-audit before delivering.** Re-read your draft and delete every line that:
   - Restates what the code already shows via types/signatures
   - Explains what a standard framework feature does
   - Lists files that `ls` would show
   - Describes enum values that the enum definition already contains

### Mode 2: Audit Existing Documentation

When the user asks to audit, review, or check documentation quality:

1. **Read the documentation file(s).**

2. **Score each section** against the three laws:
   - **Redundancy score:** What percentage of sentences restate what code already shows?
   - **Inference score:** What percentage of content could be derived from reading the source?
   - **Position score:** Are critical constraints at the end? Is the doc short enough to avoid middle-burial?

3. **Produce an audit report** in this format:

```
## Audit: {filename}

Lines: {count} (target: < {80|100|150})
Redundancy: {X}% of content is inferable from code
Position: {Critical rules at end? Y/N}

### Lines to Remove
- L{n}: "{quoted text}" — Reason: {restates types | explains standard pattern | file inventory}
- L{n}: "{quoted text}" — Reason: {…}

### Lines to Add (Missing Non-Inferables)
- {Business rule or edge case discovered in code but not documented}

### Structural Issues
- {Position problems, missing critical-rules-last section, too long, etc.}
```

### Mode 3: Compress Existing Documentation

When the user asks to compress, shorten, or optimize existing docs:

1. **Read the document and the code it describes.**

2. **Apply the ShortenDoc filter:** For each line, ask:
   - Does this restate the function/class name? → Delete
   - Does this explain a standard framework pattern? → Delete
   - Does this list files or directory structure? → Delete
   - Does this describe what an enum/constant means when the name is self-explanatory? → Delete
   - Does this contain business logic, edge cases, or non-obvious constraints? → Keep
   - Does this document a bug-prone integration point? → Keep

3. **Restructure the survivor content:**
   - Move critical constraints to the end
   - Merge redundant sections
   - Convert prose paragraphs into single-line rules

4. **Report the compression ratio:** `"Compressed from {X} to {Y} lines ({Z}% reduction)"`

### Mode 4: Generate Module-Level Documentation Map

When the user asks to document the entire project or create a documentation index:

1. **Scan the module structure:** `ls backend/src/modules/` and `ls frontend/src/features/`

2. **For each module,** read 2-3 key files (main model, main service, main router) to understand its purpose.

3. **Create an INDEX.md** with one line per module — just name and one-phrase purpose.

4. **Identify which modules need dedicated docs** based on complexity:
   - Simple CRUD modules: index entry is sufficient, no dedicated doc needed
   - Modules with business rules, complex state machines, or cross-module integrations: need a dedicated doc
   - Report the list to the user for prioritization

---

## Anti-Patterns — Reject These on Sight

When generating or auditing docs, actively reject these patterns:

| Pattern | Example | Why It's Harmful |
|---------|---------|-----------------|
| File inventory | `src/models/user.py — User model` | `ls` shows this; wastes tokens |
| Type narration | "Takes a UUID and returns Optional[Lead]" | The signature says this |
| Framework tutorials | "FastAPI uses Depends() for injection" | The agent knows FastAPI |
| Auto-generated trees | Full directory tree dumps | Paper 1: -3% success rate |
| Architecture novels | 500-line design documents | Paper 3: middle is ignored |
| Obvious comments | "# Initialize the database" above `db = init_db()` | Paper 2: pure redundancy |
| Enum explanations | "COLD means the lead is cold" | The enum name is the doc |

---

## Quality Checklist

Before delivering any documentation, verify:

- [ ] Total lines under target (80 for CLAUDE.md, 100 for module, 150 for feature)
- [ ] Every sentence passes the non-redundancy test
- [ ] No file inventories or directory trees
- [ ] No type signature narration
- [ ] No framework tutorial content
- [ ] Critical constraints are in the LAST section
- [ ] Identity/scope is in the FIRST lines
- [ ] Business rules focus on what DEVIATES from standard patterns
- [ ] Edge cases reference actual bugs or realistic failure modes

## The Golden Rule

> Documentation for AI agents should read like a telegram: every word costs money, so every word must earn its place. The code is the source of truth. Your job is to document only what the code cannot say about itself.
