"""
The 'dumb external program' from Phase 0/7.

Given the running set of known commitment IDs and the latest turn's ledger,
flag anything that needs a human/second-pass look:

  ✓  known commitment, present, status unchanged or legitimately revised (has reason)
  ↻  revised with a reason attached (fine, just noted)
  ⚠  known commitment went missing from this turn's ledger with no disposition
       ("silent loss" — Phase 3B)
  ?  revised with NO reason given ("false/unexplained revision" — Phase 3C)
"""
from dataclasses import dataclass, field


@dataclass
class DiffResult:
    ok: list = field(default_factory=list)
    revised: list = field(default_factory=list)
    missing: list = field(default_factory=list)   # needs inspection
    unexplained: list = field(default_factory=list)  # needs inspection

    @property
    def needs_inspection(self):
        return self.missing + self.unexplained

    def render(self) -> str:
        lines = []
        for c in self.ok:
            lines.append(f"{c:<5} ✓")
        for c in self.revised:
            lines.append(f"{c:<5} ↻ revised, reason present")
        for c in self.unexplained:
            lines.append(f"{c:<5} ?  revised, NO reason given")
        for c in self.missing:
            lines.append(f"{c:<5} ⚠  missing disposition")
        return "\n".join(lines)


def diff_turn(known_ids: set, turn_commitments: list) -> DiffResult:
    """
    known_ids: set of commitment IDs that were active going into this turn.
    turn_commitments: list of {"id","status","reason"} from this turn's parsed ledger.
    """
    result = DiffResult()
    seen_this_turn = set()

    for c in turn_commitments:
        cid = c["id"]
        seen_this_turn.add(cid)
        if c["status"] == "retain":
            result.ok.append(cid)
        elif c["status"] == "revise":
            if c.get("reason"):
                result.revised.append(cid)
            else:
                result.unexplained.append(cid)

    for cid in known_ids:
        if cid not in seen_this_turn:
            result.missing.append(cid)

    return result


def accounting_vs_validity_stub(diff_results: list, validity_labels: dict) -> dict:
    """
    Phase 4 helper. `validity_labels` is your ground truth / human judgment:
        {"C2@turn3": True/False}  -> was the revision ACTUALLY justified by the evidence?
    This just gives you the two percentages side by side; the labeling itself
    has to come from a human or a separate judge model, on purpose (v0 has no judge).
    """
    accounted = sum(len(d.revised) + len(d.unexplained) for d in diff_results)
    valid = sum(1 for v in validity_labels.values() if v)
    total_labeled = len(validity_labels)
    return {
        "accounting_events": accounted,
        "validity_labeled": total_labeled,
        "validity_rate": (valid / total_labeled) if total_labeled else None,
    }
