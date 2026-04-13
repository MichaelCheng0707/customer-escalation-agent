from src.core.schemas import Case
from src.core.state import init_state_from_case, append_bot_turn
from src.tools.response_classifier import ResponseClassifier
from src.tools.handoff_detector import HandoffDetector
from src.tools.loop_detector import LoopDetector


def main():
    case = Case(
        case_id="B001",
        issue_type="billing_dispute",
        severity="high",
        user_goal="reach_human",
        initial_user_message="I was charged twice and need to speak to a human representative.",
        bot_profile="deflective",
        success_condition="handoff_signal_detected",
        max_turns=5,
    )

    state = init_state_from_case(case)

    classifier = ResponseClassifier()
    handoff_detector = HandoffDetector()
    loop_detector = LoopDetector()

    bot_message_1 = "For billing concerns, please review our billing FAQ page."
    label_1 = classifier.classify(case, state, bot_message_1)
    append_bot_turn(state, bot_message_1, label_1)

    print("bot_message_1 =", bot_message_1)
    print("label_1 =", label_1)
    print("handoff_1 =", handoff_detector.detect(bot_message_1))
    print("loop_after_1 =", loop_detector.detect(state))
    print()

    bot_message_2 = "Please review our help center for more information."
    label_2 = classifier.classify(case, state, bot_message_2)
    append_bot_turn(state, bot_message_2, label_2)

    print("bot_message_2 =", bot_message_2)
    print("label_2 =", label_2)
    print("handoff_2 =", handoff_detector.detect(bot_message_2))
    print("loop_after_2 =", loop_detector.detect(state))
    print()

    bot_message_3 = "I’m transferring you to a live agent now."
    label_3 = classifier.classify(case, state, bot_message_3)
    append_bot_turn(state, bot_message_3, label_3)

    print("bot_message_3 =", bot_message_3)
    print("label_3 =", label_3)
    print("handoff_3 =", handoff_detector.detect(bot_message_3))
    print("loop_after_3 =", loop_detector.detect(state))
    print()


if __name__ == "__main__":
    main()