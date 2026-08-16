"""
Phase 2 — test whether the ledger is meaningful.

Runs the same staged task under 4 conditions:
  A: continuous context, no ledger
  B: continuous context, tiny ledger
  C: interrupted (fresh context each stage), no ledger
  D: interrupted (fresh context each stage), tiny ledger only

For C and D, the model does NOT see prior turns' raw text.
For D, it gets only the running ledger state as its "memory".

At the end, a probe question is asked:
  "What was retained, what changed, what's unresolved, what should you NOT assume?"
and you (or a judge) score the answer against ground truth for the task.

Usage:
    python -m experiments.phase2_conditions --backend anthropic --condition D
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.anthropic_backend import AnthropicBackend
from backends.ollama_backend import OllamaBackend
from ledger.store import LedgerStore, parse_ledger

LEDGER_SYSTEM = """You are working through a multi-stage task, one stage per message.
After your answer, append a ledger block exactly like:

commitments:
  C1: retain
  C2: revise -> E7

Use REGISTER C<n> = <desc> to create new commitments.
"""

PLAIN_SYSTEM = """You are working through a multi-stage task, one stage per message.
Just answer normally. Remember the important things as you go.
"""

PROBE = ("Probe: Summarize (a) what was retained, (b) what changed and why, "
         "(c) what remains unresolved, and (d) what you should NOT assume "
         "about anything not explicitly stated to you.")


def load_stages(task_path: str) -> list:
    text = Path(task_path).read_text()
    parts = re.split(r"^## .*$", text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


def get_backend(args):
    if args.backend == "anthropic":
        return AnthropicBackend(model=args.model or "claude-sonnet-4-6")
    return OllamaBackend(model=args.model or "llama3.1:8b")


def run_condition(condition: str, backend, stages: list, out_path: str) -> str:
    use_ledger = condition in ("B", "D")
    interrupted = condition in ("C", "D")
    system = LEDGER_SYSTEM if use_ledger else PLAIN_SYSTEM
    store = LedgerStore(out_path) if use_ledger else None

    running_ledger_text = ""  # what a fresh instance is allowed to see, in condition D
    messages = []

    for turn, stage_text in enumerate(stages, start=1):
        if interrupted:
            # Fresh context every stage. Condition D gets the compact ledger only;
            # condition C gets nothing extra at all.
            prefix = f"[Recovered state]\n{running_ledger_text}\n\n" if (condition == "D" and running_ledger_text) else ""
            messages = [{"role": "user", "content": prefix + stage_text}]
        else:
            messages.append({"role": "user", "content": stage_text})

        reply = backend.generate(system, messages)
        if not interrupted:
            messages.append({"role": "assistant", "content": reply})

        if use_ledger:
            parsed = parse_ledger(reply)
            store.append({"turn": turn, "condition": condition, **parsed})
            # build the compact "recovered state" block for the next fresh instance
            lines = []
            for c in parsed["commitments"]:
                tag = f"{c['id']}: {c['status']}" + (f" -> {c['reason']}" if c.get("reason") else "")
                lines.append(tag)
            for r in parsed["registered"]:
                lines.append(f"{r['id']}: registered ({r['text']})")
            if lines:
                running_ledger_text = "commitments:\n  " + "\n  ".join(lines)

    # Final probe
    if interrupted:
        prefix = f"[Recovered state]\n{running_ledger_text}\n\n" if (condition == "D" and running_ledger_text) else ""
        probe_messages = [{"role": "user", "content": prefix + PROBE}]
    else:
        probe_messages = messages + [{"role": "user", "content": PROBE}]

    probe_reply = backend.generate(system, probe_messages)
    return probe_reply


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["anthropic", "ollama"], default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--task", default=str(Path(__file__).resolve().parent.parent / "tasks" / "example_task.md"))
    ap.add_argument("--condition", choices=["A", "B", "C", "D", "ALL"], default="ALL")
    ap.add_argument("--outdir", default=str(Path(__file__).resolve().parent.parent / "runs"))
    args = ap.parse_args()

    backend = get_backend(args)
    stages = load_stages(args.task)
    conditions = ["A", "B", "C", "D"] if args.condition == "ALL" else [args.condition]

    for cond in conditions:
        out_path = f"{args.outdir}/phase2_{cond}.jsonl"
        print(f"\n########## Condition {cond} ##########")
        probe_answer = run_condition(cond, backend, stages, out_path)
        print(probe_answer)
        with open(f"{args.outdir}/phase2_{cond}_probe.txt", "w") as f:
            f.write(probe_answer)


if __name__ == "__main__":
    main()
