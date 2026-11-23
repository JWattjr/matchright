# Independent review outcome

The independent review of the first deployment found two design gaps. Both were fixed in the current source and redeployed:

1. **Clarification could change the deal.** An incumbent could submit clarification text that validators read, for example redefining "acknowledge" as "restore". Only the prompt forbade new promises. The clarification step is removed: `INSUFFICIENT` now reopens the entitlement with no winner, and no party can add validator-visible text after exercise.
2. **Validators saw the leader's verdict.** The old validator prompt included the leader's label and reason, which invites anchoring. Validators now run the same blind clause review as the leader. Code accepts the leader only when a validator's own verdict is identical. The leader's reason is stored as non-binding rationale.

A third question, whether a queued review can interfere with recovery or a newer offer, needed no change. Every write calls `_require_current`, and a release gives the next offer a new ID, so a late or replayed adjudication reverts with `[STALE]`. The live run records one such rollback.

The source is LF-only, published at https://github.com/JWattjr/matchright, and the on-chain code matches commit `4b76a09` byte for byte. See [the verification report](../evidence/RESULTS.md).

## Remaining limitations

- Direct tests mock LLM output. Live consensus shows MATCH, NO_MATCH and confirmed expiry only.
- Whole-second transaction timestamps; exercise at exactly `expires_at` is late.
- Assignment is irreversible; there is no appeal path.
- Storage and the assignment-history scan grow with offers. This is a demo contract.
