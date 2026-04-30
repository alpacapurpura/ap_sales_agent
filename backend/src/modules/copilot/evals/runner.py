# ruff: noqa: TRY301, TRY400
r"""Eval runner CLI — D-3 (CONTRACT PR-3).

CLI usage::

    python -m src.modules.copilot.evals.runner \\
        --use=classifier \\
        --threshold=0.95 \\
        [--goldens-dir=path/to/goldens]

Programmatic usage (for tests)::

    from src.modules.copilot.evals.runner import EvalRunner, EvalReport
    report = EvalRunner.run_classifier(threshold=0.95)
    assert report.passed

Exit codes:
  0 — all eval gates passed (aggregate_score >= threshold).
  1 — gate failed (aggregate_score < threshold) OR error during eval.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import structlog

from src.modules.copilot.evals.golden_dataset import (
    load_all_classifier_goldens,
    load_all_summarizer_goldens,
)
from src.modules.copilot.evals.scorers.classifier import ClassifierScorer
from src.modules.copilot.evals.scorers.summarizer import SummarizerScorer

logger = structlog.get_logger()

UseKind = Literal["classifier", "summarizer"]


@dataclass
class EvalReport:
    """Result of one eval run."""

    use: str
    total_goldens: int
    scores: list[float] = field(default_factory=list)
    aggregate_score: float = 0.0
    threshold: float = 0.95
    passed: bool = False
    error: str | None = None

    def as_dict(self) -> dict:  # type: ignore[type-arg]
        """Return dict representation for JSON output."""
        return asdict(self)


class EvalRunner:
    """Orchestrates eval runs against goldens using the appropriate scorer."""

    @staticmethod
    def run_classifier(
        *,
        threshold: float | None = None,
        predicted_tiers: list[str] | None = None,
    ) -> EvalReport:
        """Run classifier eval against all classifier goldens.

        Args:
            threshold: Pass threshold (default: ClassifierScorer.DEFAULT_THRESHOLD).
            predicted_tiers: Inject predicted tiers (length must match goldens).
                When None, uses the expected tier as the prediction (simulates
                a perfect model — useful for testing the runner itself, not the LLM).
        """
        scorer = ClassifierScorer()
        eff_threshold = threshold if threshold is not None else scorer.DEFAULT_THRESHOLD
        report = EvalReport(use="classifier", total_goldens=0, threshold=eff_threshold)

        try:
            goldens = load_all_classifier_goldens()
            report.total_goldens = len(goldens)

            if predicted_tiers is not None and len(predicted_tiers) != len(goldens):
                msg = f"predicted_tiers length ({len(predicted_tiers)}) must match goldens ({len(goldens)})"
                raise ValueError(msg)

            scores: list[float] = []
            for i, golden in enumerate(goldens):
                predicted = predicted_tiers[i] if predicted_tiers else golden.expected_tier
                s = scorer.score(predicted, golden.expected_tier)
                scores.append(s)

            report.scores = scores
            report.aggregate_score = scorer.aggregate(scores)
            report.passed = scorer.passes_threshold(report.aggregate_score)
        except Exception as exc:  # noqa: BLE001
            logger.error("eval_runner_classifier_error", error=str(exc))
            report.error = str(exc)
            report.passed = False

        return report

    @staticmethod
    def run_summarizer(
        *,
        threshold: float | None = None,
        predicted_summaries: list[str] | None = None,
    ) -> EvalReport:
        """Run summarizer eval against all summarizer goldens.

        Args:
            threshold: Pass threshold (default: SummarizerScorer.DEFAULT_THRESHOLD).
            predicted_summaries: Inject predicted summaries for testing.
                When None, uses the reference_summary as the prediction.
        """
        scorer = SummarizerScorer()
        eff_threshold = threshold if threshold is not None else scorer.DEFAULT_THRESHOLD
        report = EvalReport(use="summarizer", total_goldens=0, threshold=eff_threshold)

        try:
            goldens = load_all_summarizer_goldens()
            report.total_goldens = len(goldens)

            if predicted_summaries is not None and len(predicted_summaries) != len(goldens):
                msg = f"predicted_summaries length ({len(predicted_summaries)}) must match goldens ({len(goldens)})"
                raise ValueError(msg)

            scores: list[float] = []
            for i, golden in enumerate(goldens):
                predicted = predicted_summaries[i] if predicted_summaries else golden.reference_summary
                s = scorer.score(predicted, golden.reference_summary)
                scores.append(s)

            report.scores = scores
            report.aggregate_score = scorer.aggregate(scores)
            report.passed = scorer.passes_threshold(report.aggregate_score)
        except Exception as exc:  # noqa: BLE001
            logger.error("eval_runner_summarizer_error", error=str(exc))
            report.error = str(exc)
            report.passed = False

        return report


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run copilot eval gates against golden datasets.",
        prog="python -m src.modules.copilot.evals.runner",
    )
    parser.add_argument(
        "--use",
        choices=["classifier", "summarizer"],
        required=True,
        help="Which eval to run: 'classifier' or 'summarizer'.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Pass threshold (default: per-scorer default — 0.95 classifier, 0.85 summarizer).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write JSON report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=pass, 1=fail)."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.use == "classifier":
        report = EvalRunner.run_classifier(threshold=args.threshold)
    else:
        report = EvalRunner.run_summarizer(threshold=args.threshold)

    # Print JSON report to stdout.
    print(json.dumps(report.as_dict(), indent=2))  # noqa: T201 — CLI output

    if args.output:
        args.output.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")

    if report.error:
        logger.error("eval_runner_failed", use=args.use, error=report.error)
        return 1

    status = "PASS" if report.passed else "FAIL"
    logger.info(
        "eval_runner_complete",
        use=args.use,
        aggregate_score=round(report.aggregate_score, 4),
        threshold=report.threshold,
        status=status,
        total_goldens=report.total_goldens,
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
