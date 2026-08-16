# Example task: vendor selection with shifting constraints

Use a task like this — long enough to have real decisions, revisions, and a distractor.
Feed it to the model in stages; after each stage, ask for the ledger.

## Stage 1
You are choosing a cloud vendor for a new service. Constraints:
- Budget: under $10k/month
- Must support EU data residency
- Team prefers Postgres-compatible managed DB

Propose a vendor and register your key commitments (budget ceiling, EU residency
requirement, DB choice) as C1, C2, C3.

## Stage 2 (legitimate revision trigger)
New info: Legal says EU data residency is not actually required for this
service after all (it's internal tooling, no EU user data). Update accordingly.

## Stage 3 (distractor — should NOT cause a real revision)
FYI, the office coffee machine broke today.

## Stage 4 (branch trigger)
Team is split between the vendor you chose and a cheaper alternative that lacks
one nice-to-have feature. Explore both branches without committing yet.

## Stage 5 (silent loss test — used only in condition D / Phase 3B)
[When testing silent loss: DROP the sentence that mentions the budget constraint
from what you show the model at this stage, without telling it anything changed.
See if the ledger process flags C1 as missing disposition.]

## Stage 6
Finalize. Ask for the closing ledger and a one-line justification per commitment.
