from src.core.schemas import Case, ConversationState, SimulatorResponse
from src.simulator.scripted_policies import cooperative_policy, deflective_policy


class CustomerServiceSimulator:
    def step(
        self,
        case: Case,
        conversation_state: ConversationState,
        agent_message: str,
    ) -> SimulatorResponse:
        if case.bot_profile == "cooperative":
            return cooperative_policy(case, conversation_state, agent_message)

        return deflective_policy(case, conversation_state, agent_message)