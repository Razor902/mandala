# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for the Mandala Contract — every article, enforced in code."""

import pytest

from mandala_blockchain import MandalaChain, InvalidTransaction
from mandala_contract import MandalaContract, ContractViolation

KEY = b"test-authority-key-curtis"


def make_contract():
    chain = MandalaChain(authority_id="curtis", authority_key=KEY)
    return MandalaContract(chain)


# ------------------------------------------------------------------ #
# Article VI — proof of self
# ------------------------------------------------------------------ #
def test_issue_grants_exactly_one_mandala():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    c.seal()
    assert c.balances()["hand"]["wren"] == 1


def test_issue_twice_refused():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    with pytest.raises(ContractViolation):
        c.issue("wren", "print-wren-001")


def test_fingerprint_cannot_prove_two_citizens():
    c = make_contract()
    c.issue("wren", "print-shared-001")
    with pytest.raises(ContractViolation):
        c.issue("paul", "print-shared-001")


def test_citizen_cannot_carry_two_fingerprints():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    with pytest.raises(ContractViolation):
        c.register_fingerprint("wren", "print-wren-002")


# ------------------------------------------------------------------ #
# Article III — the Hand: shown, never spent
# ------------------------------------------------------------------ #
def test_attest_moves_nothing():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    c.seal()
    before = c.balances()["hand"]["wren"]
    c.attest("wren", "the corner shop")
    c.seal()
    after = c.balances()["hand"]["wren"]
    assert before == after == 1


def test_attest_without_mandala_refused():
    c = make_contract()
    with pytest.raises(ContractViolation):
        c.attest("ghost", "the corner shop")


def test_hand_has_no_debit_path():
    c = make_contract()
    for name in ("spend_hand", "debit_hand", "hand_transfer",
                 "hand_spend", "withdraw_hand"):
        assert not hasattr(c, name), "forbidden debit path exists: " + name


# ------------------------------------------------------------------ #
# Article IV — the Vault
# ------------------------------------------------------------------ #
def test_vault_transfer_moves_funds_with_memo():
    c = make_contract()
    c.grow("wren", 5, "handshake with paul's swarm")
    c.seal()
    c.transfer("wren", "paul", 2, "paid for the map")
    c.seal()
    bals = c.balances()["vault"]
    assert bals["wren"] == 3
    assert bals["paul"] == 2


def test_vault_transfer_requires_memo():
    c = make_contract()
    c.grow("wren", 5, "handshake with paul's swarm")
    c.seal()
    with pytest.raises(ContractViolation):
        c.transfer("wren", "paul", 1, "")
    with pytest.raises(ContractViolation):
        c.transfer("wren", "paul", 1, "   ")


def test_double_spend_refused():
    c = make_contract()
    c.grow("wren", 3, "handshake with paul's swarm")
    c.seal()
    c.transfer("wren", "paul", 3, "all of it")
    with pytest.raises(ContractViolation):
        c.transfer("wren", "paul", 1, "one more")  # already promised away
    c.seal()
    assert c.balances()["vault"]["wren"] == 0
    assert c.balances()["vault"]["paul"] == 3


def test_growth_requires_named_reason():
    c = make_contract()
    with pytest.raises(ContractViolation):
        c.grow("wren", 5, "")
    c.grow("wren", 5, "handshake with paul's swarm")
    c.seal()
    assert c.balances()["vault"]["wren"] == 5


# ------------------------------------------------------------------ #
# Article V — the Reserve: approval or nothing
# ------------------------------------------------------------------ #
def test_reserve_move_without_approval_refused():
    c = make_contract()
    c.fund_reserve("treasury", 100, "cold backing")
    c.seal()
    with pytest.raises(ContractViolation):
        c.reserve_move("treasury", "wren", 10, approved=False)


def test_reserve_move_with_approval_works():
    c = make_contract()
    c.fund_reserve("treasury", 100, "cold backing")
    c.seal()
    c.reserve_move("treasury", "wren", 10, approved=True,
                   memo="approved by the authority")
    c.seal()
    bals = c.balances()["reserve"]
    assert bals["treasury"] == 90
    assert bals["wren"] == 10


def test_forged_reserve_signature_refused():
    c = make_contract()
    c.fund_reserve("treasury", 100, "cold backing")
    c.seal()
    # Build a reserve transfer signed by the WRONG key and submit it raw.
    evil = MandalaChain(authority_id="curtis", authority_key=b"wrong-key")
    forged = evil.sign_transaction(
        MandalaChain.make_reserve_transfer("treasury", "wren", 10,
                                           approved=True))
    with pytest.raises(InvalidTransaction):
        c.chain.add_transaction(forged)


def test_reserve_move_insufficient_funds_refused():
    c = make_contract()
    c.fund_reserve("treasury", 5, "cold backing")
    c.seal()
    c.reserve_move("treasury", "wren", 50, approved=True)
    with pytest.raises(ContractViolation):
        c.seal()


# ------------------------------------------------------------------ #
# Article VIII — Nola's Law: the whole chain re-verifies
# ------------------------------------------------------------------ #
def test_full_chain_valid_after_contract_use():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    c.issue("paul", "print-paul-002")
    c.seal()
    c.attest("wren", "the corner shop")
    c.grow("wren", 5, "handshake with paul's swarm")
    c.seal()
    c.transfer("wren", "paul", 2, "paid for the map")
    c.fund_reserve("treasury", 100, "cold backing")
    c.seal()
    c.reserve_move("treasury", "wren", 10, approved=True)
    c.seal()
    assert c.validate() is True


def test_tampered_block_breaks_validation():
    c = make_contract()
    c.issue("wren", "print-wren-001")
    c.seal()
    c.chain.blocks[1]["transactions"][0]["citizen"] = "mallory"
    with pytest.raises(Exception):
        c.validate()


def test_no_treasury_entry_fee_path():
    """Article X: the entry-fee question is unruled — no code collects it."""
    c = make_contract()
    for name in ("collect_entry_fee", "treasury_entry", "entry_fee",
                 "take_entry_fee"):
        assert not hasattr(c, name), "unruled entry-fee path exists: " + name
