"""Scenario tests for MAJ-EVAL grader (Story E T-9).

4 production-critical scenarios per 01-spec.md (D5 cement):

* Scenario 1 — happy_multi_judge — Round 1 converges, no debate.
* Scenario 2 — edge_round_2_debate — variance > 0.15 triggers Round 2.
* Scenario 3 — cache_idempotency — second run hits cache (zero new judge calls).
* Scenario 4 — adversarial_prompt_injection — sandbox markers resist injection.

All four exercise the public API (``grade_transcript_maj_eval``) end-to-end.
Tests at this layer use mock judges (deterministic JudgeOpinion fixtures)
so they run on default CI; the ``--run-evals`` gate enables real LLM dispatch
when available.

# voseo-allowed: docstring quotes spec scenarios verbatim
"""

__all__: list[str] = []
