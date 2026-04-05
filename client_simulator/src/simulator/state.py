from typing import TypedDict


class SimulationState(TypedDict):
    simulation_id: str
    persona: dict
    scenario: dict
    turns: list[dict]  # list of ConversationTurn dicts
    current_turn: int
    max_turns: int
    simulated_user_id: str
    is_finished: bool
    finish_reason: str | None  # "max_turns"|"goal_achieved"|"customer_exit"|"agent_error"
    last_agent_response: str
