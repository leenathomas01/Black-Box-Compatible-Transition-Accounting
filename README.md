### !!! still a work in progress!!

# Commitment Ledger — v0

The "embarrassingly primitive" prototype: model → tiny commitment ledger → JSONL →
dumb diff script → flag missing/changed commitments. No embeddings, no judge model,
no cryptography. Just enough to find out if the tiny interface carries signal.

## Setup

```bash
cd commitment_ledger
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Pick a backend:

- **Anthropic API**: `export ANTHROPIC_API_KEY=sk-...`
- **Fully local**: install [Ollama](https://ollama.com), then `ollama pull llama3.1:8b`
  (or any model you like — pass `--model <name>`)

## Run Phase 1 (baseline: does the ledger track a real run cleanly?)

```bash
python -m experiments.phase1_baseline --backend anthropic
# or fully local:
python -m experiments.phase1_baseline --backend ollama --model llama3.1:8b
```

This runs `tasks/example_task.md` stage by stage, asks for a ledger block after
every reply, logs each turn to `runs/phase1.jsonl`, and prints the diff
(✓ / ↻ / ⚠ / ?) after each turn.

## Run Phase 2 (does the ledger actually do anything?)

```bash
python -m experiments.phase2_conditions --backend anthropic --condition ALL
```

Runs conditions A/B/C/D from the design doc:

| Condition | Context | Ledger |
|---|---|---|
| A | continuous | none |
| B | continuous | tiny ledger |
| C | interrupted (fresh each stage) | none |
| D | interrupted (fresh each stage) | ledger only |

Each condition ends with the same probe question ("what was retained / changed /
unresolved / what should you not assume") and saves the answer to
`runs/phase2_<X>_probe.txt`. **Scoring the probe answers against ground truth is
on you (or a separate judge call) — v0 deliberately has no automatic judge.**

## Where the rest of the design doc plugs in

- **Phase 3 (perturbations A–F)**: reuse `phase2_conditions.run_condition`. For
  silent loss (B), edit a stage in `tasks/example_task.md` to drop a fact without
  flagging it, rerun condition D, check whether `ledger/diff.py` flags the
  commitment as `⚠ missing disposition`. For false revision (C), add a distractor
  stage and confirm the model doesn't revise. For model handoff (F), just swap
  `--backend` / `--model` mid-run by hand-editing `messages` between stages.
- **Phase 4 (accounting vs validity)**: use `ledger/diff.py`'s
  `accounting_vs_validity_stub` — feed it your own human-labeled
  `{"C2@turn3": True/False}` judgments once you've read the transcripts.
- **Phase 5 (field ablations)**: edit `LEDGER_LINE` / `REGISTER_LINE` regexes in
  `ledger/store.py` and the system prompts in the experiment scripts to drop
  `reason`, drop `id`, etc. Rerun Phase 2 D and compare probe quality.
- **Phase 6 (REGISTER-only bookkeeping)**: already implemented — commitments only
  exist once `REGISTER C<n> = ...` is emitted; everything else is untracked
  ordinary reasoning. Count `len(known_ids)` per run to see how few commitments
  are actually needed.
- **Phase 7 (sparse ripple)**: `ledger/diff.py`'s `needs_inspection` list *is* the
  ripple signal — right now it's printed, not acted on. Next step: only re-fetch
  full context/evidence for IDs in `needs_inspection`, and measure tokens
  retrieved vs. a full-context baseline.

## Notes

- The ledger regex is strict on purpose (`ledger/store.py`). If a model doesn't
  comply with the format, that's itself a data point — log the raw reply anyway
  (already done) rather than silently dropping it.
- `runs/*.jsonl` is the only state. Delete it to reset a condition.
- Keep task stages short and swap in your own `tasks/*.md` — the split logic
  just looks for `## Stage N` headers.
