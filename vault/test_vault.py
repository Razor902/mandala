# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — tests for the off-chain mandala vault model.
# Deterministic: every test runs on a fake clock, never real time.
# ============================================================================
"""Unit tests for vault.py. Run:  cd ~/workspace/mandala-vault && python3 test_vault.py"""

from decimal import Decimal

from vault import Vault, VaultError, WEEK_SECONDS


class Clock:
    def __init__(self, start=1_700_000_000):
        self.t = start

    def __call__(self):
        return self.t

    def weeks(self, n):
        self.t += n * WEEK_SECONDS


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        raise AssertionError(name)


def fresh(**kw):
    c = Clock()
    return Vault(clock=c, **kw), c


def test_deposit_and_balances():
    v, _ = fresh()
    lid = v.deposit("curtis", "1000", 12)
    b = v.balances("curtis")
    check("deposit -> locked 1000", b["locked"] == Decimal("1000"))
    check("deposit -> unlocked 0", b["unlocked"] == Decimal("0"))
    check("deposit -> total 1000", b["total"] == Decimal("1000"))
    check("lock id starts at 1", lid == 1)


def test_withdraw_locked_refused():
    v, _ = fresh()
    v.deposit("curtis", "1000", 12)
    try:
        v.withdraw("curtis", "100")
        check("withdraw locked -> refused", False)
    except VaultError:
        check("withdraw locked -> refused", True)


def test_release_after_expiry():
    v, c = fresh()
    v.deposit("curtis", "1000", 12)
    check("nothing matures early", v.release_matured() == [])
    c.weeks(11)
    check("still locked at 11 weeks", v.release_matured() == [])
    c.weeks(1)
    check("releases at 12 weeks", v.release_matured() == [1])
    b = v.balances("curtis")
    check("released -> unlocked", b["unlocked"] == Decimal("1000"))
    check("released -> locked 0", b["locked"] == Decimal("0"))
    v.withdraw("curtis", "250")
    check("withdraw after release works",
          v.balances("curtis")["unlocked"] == Decimal("750"))


def test_overdraw_refused():
    v, c = fresh()
    v.deposit("curtis", "1000", 4)
    c.weeks(5)
    v.release_matured()
    try:
        v.withdraw("curtis", "1001")
        check("overdraw -> refused", False)
    except VaultError:
        check("overdraw -> refused", True)


def test_early_exit_forbidden_default():
    v, _ = fresh()
    lid = v.deposit("curtis", "1000", 52)
    try:
        v.early_withdraw("curtis", lid)
        check("early exit forbidden by default", False)
    except VaultError as e:
        check("early exit forbidden by default", "FORBIDDEN" in str(e))
    check("lock untouched after refused exit",
          v.balances("curtis")["locked"] == Decimal("1000"))


def test_early_exit_penalty_mode():
    v, _ = fresh(early_exit="penalty", early_exit_penalty=Decimal("0.10"))
    lid = v.deposit("curtis", "1000", 52)
    out = v.early_withdraw("curtis", lid)
    check("penalty burned 100", out["burned"] == Decimal("100"))
    check("900 freed", out["freed"] == Decimal("900"))
    check("burned feeds totals", v.totals()["burned"] == Decimal("100"))
    b = v.balances("curtis")
    check("freed lands unlocked", b["unlocked"] == Decimal("900"))
    check("lock drained", b["locked"] == Decimal("0"))


def test_early_exit_wrong_holder():
    v, _ = fresh(early_exit="penalty")
    lid = v.deposit("curtis", "1000", 52)
    try:
        v.early_withdraw("maddie", lid)
        check("wrong holder -> refused", False)
    except VaultError:
        check("wrong holder -> refused", True)


def test_rewards_accrue():
    v, c = fresh(reward_rate_per_week=Decimal("0.001"))
    v.deposit("curtis", "1000", 52)
    c.weeks(10)
    paid = v.accrue_rewards()
    # 1000 * 0.001 * 10 = 10
    check("10 weeks rewards = 10", paid.get("curtis") == Decimal("10"))
    check("rewards land unlocked",
          v.balances("curtis")["unlocked"] == Decimal("10"))
    # no double-pay for the same weeks
    paid2 = v.accrue_rewards()
    check("no double accrual", paid2 == {})


def test_rewards_zero_rate():
    v, c = fresh(reward_rate_per_week=Decimal("0"))
    v.deposit("curtis", "1000", 52)
    c.weeks(10)
    check("zero rate pays zero", v.accrue_rewards() == {})


def test_ledger_chain_verifies():
    v, c = fresh()
    v.deposit("curtis", "1000", 4)
    c.weeks(5)
    v.release_matured()
    v.withdraw("curtis", "100")
    check("chain verifies after full lifecycle", v.verify_chain())
    check("ledger has 3 entries", len(v.ledger()) == 3)


def test_ledger_tamper_detected():
    v, _ = fresh()
    v.deposit("curtis", "1000", 4)
    v._ledger[0]["amount"] = "999999"  # rewrite a page of the notebook
    check("tampered page detected", not v.verify_chain())


def test_multiple_holders_and_locks():
    v, c = fresh()
    v.deposit("curtis", "1000", 4)
    v.deposit("maddie", "500", 12)
    v.deposit("curtis", "250", 52)
    check("curtis locked 1250", v.balances("curtis")["locked"] == Decimal("1250"))
    check("maddie locked 500", v.balances("maddie")["locked"] == Decimal("500"))
    c.weeks(5)
    check("only curtis 4-week lock matures", v.release_matured() == [1])
    check("curtis unlocked 1000", v.balances("curtis")["unlocked"] == Decimal("1000"))
    check("curtis still locked 250", v.balances("curtis")["locked"] == Decimal("250"))
    t = v.totals()
    check("totals locked 750", t["locked"] == Decimal("750"))
    check("totals unlocked 1000", t["unlocked"] == Decimal("1000"))


def test_bad_inputs_refused():
    v, _ = fresh()
    for bad in ("0", "-5"):
        try:
            v.deposit("curtis", bad, 12)
            check(f"deposit {bad} -> refused", False)
        except VaultError:
            check(f"deposit {bad} -> refused", True)
    try:
        v.deposit("curtis", "100", 0)
        check("zero-week lock -> refused", False)
    except VaultError:
        check("zero-week lock -> refused", True)
    try:
        Vault(early_exit="sometimes")
        check("bad early_exit mode -> refused", False)
    except VaultError:
        check("bad early_exit mode -> refused", True)


if __name__ == "__main__":
    test_deposit_and_balances()
    test_withdraw_locked_refused()
    test_release_after_expiry()
    test_overdraw_refused()
    test_early_exit_forbidden_default()
    test_early_exit_penalty_mode()
    test_early_exit_wrong_holder()
    test_rewards_accrue()
    test_rewards_zero_rate()
    test_ledger_chain_verifies()
    test_ledger_tamper_detected()
    test_multiple_holders_and_locks()
    test_bad_inputs_refused()
    print("\nAll vault tests passed.")
