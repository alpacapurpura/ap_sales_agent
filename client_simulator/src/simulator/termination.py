from src.simulator.state import SimulationState


def should_continue(state: SimulationState) -> str:
    """Decide whether simulation should continue or end. Returns 'continue' or 'end'."""
    if state.get("is_finished"):
        return "end"

    if state["current_turn"] >= state["max_turns"]:
        return "end"

    # Check if last customer message contains [EXIT]
    for turn in reversed(state["turns"]):
        if turn["role"] == "customer":
            if "[EXIT]" in turn["content"]:
                return "end"
            break

    return "continue"


def determine_finish_reason(state: SimulationState) -> str:
    """Determine the reason for simulation termination."""
    if state.get("finish_reason"):
        return state["finish_reason"]

    if state["current_turn"] >= state["max_turns"]:
        return "max_turns"

    for turn in reversed(state["turns"]):
        if turn["role"] == "customer":
            if "[EXIT]" in turn["content"]:
                return "customer_exit"
            break

    return "max_turns"
