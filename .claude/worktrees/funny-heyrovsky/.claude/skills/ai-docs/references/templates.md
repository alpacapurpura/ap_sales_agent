# Documentation Templates

Use these templates as starting points. They encode the research principles structurally — short, position-aware, zero-redundancy.

---

## Template 1: CLAUDE.md (Project Root)

Target: < 80 lines. This is always in context — every wasted line costs 20%+ more inference.

```markdown
# {Project Name}

{One sentence: what it is and who it's for.}

## Stack
{Bulleted list. Only technologies — no explanations of what they do.}

## Commands
{Only non-obvious commands. If it's `npm install` or `pip install -r requirements.txt`, skip it.}
- Dev: `{command}`
- Test: `{command}`
- Lint: `{command}`
- Deploy: `{command}`

## Module Map
{Table: module name → one-phrase purpose. Link to module doc if exists.}

## Rules
{Only rules that CONTRADICT standard practices or that have caused bugs before.
Place the most critical rules LAST — they get highest attention weight.}
```

---

## Template 2: Module Documentation

Target: < 100 lines per module. Covers one bounded context.

```markdown
# Module: {name}

{One sentence: what business problem this module solves.}

## Domain Concepts
{Only non-obvious domain terms. Skip anything a developer would understand from the code.}
- **{Term}**: {Definition only if the term is domain-specific or overloaded}

## Data Flow
{Mermaid diagram or ASCII: entry point → processing → output. Max 10 nodes.}

## Business Rules (Non-Inferable)
{Rules that code structure alone doesn't reveal. Each rule on one line.}
- {Rule 1}
- {Rule 2}

## Edge Cases & Gotchas
{Things that have caused bugs or that deviate from standard patterns.}
- {Gotcha 1}
- {Gotcha 2}

## CRITICAL — Do Not Violate
{Place the absolute hardest constraints here — last position = highest attention.}
- {Constraint 1}
- {Constraint 2}
```

---

## Template 3: Domain/Feature Doc (Detailed Reference)

Target: < 150 lines. Only load when working on this specific feature.

```markdown
# {Feature/Domain Name}

## Purpose
{One paragraph max. Business context only — not technical description.}

## Architecture Decisions
{Only decisions that aren't obvious from the code. Why, not what.}
- **{Decision}**: {Why it was made — what problem it prevents}

## Integration Points
{How this module connects to others. Only non-obvious connections.}
| Depends On | How | Why |
|-----------|-----|-----|
| {module} | {mechanism} | {business reason} |

## API Contracts (Non-Standard)
{Only endpoints or contracts that deviate from the project's standard patterns.}

## Known Technical Debt
{Active issues that affect development decisions.}

## INVARIANTS — These Must Always Hold
{Last position. The rules that, if broken, cause data corruption or security issues.}
- {Invariant 1}
- {Invariant 2}
```

---

## Anti-Patterns to Avoid

These patterns violate the research and MUST be removed when found:

| Anti-Pattern | Why It's Harmful | Fix |
|-------------|-----------------|-----|
| File inventories (`src/foo.py — does X`) | Code already shows this; wastes tokens | Delete |
| Restating type signatures in prose | Redundant with code; Paper 2 | Delete |
| Auto-generated docs (tree dumps, AST summaries) | Paper 1: reduces success 3% | Delete |
| Inline code examples for standard patterns | Agent knows FastAPI/React patterns | Delete |
| Multi-page architecture essays | Paper 3: middle content ignored | Compress to < 150 lines |
| Explaining what enums/constants mean | Read the enum definition | Delete |
| "This file contains..." headers | File name already says this | Delete |
