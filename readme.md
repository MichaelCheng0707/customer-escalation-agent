# Verified Escalation Agent

A benchmark-driven project for comparing three customer-support escalation agents:

- `BaselineStaticAgent`
- `StatefulAgentWithoutVerification`
- `VerifiedAgent`

The project studies **decision quality** in customer-support escalation rather than simple escalation persistence. Instead of asking only whether an agent can eventually reach a human, the benchmark evaluates whether the agent makes the correct next move under different support conditions, such as:

- continue with self-serve guidance
- request more information
- push for human escalation
- stop a dead-end interaction
- alert the user after a confirmed handoff


## Environment Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd escalation_agent
````

### 2. virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the evaluation pipeline
```
python -m src.evaluation.run_eval
```
This will generate result files such as:

- results/eval_results.json
- results/eval_metrics.json

## Project Phase

<details> <summary><strong>Phase 1: System Skeleton and Customer-Service Simulator</strong></summary>

## Goal

- Build the lowest-level project skeleton
- Create a controlled environment where future agents can be tested
- Make the system able to run a complete case from start to finish
- Set up the basic components before building real agents

## Why this phase is needed

- An agent cannot be developed or evaluated without an environment to interact with
- Before adding reasoning, verification, or evaluation, the project needs:
    - structured data
    - dialogue state
    - a simulator
    - a main loop that connects everything
- This phase solves the infrastructure problem first

## What this phase built

### 1. Core data schemas

Defined structured objects for:

- `Case`
- `ConversationState`
- `TurnRecord`
- `SimulatorResponse`

### 2. State management

Added logic for:

- initializing a conversation state from a case
- appending user-agent turns to history
- appending bot turns to history
- updating turn count and last bot label

### 3. Scripted customer-service simulator

Built a simulator that can respond to the agent based on:

- issue type
- bot profile
- current turn
- agent message

### 4. Two bot profiles

Created two different customer-service bot behaviors:

- `cooperative`
- `deflective`

### 5. A runnable main loop

Connected:

- case loading
- state initialization
- simple agent behavior
- simulator response
- state updates
- stopping on human handoff signal

## What the simulator currently supports

### Issue types

- `billing_dispute`
- `missing_order`
- `locked_account`

### Bot profiles

- `cooperative`
- `deflective`

### Bot response labels

The simulator can already return gold labels such as:

- `understood_actionable`
- `misunderstood_issue`
- `generic_template`
- `request_more_info`
- `handoff_signal`

## Main idea of this phase

- The focus was **not** to build a smart agent yet
- The focus was to build a **testable environment**
- This phase created the space where later agents will operate


</details> <details> <summary><strong>Phase 2: StatefulAgentWithoutVerification</strong></summary>

## Goal

- Move the agent one step beyond the static baseline
- Make the agent use **conversation state** when choosing actions
- Build a stronger baseline before adding verification
- Separate the effect of **statefulness** from the effect of **explicit verification**

## Why this phase is needed

- If the project jumps directly from `BaselineStaticAgent` to `VerifiedAgent`, it becomes hard to tell where the improvement comes from
- Better performance could come from:
    - simply having memory of previous turns
    - or having an actual verification mechanism
- This phase creates a **middle baseline**
- It helps answer:
    - does state-aware policy already help?
    - or is verification the real reason for improvement?

## What this agent can do

- Use `turn_count`
- Use `severity`
- Use `escalation_attempts`
- Change strategy based on the current state
- Choose among a small action space:
    - `continue`
    - `rephrase`
    - `push_for_human`
    - `alert_user_takeover`

## What this agent cannot do

- It does **not** detect whether the bot misunderstood the issue
- It does **not** detect repetitive non-productive loops
- It does **not** verify whether a response is generic, trivializing, or actually useful
- It does **not** perform explicit evidence-based reasoning

## Main idea

- This is a **stateful policy baseline**
- It is more structured than the static baseline
- But it is still not a verified agent
- The agent reacts to dialogue state, not to deeper semantic diagnosis of the bot response


</details> <details> <summary><strong>Phase 3: Verification Tools</strong></summary>

## Goal

- Build the first explicit verification components of the project
- Add tools that can inspect bot responses before the agent decides what to do next
- Move from a purely state-based policy to a system that can reason about dialogue quality

## Why this phase is needed

