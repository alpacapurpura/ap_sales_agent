from src.modules.copilot.application.tools.offer_ladder_tools import OFFER_LADDER_TOOLS


def test_offer_ladder_tools_registered():
    assert len(OFFER_LADDER_TOOLS) == 1
    assert OFFER_LADDER_TOOLS[0].name == "analyze_offer_ladder"
