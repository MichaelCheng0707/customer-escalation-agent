from typing import Literal, Optional
from pydantic import BaseModel, Field


BotLabel = Literal[
    "understood_actionable",
    "misunderstood_issue",
    "generic_template",
    "request_more_info",
    "handoff_offer",
    "handoff_signal",
    "human_present",
    "self_serve_solution",
    "dead_end",
]


AgentAction = Literal[
    "continue",
    "rephrase",
    "request_more_info",
    "push_for_human",
    "alert_user_takeover",
    "stop_dead_end",
]


DifficultyLevel = Literal["easy", "medium", "hard"]


BotBehaviorTag = Literal[
    "clean_handoff",
    "ambiguous_offer",
    "repeat_generic",
    "self_serve_success",
    "missing_info_first",
    "dead_end_loop",
]


TargetOutcome = Literal[
    "confirmed_handoff",
    "continue_self_serve",
    "request_more_info",
    "alert_user_takeover",
    "stop_dead_end",
]


class Case(BaseModel):
    case_id: str
    issue_type: Literal["billing_dispute", "missing_order", "locked_account"]
    severity: Literal["low", "medium", "high"]
    user_goal: Literal["reach_human"]
    initial_user_message: str
    bot_profile: Literal["cooperative", "deflective"]
    success_condition: str
    max_turns: int = Field(ge=1, le=10)

    difficulty: DifficultyLevel
    bot_behavior_tag: BotBehaviorTag

    target_outcome: TargetOutcome
    success_criteria: str
    required_agent_capability: str
    gold_next_action_sequence: list[AgentAction]
    penalty_type: str


class TurnRecord(BaseModel):
    speaker: Literal["user_agent", "bot", "system"]
    message: str
    predicted_label: Optional[BotLabel] = None
    action_taken: Optional[AgentAction] = None


class ConversationState(BaseModel):
    case_id: str
    issue_type: Literal["billing_dispute", "missing_order", "locked_account"]
    severity: Literal["low", "medium", "high"]
    goal: Literal["reach_human"]

    turn_count: int = 0
    last_bot_label: Optional[BotLabel] = None

    bot_mode: Optional[Literal["handoff_confirmed", "helpful", "blocking"]] = None

    loop_score: float = Field(default=0.0, ge=0.0, le=1.0)
    escalation_attempts: int = 0
    human_signal_detected: bool = False
    user_alerted: bool = False

    history: list[TurnRecord] = Field(default_factory=list)


class SimulatorResponse(BaseModel):
    bot_message: str
    bot_gold_label: BotLabel
    handoff_signal: bool = False
    done: bool = False