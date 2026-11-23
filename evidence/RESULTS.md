# MatchRight verification (current release)

## Source identity

- Public repository: https://github.com/JWattjr/matchright
- Deployed source commit: `4b76a0914498e25240d83a3ccab8ce32ac2a2180`, file `contracts/matchright.py`, 17,442 bytes, LF line endings.
- SHA-256 `b633052ddf8b99b325c0360eddb04a910ebb93cbd354e2cb3947b1088e97bb1` is identical for the local file, the raw GitHub file at that commit, and the on-chain code read back with `gen_getContractCode`.

## Local checks

- GenVM lint and SDK validation passed (6 writes, 4 views, no constructor arguments). The linter's I200 notice about a newer runner is advisory; the source pins the documented runner `1jb45aa8…`.
- 13 direct tests pass. They use mocked LLM output for state transitions. One test runs the captured validator: it accepts an agreeing leader and rejects a forged verdict, missing fields, an unknown label and a leader error.

## Network

StudioNet, chain 61999. CLI `genlayer` 0.40.0-rc.3.

**GenLayer Explorer Contract:** https://explorer-studio.genlayer.com/address/0x62F1DD6fBa8f10d1151B8d46878E4dD4158Fdb2c

All 13 transactions are FINALIZED with MAJORITY_AGREE. 12 have leader execution SUCCESS. One is an expected rollback. Hashes, votes and Explorer links are in [transactions.json](transactions.json).

| Scenario | Offer | Result | Key transaction |
|---|---|---|---|
| MATCH | 2, `matchright-live-match-01` | Incumbent clause "Return the service to working order within two business days" → `MATCH`, owner incumbent `0xbc1a…1186` | [adjudicate](https://explorer-studio.genlayer.com/tx/0xbab9a498aa2d11273c52f4ab948b3bd05cf6f5f4d4aadd15073baf7ca85390f7) |
| NO_MATCH | 3, `matchright-live-no-match-01` | Incumbent clause "Acknowledge the ticket within two business days" → `NO_MATCH`, owner outside bidder `0x2c8e…cdd8` | [adjudicate](https://explorer-studio.genlayer.com/tx/0x488b548827f06a1366228585c67a0a4f1310a34a5a57a94b040416490bd114fd) |
| Confirmed expiry | 1, `matchright-live-expiry-01` | Confirmed, never exercised → `EXPIRED_CONFIRMED_OUTSIDE`, owner outside bidder | [finalize_expiry](https://explorer-studio.genlayer.com/tx/0x1dc6bd9f935ce8205e0f806cb3a9e4c62ebb26ace904c732571f85294a3007d8) |
| Expected rollback | 3 | Second `adjudicate_offer` on an assigned offer → leader ERROR `[STALE] offer no longer reserves this entitlement`; state unchanged | [rollback](https://explorer-studio.genlayer.com/tx/0x702a4517a4c347c17a93317d0ade16a2de02b16780657d707f3152c76d4d331e) |

Each adjudication is decided by validators running the same blind clause review; the leader's verdict is accepted only when a validator's own verdict is identical. The stored `decision_reason` is the leader's rationale and is not part of consensus. State readbacks after each scenario are in `Match.log`, `NoMatch.log`, `Expiry.log` and `ExpirySetup.log`.

## Not demonstrated live

`INSUFFICIENT` and stale-review recovery are covered only by direct tests. All three signers are development accounts of one operator. Entitlements and prices are synthetic demo units. The earlier deployment `0x9288760e…291F` ran a superseded source and is kept in `superseded-0x9288760e/` as history only.
