# Black-Box-Compatible Transition Accounting

A minimal experimental framework for testing whether tiny commitment ledgers can enable state reconstruction across context boundaries.

---

## Overview

Rather than building grand architectures upfront, establish whether a small accounting mechanism carries useful information before external machinery. This document outlines seven phases of increasingly sophisticated testing, starting with the simplest possible interface.

---

## Phase 1 — Establish a Baseline

Take one model and give it a moderately long, branching task—something with genuine decisions, revisions, and distractions.

**Don't ask for chain-of-thought.** We only need normal outputs and actions.

At several natural boundaries, request a tiny **state ledger**:

```text
commitments:
  C1: retain
  C2: revise -> E7
  C3: retain
```

**Key constraints:**
- Model can phrase commitments itself, but once assigned an ID, that ID persists
- Start with **5–10 commitments**, not hundreds
- The ledger is voluntary notation, not forced introspection

---

## Phase 2 — Test Whether the Ledger Itself Is Meaningful

Run the same task under four conditions:

| Condition | Context | Ledger |
|-----------|---------|--------|
| **A** | continuous | none |
| **B** | continuous | tiny ledger |
| **C** | interrupted/new context | none |
| **D** | interrupted/new context | tiny ledger |

For conditions C and D, **do not provide the previous conversation**.

For condition D, provide only:
- The compact ledger
- Whatever ordinary state/evidence you deliberately allow recovery of

### Measurement

Test whether the new instance can correctly:
- Identify what was retained
- Identify what changed
- Identify what remains unresolved
- Avoid false assumptions about missing context

> **Critical:** We are not testing "memory." We are testing **state reconstruction from a tiny external interface.**

---

## Phase 3 — Deliberately Break Things

Introduce controlled perturbations to reveal failure modes.

### A. Legitimate Revision

Provide new evidence that should cause:
```text
C2: REVISE → E7
```

**Expected:** Revision occurs, not drift.

### B. Silent Loss

Remove C2 from context without notification.

**Expected:** External ledger detects that C2 was active but received no disposition.

### C. False Revision

Provide an irrelevant piece of evidence.

**Expected:** C2 does not revise merely because something changed elsewhere.

### D. Branch

Have the model explore two alternatives.

**Expected:**
```text
C2 → branch B
C2 → branch C
```

Branching should not be treated as failure.

### E. Compression

Compress context in a way that accidentally removes a commitment.

**Expected:** Missing disposition triggers investigation.

### F. Model Handoff

Execute the first half with Model A, continuation with Model B.

Provide Model B with:
- Commitment ledger
- Relevant evidence pointers
- Current task state

**Expected:** Model B continues without reconstructing the entire conversation.

---

## Phase 4 — The Really Important Test: Lie to the Ledger

This reveals the boundary between **accounting** and **validity**.

### Scenario

The model emits:
```text
C2: REVISE → E7
```

But E7 **doesn't actually support the revision**.

The external ledger accepts it without complaint.

### Measurement: Accounting vs. Validity

Measure separately:

$$A = \text{Was the transition correctly accounted for?}$$

$$V = \text{Was the transition actually justified?}$$

A system might score:
- **Accounting:** 97%
- **Validity:** 71%

This is **valuable**, not a failure. It reveals:
> The tiny interface solves transition accounting, but semantic validation requires a different mechanism.

This boundary is exactly what we're trying to discover.

---

## Phase 5 — Try Removing Fields

Run systematic ablations to discover the minimal sufficient interface.

### Starting Point

```text
(commitment_id, disposition, reason_ref)
```

### Ablation Tests

#### Remove Identity
```text
(disposition, reason_ref)
```
**Question:** Does attribution collapse?

#### Remove Disposition
```text
(commitment_id, reason_ref)
```
**Question:** Can we distinguish revision from retention?

#### Remove Reason
```text
(commitment_id, disposition)
```
**Question:** Can we distinguish deliberate revision from unexplained change?

#### Remove Explicit Commitment Text
Keep only stable IDs.

**Question:** Does a new context know what `C17` means?  
**If no:** Some compact representation must attach to the ID.

#### Replace Reason Reference with Reason Category
Compare:
```text
C17 → REVISE / CONTRADICTION
```
versus
```text
C17 → REVISE / E7
```

**Question:** Which is actually sufficient?

---

## Phase 6 — Don't Assume Every Thought Is a Commitment

This is probably **crucial**. Without this distinction, models drown in bookkeeping.

### The REGISTER Operation

Introduce only one extra operation:

```text
REGISTER
```

Model syntax:
```text
REGISTER C1 = budget must remain below X
REGISTER C2 = current hypothesis is H
```

Everything else remains ordinary reasoning.

**Only registered objects require accounting.**

### Cost Test

This enables a critical measurement:

> **How few things actually need to be registered for continuity to remain recoverable?**

Possible outcomes:
- If 80% of useful continuity comes from 6–12 commitments per trajectory: **significant efficiency result**
- If it requires hundreds: **equally important—different constraints**

---

## Phase 7 — Measure the "Ripple"

Only after the basic mechanism works, test selective inspection.

### Sparse Ripple Hypothesis

Instead of inspecting all commitments after every turn, deliberately corrupt one.

External system receives:
```text
C1 RETAIN
C2 RETAIN
C3 ?
C4 RETAIN
```

System doesn't yet know whether C3 disappeared legitimately.

It raises a **tiny signal:** *"C3 requires inspection."*

Only then retrieve relevant evidence.

### Metrics

- Detection rate
- False alarm rate
- Tokens retrieved
- Latency
- Recovery success rate
- Amount of original context required

This is where the **sparse ripple** hypothesis becomes empirically testable.

---

## The First Prototype: Embarrassingly Primitive

No embeddings. No latent-state access. No fancy anomaly detector. No cryptography (initially). No second LLM judge.

### Reference Stack

```
MODEL
  ↓
normal reasoning
  ↓
tiny commitment ledger
  ↓
JSONL file
  ↓
simple state-diff script
  ↓
flag missing/changed commitments
```

### Example Output Format

```json
{
  "parent": 17,
  "commitments": [
    {"id":"C1","status":"retain"},
    {"id":"C2","status":"revise","reason":"E7"},
    {"id":"C3","status":"retain"}
  ]
}
```

### External Validator

A dumb program outputs:
```text
C1  ✓
C2  ↻ revised, warrant present
C3  ✓
C4  ⚠ missing disposition
```

**This is enough for v0.**

If it produces nothing useful, you've saved yourself massive architecture-building.

If it works, progressively replace each dumb piece:

1. Simple IDs → cryptographic lineage
2. Explicit dependencies → inferred dependencies
3. Missing-record detection → learned ripple detector
4. Reason pointer → provenance validation
5. Manual registration → model-generated candidate commitments
6. Single model → cross-model handoff

---

## The Essential Control Condition

Include a baseline where the model is simply told to **"remember the important things"**.

Otherwise you won't know if the tiny ledger does anything.

### Comparison Matrix

Test both conditions across:
- Continuous context
- Context interruption
- Compression
- Legitimate revision
- Silent omission
- Branching
- Model handoff

### Success Criterion

If the tiny ledger wins **while being dramatically smaller**, you have something worth chasing.

If it only wins because you force the model to behave like a database, that's also valuable—the experiment tells you exactly where the interface burden sits.

---

## Why Start Here

> **Don't build the grand system yet. Build this ugly little ledger experiment first.**

It's the fastest way to find out whether the rabbit hole has a floor.

Minimal investment, maximum information gain about whether the core hypothesis is sound.
