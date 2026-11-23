import json
from datetime import datetime, timezone

import pytest

BASE = "2024-06-01T12:00:00Z"
BASE_EPOCH = int(datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())


def _as_address(value):
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    return str(value).lower()

def _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, entitlement="test-entitlement-01", expiry=None, confirm=True):
    direct_vm.warp(BASE)
    direct_vm.sender = direct_owner
    contract = direct_deploy("contracts/matchright.py")
    direct_vm.sender = direct_owner
    offer_id = contract.create_offer(
        entitlement,
        direct_alice,
        direct_bob,
        100,
        "restore service within two business days",
        expiry or BASE_EPOCH + 600,
    )
    if confirm:
        terms_hash = contract.get_terms_hash(offer_id)
        direct_vm.sender = direct_bob
        contract.confirm_offer(offer_id, terms_hash)
    return contract, offer_id


def _exercise(direct_vm, contract, offer_id, direct_alice, price=100, clause="Return the service to working order within two business days"):
    direct_vm.sender = direct_alice
    contract.exercise_offer(offer_id, price, clause)


def _mock_verdict(direct_vm, verdict, reason):
    direct_vm.mock_llm(
        r".*MATCHRIGHT CLAUSE REVIEW.*",
        json.dumps({"verdict": verdict, "reason": reason}),
    )


def test_match_awards_incumbent_after_expiry_when_exercise_was_timely(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, expiry=BASE_EPOCH + 60)
    direct_vm.warp("2024-06-01T12:00:59Z")
    _exercise(direct_vm, contract, offer_id, direct_alice)
    direct_vm.warp("2024-06-01T12:01:30Z")
    _mock_verdict(direct_vm, "MATCH", "Both clauses require restoring service within the same two-business-day window.")
    direct_vm.sender = direct_charlie
    result = contract.adjudicate_offer(offer_id)
    assert result["status"] == "ASSIGNED"
    assert result["decision"] == "MATCH"
    assert result["winner"].lower() == _as_address(direct_alice)
    assert contract.get_entitlement("test-entitlement-01")["owner"].lower() == _as_address(direct_alice)
    assert contract.get_assignment_history("test-entitlement-01")[0]["cause"] == "MATCH"


def test_acknowledging_ticket_is_no_match_and_outsider_wins(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    _exercise(direct_vm, contract, offer_id, direct_alice, clause="Acknowledge the ticket within two business days")
    _mock_verdict(direct_vm, "NO_MATCH", "Acknowledging a ticket does not restore service as the outside clause requires.")
    direct_vm.sender = direct_charlie
    result = contract.adjudicate_offer(offer_id)
    assert result["decision"] == "NO_MATCH"
    assert result["status"] == "ASSIGNED"
    assert result["winner"].lower() == _as_address(direct_bob)
    assert len(contract.get_assignment_history("test-entitlement-01")) == 1


@pytest.mark.parametrize(("offset", "accepted"), [(-1, True), (0, False), (1, False)])
def test_exercise_is_strictly_before_expiry(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, offset, accepted):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, expiry=BASE_EPOCH + 60)
    point = datetime.fromtimestamp(BASE_EPOCH + 60 + offset, timezone.utc)
    direct_vm.warp(point.strftime("%Y-%m-%dT%H:%M:%SZ"))
    direct_vm.sender = direct_alice
    if accepted:
        contract.exercise_offer(offer_id, 100, "restore service within two business days")
        assert contract.get_offer(offer_id)["status"] == "AWAITING_ADJUDICATION"
    else:
        with direct_vm.expect_revert("strictly before expiry"):
            contract.exercise_offer(offer_id, 100, "restore service within two business days")
        assert contract.get_offer(offer_id)["status"] == "CONFIRMED"


def test_unconfirmed_expiry_releases_without_assignment(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, expiry=BASE_EPOCH + 60, confirm=False)
    direct_vm.warp("2024-06-01T12:01:00Z")
    direct_vm.sender = direct_charlie
    contract.finalize_expiry(offer_id)
    assert contract.get_offer(offer_id)["status"] == "EXPIRED_UNCONFIRMED"
    assert contract.get_entitlement("test-entitlement-01")["state"] == "AVAILABLE"
    assert contract.get_entitlement("test-entitlement-01")["owner"] == ""
    assert contract.get_assignment_history("test-entitlement-01") == []


def test_only_outsider_can_confirm_exact_frozen_hash_and_confirmation_is_once(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, confirm=False)
    terms_hash = contract.get_terms_hash(offer_id)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("only the named outside bidder"):
        contract.confirm_offer(offer_id, terms_hash)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("frozen terms hash"):
        contract.confirm_offer(offer_id, "sha256:" + "0" * 64)
    contract.confirm_offer(offer_id, terms_hash)
    with direct_vm.expect_revert("offer status must be AWAITING_CONFIRMATION"):
        contract.confirm_offer(offer_id, terms_hash)


