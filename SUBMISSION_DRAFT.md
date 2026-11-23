# Submission draft (not submitted)

## Note (under 1,000 characters)

MatchRight is an on-chain right of first refusal. A seller freezes an outside offer: price, one service obligation and an expiry. The outside bidder confirms the exact terms hash. Before expiry, only the named incumbent can exercise, at the exact price, with its own obligation. Validators then decide one thing: does the incumbent's clause promise the same outcome within the same time as the outsider's? Each validator judges blind and must reach the leader's exact verdict. Code assigns the entitlement: MATCH to the incumbent, NO_MATCH to the outsider, and a confirmed offer that is not exercised goes to the outsider at expiry. INSUFFICIENT or a stalled review reopens it with no winner. No text can be added after exercise. Live on StudioNet: MATCH, NO_MATCH, confirmed expiry and one expected stale rollback, all finalized. Units are synthetic.

## Evidence entries

1. **GenLayer Explorer Contract (StudioNet):** https://explorer-studio.genlayer.com/address/0x62F1DD6fBa8f10d1151B8d46878E4dD4158Fdb2c
2. **Source repository:** https://github.com/JWattjr/matchright (deployed commit `4b76a0914498e25240d83a3ccab8ce32ac2a2180`; on-chain code SHA-256 matches)
3. **Verification report:** https://github.com/JWattjr/matchright/blob/main/evidence/RESULTS.md
4. **MATCH adjudication:** https://explorer-studio.genlayer.com/tx/0xbab9a498aa2d11273c52f4ab948b3bd05cf6f5f4d4aadd15073baf7ca85390f7
5. **NO_MATCH adjudication:** https://explorer-studio.genlayer.com/tx/0x488b548827f06a1366228585c67a0a4f1310a34a5a57a94b040416490bd114fd
6. **Confirmed expiry:** https://explorer-studio.genlayer.com/tx/0x1dc6bd9f935ce8205e0f806cb3a9e4c62ebb26ace904c732571f85294a3007d8

## Comparison with the author's same-week projects

| Project | What validators judge | What code does with it |
|---|---|---|
| recusal | Whether disclosed conduct meets a frozen grant policy | Applies the date rule and the ballot roster |
| quorum-of-sources | How many distinct first-hand origins a record documents | Counts against a quorum |
| **matchright** | Whether the incumbent's clause equals the outsider's in action and time | Assigns to incumbent or outsider; confirmed expiry defaults to the outsider |

The distinct part is the right-of-first-refusal protocol around the judgment: outsider-confirmed frozen terms, exact-price exercise, a strict deadline and an outsider default. The judgment itself is a single label that code turns into an owner.

## This does not prove

Semantic correctness for all clause wording, adversarial validators, independent parties (one operator holds all three keys), `INSUFFICIENT` or stale recovery on StudioNet (direct tests only), or any real asset transfer. No Portal submission or score is claimed.
