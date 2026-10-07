# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom token contract, not a production one.
# No network, no wallets, no value. It teaches how a fixed-supply token,
# transfers, burns, and locks work as rules enforced by code.
# ============================================================================
"""mandala.py -- the MANDALA token contract, living on the classroom chain.

The contract is a set of RULES, enforced the same way every time:

  - SUPPLY CAP: mandalas can never exceed CAP. The minter cannot print
    past it. (CAP is marked ASSUMED -- Curtis sets the real number.)
  - MINT: only the minter address can create mandalas, and only under the cap.
  - TRANSFER: mandalas move holder to holder. No negative amounts, no
    spending what you do not have (double-spend refusal).
  - BURN: mandalas can be destroyed on purpose, shrinking the supply.
    This is the flywheel's burn line, as code.
  - LOCK: holders can lock mandalas for a chosen number of weeks, the
    way the vault does. Locked mandalas cannot move until released.
    This is the flywheel's lock line, as code.

Every action is also written to the chain as a transaction -- the public
notebook records the contract's every move.

MAPPING TO THE VAULT (~/workspace/mandala-vault/vault.py):
  The vault is the richer off-chain ledger (hash-chained entries, rewards,
  early-exit policy). This contract mirrors its CORE mechanics on-chain:
    vault.deposit(holder, amount, lock_weeks)  -> contract.lock(holder, amount, lock_weeks)
    vault.release_matured()                    -> contract.release_matured(now)
    vault.withdraw(holder, amount)             -> contract.transfer(holder, holder, ...) is NOT a thing;
                                                 use contract.transfer(holder, recipient, amount) for moves
                                                 and contract.unlock + transfer for released funds
    vault.balances(holder)                     -> contract.balances(holder)  (unlocked / locked / total)
    vault.totals()                             -> contract.totals()
  Deliberately NOT duplicated: the vault's reward accrual and early-exit
  penalty policy stay in the vault. The chain contract is the record of
  what moved; the vault is the policy of how locking behaves.
"""

import time

# ASSUMED -- Curtis sets the real number. Nothing here promises value.
CAP = 1_000_000

# Lock presets, same shelves as the vault (weeks).
LOCK_PRESETS = (4, 12, 52)


class ContractError(Exception):
    pass


class MandalaContract:
    """The mandala, as rules. Optionally writes every action to a chain."""

    def __init__(self, minter, chain=None, clock=None):
        self.minter = minter
        self.chain = chain
        self.clock = clock or time.time
        self.total_supply = 0
        self.balances = {}   # holder -> unlocked mandalas
        self.locked = {}     # holder -> list of {"amount", "unlock_at", "lock_weeks"}

    # -- internal helpers ----------------------------------------------------

    def _now(self):
        return self.clock()

    def _record(self, tx):
        """Write the action to the public notebook, if a chain is attached."""
        if self.chain is not None:
            self.chain.add_block([tx], timestamp=self._now())

    def _check_amount(self, amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ContractError(f"amount must be positive, got {amount!r}")

    # -- the rules ------------------------------------------------------------

    def mint(self, to, amount, by):
        """Create new mandalas. Only the minter, never past the CAP."""
        if by != self.minter:
            raise ContractError("only the minter can mint")
        self._check_amount(amount)
        if self.total_supply + amount > CAP:
            raise ContractError(
                f"mint of {amount} would pass the cap of {CAP} "
                f"(supply now {self.total_supply})")
        self.total_supply += amount
        self.balances[to] = self.balances.get(to, 0) + amount
        self._record({"type": "mint", "to": to, "amount": amount,
                      "supply": self.total_supply})
        return self.total_supply

    def transfer(self, frm, to, amount):
        """Move mandalas holder to holder. No spending what you lack."""
        self._check_amount(amount)
        if self.balances.get(frm, 0) < amount:
            raise ContractError(
                f"{frm} holds {self.balances.get(frm, 0)}, cannot send {amount}")
        self.balances[frm] -= amount
        self.balances[to] = self.balances.get(to, 0) + amount
        self._record({"type": "transfer", "from": frm, "to": to, "amount": amount})
        return self.balances[frm]

    def burn(self, frm, amount):
        """Destroy mandalas on purpose. The flywheel's burn line, as code."""
        self._check_amount(amount)
        if self.balances.get(frm, 0) < amount:
            raise ContractError(
                f"{frm} holds {self.balances.get(frm, 0)}, cannot burn {amount}")
        self.balances[frm] -= amount
        self.total_supply -= amount
        self._record({"type": "burn", "from": frm, "amount": amount,
                      "supply": self.total_supply})
        return self.total_supply

    def lock(self, holder, amount, lock_weeks):
        """Lock mandalas for N weeks. Locked funds cannot move until released."""
        self._check_amount(amount)
        if lock_weeks not in LOCK_PRESETS:
            raise ContractError(
                f"lock_weeks must be one of {LOCK_PRESETS}, got {lock_weeks}")
        if self.balances.get(holder, 0) < amount:
            raise ContractError(
                f"{holder} holds {self.balances.get(holder, 0)}, cannot lock {amount}")
        self.balances[holder] -= amount
        entry = {"amount": amount,
                 "lock_weeks": lock_weeks,
                 "unlock_at": self._now() + lock_weeks * 7 * 24 * 3600}
        self.locked.setdefault(holder, []).append(entry)
        self._record({"type": "lock", "holder": holder, "amount": amount,
                      "lock_weeks": lock_weeks})
        return entry

    def release_matured(self, now=None):
        """Free every lock whose time has come. Returns total released."""
        now = self._now() if now is None else now
        released = 0
        for holder, locks in list(self.locked.items()):
            kept = []
            for entry in locks:
                if entry["unlock_at"] <= now:
                    self.balances[holder] = self.balances.get(holder, 0) + entry["amount"]
                    released += entry["amount"]
                    self._record({"type": "unlock", "holder": holder,
                                  "amount": entry["amount"]})
                else:
                    kept.append(entry)
            if kept:
                self.locked[holder] = kept
            else:
                self.locked.pop(holder, None)
        return released

    # -- reading the state ----------------------------------------------------

    def balances_of(self, holder):
        unlocked = self.balances.get(holder, 0)
        locked = sum(e["amount"] for e in self.locked.get(holder, []))
        return {"unlocked": unlocked, "locked": locked, "total": unlocked + locked}

    def totals(self):
        locked = sum(e["amount"] for locks in self.locked.values() for e in locks)
        unlocked = sum(self.balances.values())
        return {"supply": self.total_supply, "cap": CAP,
                "locked": locked, "unlocked": unlocked}


def demo():
    from chain import Chain
    print("MANDALA CONTRACT -- classroom demo")
    chain = Chain()
    now = [1_000_000.0]
    m = MandalaContract(minter="curtis", chain=chain, clock=lambda: now[0])
    m.mint("curtis", 29_000, by="curtis")
    m.transfer("curtis", "maddie", 1_000)
    m.lock("curtis", 5_000, 12)
    m.burn("curtis", 500)
    now[0] += 13 * 7 * 24 * 3600  # thirteen weeks pass
    print("released:", m.release_matured())
    print("curtis:", m.balances_of("curtis"))
    print("totals:", m.totals())
    ok, reason = chain.verify_chain()
    print(f"chain pages: {len(chain.blocks)} | verify: {reason}")


if __name__ == "__main__":
    demo()
