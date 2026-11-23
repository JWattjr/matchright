param([Parameter(Mandatory)][string]$Contract,[ValidateSet('ExpirySetup','Expiry','Match','NoMatch','Insufficient')][string]$Scenario,[string]$Cli='genlayer.cmd')
$ErrorActionPreference='Stop'
function Invoke-MatchCli {
    $out = if($Cli.EndsWith('.js')) { & node $Cli @args } else { & $Cli @args }
    if($LASTEXITCODE -ne 0){ throw "CLI failed on $($args[0]). Check the receipt and state before repeating any write." }
    return ($out | Out-String)
}
$seller='moment-grid-studionet'
$outside='portal-five-release'
$incumbent='footnote-independent-studionet'
$outsideAddress='0x2c8eb5db1105a85be66badafed88d10cf393cdd8'
$incumbentAddress='0xbc1a363b1427531fcb05d03ddf4d34e729011186'
$network=Invoke-MatchCli network info
if($network -notmatch "chainId: '61999'" -or $network -notmatch "alias: 'studionet'"){throw 'Expected StudioNet chain 61999.'}
$accounts=Invoke-MatchCli account list
$original=[regex]::Match($accounts,'(?m)^\*\s+(\S+)').Groups[1].Value
if(!$original){throw 'Cannot identify the original signer.'}
if($accounts -notmatch [regex]::Escape("$outside $outsideAddress") -or $accounts -notmatch [regex]::Escape("$incumbent $incumbentAddress")){throw 'Unexpected actor addresses.'}
$quote=(Invoke-MatchCli estimate-fees --json | ConvertFrom-Json)
if([decimal]$quote.feeValue -le 0 -or [decimal]$quote.feeValue -gt 200000000000000000){throw 'Unexpected fee quote.'}
$fee=@{distribution=$quote.distribution} | ConvertTo-Json -Depth 12 -Compress
function Write-OfferMethod($method,[object[]]$values){
    $raw=Invoke-MatchCli write $Contract $method --fees $fee --fee-value $quote.feeValue --args @values
    $id=[regex]::Match($raw,'Write Transaction Hash:\s*(0x[a-fA-F0-9]{64})').Groups[1].Value
    if(!$id){throw "No transaction ID for $method. Inspect state before retrying."}
    Write-Host "$method $id"
    if($raw -notmatch "consensusStatus: '(ACCEPTED|FINALIZED)'" -or $raw -match "execution_result_name: '(ERROR|VM_ERROR|FAILURE)'"){throw "Check execution of $id before continuing."}
}
$entitlement= switch($Scenario){'ExpirySetup'{'matchright-live-expiry-01'} 'Expiry'{'matchright-live-expiry-01'} 'Match'{'matchright-live-match-01'} 'NoMatch'{'matchright-live-no-match-01'} 'Insufficient'{'matchright-live-insufficient-01'}}
try{
    $null=Invoke-MatchCli account use $seller
    if($Scenario -eq 'Expiry'){
        $ent=Invoke-MatchCli call $Contract get_entitlement --args $entitlement
        $id=[long][regex]::Match($ent,'latest_offer_id:\s*(\d+)').Groups[1].Value
        $offer=Invoke-MatchCli call $Contract get_offer --args $id
        if($offer -notmatch "status: 'CONFIRMED'" -or $offer -notmatch [regex]::Escape($entitlement)){throw 'Expected the existing confirmed expiry offer.'}
        $expires=[long][regex]::Match($offer,'expires_at:\s*(\d+)').Groups[1].Value
        if($expires -le 0 -or [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -lt $expires){throw "The expiry boundary has not passed: $expires"}
        Write-OfferMethod finalize_expiry @($id)
        $cause='EXPIRED_CONFIRMED_OUTSIDE'
        $winner=$outsideAddress
    } else {
        $prior=Invoke-MatchCli call $Contract get_entitlement --args $entitlement
        if($prior -notmatch 'latest_offer_id: 0'){throw 'The scenario already has an offer. Inspect it before proceeding.'}
        $expires=[DateTimeOffset]::UtcNow.AddMinutes($(if($Scenario -eq 'ExpirySetup'){6}else{15})).ToUnixTimeSeconds()
        Write-OfferMethod create_offer @($entitlement,$incumbentAddress,$outsideAddress,100,'restore service within two business days',$expires)
        $ent=Invoke-MatchCli call $Contract get_entitlement --args $entitlement
        $id=[long][regex]::Match($ent,'active_offer_id:\s*(\d+)').Groups[1].Value
        if($id -le 0){throw 'Offer was not reserved.'}
        $hash=[regex]::Match((Invoke-MatchCli call $Contract get_terms_hash --args $id),'sha256:[a-f0-9]{64}').Value
        if(!$hash){throw 'Terms hash unavailable.'}
        $null=Invoke-MatchCli account use $outside
        Write-OfferMethod confirm_offer @($id,$hash)
        if((Invoke-MatchCli call $Contract get_offer --args $id) -notmatch "status: 'CONFIRMED'"){throw 'Confirmation did not apply.'}
        if($Scenario -eq 'ExpirySetup'){ Write-Host "Expiry offer $id confirmed; expires_at $expires. Run -Scenario Expiry after that time."; return }
        $clause=if($Scenario -eq 'Match'){'Return the service to working order within two business days'}elseif($Scenario -eq 'Insufficient'){'Provide service soon'}else{'Acknowledge the ticket within two business days'}
        $cause=if($Scenario -eq 'Match'){'MATCH'}elseif($Scenario -eq 'Insufficient'){'NONE'}else{'NO_MATCH'}
        $winner=if($Scenario -eq 'Match'){$incumbentAddress}else{$outsideAddress}
        $null=Invoke-MatchCli account use $incumbent
        Write-OfferMethod exercise_offer @($id,100,$clause)
        if((Invoke-MatchCli call $Contract get_offer --args $id) -notmatch "status: 'AWAITING_ADJUDICATION'"){throw 'Exercise did not apply.'}
        $null=Invoke-MatchCli account use $seller
        Write-OfferMethod adjudicate_offer @($id)
    }
    $offer=Invoke-MatchCli call $Contract get_offer --args $id
    $state=Invoke-MatchCli call $Contract get_entitlement --args $entitlement
    $history=Invoke-MatchCli call $Contract get_assignment_history --args $entitlement
    Write-Host $offer
    Write-Host $state
    Write-Host $history
    if($Scenario -eq 'Insufficient'){ if($offer -notmatch "status: 'REOPENED_INSUFFICIENT'" -or $state -notmatch "state: 'AVAILABLE'" -or $history -match 'cause:'){throw 'INSUFFICIENT outcome not observed; record as not shown, do not retry.'}; return }
    if($offer -notmatch "assignment_cause: '$cause'" -or $state -notmatch "owner: '$winner'" -or $history -notmatch "cause: '$cause'"){throw 'Unexpected assignment. Read the receipt and investigate before continuing.'}
}finally{
    $null=Invoke-MatchCli account use $original
}

