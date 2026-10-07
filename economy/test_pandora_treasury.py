# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY -- tests for the classroom treasury. Deterministic:
# a fake clock, fixed amounts, no network, no real funds anywhere.
# ============================================================================
"""Tests for pandora_treasury.py. Run:  python3 test_pandora_treasury.py"""

from pandora_treasury import PandoraTreasury, FakeClock, TREASURY
from mandala import ContractError

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[ok ] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def fresh():
    """A treasury on a fake clock, deterministic every run."""
    clock = FakeClock()
    return PandoraTreasury(clock=clock), clock


# 1 -- session payment moves patron -> treasury, books updated ---------------
pt, clock = fresh()
pt.fund_patron("amy", 500)
fee = pt.run_session("amy", sessions=3)
check("session fee is price x sessions", fee == 30)
check("patron debited", pt.contract.balances_of("amy")["unlocked"] == 470)
check("treasury credited", pt.contract.balances_of(TREASURY)["unlocked"] == 30)
check("sessions counted", pt.sessions_run == 3)
check("revenue counted", pt.revenue_total == 30)

# 2 -- the split adds up: liquid + locked + burned == revenue -----------------
split = pt.split_revenue()
b = pt.books()
check("locked 50% of 30", split["locked"] == 15)
check("burned 20% of 30", split["burned"] == 6)
check("liquid left 9", split["liquid_left"] == 9)
check("split conservation", b["treasury_liquid"] + b["treasury_locked_contract"]
      + b["burned_total"] == b["revenue_total"])
check("check_books all hold", pt.check_books()["all_hold"])

# 3 -- overspend refused: broke patron cannot run a session -------------------
pt2, _ = fresh()
pt2.fund_patron("broke-ben", 5)
rev_before = pt2.revenue_total
treas_before = pt2.contract.balances_of(TREASURY)["unlocked"]
try:
    pt2.run_session("broke-ben", sessions=1)  # costs 10, holds 5
    check("overspend refused", False)
except ContractError:
    check("overspend refused", True)
check("revenue untouched after refusal", pt2.revenue_total == rev_before)
check("treasury untouched after refusal",
      pt2.contract.balances_of(TREASURY)["unlocked"] == treas_before)
check("sessions not counted after refusal", pt2.sessions_run == 0)

# 4 -- full run: chain and vault ledger stay valid -----------------------------
pt3, clock3 = fresh()
pt3.fund_patron("cara", 1_000)
for _ in range(10):
    pt3.run_session("cara", sessions=2)
pt3.split_revenue()
clock3.advance_weeks(13)
pt3.sweep_released()
ok, reason = pt3.chain.verify_chain()
check("chain valid after full run", ok)
check("vault ledger valid after full run", pt3.vault.verify_chain())
check("books hold after full run", pt3.check_books()["all_hold"])

# 5 -- sweep returns matured locks to liquid -----------------------------------
pt4, clock4 = fresh()
pt4.fund_patron("dan", 200)
pt4.run_session("dan", sessions=10)   # 100 revenue
pt4.split_revenue()                    # locks 50, burns 20, liquid 30
liq_before = pt4.books()["treasury_liquid"]
clock4.advance_weeks(13)
swept = pt4.sweep_released()
check("sweep released the lock", swept["contract_released"] == 50)
liq_after = pt4.books()["treasury_liquid"]
check("liquid grew by released amount", liq_after == liq_before + 50)
check("books hold after sweep", pt4.check_books()["all_hold"])

# 6 -- burn shrinks the supply --------------------------------------------------
pt5, _ = fresh()
pt5.fund_patron("eli", 200)
supply_minted = pt5.contract.totals()["supply"]   # 200, after the demo mint
pt5.run_session("eli", sessions=10)
pt5.split_revenue()
supply_after = pt5.contract.totals()["supply"]
check("burn reduced supply", supply_after == supply_minted - pt5.burned_total)
check("burned_total tracked", pt5.burned_total == 20)

# 7 -- vault mirror matches the contract ----------------------------------------
pt6, _ = fresh()
pt6.fund_patron("fay", 400)
pt6.run_session("fay", sessions=20)   # 200 revenue
pt6.split_revenue()                    # locks 100
check("vault mirror matches contract",
      pt6.books()["treasury_locked_vault"] ==
      pt6.books()["treasury_locked_contract"] == 100)

# 8 -- split on empty treasury is a no-op ----------------------------------------
pt7, _ = fresh()
split7 = pt7.split_revenue()
check("empty split locks nothing", split7["locked"] == 0)
check("empty split burns nothing", split7["burned"] == 0)
check("empty books hold", pt7.check_books()["all_hold"])

print(f"\n{PASS} passed, {FAIL} failed")
raise SystemExit(1 if FAIL else 0)
