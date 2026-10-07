# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — integration tests for the classroom economy.
# ============================================================================
"""test_economy.py -- the whole body, checked as one.

Run:  cd ~/workspace/mandala-economy && python3 test_economy.py

Every test below runs the real loop (imports the real organs, never forks)
and checks the properties the economy promises:
  1. the full loop runs without exceptions,
  2. tokens are conserved (nothing appears or vanishes but by the rules),
  3. the chain stays tamper-evident through the whole run,
  4. the vault's locked line always matches the contract's locked line,
  5. the rules still bite (overspending refused, even mid-economy).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from economy import MandalaEconomy
from mandala import ContractError

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[ok] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name} {detail}")


def approx(a, b, tol=0.01):
    return abs(float(a) - float(b)) <= tol


# 1. the full loop runs -------------------------------------------------------
eco = MandalaEconomy(cycles=24)
d = eco.run(verbose=False)
check("full 24-cycle loop runs", True)

# 2. conservation: minted == supply + burned ----------------------------------
check("minted == supply + burned",
      approx(d["minted"], d["supply"] + d["burned_tracked"]),
      f"minted={d['minted']} supply={d['supply']} burned={d['burned_tracked']}")
check("supply == locked + unlocked",
      approx(d["supply"], d["locked_contract"] + d["unlocked"]),
      f"supply={d['supply']} locked={d['locked_contract']} unlocked={d['unlocked']}")
check("tracked burns match implied burns",
      approx(d["burned_tracked"], d["burned_implied"]),
      f"tracked={d['burned_tracked']} implied={d['burned_implied']}")

# 3. the chain stayed honest ---------------------------------------------------
ok, reason = eco.chain.verify_chain()
check("chain valid after full run", ok, reason)
check("chain grew (genesis + boot + cycles)",
      d["chain_height"] > 24, f"height={d['chain_height']}")
check("vault ledger hash-chain valid", d["vault_ledger_valid"] is True)

# 4. vault locked line matches contract locked line -----------------------------
check("vault locked == contract locked",
      approx(d["locked_vault"], d["locked_contract"]),
      f"vault={d['locked_vault']} contract={d['locked_contract']}")

# 5. the rules still bite -------------------------------------------------------
try:
    eco.contract.transfer("demo-builder", "demo-keeper", 10**12)
    check("overspend refused", False, "transfer of 10^12 succeeded?!")
except ContractError:
    check("overspend refused", True)

try:
    eco.contract.lock("demo-keeper", 10**12, 12)
    check("lock-what-you-lack refused", False, "lock of 10^12 succeeded?!")
except ContractError:
    check("lock-what-you-lack refused", True)

# locks actually released mid-run (12-week shelf inside a 24-cycle run) --------
check("holder locks matured and released",
      all(approx(eco.contract.balances_of(h)["locked"], 0.0)
          for h in MandalaEconomy.HOLDERS),
      "a demo holder still shows locked funds after 24 weeks")

# no holder ever went negative ---------------------------------------------------
neg = [h for h in MandalaEconomy.HOLDERS
       if eco.contract.balances_of(h)["unlocked"] < -0.01]
check("no holder negative", not neg, f"negative: {neg}")

# the flywheel turned: users grew, burns happened ---------------------------------
check("flywheel users grew", d["users"] > 500, f"users={d['users']}")
check("flywheel burned tokens", d["burned_tracked"] > 0,
      f"burned={d['burned_tracked']}")

# Curtis's decided law: proof-of-self -> one mandala; show -> one thing --------
eco.prove_self("demo-citizen-test")
check("proof-of-self earns exactly one mandala",
      approx(eco.contract.balances_of("demo-citizen-test")["unlocked"], 1.0))
minted_after = eco.minted_total
check("citizen mint counted in minted_total",
      approx(minted_after, d["minted"] + 1),
      f"minted_total={minted_after}")
try:
    eco.prove_self("demo-citizen-test")
    check("double proof-of-self refused", False, "second mandala minted?!")
except ContractError:
    check("double proof-of-self refused", True)
before = eco.contract.balances_of("demo-citizen-test")["unlocked"]
shown = eco.show_for_item("demo-citizen-test", "demo-shop-test")
after = eco.contract.balances_of("demo-citizen-test")["unlocked"]
check("show at shop succeeds with a mandala", shown is True)
check("showing never spends (balance unchanged)", approx(before, after),
      f"before={before} after={after}")
check("show with no mandala refused",
      eco.show_for_item("demo-nobody", "demo-shop-test") is False)
cc = eco.conservation_check()
check("conservation still holds after citizen mints", cc["all_hold"],
      str({k: v for k, v in cc.items() if not v}))
ok3, _ = eco.chain.verify_chain()
check("chain valid after citizen pages", ok3)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
