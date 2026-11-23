# MatchRight verification

## Local checks

- GenVM lint and SDK semantic validation passed. Extracted ABI has 8 writes, 4 views, and a constructor with no arguments.
- All 12 direct tests passed on Windows with Python 3.14.2 and genlayer-test 0.30.0rc2. The Windows shim is scoped to the test harness.
- Direct semantic results are mocked. The suite covers exercise one second before, at, and one second after expiry, late adjudication after timely exercise, confirmation and caller guards, exact price, duplicate assignment, unconfirmed expiry, unresolved adjudication recovery, and insufficient judgment recovery.
- Source SHA-256: `2406646bb59b9b40e8f6ed191ff2ea53bd1395af06ed3a08cb842b0fe26ae989`.
- The linter reported an advisory for a newer runner. The documented, pinned runner passed local checks and deployed successfully to StudioNet.

## Network

StudioNet chain 61999. The first deployment attempt using CLI 0.39.2 reverted before creating a contract. The EVM receipt showed status 0x0, a null contract address, and `FeesDistributionMissing`. The successful deployment used one live fee quote on CLI 0.40.0. The existing incumbent received 1 test GEN via the official Studio faucet RPC.

**GenLayer Explorer Contract** — [0x9288760e038b9E1505719C4844A792BEeCAb291F](https://explorer-studio.genlayer.com/address/0x9288760e038b9E1505719C4844A792BEeCAb291F). Opened and verified the exact address, constructor transaction, FINALIZED status, and SUCCESS result on the official Studio Explorer.

[Finalized deployment](https://explorer-studio.genlayer.com/tx/0x7fb1f87e0575c04f296ddab7a15dc8cdf325eed7c033e016de9a4a1fff95f0bf)

## Confirmed expiry

Offer 1, `matchright-live-expiry-01`, confirmed before expiry and had no exercise. It assigned once to the outside bidder `0x2c8eb5db1105a85be66badafed88d10cf393cdd8`. The state showed `ASSIGNED`, `EXPIRED_CONFIRMED_OUTSIDE`, no active offer and one assignment history entry. The `decision` field tracks semantic review and remains `PENDING` for expiry.

- [Create offer](https://explorer-studio.genlayer.com/tx/0xdcab57500a775935a7d4669bf5c612801259732fc2ea39ac589696811b3cffb0)
- [Confirm frozen offer](https://explorer-studio.genlayer.com/tx/0x39cb438c510c645e72948c42978cb426c9f9ab8bac7c5d6f899c78552946ac65)
- [Finalize expiry](https://explorer-studio.genlayer.com/tx/0x38c3f3d9940f0180ea35791146514cab95c4663ae54696e07d168c638bd3f276)
- [State readbacks](Expiry.log)


## MATCH

Offer 2 used the two equivalent restoration clauses at price 100. The finalized adjudication recorded `MATCH`. The live state and assignment history identify the incumbent, `0xbc1a363b1427531fcb05d03ddf4d34e729011186`, as the owner. The rationale identified the same restoration outcome and two business day deadline in both clauses.

- [Finalized MATCH adjudication](https://explorer-studio.genlayer.com/tx/0xba7a6a742036c148e3eaa59b116e0ad468748f63f69b0c7a33ab9086c4365f1d)
- [Receipt excerpt](Match-adjudication-receipt.txt)
- [State readbacks](Match.log)


## NO_MATCH

Offer 3 used an acknowledgment-only incumbent clause at the same price of 100. The finalized adjudication recorded `NO_MATCH` because acknowledging the ticket does not restore the service. The state and assignment history identify the outside bidder, `0x2c8eb5db1105a85be66badafed88d10cf393cdd8`, as the sole owner.

- [Finalized NO_MATCH adjudication](https://explorer-studio.genlayer.com/tx/0x0eb2113a557b7efca4dee8705a25ced1308731959aa4c81ba5afa2be75070919)
- [Receipt excerpt](NoMatch-adjudication-receipt.txt)
- [State readbacks](NoMatch.log)

[Complete transaction list](transactions.json) contains 12 finalized receipts across deployment and all three scenarios. Each records a majority agreement. The reported execution results can include individual validator errors alongside successful executions. The receipt excerpts and the resulting state distinguish the accepted outcome from those individual entries.