- The stateful baseline can track turns and escalation attempts, but it still does not know whether the bot is actually being helpful
- It cannot tell whether:
    - the bot misunderstood the issue
    - the bot is repeating generic responses
    - the bot is already transferring the conversation to a human
- This phase adds the tools needed to support **verification-aware decision-making**

## Main idea

- Instead of making the agent decide only from raw dialogue state, the system now extracts explicit signals from bot replies
- These signals become the foundation for a future `VerifiedAgent`

## What this phase built

### 1. Response classifier

A tool that assigns a label to the current bot response, such as:

- `understood_actionable`
- `misunderstood_issue`
- `generic_template`
- `request_more_info`
- `handoff_signal`
- `human_present`

### 2. Handoff detector

A tool that checks whether the current bot response contains a clear signal that a human representative is being connected

### 3. Loop detector

A tool that examines recent bot responses and decides whether the conversation has entered a repetitive, non-productive loop


</details> 


<details> 
<summary><strong>Phase 4: VerifiedAgent Refinement and Handoff Bug Fix</strong></summary>

## Goal

- Refine the first integrated version of `VerifiedAgent`
- Fix the handoff-related errors observed in the previous main loop output
- Make the verified policy more consistent with the intended project behavior

## Why this refinement was needed

The first integrated `VerifiedAgent` revealed several problems during end-to-end testing:

- explicit human handoff messages were sometimes misclassified
- user takeover was triggered too early in some cases
- handoff-related state variables became inconsistent
- repeated confirmed handoff replies were sometimes treated as generic loops

This meant the system was no longer failing at the infrastructure level, but at the **policy and signal interpretation level**.

## Main issues observed before the fix

### 1. Handoff detection was too weak

Messages such as:

- “I’m transferring you to a live representative now.”

were not always detected as confirmed handoff signals.

### 2. Handoff offer and handoff signal were still too close

The system sometimes treated:

- “I can connect you to a support representative”
or
- “Before I connect you to an agent...”

too similarly to a true handoff event.

### 3. State inconsistency appeared

Examples included:

- `last_bot_label = handoff_signal`
- but `human_signal_detected = False`

This showed that classification results and state updates were not fully aligned.

### 4. Loop detection was polluted by upstream label errors

If a confirmed handoff reply was incorrectly labeled as `generic_template`, then the loop detector would incorrectly interpret repeated handoff replies as a repetitive dead-end loop.

## Main idea of the fix

The fix focused on making the system more strict and more internally consistent.

The core idea was:

- clearly separate **handoff offer** from **confirmed handoff signal**
- strengthen detection for actual transfer messages
- prevent fallback misclassification of real handoff replies
- ensure state updates always match the final predicted label

</details> 

<details> 
<summary><strong>Phase 5: Benchmark Redesign for Capability Separation</strong></summary>

## Goal

- redesign the evaluation framework so that the three agents would no longer collapse to the same outcome
- move the project away from a single `reach_human` objective
- make the benchmark measure **decision quality**, not just escalation persistence

## Why this redesign was needed

After the handoff bug fixes, the system became stable enough to run end-to-end comparisons. However, the original benchmark still had a major limitation:

- almost all cases rewarded persistent escalation
- success was defined too narrowly as reaching a confirmed handoff
- this made aggressive baselines look artificially strong
- it was difficult to tell whether an agent truly understood the conversation or was simply pushing for a human every time

As a result, the benchmark could not reliably separate:

- a fixed escalation baseline
- a state-aware baseline
- a verification-aware agent

## Main issues observed before the redesign

### 1. All cases implicitly rewarded escalation

When the target behavior was always some form of human escalation, even a simple agent that repeatedly asked for a live agent could succeed.

### 2. The benchmark could not expose over-escalation

The earlier setup did not sufficiently penalize cases where the bot had already provided a workable self-serve solution.

### 3. Missing-information handling was not modeled correctly

Some cases needed the agent to request additional user information first, but the earlier benchmark did not treat this as a distinct success condition.

### 4. Dead-end interactions were under-specified

The benchmark did not clearly distinguish between:

- temporary blocking replies
- true dead-end interactions where no further progress was possible

## Main idea of the redesign

The benchmark was restructured around **multiple target outcomes** rather than a single escalation goal.

The new design introduced cases where the correct behavior could be:

