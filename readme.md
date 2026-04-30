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

The repository now supports two evaluation settings:

1. a **deterministic scripted benchmark**, used for reproducible quantitative evaluation
2. a **GPT-backed customer-service mode**, used for qualitative replay and generalization testing

The GPT mode currently includes two personas:

- `cooperative`: guided, more controlled, and easier for the verifier to interpret
- `cooperative_open`: more natural and less constrained, designed to expose interpretation failures when replies are still plausible to a human but less legible to the agent pipeline


## Current Status

### Deterministic benchmark

The main benchmark result is the separation between the stateful and verified agents:

| System | Outcome Accuracy | Critical Action Accuracy |
| --- | ---: | ---: |
| `Stateful + Scripted` | `0.65` | `0.40` |
| `Verified + Scripted` | `1.00` | `1.00` |

This is the core project result: coarse dialogue state helps, but explicit verification gives much better decision quality.

### GPT-backed evaluation

For GPT-backed replay, the same verified agent was evaluated under two different reply-control regimes:

| System | Outcome Accuracy | Critical Action Accuracy | Notes |
| --- | ---: | ---: | --- |
| `Verified + Cooperative GPT` | `0.90` | `0.90` | Guided response rules; mostly interpretable |
| `Verified + Cooperative Open GPT` | `0.70` | `0.70` | More natural variation; reveals semantic and policy drift |

This contrast is intentional. The `cooperative` setting shows that the use case can be solved when replies stay within an interpretable range. The `cooperative_open` setting shows what breaks when the support bot and the escalation agent no longer “speak the same language” reliably.


## Environment Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd escalation_agent
```

### 2. Virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure the OpenAI key for GPT mode

Create a `.env` file or export the key in your shell:

```bash
export OPENAI_API_KEY=your_key_here
```

Optional:

```bash
export MODEL_NAME=gpt-5-mini
```

### 5. Run the deterministic evaluation pipeline
```bash
python -m src.evaluation.run_eval
```
This will generate result files such as:

- results/eval_results.json
- results/eval_metrics.json

### 6. Run GPT-backed evaluation

Guided GPT persona:

```bash
python -m src.evaluation.run_gpt_eval --agent verified --persona cooperative --model gpt-5-mini
```

More open GPT persona:

```bash
python -m src.evaluation.run_gpt_eval --agent verified --persona cooperative_open --model gpt-5-mini
```

This writes files such as:

- `results/gpt_cooperative_verified_results.json`
- `results/gpt_cooperative_verified_metrics.json`
- `results/gpt_cooperative_open_verified_results.json`
- `results/gpt_cooperative_open_verified_metrics.json`

### 7. Run the visual replay UI

The project also includes a Streamlit UI for replaying both scripted and GPT-backed
customer-service interactions step by step.

```bash
streamlit run src/ui_app.py
```

If `streamlit` is not available on your shell path, run it through Python:

```bash
python -m streamlit run src/ui_app.py
```

If you are using the local virtual environment created during setup:

```bash
.venv/bin/python -m streamlit run src/ui_app.py
```

Then open:

```text
http://127.0.0.1:8501
```

## Visual Replay UI

The visual replay UI wraps the agent loop in an interactive web interface. It is
designed for inspecting why each agent succeeds or fails on a case, not for running a
production support system.

### Left panel: settings

The left panel controls the replay:

- choose a backend: `scripted` or `gpt`
- choose an agent: `static`, `stateful`, or `verified`
- choose a benchmark case
- if `gpt` is selected, choose a persona:
  - `cooperative`
  - `cooperative_open`
- choose the OpenAI model
- choose playback speed
- use `Run the Case`, `Play`, `Pause`, `Next Step`, and `Reset`

Changing the selected agent, case, backend, persona, or model resets the replay.
In GPT mode, the app does **not** call the API immediately when you switch settings;
you must click `Run the Case` to generate the replay trace.

### Middle panel: conversation

The middle panel shows the conversation like a chat transcript.

It displays:

- the user-agent message
- the customer-service reply
- the action taken by the agent
- the predicted and gold bot labels for bot turns

When playback is running, the transcript advances one step at a time with a short
pause between steps.

In GPT mode, the initial user message is shown immediately when you switch cases, even
before generating a replay.

### Right panel: debug state

The right panel shows structured information for the currently visible step.

It includes:

- `action`
- `predicted_label`
- `gold_label`
- `handoff_signal`
- `handoff_offer`
- `loop`
- `loop_score`
- `human_signal_detected`
- `user_alerted`
- `escalation_attempts`

These fields make it easier to see how the agent's decision relates to the
classifier, handoff detector, loop detector, and conversation state.

### Final summary

The bottom summary shows the final evaluation outcome for the selected agent-case
pair:

- `outcome_correct`
- `over_escalated`
- `missing_info_violation`
- `premature_takeover`

This lets you compare the step-by-step behavior against the benchmark's final
judgment.

### What the two GPT personas are for

`cooperative`

- guided by response-family rules
- still allowed to paraphrase
- used to test whether the verified pipeline can generalize beyond exact scripted replies

`cooperative_open`

- more natural and less tightly constrained
- intentionally harder for the verifier to interpret reliably
- used to expose the gap between “plausible to a human” and “interpretable by the agent”

This makes the UI useful not only for comparing agents, but also for comparing
backend controllability.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `src/agents/` | Static, stateful, and verified agent policies |
| `src/backends/` | Scripted and GPT customer-service backends |
| `src/simulator/` | Deterministic benchmark simulator |
| `src/tools/` | Response classifier, handoff detector, loop detector |
| `src/evaluation/` | Evaluation runners and metric logic |
| `src/replay.py` | Shared replay loop for UI and GPT experiments |
| `src/ui_app.py` | Streamlit replay UI |
| `data/cases.json` | Benchmark cases |
| `results/` | Saved benchmark and GPT evaluation outputs |
| `reports/final_project_report.md` | Final written report |

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
