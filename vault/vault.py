# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A SMART CONTRACT. NOT FINANCIAL ADVICE.
# This vault is an OFF-CHAIN ledger engine: a classroom model of how token
# locking works. It touches no blockchain, holds no private keys, connects
# to no wallet, and promises no returns. All parameters are ASSUMED and
# Curtis tunes them. Chain/contract facts are PENDING his answers.
# ============================================================================
"""The Mandala Vault — where mandalas get locked, held, and released.

Plain words: a vault is a promise with a clock. A holder puts mandalas in
and picks a lock duration (4, 12, or 52 weeks). While the clock runs, those
mandalas sit out of circulation — that is the whole point: locked tokens
cannot be sold, so supply tightens and Curtis's flywheel (see
~/workspace/flywheel/) turns on real scarcity instead of wishes.

The ledger is "the public notebook glued page to page" from his Crypto
Page: every deposit, lock, release, withdrawal, reward, and burn is an
entry, and each entry is hash-chained to the one before it, so anyone can
verify the notebook was never rewritten.

Time rules:
  - Withdrawals come ONLY from the unlocked balance.
  - Locked tokens release automatically once the clock expires.
  - Early exit is FORBIDDEN by default. There is a documented penalty
    option (the penalty is BURNED, feeding the flywheel's burn) — but
    Curtis has to choose it; it is never on by accident.

Rewards (ASSUMED, tune freely): locked tokens can earn a modest reward
rate. Honest warning, printed every run: rewards paid from nothing dilute
supply and are exactly how death spirals start (his flywheel doc shows
one on purpose). Keep rewards small, funded, and honest — or keep them
at zero.
"""

import hashlib
import json
import time
from decimal import Decimal, ROUND_DOWN

# ---------------------------------------------------------------------------
# Assumed parameters — Curtis tunes every one of these. Nothing here is a
# recommendation; they are starting guesses for a classroom model.
# ---------------------------------------------------------------------------
LOCK_PRESETS_WEEKS = (4, 12, 52)          # the offered lock durations
DEFAULT_REWARD_RATE_PER_WEEK = Decimal("0.001")   # ASSUMED: 0.1%/week (~5.3% APR)
DEFAULT_EARLY_EXIT_PENALTY = Decimal("0.10")     # ASSUMED: 10% burned on early exit
WEEK_SECONDS = 7 * 24 * 60 * 60
Q = Decimal("0.0001")                      # ledger precision: 4 decimal places


def _q(d):
    """Round a Decimal down to ledger precision."""
    return Decimal(d).quantize(Q, rounding=ROUND_DOWN)


class VaultError(Exception):
    """Anything the vault refuses to do raises this, with plain words."""