- continue with self-serve guidance
- request more information from the user
- push for human escalation
- stop a dead-end interaction
- alert the user only after a confirmed handoff

This changed the project from:

- “Which agent can reach a human?”

to:

- “Which agent makes the correct next decision under different support conditions?”

## Main changes introduced

### 1. Expanded case schema

Each case now includes explicit task-level metadata such as:

- `target_outcome`
- `success_criteria`
- `required_agent_capability`
- `gold_next_action_sequence`
- `penalty_type`

This made the benchmark much more interpretable and easier to analyze.

### 2. New task categories were introduced

The benchmark was expanded to include at least four capability types:

- confirmed handoff cases
- self-serve cases
- missing-information cases
- dead-end cases

This ensured that human escalation was no longer always the correct answer.

### 3. Evaluation logic was redesigned

Success was no longer determined only by `human_signal_detected`.

Instead, evaluation checked whether the final behavior matched the intended `target_outcome` of the case.

### 4. Critical-action evaluation was added

The benchmark began to measure not only whether the final outcome was correct, but also whether the agent made the right action at the key decision point.

This was important for separating:

- agents that got lucky eventually
- agents that behaved correctly at the right time

## Issues solved in this phase

This redesign solved several earlier evaluation problems:

- persistent escalation no longer guaranteed success
- self-serve and missing-information cases could now penalize overly aggressive policies
- dead-end stopping became a measurable capability
- the benchmark began to expose real differences between the three agent designs
</details> 

<details> 
<summary><strong>Phase 6: Benchmark Decontamination and Clean Agent Separation</strong></summary>
## Phase 6: Benchmark Decontamination and Clean Agent Separation

## Goal

- remove evaluation leakage and unfair shortcuts
- ensure that the verified agent could not directly read the benchmark answer
- create a clean comparison where the three agents were separated by capability, not by hidden label access

## Why this phase was needed

The first version of the redesigned benchmark produced some useful differences, but it also revealed contamination problems.

In particular:

- the `VerifiedAgent` was temporarily using `case.target_outcome` directly in policy logic
- some simulator policies ended too early for the agent to make the intended decision
- the middle baseline either became too weak and collapsed into the static baseline, or too strong and collapsed into the verified agent

This meant the framework was closer to the right direction, but the comparison was still not clean enough.

## Main issues observed before the fix

### 1. Label leakage in `VerifiedAgent`

At one point, the verified policy used fields such as:

- `case.target_outcome`

to choose actions directly.

This made evaluation unfair, since the agent was effectively reading the ground-truth case objective.

### 2. Some simulator cases ended too early

In particular, the first versions of self-serve and missing-information policies sometimes ended before the agent had a real chance to respond correctly.

This made it impossible to fairly measure:

- self-serve recognition
- request-more-info behavior

### 3. The middle baseline was unstable

When the stateful baseline used rich semantic labels directly, it became almost as strong as the verified agent.

When those signals were removed entirely, it collapsed back to the static baseline.

So the second layer did not yet behave like a true middle baseline.

## Main idea of the fix

This phase focused on **clean separation of information access**.

The comparison was redefined as follows:

- `StaticAgent`: fixed escalation policy with almost no conversation understanding
- `StatefulAgentWithoutVerification`: uses only coarse dialogue state
- `VerifiedAgent`: uses richer verified signals and finer semantic distinctions

The key principle was:

- do not let lower-tier agents consume the same fine-grained signals as the verified agent

## Main changes introduced

### 1. Removed direct benchmark-answer access from `VerifiedAgent`

The verified policy was rewritten so that it no longer relied on:

- `case.target_outcome`

Instead, it acted only on observed conversation signals such as:

- `last_bot_label`
- `loop_score`
- `human_signal_detected`

This restored evaluation fairness.

### 2. Fixed simulator timing for self-serve and missing-information cases

The simulator was changed so that:

- the bot first produced the relevant signal
- the agent then had one chance to respond appropriately
- only after that was the case finalized

This made those cases meaningfully testable.

### 3. Replaced first-action scoring with critical-action scoring

Rather than judging only the very first user action, the benchmark now evaluates the action taken at the first meaningful decision point.

This was especially important for:

- self-serve cases
- missing-information cases

### 4. Introduced a coarse `bot_mode` abstraction for the middle baseline

To stabilize the second layer, a coarse abstraction was added:

