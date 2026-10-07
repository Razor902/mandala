# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom economy, not a production network.
# Demo holders only, assumed parameters, one machine, no peers, no wallets,
# no value. It teaches how a chain, a token contract, a vault, and a
# flywheel fit together as one body. It promises nothing and predicts nothing.
# ============================================================================
"""economy.py -- the whole mandala economy, working as one body.

Plain words: four organs, one bloodstream.

  - The CHAIN (mandala-chain/chain.py) is the public notebook. Every move
    the economy makes is written on its pages, sealed, and verifiable.
  - The CONTRACT (mandala-chain/mandala.py) is the rulebook. It mints,
    moves, burns, and locks mandalas -- and it refuses anything illegal
    (overspending, printing past the cap, moving locked funds).
  - The VAULT (mandala-vault/vault.py) is the promise with a clock. Every
    lock the contract enforces is mirrored in the vault's hash-chained
    ledger, so the policy ("locked for N weeks") and the record agree.
  - The FLYWHEEL (flywheel/flywheel.py) is the heartbeat. Each cycle,
    real usage pays fees, fees buy back tokens, half the buyback burns
    (through the contract's burn function) and half re-locks for 12 weeks.

THE INTEGRATION RULE (the one rule that holds it together):
  contract first, vault second. The chain contract ENFORCES (it checks
  funds, so a holder can never lock what they lack); the vault REMEMBERS
  (its ledger mirrors every lock). Never write a lock to the vault
  without the contract's lock succeeding first.

Data flow, in words:
  boot: mint -> treasury -> grants to demo holders -> initial locks
  each cycle: clock +1 week -> release matured locks -> demo transfer ->
    flywheel math (volume -> fees -> buyback -> burn + relock) ->
    burns via contract.burn, relocks via contract.lock + vault mirror ->
    users grow via ecosystem spend
  citizens (Curtis's decided law, 2026-10-07): proof-of-self -> earn one
    mandala (minted by the treasury); one mandala shown at any shop ->
    one thing. Showing never spends: the mandala stays with the citizen.
  end: dashboard -- supply, circulating, locked, burned, balances,
    citizens, chain height, chain validity.

Run:  cd ~/workspace/mandala-economy && python3 economy.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# Import the organs; never fork them. If an interface ever stops fitting,
# the adapter lives HERE (documented below), not in the component files.
sys.path.insert(0, os.path.join(_HERE, "..", "mandala-chain"))
sys.path.insert(0, os.path.join(_HERE, "..", "mandala-vault"))
sys.path.insert(0, os.path.join(_HERE, "..", "flywheel"))

from chain import Chain
from mandala import MandalaContract, ContractError
from vault import Vault, VaultError
import flywheel as flywheel_params  # ASSUMED constants only; cycle math is below

from decimal import Decimal

WEEK_SECONDS = 7 * 24 * 3600

# -- adapters (thin, documented) ----------------------------------------------
# The vault speaks Decimal; the contract speaks float. The economy speaks
# whole numbers, so both agree exactly. All demo amounts below are integers.
def _as_float(x):
    return float(x)


class FakeClock:
    """One clock for the whole economy, so runs are deterministic."""

    def __init__(self, start=1_700_000_000):
        self.t = start

    def __call__(self):
        return self.t

    def advance_weeks(self, n=1):
        self.t += n * WEEK_SECONDS


class MandalaEconomy:
    """The four organs wired into one body."""

    # Demo holders: clearly fictional. No real identities, ever.
    HOLDERS = ("demo-builder", "demo-keeper", "demo-trader")
    TREASURY = "demo-treasury"

    def __init__(self, cycles=24, seed_mint=100_000, holder_grant=10_000,
                 lock_amount=4_000, lock_weeks=12):
        self.cycles = cycles
        self.lock_amount = lock_amount
        self.lock_weeks = lock_weeks
        self.holder_grant = holder_grant
        self.clock = FakeClock()
        self.chain = Chain()
        self.contract = MandalaContract(minter=self.TREASURY,
                                        chain=self.chain,
                                        clock=self.clock)
        # Rewards OFF: the vault's own docs warn that unfunded rewards
        # dilute supply (the death-spiral shape). This classroom keeps
        # the ledger conservative: locks earn nothing but time.
        self.vault = Vault(clock=self.clock, reward_rate_per_week=Decimal("0"))
        self.users = float(flywheel_params.INITIAL_USERS)
        self.minted_total = 0
        self.burned_total = 0.0
        self.cycle_log = []
        self.citizens = []  # names that proved self, in order

        # -- boot: mint, grant, lock --------------------------------------
        self.contract.mint(self.TREASURY, seed_mint, by=self.TREASURY)
        self.minted_total = seed_mint
        for h in self.HOLDERS:
            self.contract.transfer(self.TREASURY, h, holder_grant)
        for h in self.HOLDERS:
            self.lock(h, lock_amount, lock_weeks)

    # -- the integration rule: contract first, vault second ------------------
    def lock(self, holder, amount, weeks):
        """Lock mandalas: the contract enforces, the vault remembers."""
        self.contract.lock(holder, amount, weeks)   # raises if funds lacking
        self.vault.deposit(holder, amount, weeks)   # policy mirror only

    # -- Curtis's decided law (2026-10-07): the mandala is Pandora's -------
    # currency. Proof-of-self earns ONE mandala; showing it at any shop
    # gets one thing. Showing never spends -- the mandala stays put.
    def prove_self(self, citizen):
        """A citizen proves their self and earns one mandala. Minted, on-chain."""
        if citizen in self.citizens:
            raise ContractError(f"{citizen} already proved self -- one mandala each.")
        self.contract.mint(citizen, 1, by=self.TREASURY)
        self.minted_total += 1
        self.citizens.append(citizen)
        return 1

    def show_for_item(self, citizen, shop):
        """Show one mandala at a shop for one thing. Non-destructive.

        Returns True and writes a 'show' page to the chain if the citizen
        holds at least one unlocked mandala; False otherwise. Nothing moves.
        """
        holds = self.contract.balances_of(citizen)["unlocked"] >= 1
        if holds:
            self.chain.add_block([{"type": "show", "citizen": citizen,
                                   "shop": shop,
                                   "note": "one mandala shown, one thing taken"}],
                                 timestamp=self.clock())
        return holds

    # -- one flywheel heartbeat (same formulas as flywheel.py simulate()) ----
    def flywheel_cycle(self):
        vault_totals = self.vault.totals()
        volume = (self.users * flywheel_params.TX_PER_USER_PER_CYCLE
                  * flywheel_params.AVG_TX_SIZE)
        fees = volume * flywheel_params.FEE_RATE
        buyback = fees * flywheel_params.BUYBACK_SHARE
        burn_now = buyback * flywheel_params.BURN_SHARE
        relock_now = buyback - burn_now

        if burn_now > 0:
            self.contract.burn(self.TREASURY, burn_now)
            self.burned_total += burn_now
        if relock_now > 0:
            # Protocol re-lock: same 12-week shelf, mirrored in the vault
            # so the vault's locked line always matches the contract's.
            self.lock(self.TREASURY, relock_now, 12)

        # Growth: ecosystem spend wins new users -- the loop turning.
        ecosystem_spend = fees * flywheel_params.ECOSYSTEM_SHARE
        new_users = ecosystem_spend / flywheel_params.CAC_MANDALAS
        self.users = min(flywheel_params.USER_GROWTH_CAP, self.users + new_users)

        return {"volume": volume, "fees": fees, "buyback": buyback,
                "burned": burn_now, "relocked": relock_now,
                "users": self.users,
                "vault_locked": float(vault_totals["locked"])}

    def run(self, verbose=True):
        pairs = [(self.HOLDERS[0], self.HOLDERS[1]),
                 (self.HOLDERS[1], self.HOLDERS[2]),
                 (self.HOLDERS[2], self.HOLDERS[0])]
        for cycle in range(1, self.cycles + 1):
            self.clock.advance_weeks(1)
            c_released = self.contract.release_matured()
            v_released = self.vault.release_matured()
            # Demo commerce: a small transfer rotating through the holders.
            frm, to = pairs[(cycle - 1) % len(pairs)]
            self.contract.transfer(frm, to, 100)
            fw = self.flywheel_cycle()
            fw.update({"cycle": cycle, "contract_released": c_released,
                       "vault_released": len(v_released)})
            self.cycle_log.append(fw)
            if verbose:
                print(f"  wk {cycle:3d} | users {fw['users']:9,.0f} | "
                      f"fees {fw['fees']:9,.1f} | burned {fw['burned']:9,.1f} | "
                      f"relocked {fw['relocked']:9,.1f} | "
                      f"vault locked {fw['vault_locked']:10,.1f}")
        return self.dashboard()

    # -- the dashboard -------------------------------------------------------
    def dashboard(self):
        ct = self.contract.totals()
        vt = self.vault.totals()
        ok, reason = self.chain.verify_chain()
        return {
            "minted": self.minted_total,
            "supply": ct["supply"],
            "burned_tracked": round(self.burned_total, 4),
            "burned_implied": round(self.minted_total - ct["supply"], 4),
            "locked_contract": round(ct["locked"], 4),
            "locked_vault": float(vt["locked"]),
            "unlocked": round(ct["unlocked"], 4),
            "users": round(self.users, 1),
            "chain_height": len(self.chain.blocks),
            "chain_valid": ok,
            "chain_reason": reason,
            "vault_ledger_valid": self.vault.verify_chain(),
            "citizens": list(self.citizens),
            "citizen_mandalas_earned": len(self.citizens),  # one each, by law
            "holders": {h: {k: round(v, 4)
                            for k, v in self.contract.balances_of(h).items()}
                        for h in self.HOLDERS + (self.TREASURY,)},
        }

    def conservation_check(self):
        """minted == supply + burned, and supply == locked + unlocked."""
        d = self.dashboard()
        c1 = abs(d["minted"] - (d["supply"] + d["burned_tracked"])) < 0.01
        c2 = abs(d["supply"] - (d["locked_contract"] + d["unlocked"])) < 0.01
        c3 = abs(d["burned_tracked"] - d["burned_implied"]) < 0.01
        c4 = abs(d["locked_contract"] - d["locked_vault"]) < 0.01
        return {"minted_equals_supply_plus_burned": c1,
                "supply_equals_locked_plus_unlocked": c2,
                "burned_tracked_matches_burned_implied": c3,
                "vault_locked_matches_contract_locked": c4,
                "all_hold": all([c1, c2, c3, c4])}


BANNER = """
================================================================
 MANDALA ECONOMY -- EDUCATIONAL MODEL ONLY
