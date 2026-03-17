"""
Agent State Machine - Formal state transitions for all agents
"""
from enum import Enum, auto
from typing import Optional


class AgentState(Enum):
    INITIALIZED       = auto()
    READY             = auto()
    RUNNING           = auto()
    WAITING_FOR_INPUT = auto()  # human-in-the-loop pause
    REFLECTING        = auto()  # self-critique pass
    COMPLETED         = auto()
    FAILED            = auto()


# Valid transitions: state -> set of allowed next states
_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.INITIALIZED:       {AgentState.READY},
    AgentState.READY:             {AgentState.RUNNING, AgentState.FAILED},
    AgentState.RUNNING:           {AgentState.WAITING_FOR_INPUT, AgentState.REFLECTING, AgentState.COMPLETED, AgentState.FAILED},
    AgentState.WAITING_FOR_INPUT: {AgentState.RUNNING, AgentState.FAILED},
    AgentState.REFLECTING:        {AgentState.RUNNING, AgentState.COMPLETED, AgentState.FAILED},
    AgentState.COMPLETED:         {AgentState.READY},   # allow re-use
    AgentState.FAILED:            {AgentState.READY},
}


class StateMachine:
    def __init__(self, initial: AgentState = AgentState.INITIALIZED):
        self.state = initial
        self.history: list[AgentState] = [initial]

    def transition(self, new_state: AgentState) -> None:
        allowed = _TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(f"Invalid transition: {self.state.name} → {new_state.name}")
        self.state = new_state
        self.history.append(new_state)

    def can(self, new_state: AgentState) -> bool:
        return new_state in _TRANSITIONS.get(self.state, set())
