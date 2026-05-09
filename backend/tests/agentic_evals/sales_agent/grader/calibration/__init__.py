"""Calibration package — Chris seed labels + auto-baseline (Story E T-9).

Calibration MD files (one per rubric in scope, D5 cement):
  - voice_fidelity_calibration.md
  - qualification_accuracy_calibration.md
  - no_overpromise_calibration.md
  - no_hallucination_calibration.md

Each file carries:
  1. Frontmatter (rubric_id, version 1, last_modified, owner_story)
  2. Calibration methodology
  3. Chris seed labels skeleton (Chris fills 10 turn-segments x 4 rubrics
     post-merge per D11 cement)
  4. Auto-calibration baseline section (frozen v1 commit)
  5. Re-calibration triggers (D11 cement)

# voseo-allowed: docstring quotes calibration MD names
"""

__all__: list[str] = []