================================================================
 Four organs, one body: chain + contract + vault + flywheel.
 Demo holders, assumed parameters, classroom chain.
 Tracks TOKENS, not price. Promises no returns.
================================================================
"""


def main():
    print(BANNER)
    eco = MandalaEconomy()
    print(f"Boot: minted {eco.minted_total:,} to treasury; granted "
          f"{eco.holder_grant:,} each to {', '.join(MandalaEconomy.HOLDERS)}; "
          f"each locked {eco.lock_amount:,} for {eco.lock_weeks} weeks.")
    print("Running 24 weekly cycles:")
    d = eco.run(verbose=True)
    print("\n--- WHOLE-ECONOMY DASHBOARD ---")
    print(f"  Minted (all time) : {d['minted']:>15,.1f}")
    print(f"  Supply (now)      : {d['supply']:>15,.1f}")
    print(f"  Burned (tracked)  : {d['burned_tracked']:>15,.1f}")
    print(f"  Locked (contract) : {d['locked_contract']:>15,.1f}")
    print(f"  Locked (vault)    : {d['locked_vault']:>15,.1f}")
    print(f"  Unlocked          : {d['unlocked']:>15,.1f}")
    print(f"  Users (flywheel)  : {d['users']:>15,.1f}")
    print(f"  Chain height      : {d['chain_height']:>15d} pages")
    print(f"  Chain valid       : {d['chain_valid']} ({d['chain_reason']})")
    print(f"  Vault ledger ok   : {d['vault_ledger_valid']}")
    print("  Holder balances:")
    for h, b in d["holders"].items():
        print(f"    {h:15s} unlocked {b['unlocked']:>12,.1f} | "
              f"locked {b['locked']:>10,.1f} | total {b['total']:>12,.1f}")
    print("\n--- CITIZENS: proof-of-self, one mandala, shown at the shops ---")
    print("  (Curtis's decided law: the mandala is Pandora's currency.)")
    for citizen, shop in [("demo-citizen-ara", "demo-shop-valhalla"),
                          ("demo-citizen-bex", "demo-shop-constellation"),
                          ("demo-citizen-cy", "demo-shop-valhalla")]:
        eco.prove_self(citizen)
        ok_show = eco.show_for_item(citizen, shop)
        bal = eco.contract.balances_of(citizen)["unlocked"]
        print(f"  {citizen} proved self -> earned 1 mandala; "
              f"showed at {shop} -> {'one thing taken' if ok_show else 'REFUSED'}; "
              f"still holds {bal:.0f} (showing never spends)")
    d2 = eco.dashboard()
    ok2, reason2 = eco.chain.verify_chain()
    print(f"  Citizens: {len(d2['citizens'])} | chain still valid: {ok2} "
          f"({reason2}) | height now {d2['chain_height']} pages")
    print("\n--- CONSERVATION CHECK ---")
    for name, ok in eco.conservation_check().items():
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    print("\nDone. EDUCATIONAL MODEL ONLY. The Valhalla question stays open:\n"
          "what Valhalla is, and the stores that plug into this economy next.")


if __name__ == "__main__":
    main()
