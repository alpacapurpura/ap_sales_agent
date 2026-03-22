# Research Foundations for AI-Optimized Documentation

This file summarizes the three peer-reviewed studies that underpin every decision in this skill. Read this when you need to justify a recommendation or when auditing existing docs.

---

## 1. The Context File Paradox

**Paper:** "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"
Gloaguen et al., ETH Zurich — February 2026
https://arxiv.org/abs/2602.11988

### Findings
- Repository-level context files (AGENTS.md, CLAUDE.md, CONTRIBUTING.md with agent instructions) **reduce task success rate by ~3%** and **increase inference cost by 20%+**.
- Both LLM-generated and human-written context files showed this effect.
- Agents follow context file instructions faithfully — the problem is that following those instructions (broader exploration, extra testing steps, more file traversal) leads to worse outcomes.
- Agents **over-explore**: they doubt what they read in source files and try to reconcile code with documentation, wasting tokens.

### Operational Rule
Context files must contain ONLY what cannot be inferred from the code itself:
- Non-obvious build/deploy commands
- Business rules that contradict common patterns
- Custom tooling or conventions that break standard expectations
- **Nothing else.** If the code's types, signatures, and structure already convey it, the doc is noise.

---

## 2. Documentation Compression

**Paper:** "Less is More: DocString Compression in Code Generation"
Yang et al. — October 2024
https://arxiv.org/abs/2410.22793

### Findings
- Standard docstrings contain 25-40% redundant content.
- Removing this redundancy (via ShortenDoc method) **maintains or improves** code generation quality across models from 1B params to GPT-4o.
- Generic prompt compression methods plateau at ~10% reduction before degrading quality.
- The key insight: if the function name is `calculate_monthly_discount`, explaining "this function calculates the monthly discount" wastes tokens that could carry edge-case info.

### Operational Rule
Every sentence in documentation must pass the **Non-Redundancy Test**:
> "Does this sentence tell the agent something it cannot already infer from the function name, parameter types, return type, or surrounding code structure?"

If no → delete it.

Focus the freed-up tokens on:
- Edge cases and boundary conditions
- Error handling behavior that isn't obvious
- Business logic that deviates from standard patterns
- Integration gotchas between modules

---

## 3. The Attention U-Curve

**Paper:** "Lost in the Middle: How Language Models Use Long Contexts"
Liu et al., Stanford & UC Berkeley — 2024
Published in Transactions of the Association for Computational Linguistics (MIT Press)
https://arxiv.org/abs/2307.03172

### Findings
- LLMs exhibit a **U-shaped attention pattern**: they recall information at the **beginning** and **end** of context windows with high fidelity, but **catastrophically ignore** information buried in the middle.
- This holds true even for models explicitly designed for long contexts.
- In multi-document QA, accuracy for middle-positioned documents can drop by **20+ percentage points** compared to first/last position.
- The effect intensifies as context length grows.

### Operational Rules

**For document structure:**
- Place the most critical constraints (data safety, tenant isolation, architectural invariants) at the **end** of the document — the recency-bias zone.
- Use the **beginning** for identity and scope (what module, what domain).
- The middle is for reference material the agent will look up when needed but doesn't need to memorize.

**For project architecture:**
- Never dump the entire repository context. Surface only the 2-3 files relevant to the current task.
- Modular docs (one per bounded context) naturally prevent middle-burial by keeping each doc short.

---

## Combined Framework: The Documentation Triangle

```
                    ATTENTION BUDGET
                         /\
                        /  \
                       /    \
                      / KEEP \
                     / DOCS   \
                    / UNDER    \
                   / 150 LINES  \
                  /______________\
                 /                \
    MINIMAL CONTEXT    ZERO REDUNDANCY
    (Paper 1)          (Paper 2)
```

These three principles reinforce each other:
1. **Minimal context** (Paper 1) → fewer tokens → less middle-burial risk (Paper 3)
2. **Zero redundancy** (Paper 2) → higher signal density → every token earns its position
3. **Position-aware structure** (Paper 3) → critical rules survive even if the agent's attention wanders
