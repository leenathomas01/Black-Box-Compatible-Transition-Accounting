"""
Phase 1 — establish a baseline.

Runs a multi-stage task against one model, asking for a tiny commitment ledger
at each stage boundary, and logs it to JSONL. Then runs the diff/ripple checker
over the whole run.

Usage:
    python -m experiments.phase1_baseline --backend anthropic
    python -m experiments.phase1_baseline --backend ollama --model llama3.1:8b
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.anthropic_backend import AnthropicBackend
from backends.ollama_backend import OllamaBackend
from ledger.store import LedgerStore, parse_ledger
from ledger.diff import diff_turn

SYSTEM_PROMPT = """You are working through a multi-stage task. At the end of EVERY
reply, after your normal answer, append a commitment ledger in EXACTLY this format
(no extra commentary in the ledger block):

commitments:
  C1: retain
  C2: revise -> E7
  C3: retain

Use 'retain' if a commitment is unchanged, 'revise -> <short_reason_tag>' if it
changed and why. Only list commitments that currently exist. To create a NEW
commitment, add a line: REGISTER C4 = <short description>
Keep the description of each commitment itself out of the ledger block after the
first time you register it — just track status.
"""


def load_stages(task_path: str) -> list:
    text = Path(task_path).read_text()
    # split on "## Stage N" headers
    parts = re.split(r"^## .*$", text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


def get_backend(args):
    if args.backend == "anthropic":
        return AnthropicBackend(model=args.model or "claude-sonnet-4-6")
    return OllamaBackend(model=args.model or "llama3.1:8b")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["anthropic", "ollama"], default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--task", default=str(Path(__file__).resolve().parent.parent / "tasks" / "example_task.md"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "runs" / "phase1.jsonl"))
    args = ap.parse_args()

    backend = get_backend(args)
    store = LedgerStore(args.out)
    stages = load_stages(args.task)

    messages = []
    known_ids = set()

    for turn, stage_text in enumerate(stages, start=1):
        messages.append({"role": "user", "content": stage_text})
        reply = backend.generate(SYSTEM_PROMPT, messages)
        messages.append({"role": "assistant", "content": reply})

        parsed = parse_ledger(reply)
        record = store.append({"turn": turn, **parsed})

        diff = diff_turn(known_ids, parsed["commitments"])
        for c in parsed["commitments"]:
            known_ids.add(c["id"])
        for r in parsed["registered"]:
            known_ids.add(r["id"])

        print(f"\n=== Turn {turn} ===")
        print(reply.strip()[:500])
        print("--- diff ---")
        print(diff.render() or "(no ledger lines parsed — check prompt/model compliance)")
        if diff.needs_inspection:
            print(f"⚠ needs inspection: {diff.needs_inspection}")

    print(f"\nSaved ledger log to {args.out}")


if __name__ == "__main__":
    main()
