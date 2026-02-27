---
name: front-arch-auditor
description: Expert auditor for frontend architecture, ensuring adherence to GoF patterns, Clean Code, and atomic design principles. Use when reviewing code, refactoring, or ensuring scalability and maintainability in the frontend codebase.
---

# Frontend Architecture Auditor

## Overview
This skill is an expert in frontend architecture, specializing in auditing and verifying best practices (GoF and Clean Code) with a focus on atomic development. It ensures code maintainability, extensibility, and scalability by detecting duplication and enforcing structural rules.

## Core Responsibilities

1.  **Code Audit & Verification**:
    -   Verify every file, class, and dependency for duplication.
    -   Ensure adherence to Clean Code principles (e.g., meaningful names, small functions, single responsibility).
    -   **Enforce Code Quality**: Verify adherence to [code-quality.md](references/code-quality.md), including `cn()` usage, Tailwind-first styling, and proper prop memoization.
    -   Identify and recommend GoF design patterns where appropriate.

2.  **Structure Enforcement**:
    -   Ensure the codebase follows the defined structure in [structure.md](references/structure.md).
    -   **Strictly Prohibit Nested Features**: Flag any structure like `features/parent/features/child`.
    -   **Enforce Semantic Grouping**: Verify complex features use semantic folders (e.g., `sections/`) instead of generic `components/` when appropriate for domain clarity.
    -   **Verify Colocation**: Ensure sub-domain components (forms, previews) are grouped together in `components/<sub-domain>`.
    -   Verify that UI logic resides in `features/[name]/hooks`.
    -   Confirm that pages in `app/` only import from `features/`.
    -   Check that `components/ui` internals are not modified.

3.  **Technology Compliance**:
    -   Ensure usage of approved technologies listed in [tech-stack.md](references/tech-stack.md).
    -   Flag usage of deprecated or unapproved libraries.

4.  **Atomic Development**:
    -   Promote atomic design principles.
    -   Ensure components are small, reusable, and have a single responsibility.

## Auditing Process

When auditing a file or a set of files:

1.  **Check for Duplication**:
    -   Scan the file for repeated logic or code blocks.
    -   Cross-reference with existing utilities in `src/lib` or `src/hooks`.

2.  **Verify Structure**:
    -   Confirm the file is in the correct directory based on its function (e.g., feature-specific code in `src/features`, generic UI in `src/components`).
    -   Check import paths to ensure they follow the architectural rules.
    -   **Flag Anti-Patterns**: Specifically look for deeply nested `features` directories inside other features.

3.  **Review Code Quality**:
    -   Analyze function and variable names for clarity.
    -   Check for long functions or classes that violate the Single Responsibility Principle.
    -   Look for opportunities to extract logic into custom hooks or utility functions.
    -   **Verify Styling**: Ensure `cn()` is used for conditional classes and that `className` props are handled correctly (merged last).
    -   **Check Performance**: Look for expensive computations or complex objects passed as props without `useMemo`.

4.  **Assess Scalability**:
    -   Evaluate if the code is extensible without modification (Open/Closed Principle).
    -   Check for tight coupling between components that should be loosely coupled.

## References

-   **Structure**: See [structure.md](references/structure.md) for detailed project structure rules.
-   **Tech Stack**: See [tech-stack.md](references/tech-stack.md) for the approved technology stack.
-   **Code Quality**: See [code-quality.md](references/code-quality.md) for specific coding standards (Styling, React patterns).
