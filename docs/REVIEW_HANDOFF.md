# Independent review handoff

Please review the implementation and evidence independently before treating MatchRight as submission-ready. This is a demo contract for a test entitlement only; it does not transfer or encumber a real asset, funds, token, or payment.

## Start here

1. `contracts/matchright.py`: inspect clause judgment/validator prompts, state transitions, and assignment invariants.
2. `tests/direct/test_matchright.py`: inspect boundary, authorization, duplicate, no-assignment, and recovery coverage. These tests mock the leader output.
3. `contracts/abi.json` and `README.md`: inspect public interface and documented timing rules.
4. `evidence/RESULTS.md`, the three scenario logs and `evidence/transactions.json`: inspect finalized network receipts and post-state reads. Explorer address evidence must be a separate entry labeled `GenLayer Explorer Contract` and verified against the `studionet` deployment.

## Invariants to challenge

- One active offer per entitlement; one permanent owner after assignment.
- Seller, incumbent, and outside bidder are distinct. The outside bidder alone confirms the exact frozen terms hash. Only the incumbent can exercise at the exact price.
- Exercise is accepted only when deterministic transaction time is strictly earlier than expiry. Once recorded, the outside bidder cannot leapfrog while validators deliberate.
- Validators independently assess both frozen clauses, especially action and time to perform, and validate the leader's decision and reason. Only contract code assigns.
- `INSUFFICIENT` does not award either side. One clarification and one second review are bounded. Stale or unresolved reviews can release the entitlement; an old offer cannot affect a newer active offer.
- Unconfirmed expiry assigns nobody; confirmed expiry without exercise assigns the outsider once.

## Review questions

- Does the validator prompt adequately test the promised action and time window, and is the leader's rationale validation strong enough against adversarial or ambiguous clause text?
- Is one clarification enough, and does the prompt reliably reject a clarification that tries to add a new promise? The contract limits clarification to explanatory text but relies on validators to ignore any newly asserted undertaking.
- Are whole-second transaction timestamps and strict equality at expiry appropriate for the selected network ordering?
- Can a timed-out pending judgment ever be replayed against the new offer? Confirm the active-offer guard under actual transaction re-execution.
- Are status names, global assignment history scan, storage growth, and irreversible assignment acceptable for a demo?

## Known limitations

- Direct tests run leader-only mocked judgments. Only the live consensus calls demonstrate validator behavior, and they do not prove semantic correctness for all wording.
- Clarification changes interpretation context only; it does not change the frozen outside or incumbent clause. The validator is instructed not to treat it as a new promise.
- After the adjudication window, recovery releases the entitlement without choosing a party if the network executes the recovery call against an unresolved offer. A transaction stuck in the network queue can delay later calls. The live demo does not establish a maximum network queue delay.
- Assignment is irreversible in this prototype; no administrator override or appeal path exists.
- On-chain strings and assignment history grow with offers. This is a small demo contract, not a high-volume registry.
- The source pins the currently documented GenVM runner hash. Local linter output includes an advisory for a newer manager hash not available in its cache; record the exact lint output in the results.

## Live outcomes

See [the verification report](../evidence/RESULTS.md) for finalized receipts and state reads. Inspect the validator prompt for anchoring on the leader proposal, and test whether adversarial clarification can alter the action or deadline. Review network ordering separately from the contract deadline, especially a pending adjudication racing recovery and a fresh offer.
