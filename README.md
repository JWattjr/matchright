# MatchRight

MatchRight is a standalone GenLayer intelligent contract demo for a right of first refusal over a uniquely keyed test entitlement. It stores no funds and moves no real-world asset. The seller freezes a named incumbent, a named outside bidder, an integer price, one service obligation, and an expiry. The outside bidder confirms the exact terms hash. Only the incumbent can exercise, at the same price, with one proposed obligation. Validators interpret the two clauses; contract code assigns the entitlement.

## Scope boundary

- **Contract:** party checks, frozen-term confirmation, price equality, deadline checks, entitlement reservation, semantic verdict consensus, assignment, recovery, and history.
- **Validators:** compare the promised action and performance window in the two clauses, including whether the incumbent promises the required outcome rather than a weaker acknowledgement.
- **Client/operator:** chooses the unique test entitlement, names the parties, provides the clauses and expiry, reads the terms hash, submits calls, and indexes events.
- **Excluded:** frontend, token, escrow, payments, fees, or real-world asset transfer.

Prices are bounded integer demo units (`1..1,000,000,000,000`), not GEN or a monetary representation.

## State flow

1. `create_offer(...)` reserves an unassigned entitlement and returns a monotonically increasing offer ID. Seller, incumbent, and outside bidder must be three distinct EVM addresses. Another live offer for the same entitlement is rejected.
2. The outside bidder reads `get_offer(id)` / `get_terms_hash(id)` and calls `confirm_offer(id, expected_terms_hash)`. The contract checks the hash against the frozen seller, parties, entitlement, price, obligation, expiry, offer ID, and contract address.
3. Before expiry, the incumbent calls `exercise_offer(id, same_price, proposed_obligation)`. Equality with expiry is late. The submitted clause is frozen before adjudication. Expiry cannot finalize an offer once timely exercise has been recorded.
4. Anyone can call `adjudicate_offer(id)` once. The leader and every validator run the same blind review of the two frozen clauses and each returns `MATCH`, `NO_MATCH`, or `INSUFFICIENT`. Validators never see the leader's answer; code accepts the leader only when a validator's own verdict is identical. The leader's short reason is stored as non-binding rationale. Code alone selects and records the owner.
5. `MATCH` assigns the incumbent. `NO_MATCH` assigns the confirmed outside bidder. If no timely exercise occurs, anyone may finalize expiry: a confirmed outside bidder is assigned once; an unconfirmed offer closes without assignment.
6. `INSUFFICIENT` or an adjudication timeout closes the offer without a winner and releases the entitlement for a fresh offer. There is no clarification step: after exercise, no party can add text that the validators read, so the incumbent cannot rewrite its promise.

A closed offer ID remains readable but cannot alter an entitlement. Mutating calls require the offer to remain the active reservation; a newer offer makes older calls stale. Assigned entitlements cannot be offered again.

## Time and bounded recovery

The contract reads GenVM's deterministic transaction timestamp (`gl.message_raw["datetime"]`), not the operator's wall clock. Expiry is a Unix timestamp in whole seconds. Exercise requires `now < expires_at`; expiry finalization requires `now >= expires_at`. Thus a transaction at the exact boundary cannot exercise. The network sequences transactions; each execution uses its transaction timestamp, so the timestamp and consensus ordering resolve competing calls. This contract does not depend on a block number.

- Offer expiry: seller-chosen, at most 30 days from creation.
- Adjudication window: 30 minutes from recorded exercise.
- If adjudication does not finalize within its window, anyone may call `recover_stale_review`; the old offer is released with no winner. A delayed old review cannot assign after a newer offer becomes active.

These are demo bounds, not a legal or production SLA. If an LLM call fails or validators do not finalize, state remains recoverable after the timeout.

## Build, lint, schema, and direct tests

With Python 3.14 and the pinned dependencies in `requirements.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
genvm-lint check contracts/matchright.py
genvm-lint schema contracts/matchright.py --json
python -m pytest tests/direct -v -s
```

The generated ABI is [contracts/abi.json](contracts/abi.json). Direct tests use mocked leader judgments to exercise deterministic state transitions; they do not prove validator consensus. The live StudioNet demo is the consensus demonstration. The contract pins the documented `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` runner. The installed local linter reports a newer manager hash, but that SDK is not present in its offline cache; the pinned runner passes lint and schema validation.

## Network and evidence

The live demo uses the stable hosted `studionet` alias (chain ID 61999), after checking `genlayer network info`. The live StudioNet quote reported that consensus fees are enabled. Each signer needs enough test GEN for its fee deposit. Existing configured development accounts are used as distinct signers for the named seller, incumbent, and outside bidder.

See [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md) for call order and [docs/REVIEW_HANDOFF.md](docs/REVIEW_HANDOFF.md) for the independent review brief. See [the verification report](evidence/RESULTS.md) for the Explorer contract address, finalized transactions and state readbacks. No Portal form is submitted.