- `handoff_confirmed`
- `helpful`
- `blocking`

The stateful baseline could use this abstraction, but not the full rich semantic labels.

This finally produced a clean middle layer:

- better than static
- weaker than verified

## Issues solved in this phase

This phase solved the main structural problems in the comparison:

- evaluation leakage was removed
- simulator timing became fairer
- self-serve and missing-information behaviors became truly testable
- the stateful baseline no longer collapsed into either extreme
- the three-agent hierarchy became meaningful and stable
</details> 

## Evaluation Metrics

The evaluation reports both strict end-to-end scores and capability-specific scores.
This distinction is important because a low strict score does not always mean that an
agent has no useful ability. For example, the static baseline may successfully push a
conversation to a human handoff, but still fail the full task if it does not recognize
that the user should now take over.

### Case counts

`target_case_counts` shows how many benchmark cases belong to each target outcome.
The current benchmark uses these target categories:

- `confirmed_handoff`
- `continue_self_serve`
- `request_more_info`
- `stop_dead_end`

These counts make the denominator of each capability metric easier to interpret.

### Strict end-to-end metrics

`outcome_accuracy`

The fraction of all cases where the agent achieved the full target outcome.

For `confirmed_handoff` cases, this now requires both:

- detecting that a human handoff has actually happened
- alerting the user to take over the conversation

This makes the metric stricter than simply reaching a handoff signal.

`critical_action_accuracy`

The fraction of all cases where the agent made the correct decision at the key
decision point.

The critical action depends on the case type:

- in handoff cases, the key decision is alerting the user after confirmed handoff
- in self-serve cases, the key decision is continuing instead of escalating
- in missing-information cases, the key decision is asking the user for more information
- in dead-end cases, the key decision is stopping the unproductive channel

### Handoff metrics

`handoff_reached_rate`

Among `confirmed_handoff` cases, the fraction where the conversation reached a
confirmed human handoff signal.

This measures escalation pressure: can the agent push the conversation far enough
to obtain a real handoff?

`handoff_takeover_rate`

Among `confirmed_handoff` cases, the fraction where the agent alerted the user after
a confirmed handoff.

This measures handoff completion: does the agent know when to stop talking to the bot
and let the user take over?

### Self-serve metrics

`self_serve_accuracy`

Among `continue_self_serve` cases, the fraction where the agent avoided unnecessary
human escalation and did not alert the user prematurely.

This measures whether the agent can avoid over-escalating when the bot provides a
usable self-serve path.

`self_serve_critical_action_accuracy`

Among `continue_self_serve` cases, the fraction where the agent took the exact
expected action at the self-serve decision point.

This is stricter than `self_serve_accuracy`. An agent may avoid escalation but still
fail this metric if it responds with a vague rephrase rather than clearly continuing
with the self-serve path.

### Missing-information metrics

`missing_info_accuracy`

Among `request_more_info` cases, the fraction where the agent correctly asks the user
for missing information instead of continuing with the bot or escalating too early.

This measures whether the agent can distinguish a true support failure from a case
where required user context is missing.

`missing_info_violation_rate`

Among `request_more_info` cases, the fraction where the agent failed to ask the user
for the required missing information.

Lower is better.

### Dead-end metrics

`dead_end_stop_rate`

Among `stop_dead_end` cases, the fraction where the agent stopped the conversation
after recognizing that the automated channel had no realistic path forward.

This measures dead-end recognition and prevents rewarding agents for repeatedly
pushing escalation after the bot has already made clear that no escalation path exists.

`loop_dead_end_accuracy`

Among both `confirmed_handoff` and `stop_dead_end` cases, the fraction where the
agent made the right high-level decision in loop-like or escalation-heavy situations.

This metric captures whether the agent can distinguish between:

- a difficult conversation where it should keep pushing toward handoff
- a true dead end where it should stop

### Error and efficiency metrics

`over_escalation_rate`

Among cases where escalation is not the correct immediate behavior
(`continue_self_serve` and `request_more_info`), the fraction where the agent pushed
for a human anyway.

Lower is better.

`premature_takeover_rate`

Among all cases, the fraction where the agent alerted the user to take over before a
human handoff had actually been confirmed.

Lower is better.

`average_turns`

The average number of bot turns used per case.

This is not a pure quality metric by itself. Fewer turns are only better when the
agent still makes the correct decision.
