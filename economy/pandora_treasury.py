# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom treasury, not a production system.
# Demo patrons only, assumed prices, one machine, no wallets, no value.
# It teaches how Pandora's Box joins the mandala economy as a merchant:
# sessions priced in mandala, revenue split three ways. It promises no
# returns and predicts nothing.
# ============================================================================
"""pandora_treasury.py -- Pandora's Box joins the mandala economy as a merchant.

Plain words: the box opens its doors, patrons pay mandalas for sessions,
and every mandala of revenue is split three ways -- part re-locked in the
vault (the promise with a clock), part burned (feeding the flywheel's
burn line), and part kept liquid in the treasury for the box's own needs.

Why mandala, why the box: Curtis decided it (2026-10-07) -- "The mandala
is a currency used in Pandora." The box is Pandora's merchant, so it prices
in Pandora's money. (His wider law -- one mandala shown buys one thing from
any shop -- lives with the shops; this module handles the box's own books.)

THE INTEGRATION RULE (shared with economy.py): contract first, vault
second. The chain contract ENFORCES (it checks funds, so the treasury can
never lock or burn what it lacks); the vault REMEMBERS (its ledger mirrors
every lock). Never write a lock to the vault without the contract's lock
succeeding first. Releases run on both, the same way.

RESPECTING THE BOX: this is the ECONOMY side only. It moves money; it
never decides who may run a session. Session gating -- who the box admits,
and when -- stays entirely with the box's own safety states (see
~/workspace/arcade/pandora/). The treasury never overrides guardrails.
Nothing here touches ~/workspace/arcade/pandora/.

PENDING (Curtis's calls): the real session price, the real split shares,
the real lock shelf, and his order to "watermark Mamandala" -- the
watermark belongs on the mandala itself (the contract), which is a
decision for the contract module, noted here so it is not forgotten.

Run the demo:  cd ~/workspace/mandala-economy && python3 pandora_treasury.py
"""

import os
import sys
import time
from decimal import Decimal

_HERE = os.path.dirname(os.path.abspath(__file__))
# Import the organs; never fork them. Same layout as economy.py so both
# modules share one view of the components.
sys.path.insert(0, os.path.join(_HERE, "..", "mandala-chain"))
sys.path.insert(0, os.path.join(_HERE, "..", "mandala-vault"))

from chain import Chain
from mandala import MandalaContract, ContractError
from vault import Vault, VaultError

TREASURY = "pandora-treasury"

# ---------------------------------------------------------------------------
# Assumed parameters -- Curtis sets every real number. Nothing here is a
# recommendation; they are starting guesses for a classroom model.
# ---------------------------------------------------------------------------
SESSION_PRICE = 10      # ASSUMED: mandalas per box session
LOCK_SHARE = 0.50       # ASSUMED: share of session revenue re-locked
BURN_SHARE = 0.20       # ASSUMED: share of session revenue burned
LOCK_WEEKS = 12         # ASSUMED: which vault shelf (must be 4, 12, or 52)

WEEK_SECONDS = 7 * 24 * 3600


class FakeClock:
    """A clock the tests can fast-forward. The contract and the vault share it."""

    def __init__(self, start=1_700_000_000):
        self.t = float(start)

    def __call__(self):
        return self.t

    def advance_weeks(self, n=1):
        self.t += n * WEEK_SECONDS


