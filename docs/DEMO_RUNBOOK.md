# StudioNet demo runbook

Use three distinct configured development signers. Set $cliEntry to the absolute path to dist/index.js from the official genlayer npm package version 0.40.0. Calling the Node entry directly on PowerShell preserves the quoted fee JSON. Check `network info` for `studionet`, chain 61999 and `https://studio.genlayer.com/api`. Check each signer's address, unlock status and faucet balance with `account list` and `account show --account NAME`. Keep all three addresses public and the keystores local.

Run from the MatchRight directory in PowerShell 7. Substitute your existing signer names.

```powershell
function Invoke-GL { & node $cliEntry @args }
Invoke-GL network info
Invoke-GL account list
Invoke-GL estimate-fees --json
```

Use the quote's distribution and feeValue for deployment. Save the actual transaction ID. Before proceeding, inspect its receipt and verify successful finalized execution and the resulting address.

```powershell
$quote = (Invoke-GL estimate-fees --json | Out-String) | ConvertFrom-Json
$fees = @{ distribution = $quote.distribution } | ConvertTo-Json -Depth 12 -Compress
Invoke-GL deploy --contract contracts/matchright.py --fees $fees --fee-value $quote.feeValue
Invoke-GL receipt $deployTx --wait-until finalized
Invoke-GL schema $contract
```

For each write, refresh the fee quote for that call with `estimate-fees ADDRESS METHOD --json --args ...` using its actual arguments and signer. Pass its distribution and feeValue to `write`. Check that the execution succeeded and record its finalized receipt. If a write returns an unknown outcome, inspect its receipt and the state first. Restore the original active CLI account after switching signers for the demo.

| Signer | Method | Arguments |
| --- | --- | --- |
| Seller | `create_offer` | A unique test entitlement ID, incumbent address, outsider address, 100, “restore service within two business days”, future Unix expiry |
| Outsider | `confirm_offer` | Offer ID and exact result of `get_terms_hash` |
| Incumbent | `exercise_offer` | Offer ID, 100 and the scenario's incumbent clause |
| Any | `adjudicate_offer` | Offer ID |
| Any | `finalize_expiry` | Offer ID, submitted after chain expiry |

Use one deployed contract. Create a separate entitlement for each scenario. Read its latest offer ID with `get_entitlement` and check frozen terms with `get_offer`. Pick an expiry with enough room for confirmation and exercise. For expiry, allow enough time to confirm, skip exercise and submit finalization once the timestamp is reached.

| Scenario | Incumbent clause | Expected assignment cause and owner |
| --- | --- | --- |
| Match | Return the service to working order within two business days | MATCH, incumbent |
| Different action | Acknowledge the ticket within two business days | NO_MATCH, outsider |
| Expiry | No exercise | EXPIRED_CONFIRMED_OUTSIDE, outsider |

```powershell
Invoke-GL account use $seller
$expiry = [DateTimeOffset]::UtcNow.AddMinutes(15).ToUnixTimeSeconds()
Invoke-GL write $contract create_offer --fees $fees --fee-value $quote.feeValue --args $entitlement $incumbentAddress $outsideAddress 100 'restore service within two business days' $expiry
Invoke-GL call $contract get_entitlement --args $entitlement
Invoke-GL call $contract get_terms_hash --args $offerId
Invoke-GL call $contract get_offer --args $offerId
Invoke-GL call $contract get_assignment_history --args $entitlement
```

Refresh `$quote` and `$fees` as described above before each write. The recorded live run used the network default fee quote for its writes. The PowerShell scenario script in scripts/Demo-MatchRight.ps1 captures the run with the original configured signers and evidence IDs. The table above can be run with other development signers and fresh entitlement IDs. Save `get_offer`, `get_entitlement` and `get_assignment_history` after each successful scenario, along with finalized transaction links. On the official Studio Explorer, open the exact deployed contract address and check the successful constructor and MatchRight calls. Record the address URL separately as **GenLayer Explorer Contract**.