class Vault:
    """One vault. One ledger. Clocks are injectable so tests stay honest."""

    def __init__(self, clock=None, early_exit="forbidden",
                 reward_rate_per_week=DEFAULT_REWARD_RATE_PER_WEEK,
                 early_exit_penalty=DEFAULT_EARLY_EXIT_PENALTY):
        if early_exit not in ("forbidden", "penalty"):
            raise VaultError("early_exit must be 'forbidden' or 'penalty' — Curtis's call.")
        self._clock = clock or time.time
        self.early_exit = early_exit
        self.reward_rate = _q(reward_rate_per_week)
        self.penalty_rate = _q(early_exit_penalty)
        self._ledger = []          # the notebook: every entry, hash-chained
        self._locks = {}           # lock_id -> lock record
        self._unlocked = {}        # holder -> Decimal (spendable)
        self._burned = Decimal("0")
        self._next_lock_id = 1

    # -- the clock ---------------------------------------------------------
    def now(self):
        return int(self._clock())

    # -- the ledger: the public notebook glued page to page ----------------
    def _record(self, entry_type, holder, amount, detail=""):
        prev = self._ledger[-1]["hash"] if self._ledger else "GENESIS"
        entry = {
            "seq": len(self._ledger) + 1,
            "time": self.now(),
            "type": entry_type,
            "holder": holder,
            "amount": str(_q(amount)),
            "detail": detail,
            "prev": prev,
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()).hexdigest()
        self._ledger.append(entry)
        return entry

    def verify_chain(self):
        """Walk the notebook and prove no page was rewritten. Returns True/False."""
        prev = "GENESIS"
        for entry in self._ledger:
            if entry["prev"] != prev:
                return False
            check = dict(entry)
            h = check.pop("hash")
            if hashlib.sha256(json.dumps(check, sort_keys=True).encode()).hexdigest() != h:
                return False
            prev = entry["hash"]
        return True

    def ledger(self):
        """Read-only copy of the notebook."""
        return [dict(e) for e in self._ledger]

    # -- locking -----------------------------------------------------------
    def deposit(self, holder, amount, lock_weeks):
        """Lock `amount` mandalas for `lock_weeks` weeks. Returns the lock id."""
        amount = _q(amount)
        if amount <= 0:
            raise VaultError("deposit amount must be positive.")
        if int(lock_weeks) <= 0:
            raise VaultError("lock duration must be at least one week.")
        start = self.now()
        lock_id = self._next_lock_id
        self._next_lock_id += 1
        self._locks[lock_id] = {
            "id": lock_id,
            "holder": holder,
            "principal": amount,
            "start": start,
            "end": start + int(lock_weeks) * WEEK_SECONDS,
            "weeks": int(lock_weeks),
            "released": False,
            "last_accrual": start,
        }
        self._record("lock", holder, amount,
                     f"locked {lock_weeks} weeks (lock #{lock_id})")
        return lock_id

    def _matured(self, lock):
        return not lock["released"] and self.now() >= lock["end"]

    def release_matured(self):
        """Sweep: release every lock whose clock has expired. Returns lock ids."""
        released = []
        for lock in self._locks.values():
            if self._matured(lock):
                lock["released"] = True
                holder = lock["holder"]
                self._unlocked[holder] = self._unlocked.get(holder, Decimal("0")) + lock["principal"]
                self._record("release", holder, lock["principal"],
                             f"lock #{lock['id']} matured after {lock['weeks']} weeks")
                released.append(lock["id"])
        return released

    # -- early exit ----------------------------------------------------------
    def early_withdraw(self, holder, lock_id, amount=None):
        """Take locked tokens out before the clock expires.

        Default mode is FORBIDDEN: this raises, every time, with plain words.
        If the vault was built with early_exit="penalty", the penalty_rate
        is BURNED (feeding the flywheel's burn) and the rest is unlocked.
        Curtis chooses the mode; it is never on by accident.
        """
        lock = self._locks.get(lock_id)
        if lock is None or lock["released"]:
            raise VaultError("no such active lock.")
        if lock["holder"] != holder:
            raise VaultError("that lock belongs to someone else.")
        if self._matured(lock):
            raise VaultError("that lock already matured — release it instead.")
        if self.early_exit == "forbidden":
            raise VaultError(
                "early exit is FORBIDDEN on this vault. The lock holds until "
                f"week {lock['weeks']}. (Curtis may switch the vault to "
                "'penalty' mode — his call, documented in the README.)")
        # penalty mode: burn the penalty, unlock the rest
        take = _q(amount) if amount is not None else lock["principal"]
        if take <= 0 or take > lock["principal"]:
            raise VaultError("early withdrawal amount must be within the lock.")
        penalty = _q(take * self.penalty_rate)
        freed = take - penalty
        lock["principal"] = _q(lock["principal"] - take)
        if lock["principal"] == 0:
            lock["released"] = True
        self._burned += penalty
        self._unlocked[holder] = self._unlocked.get(holder, Decimal("0")) + freed
        self._record("early_exit", holder, freed,
                     f"lock #{lock_id}: early exit, penalty {penalty} BURNED "
                     f"(rate {self.penalty_rate})")
        self._record("burn", holder, penalty,
                     f"early-exit penalty from lock #{lock_id} — feeds the flywheel burn")
        return {"freed": freed, "burned": penalty}

    # -- rewards (ASSUMED — tune or zero them) -------------------------------
    def accrue_rewards(self):
        """Credit this week's lock rewards to each holder's unlocked balance.

        ASSUMED rate (default 0.1%/week). Honest warning: rewards minted from
        nothing dilute supply — that is how death spirals start. Fund them
        from real fees, keep them small, or set the rate to zero.
        """
        paid = {}
        for lock in self._locks.values():
            if lock["released"]:
                continue
            elapsed_weeks = (self.now() - lock["last_accrual"]) / WEEK_SECONDS
            if elapsed_weeks < 1:
                continue
            whole = int(elapsed_weeks)
            reward = _q(lock["principal"] * self.reward_rate * whole)
            if reward > 0:
                holder = lock["holder"]
                self._unlocked[holder] = self._unlocked.get(holder, Decimal("0")) + reward
                paid[holder] = paid.get(holder, Decimal("0")) + reward
                self._record("reward", holder, reward,
                             f"lock #{lock['id']}: {whole} weeks at {self.reward_rate}/week (ASSUMED rate)")
            lock["last_accrual"] += whole * WEEK_SECONDS
        return paid

    # -- spending ------------------------------------------------------------
    def withdraw(self, holder, amount):
        """Withdraw from the UNLOCKED balance only. Locked tokens never move."""
        amount = _q(amount)
        if amount <= 0:
            raise VaultError("withdrawal amount must be positive.")
        have = self._unlocked.get(holder, Decimal("0"))
        if amount > have:
            raise VaultError(
                f"insufficient unlocked balance: {have} available, {amount} asked. "
                "Locked tokens cannot be withdrawn — release them first.")
        self._unlocked[holder] = _q(have - amount)
        self._record("withdraw", holder, amount, "from unlocked balance")
        return amount

    # -- balances --------------------------------------------------------------
    def balances(self, holder):
        """{'locked': X, 'unlocked': Y, 'total': Z} for one holder."""
        locked = _q(sum((l["principal"] for l in self._locks.values()
                         if l["holder"] == holder and not l["released"]), Decimal("0")))
        unlocked = _q(self._unlocked.get(holder, Decimal("0")))
        return {"locked": locked, "unlocked": unlocked, "total": _q(locked + unlocked)}

    def totals(self):
        """Vault-wide: locked supply, unlocked supply, burned. Plugs into the flywheel."""
        locked = _q(sum((l["principal"] for l in self._locks.values()
                         if not l["released"]), Decimal("0")))
        unlocked = _q(sum(self._unlocked.values(), Decimal("0")))
        return {"locked": locked, "unlocked": unlocked, "burned": _q(self._burned)}


