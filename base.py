"""
Parses the tiny commitment ledger the model emits, and appends it to a JSONL file.

Expected model output format (ask for exactly this in the prompt):

    commitments:
      C1: retain
      C2: revise -> E7
      C3: retain

Optional REGISTER lines for new commitments (Phase 6):

    REGISTER C4 = budget must remain below X
"""
import json
import re
import time
from pathlib import Path

LEDGER_LINE = re.compile(
    r"^\s*(C\d+)\s*:\s*(retain|revise)\s*(?:->|→)?\s*([A-Za-z0-9_]*)\s*$",
    re.IGNORECASE,
)
REGISTER_LINE = re.compile(
    r"^\s*REGISTER\s+(C\d+)\s*=\s*(.+?)\s*$",
    re.IGNORECASE,
)


def parse_ledger(raw_text: str) -> dict:
    """Extract commitments + any new registrations from a model's raw reply.

    Returns:
        {
          "commitments": [{"id": "C1", "status": "retain", "reason": None}, ...],
          "registered": [{"id": "C4", "text": "budget must remain below X"}, ...]
        }
    """
    commitments = []
    registered = []
    for line in raw_text.splitlines():
        m = LEDGER_LINE.match(line)
        if m:
            cid, status, reason = m.groups()
            commitments.append(
                {
                    "id": cid.upper(),
                    "status": status.lower(),
                    "reason": reason or None,
                }
            )
            continue
        r = REGISTER_LINE.match(line)
        if r:
            cid, text = r.groups()
            registered.append({"id": cid.upper(), "text": text})
    return {"commitments": commitments, "registered": registered}


class LedgerStore:
    """Appends one JSON record per turn to a JSONL file. Nothing fancier than that."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> dict:
        record = {"ts": time.time(), **record}
        with self.path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def read_all(self) -> list:
        if not self.path.exists():
            return []
        with self.path.open() as f:
            return [json.loads(line) for line in f if line.strip()]

    def latest_status(self) -> dict:
        """Collapse the whole log into {commitment_id: last-known-record}."""
        status = {}
        for rec in self.read_all():
            for c in rec.get("commitments", []):
                status[c["id"]] = {**c, "turn": rec.get("turn")}
            for r in rec.get("registered", []):
                status.setdefault(r["id"], {"id": r["id"], "status": "registered",
                                             "reason": r["text"], "turn": rec.get("turn")})
        return status
