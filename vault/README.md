# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A SMART CONTRACT. NOT FINANCIAL ADVICE.
# Off-chain ledger engine. No blockchain, no private keys, no wallets,
# no real tokens, no promised returns. Parameters are ASSUMED; Curtis tunes.
# ============================================================================

# The Mandala Vault

**Where mandalas get locked, held, and released. A classroom model — not a chain.**

## What a vault is (plain words)

A vault is a promise with a clock. You put mandalas in and pick how long
they stay locked — 4, 12, or 52 weeks. While the clock runs, those mandalas
sit out of circulation: they cannot be sold, moved, or spent. When the
clock expires, they release into your unlocked balance and you can
withdraw them.

Why lock anything at all? Because locked tokens tighten supply, and
tighter supply is the honest fuel of Curtis's flywheel
(`~/workspace/flywheel/`): the loop turns on real scarcity — tokens people
chose to sit out — not on wishes. The flywheel's buyback mechanic assumes
tokens get locked for 12 weeks; this vault is where that locking lives.

## The ledger (the public notebook)

Every deposit, lock, release, withdrawal, reward, and burn is written as an
entry in the vault's ledger — "the public notebook glued page to page"
from Curtis's Crypto Page. Each entry is hash-chained to the one before it
(sha256), so anyone can run `verify_chain()` and prove no page was ever
rewritten. Tamper with one entry and the whole chain fails loudly.

## The rules

1. **Withdrawals come only from the unlocked balance.** Locked tokens never move.
2. **Locks release automatically** once their clock expires (`release_matured()` sweeps them).
3. **Early exit is FORBIDDEN by default.** The vault refuses, in plain words.
   There is a documented *penalty* option: build the vault with
   `early_exit="penalty"` and early exits burn a penalty cut (default 10%,
   ASSUMED) — the burn feeds the flywheel's burn. Curtis's call; never on
   by accident.
4. **Rewards are ASSUMED and optional** (default 0.1%/week). Honest warning:
   rewards minted from nothing dilute supply — that is exactly how death
   spirals start (his flywheel doc shows one on purpose). Fund rewards from
   real fees, keep them small, or set the rate to zero.

## How to run it

```bash
cd /home/hatch/workspace/mandala-vault
python3 vault.py        # the walkthrough: deposit, lock, refuse, release, withdraw
python3 test_vault.py  # the unit tests (fake clock — deterministic, no real time)
```

No installs. No accounts. No keys. Just Python 3, stdlib only.

## How it plugs into the flywheel

- `totals()` returns `{"locked": X, "unlocked": Y, "burned": Z}` — vault-wide.
  Feed `locked` into the flywheel's lock assumption and `burned` into its
  burn line, and the two models talk to each other.
- Lock presets (4/12/52 weeks) match the flywheel's stagger guidance:
  releases should trickle, never wave (the flywheel README's "lock cliffs"
  warning).

## The honest limits

- **Off-chain model, not a smart contract.** Nothing here enforces itself on
  a blockchain; it teaches the *mechanics* of locking.
- **Chain and contract unknown.** Curtis's MANDALA-1…5 questions are still
  open; nothing here invents chain facts.
- **Parameters are assumed.** Lock presets, reward rate, penalty rate — all
  starting guesses for the classroom, all his to tune.
- **No returns are promised.** A vault holds tokens; it does not grow them.
  Anyone who tells you otherwise is selling something.

## Still Curtis's to decide

- Early exit: keep it **forbidden**, or switch to **penalty** (and at what rate)?
- Reward rate: keep the assumed 0.1%/week, change it, or zero it?
- The Valhalla question: what Valhalla is, and what the mandala is *for* —
  the utility the whole economy hangs on.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