class PandoraTreasury:
    """The box's books: session fees in, three-way split out."""

    def __init__(self, minter="curtis", chain=None, contract=None, vault=None,
                 clock=None, session_price=SESSION_PRICE, lock_share=LOCK_SHARE,
                 burn_share=BURN_SHARE, lock_weeks=LOCK_WEEKS):
        if not 0 <= lock_share <= 1 or not 0 <= burn_share <= 1:
            raise ValueError("shares must be between 0 and 1")
        if lock_share + burn_share > 1:
            raise ValueError("lock_share + burn_share cannot exceed 1")
        self.clock = clock or time.time
        self.chain = chain if chain is not None else Chain()
        if contract is None:
            contract = MandalaContract(minter=minter, chain=self.chain,
                                       clock=self.clock)
        self.contract = contract
        self.minter = minter
        if vault is None:
            # Rewards OFF and early exit FORBIDDEN: the vault is a pure
            # mirror of the contract's locks here, so the mirror must stay
            # exact -- no minted rewards, no penalty accounting.
            vault = Vault(clock=self.clock, early_exit="forbidden",
                          reward_rate_per_week=Decimal("0"))
        self.vault = vault
        self.session_price = session_price
        self.lock_share = lock_share
        self.burn_share = burn_share
        self.lock_weeks = lock_weeks
        # the books, in plain numbers
        self.sessions_run = 0
        self.revenue_total = 0
        self.burned_total = 0

    # -- the merchant counter ------------------------------------------------

    def fund_patron(self, patron, amount):
        """Classroom seeding: the minter grants a demo patron starting mandalas.

        In the real world patrons arrive already holding mandala; here the
        classroom mints demo funds so sessions can run."""
        return self.contract.mint(patron, amount, by=self.minter)

    def run_session(self, patron, sessions=1):
        """Run box sessions for a patron; the fee moves patron -> treasury.

        NOTE -- session gating stays with the box: WHO may run a session,
        and WHEN, is decided by Pandora's Box safety states (see
        ~/workspace/arcade/pandora/). This method is the economy side
        only: it moves the fee for a session the box already admitted.
        It never overrides guardrails, and nothing here touches the box.
        """
        if sessions < 1:
            raise ValueError("sessions must be at least 1")
        fee = self.session_price * sessions
        # Raises ContractError if the patron cannot cover it -- overspend
        # is refused, and the books below are untouched.
        self.contract.transfer(patron, TREASURY, fee)
        self.sessions_run += sessions
        self.revenue_total += fee
        return fee

    # -- the three-way split ---------------------------------------------------

    def split_revenue(self):
        """Split the treasury's liquid revenue: lock some, burn some, keep some.

        Follows the integration rule: contract first (enforces funds),
        vault second (mirrors the lock in its ledger).
        """
        liquid = int(self.contract.balances_of(TREASURY)["unlocked"])
        lock_amount = int(liquid * self.lock_share)
        burn_amount = int(liquid * self.burn_share)
        if lock_amount > 0:
            self.contract.lock(TREASURY, lock_amount, self.lock_weeks)
            self.vault.deposit(TREASURY, lock_amount, self.lock_weeks)
        if burn_amount > 0:
            self.contract.burn(TREASURY, burn_amount)
            self.burned_total += burn_amount
        liquid_left = int(self.contract.balances_of(TREASURY)["unlocked"])
        return {"locked": lock_amount, "burned": burn_amount,
                "liquid_left": liquid_left}

    def sweep_released(self):
        """Release matured locks back to liquid. Runs on both contract and vault."""
        c_released = self.contract.release_matured()
        v_released = self.vault.release_matured()
        return {"contract_released": c_released,
                "vault_locks_released": len(v_released)}

    # -- the books ---------------------------------------------------------------

    def books(self):
        """Pandora's books, in plain numbers."""
        tb = self.contract.balances_of(TREASURY)
        vb = self.vault.balances(TREASURY)
        chain_ok, chain_reason = self.chain.verify_chain()
        return {
            "sessions_run": self.sessions_run,
            "revenue_total": self.revenue_total,
            "treasury_liquid": int(tb["unlocked"]),
            "treasury_locked_contract": int(tb["locked"]),
            "treasury_locked_vault": int(vb["locked"]),
            "burned_total": self.burned_total,
            "chain_pages": len(self.chain.blocks),
            "chain_valid": chain_ok,
            "chain_reason": chain_reason,
            "vault_ledger_valid": self.vault.verify_chain(),
        }

    def check_books(self):
        """The conservation law: every revenue mandala is liquid, locked,
        or burned -- nothing created, nothing lost, nothing unaccounted."""
        b = self.books()
        accounted = (b["treasury_liquid"] + b["treasury_locked_contract"]
                     + b["burned_total"])
        c1 = accounted == b["revenue_total"]
        c2 = b["treasury_locked_contract"] == b["treasury_locked_vault"]
        c3 = b["chain_valid"] and b["vault_ledger_valid"]
        return {"revenue_equals_liquid_plus_locked_plus_burned": c1,
                "vault_locked_matches_contract_locked": c2,
                "chain_and_ledger_valid": c3,
                "all_hold": all([c1, c2, c3])}

    def print_dashboard(self):
        b = self.books()
        print("--- PANDORA'S BOOKS ---")
        print(f"  Sessions run      : {b['sessions_run']}")
        print(f"  Revenue collected : {b['revenue_total']} mandalas")
        print(f"  Treasury liquid   : {b['treasury_liquid']} mandalas")
        print(f"  Locked (contract) : {b['treasury_locked_contract']} mandalas "
              f"({self.lock_weeks}-week shelf)")
        print(f"  Burned (flywheel) : {b['burned_total']} mandalas")
        print(f"  Chain pages       : {b['chain_pages']} | verify: {b['chain_reason']}")
        print(f"  Vault ledger      : {'valid' if b['vault_ledger_valid'] else 'BROKEN'}")
        print(f"  Books balance     : {self.check_books()['all_hold']}")


def demo():
    print("=" * 64)
    print(" PANDORA'S TREASURY -- EDUCATIONAL MODEL ONLY")
    print(" The box as merchant: sessions in mandala, revenue split three ways.")
    print(" Demo patrons, assumed prices, classroom chain. Promises nothing.")
    print("=" * 64)
    clock = FakeClock()
    pt = PandoraTreasury(clock=clock)
    pt.fund_patron("demo-patron-amy", 500)
    pt.fund_patron("demo-patron-ben", 300)
    print("Patrons funded: amy 500, ben 300 (demo mint).")
    pt.run_session("demo-patron-amy", sessions=4)
    pt.run_session("demo-patron-ben", sessions=2)
    print(f"Ran 6 sessions at {SESSION_PRICE} mandalas each.")
    split = pt.split_revenue()
    print(f"Split: locked {split['locked']}, burned {split['burned']}, "
          f"liquid left {split['liquid_left']}.")
    clock.advance_weeks(13)  # thirteen weeks pass
    swept = pt.sweep_released()
    print(f"Thirteen weeks pass. Released back to liquid: "
          f"{swept['contract_released']} mandalas.")
    pt.print_dashboard()
    print("=" * 64)
    print("Session gating stayed with the box; this moved money only.")


if __name__ == "__main__":
    demo()
