# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for the mandala blockchain — every law the chain enforces."""

import copy

import pytest

from mandala_blockchain import (
    MandalaChain,
    InvalidTransaction,
    InvalidChain,
)

KEY = b"test-authority-key-for-pytest-only"


def fresh_chain():
    return MandalaChain(authority_id="curtis", authority_key=KEY)


def signed(chain, tx):
    return chain.sign_transaction(tx)


# ---------------------------------------------------------------- genesis
def test_genesis_is_valid_and_empty():
    chain = fresh_chain()
    assert chain.is_valid() is True
    assert chain.balances() == {"hand": {}, "vault": {}, "reserve": {}}


def test_genesis_documents_the_audit():
    memo = chain_genesis_memo()
    assert "audit" in memo.lower()
    assert "start from scratch" in memo.lower()


def chain_genesis_memo():
    return fresh_chain().blocks[0]["transactions"][0]["memo"]


def test_genesis_fabricates_no_amounts():
    for block in fresh_chain().blocks:
        for tx in block["transactions"]:
            assert "amount" not in tx or tx["type"] == "genesis"


# ---------------------------------------------------------------- Hand law
def test_prove_self_grants_exactly_one_mandala():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_prove_self("raylea")))
    chain.seal_block()
    assert chain.balances()["hand"]["raylea"] == 1


def test_prove_self_only_once_per_citizen():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_prove_self("raylea")))
    chain.seal_block()
    chain.add_transaction(signed(chain, MandalaChain.make_prove_self("raylea")))
    with pytest.raises(InvalidTransaction):
        chain.seal_block()


def test_hand_attest_records_showing_without_spending():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_prove_self("raylea")))
    chain.seal_block()
    before = chain.balances()["hand"]["raylea"]
    chain.add_transaction(MandalaChain.make_hand_attest("raylea", "valhalla-shop"))
    chain.seal_block()
    after = chain.balances()["hand"]["raylea"]
    assert before == after == 1  # shown, never spent
    assert chain.is_valid() is True


def test_hand_attest_rejected_without_mandala():
    chain = fresh_chain()
    chain.add_transaction(MandalaChain.make_hand_attest("stranger", "shop"))
    with pytest.raises(InvalidTransaction):
        chain.seal_block()


def test_unsigned_prove_self_rejected():
    chain = fresh_chain()
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(MandalaChain.make_prove_self("raylea"))


# ---------------------------------------------------------------- Vault law
def test_vault_growth_then_transfer():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 10, "multiplication-law growth event")))
    chain.seal_block()
    chain.add_transaction(MandalaChain.make_vault_transfer("curtis", "maddie", 4))
    chain.seal_block()
    balances = chain.balances()["vault"]
    assert balances["curtis"] == 6
    assert balances["maddie"] == 4


def test_double_spend_rejected():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 10, "growth")))
    chain.seal_block()
    chain.add_transaction(MandalaChain.make_vault_transfer("curtis", "maddie", 7))
    chain.add_transaction(MandalaChain.make_vault_transfer("curtis", "raylea", 7))
    with pytest.raises(InvalidTransaction):
        chain.seal_block()


def test_unsigned_vault_growth_rejected():
    chain = fresh_chain()
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(MandalaChain.make_vault_growth("curtis", 10, "x"))


def test_zero_or_negative_amount_rejected():
    chain = fresh_chain()
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(MandalaChain.make_vault_transfer("a", "b", 0))


# ---------------------------------------------------------------- Reserve law
def fund_reserve(chain, holder="curtis", amount=50):
    chain.add_transaction(signed(chain, MandalaChain.make_reserve_allocation(
        holder, amount, "authority reserve allocation")))
    chain.seal_block()
    return chain


def test_reserve_allocation_requires_signature():
    chain = fresh_chain()
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(
            MandalaChain.make_reserve_allocation("curtis", 50, "x"))


def test_reserve_allocation_funds_reserve():
    chain = fund_reserve(fresh_chain())
    assert chain.balances()["reserve"]["curtis"] == 50
    assert chain.is_valid() is True


def test_reserve_transfer_without_approval_flag_rejected():
    chain = fund_reserve(fresh_chain())
    tx = MandalaChain.make_reserve_transfer("curtis", "maddie", 5, approved=False)
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(tx)


def test_reserve_transfer_without_signature_rejected():
    chain = fund_reserve(fresh_chain())
    tx = MandalaChain.make_reserve_transfer("curtis", "maddie", 5, approved=True)
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(tx)  # approved but unsigned


def test_reserve_transfer_with_forged_signature_rejected():
    chain = fund_reserve(fresh_chain())
    tx = MandalaChain.make_reserve_transfer("curtis", "maddie", 5, approved=True)
    tx["signature"] = "0" * 64  # forged
    with pytest.raises(InvalidTransaction):
        chain.add_transaction(tx)


def test_reserve_transfer_approved_and_signed_moves_funds():
    chain = fund_reserve(fresh_chain())
    tx = signed(chain, MandalaChain.make_reserve_transfer(
        "curtis", "maddie", 20, approved=True, memo="by Curtis's word"))
    chain.add_transaction(tx)
    chain.seal_block()
    balances = chain.balances()["reserve"]
    assert balances["curtis"] == 30
    assert balances["maddie"] == 20
    assert chain.is_valid() is True


def test_reserve_transfer_insufficient_funds_rejected():
    chain = fund_reserve(fresh_chain(), amount=10)
    tx = signed(chain, MandalaChain.make_reserve_transfer(
        "curtis", "maddie", 50, approved=True))
    chain.add_transaction(tx)
    with pytest.raises(InvalidTransaction):
        chain.seal_block()


# ---------------------------------------------------------------- tamper
def test_tamper_with_block_breaks_validation():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 10, "growth")))
    chain.seal_block()
    chain.blocks[1]["transactions"][0]["amount"] = 9999  # tamper
    with pytest.raises(InvalidChain):
        chain.is_valid()


def test_tamper_with_prev_hash_breaks_validation():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 10, "growth")))
    chain.seal_block()
    chain.blocks[1]["prev_hash"] = "f" * 64
    with pytest.raises(InvalidChain):
        chain.is_valid()


def test_swapped_block_signature_breaks_validation():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 10, "growth")))
    chain.seal_block()
    chain.blocks[1]["block_signature"] = "a" * 64
    with pytest.raises(InvalidChain):
        chain.is_valid()


def test_deepcopy_chain_stays_valid():
    chain = fresh_chain()
    chain.add_transaction(signed(chain, MandalaChain.make_prove_self("raylea")))
    chain.seal_block()
    clone = copy.deepcopy(chain)
    assert clone.is_valid() is True
    assert clone.balances() == chain.balances()


def test_chain_survives_many_blocks():
    chain = fresh_chain()
    for citizen in ["a", "b", "c", "d", "e"]:
        chain.add_transaction(signed(chain, MandalaChain.make_prove_self(citizen)))
    chain.seal_block()
    chain.add_transaction(signed(chain, MandalaChain.make_vault_growth(
        "curtis", 50, "growth")))
    chain.seal_block()
    for i in range(5):
        chain.add_transaction(
            MandalaChain.make_vault_transfer("curtis", "a", 5, memo="round %d" % i))
    chain.seal_block()
    assert chain.is_valid() is True
    balances = chain.balances()
    assert balances["vault"]["curtis"] == 25
    assert balances["vault"]["a"] == 25
    assert all(balances["hand"][c] == 1 for c in ["a", "b", "c", "d", "e"])