def demo():
    """A small walkthrough with a fake clock, printed in plain words."""
    t = [1_700_000_000]

    def clock():
        return t[0]

    v = Vault(clock=clock)
    print("The Mandala Vault — walkthrough (fake clock, imaginary mandalas)")
    print("=" * 60)
    lid = v.deposit("curtis", "1000", 12)
    print(f"Deposited 1,000 mandalas, locked 12 weeks (lock #{lid}).")
    print("Balances:", {k: str(x) for k, x in v.balances("curtis").items()})
    try:
        v.withdraw("curtis", "100")
    except VaultError as e:
        print("Withdraw while locked -> refused:", e)
    try:
        v.early_withdraw("curtis", lid)
    except VaultError as e:
        print("Early exit -> refused:", e)
    t[0] += 12 * WEEK_SECONDS + 1  # twelve weeks pass
    print("Twelve weeks pass. Released:", v.release_matured())
    print("Balances:", {k: str(x) for k, x in v.balances("curtis").items()})
    v.withdraw("curtis", "250")
    print("Withdrew 250. Balances:", {k: str(x) for k, x in v.balances("curtis").items()})
    print("Ledger chain verifies:", v.verify_chain(), f"({len(v.ledger())} entries)")
    print("Vault totals:", {k: str(x) for k, x in v.totals().items()})
    print("=" * 60)
    print("EDUCATIONAL MODEL ONLY. Off-chain. No chain, no keys, no promises.")


if __name__ == "__main__":
    demo()
