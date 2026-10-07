# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom economy, not a production network.
# Demo holders and citizens only, assumed parameters, one machine, no peers,
# no wallets, no value. Tracks TOKENS, not price. Promises no returns.
# ============================================================================

# The Mandala Economy — Four Organs, One Body

**For learning. Not for trading. Education before money — every time.**

## What it is

The mandala economy working as one system: a blockchain, a token contract,
a vault, and a flywheel, wired together so tokens flow through all four
the way blood moves through a body. Run it and watch 24 weeks of the
economy breathe.

## Curtis's decided law (2026-10-07 — this one STANDS, it's his)

> "The mandala is a currency used in Pandora. Each citizen that proves
> their self earns one mandala. That will get them one thing out of any
> shop — they just have to show it."

- **Proof-of-self → one mandala.** The treasury mints exactly one, on-chain.
  Twice is refused — one citizen, one mandala.
- **Show it → one thing.** Showing a mandala at any shop is recorded on the
  chain but moves nothing. The mandala stays with the citizen.
- **"Watermark Mamandala"** — Curtis's watermark goes on the mandala
  itself (the visual/token design; tracked as a parent-level item, not
  modeled here).

This answers the utility question the whole wheel hangs on: the mandala is
**for Pandora's citizens and shops**.

## The four organs (imported, never forked)

| Organ | File | Job in the body |
|---|---|---|
| Chain | `../mandala-chain/chain.py` | The public notebook — every move sealed on pages |
| Contract | `../mandala-chain/mandala.py` | The rulebook — mint, transfer, burn, lock; refuses the illegal |
| Vault | `../mandala-vault/vault.py` | The promise with a clock — hash-chained ledger mirroring every lock |
| Flywheel | `../flywheel/flywheel.py` | The heartbeat — usage → fees → buyback → burn + re-lock |

**The integration rule:** contract first, vault second. The contract
*enforces* (a holder can never lock what they lack); the vault *remembers*
(its ledger mirrors every lock). The economy never writes a vault lock
without the contract's lock succeeding first.

**The adapter:** the vault speaks `Decimal`, the contract speaks `float`.
The economy speaks whole numbers, so both agree exactly. (`_as_float` in
`economy.py`; documented there.)

**Flywheel constants** (`FEE_RATE`, `BUYBACK_SHARE`, `BURN_SHARE`, user-growth
math) are imported from `flywheel.py` — same formulas as its `simulate()`,
one heartbeat at a time instead of 60 at once.

**Rewards are OFF.** The vault's own docs warn that unfunded rewards dilute
supply — the death-spiral shape. This classroom keeps the ledger
conservative: locks earn nothing but time.

## Data flow, in words

```
boot:    mint 100,000 -> treasury -> 10,000 each to 3 demo holders
         -> each holder locks 4,000 for 12 weeks (contract + vault mirror)
each week (x24):
         clock +1 week
         -> release matured locks (contract + vault, in step)
         -> demo commerce: a small transfer rotating through holders
         -> flywheel heartbeat: volume -> fees (1%) -> buyback (50%)
            -> half burns via contract.burn, half re-locks 12 weeks
               (contract + vault mirror)
         -> ecosystem spend grows the user base
citizens: 3 demo citizens prove self -> 1 mandala each (minted, on-chain)
         -> each shows at a demo shop -> one thing taken, nothing spent
end:     dashboard + conservation check
```

## How to run it

```bash
cd ~/workspace/mandala-economy
python3 economy.py      # the full 24-week run + dashboard
python3 test_economy.py # 22 integration tests
```

No installs. No network. Just Python 3.

## What the last run showed

- 24 weekly cycles; flywheel users 500 → 767 on real (assumed) fee math
- ~1,113 mandalas burned through the contract's burn function
- Holder 12-week locks matured and released mid-run, on both ledgers
- 3 citizens proved self, earned 1 mandala each, showed at shops —
  balances unchanged (showing never spends)
- Chain: ~100 pages, `verify_chain()` clean; vault ledger hash-chain clean
- **Conservation: minted == supply + burned; supply == locked + unlocked;
  vault locked == contract locked. All hold.**

## Honest limits

- **Classroom chain:** one machine, no peers — it teaches blocks, hashes,
  and validation; it is not decentralization.
- **Demo actors:** holders and citizens are fictional. No real identities.
- **Assumed parameters:** fee rate, user counts, lock shelves, supply cap —
  every one is Curtis's to tune. Nothing here is a recommendation.
- **The shops are next:** the show-it/take-one mechanic is modeled as a
  chain record; the actual Valhalla and constellation storefronts plug in
  on top of this economy — that's the next build, on Curtis's word.
- **Watermark:** per Curtis's order, his watermark goes on the mandala
  itself — the visual design is a separate piece, not modeled here.

## The one rule that matters

**Education before money — every time.**

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
