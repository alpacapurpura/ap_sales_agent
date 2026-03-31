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

## The Three Laws

Before writing or auditing any documentation, internalize these research-backed principles:

**Law 1 — Minimal Context (ETH Zurich, 2026):** Extensive context reduces AI success 3%, increases cost 20%+. Write only what code can't convey.

**Law 2 — Zero Redundancy (Yang et al., 2024):** 25-40% of docs are redundant; removing them maintains or improves quality. Delete any sentence the agent can infer from function names, types, or code structure.

**Law 3 — Position-Aware Structure (Stanford/Berkeley, 2024):** LLMs have U-shaped attention — strong recall at start and end, catastrophic loss in the middle. Place critical constraints at the END. Keep docs short enough that there is no "middle."

For the full research details, read `references/research-foundations.md`.

---

## Anti-Patterns — Reject These on Sight

| Pattern | Example | Why It's Harmful |
|---------|---------|-----------------|
| File inventory | `src/models/user.py — User model` | `ls` shows this |
| Type narration | "Takes a UUID and returns Optional[Lead]" | The signature says this |
| Framework tutorials | "FastAPI uses Depends() for injection" | Agent already knows FastAPI |
| Auto-generated trees | Full directory tree dumps | Law 1: −3% success rate |
| Architecture novels | 500-line design documents | Law 3: middle is ignored |
| Obvious comments | "# Initialize the database" above `db = init_db()` | Law 2: pure redundancy |
| Enum explanations | "COLD means the lead is cold" | Redundant by definition |

---

## Modes of Operation

Determine which mode the user needs:

### Mode 1: Generate New Documentation

1. **Read the actual code first.** List the module directory, read key files (models, services, routers). Understand the domain from source code, not existing docs.

2. **Identify what's non-inferable:**
   - Build/deploy commands that aren't standard
   - Business rules that contradict common patterns
   - Edge cases that have caused or could cause bugs
   - Integration points between modules that aren't obvious from imports
   - Invariants that, if broken, cause data corruption or security issues

3. **Apply the templates.** Read `references/templates.md` and use the appropriate template:
   - **Project root (CLAUDE.md):** < 80 lines. Stack, commands, module map, critical rules.
   - **Module doc:** < 100 lines. Domain concepts, data flow, business rules, gotchas.
   - **Feature/domain doc:** < 150 lines. Architecture decisions (why, not what), integration points, invariants.

4. **Structure for attention:**
   - **First lines:** Identity and scope
   - **Middle:** Reference material (data flows, integration points)
   - **Last section:** CRITICAL constraints, invariants, "do not violate" rules

5. **Self-audit before delivering.** Delete every line matching any Anti-Patterns entry above.

### Mode 2: Audit Existing Documentation

1. **Read the documentation file(s).**

2. **Score each section** against the three laws:
   - **Redundancy score:** What percentage of sentences restate what code already shows?
   - **Inference score:** What percentage could be derived from reading the source?
   - **Position score:** Are critical constraints at the end? Is the doc short enough to avoid middle-burial?

3. **Produce an audit report:**

```
## Audit: {filename}

Lines: {count} (target: < {80|100|150})
Redundancy: {X}% of content is inferable from code
Position: {Critical rules at end? Y/N}

### Lines to Remove
- L{n}: "{quoted text}" — Reason: {restates types | explains standard pattern | file inventory}

### Lines to Add (Missing Non-Inferables)
- {Business rule or edge case discovered in code but not documented}

### Structural Issues
- {Position problems, missing critical-rules-last section, too long, etc.}
```

### Mode 3: Compress Existing Documentation

1. **Read the document and the code it describes.**

2. **Apply the Anti-Patterns filter** to each line. Also ask:
   - Does this contain business logic, edge cases, or non-obvious constraints? → Keep
   - Does this document a bug-prone integration point? → Keep
   - Does it match any Anti-Patterns entry? → Delete

3. **Restructure the survivor content:**
   - Move critical constraints to the end
   - Merge redundant sections
   - Convert prose paragraphs into single-line rules

4. **Report:** `"Compressed from {X} to {Y} lines ({Z}% reduction)"`

### Mode 4: Generate Module-Level Documentation Map

1. **Scan the module structure:** `ls backend/src/modules/` and `ls frontend/src/features/`

2. **For each module,** read 2-3 key files (main model, main service, main router) to understand its purpose.

3. **Create an INDEX.md** with one line per module — just name and one-phrase purpose.

4. **Identify which modules need dedicated docs** based on complexity:
   - Simple CRUD modules: index entry is sufficient
   - Modules with business rules, complex state machines, or cross-module integrations: need a dedicated doc
   - Report the list to the user for prioritization

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