def test_wrong_exerciser_and_price_are_rejected(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("only the named incumbent"):
        contract.exercise_offer(offer_id, 100, "restore service within two business days")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("exact outside price"):
        contract.exercise_offer(offer_id, 99, "restore service within two business days")
    assert contract.get_offer(offer_id)["status"] == "CONFIRMED"


def test_active_reservation_blocks_concurrent_offer_and_assigned_entitlement_reuse(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("already has an active offer"):
        contract.create_offer("test-entitlement-01", direct_charlie, direct_bob, 100, "restore service within two business days", BASE_EPOCH + 700)
    direct_vm.warp("2024-06-01T12:10:00Z")
    direct_vm.sender = direct_charlie
    contract.finalize_expiry(offer_id)
    assert contract.get_entitlement("test-entitlement-01")["owner"].lower() == _as_address(direct_bob)
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("already assigned"):
        contract.create_offer("test-entitlement-01", direct_alice, direct_charlie, 100, "restore service within two business days", BASE_EPOCH + 800)
    with direct_vm.expect_revert("no longer reserves"):
        contract.finalize_expiry(offer_id)
    assert len(contract.get_assignment_history("test-entitlement-01")) == 1


def test_insufficient_review_reopens_immediately_with_no_clarification_path(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    _exercise(direct_vm, contract, offer_id, direct_alice, clause="Provide service soon")
    _mock_verdict(direct_vm, "INSUFFICIENT", "The promised action and its performance window are unclear.")
    direct_vm.sender = direct_charlie
    result = contract.adjudicate_offer(offer_id)
    assert result["status"] == "REOPENED_INSUFFICIENT"
    assert not hasattr(contract, "submit_clarification")
    assert "clarification" not in contract.get_offer(offer_id)
    entitlement = contract.get_entitlement("test-entitlement-01")
    assert entitlement["state"] == "AVAILABLE"
    assert entitlement["owner"] == ""
    assert contract.get_assignment_history("test-entitlement-01") == []
    direct_vm.sender = direct_owner
    next_id = contract.create_offer("test-entitlement-01", direct_charlie, direct_bob, 120, "restore service within one business day", BASE_EPOCH + 3600)
    assert int(next_id) > int(offer_id)
    with direct_vm.expect_revert("no longer reserves"):
        contract.adjudicate_offer(offer_id)


def test_stale_review_timeout_releases_reservation_and_old_offer_cannot_finalize(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    _exercise(direct_vm, contract, offer_id, direct_alice)
    direct_vm.warp("2024-06-01T12:30:00Z")
    direct_vm.sender = direct_charlie
    contract.recover_stale_review(offer_id)
    assert contract.get_offer(offer_id)["status"] == "REOPENED_TIMEOUT"
    direct_vm.sender = direct_owner
    next_id = contract.create_offer("test-entitlement-01", direct_charlie, direct_bob, 100, "restore service within two business days", BASE_EPOCH + 7200)
    assert int(next_id) > int(offer_id)
    with direct_vm.expect_revert("no longer reserves"):
        contract.adjudicate_offer(offer_id)
    assert contract.get_entitlement("test-entitlement-01")["active_offer_id"] == int(next_id)


def test_blind_validator_rejects_forged_or_malformed_leader_and_accepts_agreement(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    _exercise(direct_vm, contract, offer_id, direct_alice, clause="Acknowledge the ticket within two business days")
    _mock_verdict(direct_vm, "NO_MATCH", "Acknowledging a ticket does not restore service.")
    direct_vm.sender = direct_charlie
    contract.adjudicate_offer(offer_id)
    assert direct_vm.run_validator() is True
    forged = {"verdict": "MATCH", "reason": "Both clauses promise restoration within two business days."}
    assert direct_vm.run_validator(leader_result=forged) is False
    assert direct_vm.run_validator(leader_result={"verdict": "MATCH"}) is False
    assert direct_vm.run_validator(leader_result={"verdict": "WIN", "reason": "invented label for the leader"}) is False
    assert direct_vm.run_validator(leader_error="leader failed") is False


def test_unknown_offer_id_and_duplicate_exercise_are_guarded(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    contract, offer_id = _offer(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob)
    with direct_vm.expect_revert("offer does not exist"):
        contract.get_offer(999)
    _exercise(direct_vm, contract, offer_id, direct_alice)
    with direct_vm.expect_revert("offer status must be CONFIRMED"):
        contract.exercise_offer(offer_id, 100, "restore service within two business days")




