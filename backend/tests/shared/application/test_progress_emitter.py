"""Tests for shared.application.progress_emitter.

These tests guard the backwards-compatibility contract: extraction
orchestrators MUST be able to call ``emit_progress`` with a legacy
``callback(pct, stage)`` callable OR a rich
``callback(pct, stage, *, new_fields, section_completed)`` callable
without caring which is which.
"""

from __future__ import annotations

from pydantic import BaseModel

from luana_core_platform.application.progress_emitter import (
    emit_progress,
    fields_from_model,
)


class TestEmitProgressBackwardsCompat:
    def test_noop_when_callback_is_none(self) -> None:
        # Must not raise
        emit_progress(None, 50, "stage")
        emit_progress(None, 0, "")

    def test_legacy_two_arg_callback(self) -> None:
        """2-arg callbacks must keep working verbatim — kwargs ignored."""
        calls: list[tuple] = []

        def legacy(pct: int, stage: str) -> None:
            calls.append((pct, stage))

        emit_progress(legacy, 42, "stage text", new_fields=["x.y"], section_completed="x")
        assert calls == [(42, "stage text")]

    def test_rich_callback_receives_kwargs(self) -> None:
        """Callbacks declaring new_fields/section_completed receive them."""
        calls: list[dict] = []

        def rich(
            pct: int,
            stage: str,
            *,
            new_fields: list[str] | None = None,
            section_completed: str | None = None,
        ) -> None:
            calls.append(
                {
                    "pct": pct,
                    "stage": stage,
                    "new_fields": new_fields,
                    "section_completed": section_completed,
                },
            )

        emit_progress(
            rich,
            60,
            "stage",
            new_fields=["identity.brand_name"],
            section_completed="identity",
        )
        assert calls == [
            {
                "pct": 60,
                "stage": "stage",
                "new_fields": ["identity.brand_name"],
                "section_completed": "identity",
            },
        ]

    def test_kwargs_only_callback_receives_kwargs(self) -> None:
        """Callbacks with **kwargs catch-all must also receive the rich payload."""
        calls: list[dict] = []

        def catch_all(pct: int, stage: str, **kwargs: object) -> None:
            calls.append({"pct": pct, "stage": stage, **kwargs})

        emit_progress(
            catch_all,
            75,
            "s",
            new_fields=["strategy.mission"],
            section_completed="strategy",
        )
        assert calls == [
            {
                "pct": 75,
                "stage": "s",
                "new_fields": ["strategy.mission"],
                "section_completed": "strategy",
            },
        ]

    def test_callback_exception_is_swallowed(self) -> None:
        """Extraction must not abort on a buggy callback."""

        def buggy(pct: int, stage: str) -> None:
            msg = "observability bug"
            raise RuntimeError(msg)

        # Must not raise
        emit_progress(buggy, 10, "x")


class TestFieldsFromModel:
    def test_none_returns_empty(self) -> None:
        assert fields_from_model("identity", None) == []

    def test_pydantic_model_dump(self) -> None:
        class Identity(BaseModel):
            brand_name: str = ""
            tagline: str = ""

        model = Identity(brand_name="Visionarias", tagline="")
        assert fields_from_model("identity", model) == ["identity.brand_name"]

    def test_dict_input(self) -> None:
        assert fields_from_model("strategy", {"mission": "X", "vision": ""}) == [
            "strategy.mission",
        ]

    def test_list_input_single_path(self) -> None:
        # A list aggregate (e.g. testimonials) collapses to one path
        assert fields_from_model("testimonials", [{"author": "Ana"}]) == ["testimonials"]

    def test_empty_list_returns_nothing(self) -> None:
        assert fields_from_model("testimonials", []) == []

    def test_unsupported_type_returns_empty(self) -> None:
        assert fields_from_model("identity", 42) == []
