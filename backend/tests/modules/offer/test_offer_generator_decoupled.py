"""Tests for offer_generator decoupling from copilot."""

import ast
import inspect

from luana_core_offer_studio.application.offer_generator import OfferGeneratorService


def test_no_copilot_application_import():
    source = inspect.getsource(OfferGeneratorService)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            assert "copilot.application" not in module


def test_generator_accepts_port_interface():
    sig = inspect.signature(OfferGeneratorService.__init__)
    params = list(sig.parameters.keys())
    assert "psychology_port" in params
    assert "session" not in params
