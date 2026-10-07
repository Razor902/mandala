# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — tests for the classroom chain and contract.
# ============================================================================
"""test_chain.py -- every claim below is checked, deterministically.

Run:  cd ~/workspace/mandala-chain && python3 test_chain.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chain import Chain, Block
from mandala import MandalaContract, ContractError, CAP

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[ok] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


T0 = 1_700_000_000.0  # fixed classroom time: everything below is deterministic


def fresh_chain():
    return Chain(difficulty=1)  # difficulty 1: seals fast, still real sealing


# -- chain -------------------------------------------------------------------

c = fresh_chain()
check("genesis block exists at index 0", c.blocks[0].index == 0)
ok, _ = c.verify_chain()
check("fresh chain verifies", ok)

b = c.add_block([{"type": "note", "text": "page one"}], timestamp=T0)
check("mined block links to previous hash",
      b.previous_hash == c.blocks[-2].compute_hash())
check("mined block meets difficulty", b.compute_hash().startswith("0"))
ok, _ = c.verify_chain()
check("chain still verifies after mining", ok)

# tamper: rewrite history on page 1
c.blocks[1].transactions = [{"type": "note", "text": "forged!"}]
ok, reason = c.verify_chain()
check("tampering is detected", not ok)

# persistence round-trip on an honest chain
c2 = fresh_chain()
c2.add_block([{"type": "note", "text": "keep me"}], timestamp=T0)
c2.save("/tmp/mandala-chain-test.json")
c3 = Chain.load("/tmp/mandala-chain-test.json")
ok, _ = c3.verify_chain()
check("save/load round-trip verifies", ok and len(c3.blocks) == len(c2.blocks))

# -- contract ------------------------------------------------------------------

now = [T0]
m = MandalaContract(minter="curtis", clock=lambda: now[0])

m.mint("curtis", 29_000, by="curtis")
check("mint credits the minter", m.balances_of("curtis")["total"] == 29_000)
check("mint raises supply", m.totals()["supply"] == 29_000)

try:
    m.mint("mallory", 10, by="mallory")
    check("non-minter mint refused", False)
except ContractError:
    check("non-minter mint refused", True)

try:
    m.mint("curtis", CAP, by="curtis")  # 29_000 + 1_000_000 > CAP
    check("cap enforced on mint", False)
except ContractError:
    check("cap enforced on mint", True)

m.mint("curtis", CAP - 29_000, by="curtis")  # fill exactly to the cap
check("mint to exactly the cap works", m.totals()["supply"] == CAP)
try:
    m.mint("curtis", 1, by="curtis")
    check("one over the cap refused", False)
except ContractError:
    check("one over the cap refused", True)

m2 = MandalaContract(minter="curtis", clock=lambda: now[0])
m2.mint("curtis", 1_000, by="curtis")
m2.transfer("curtis", "maddie", 400)
check("transfer moves funds",
      m2.balances_of("curtis")["unlocked"] == 600
      and m2.balances_of("maddie")["unlocked"] == 400)

try:
    m2.transfer("curtis", "maddie", 10_000)  # more than held
    check("overspend refused (no double-spend)", False)
except ContractError:
    check("overspend refused (no double-spend)", True)

try:
    m2.transfer("curtis", "maddie", -5)
    check("negative amount refused", False)
except ContractError:
    check("negative amount refused", True)

try:
    m2.transfer("curtis", "maddie", 0)
    check("zero amount refused", False)
except ContractError:
    check("zero amount refused", True)

m2.burn("curtis", 100)
check("burn shrinks supply and balance",
      m2.totals()["supply"] == 900 and m2.balances_of("curtis")["unlocked"] == 500)

m2.lock("curtis", 200, 12)
bal = m2.balances_of("curtis")
check("lock moves funds to locked", bal["unlocked"] == 300 and bal["locked"] == 200)

try:
    m2.transfer("curtis", "maddie", 400)  # only 300 unlocked
    check("locked funds cannot move", False)
except ContractError:
    check("locked funds cannot move", True)

try:
    m2.lock("curtis", 50, 7)  # not a preset
    check("bad lock length refused", False)
except ContractError:
    check("bad lock length refused", True)

released = m2.release_matured(now=T0)  # nothing matured yet
check("immature locks stay locked", released == 0)
now[0] = T0 + 13 * 7 * 24 * 3600
released = m2.release_matured()
check("matured locks release", released == 200
      and m2.balances_of("curtis")["unlocked"] == 500)

# contract + chain together: every action lands on the public notebook
chain4 = fresh_chain()
now4 = [T0]
m4 = MandalaContract(minter="curtis", chain=chain4, clock=lambda: now4[0])
m4.mint("curtis", 5_000, by="curtis")
m4.transfer("curtis", "rayn", 500)
ok, _ = chain4.verify_chain()
types = [tx["type"] for blk in chain4.blocks for tx in blk.transactions]
check("contract actions recorded on chain and chain verifies",
      ok and "mint" in types and "transfer" in types)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
