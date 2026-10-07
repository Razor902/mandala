# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom blockchain and token contract.
# One machine, one chain, no peers, no value. For learning, not for launching.
# ============================================================================

# The Mandala Chain — a classroom blockchain with the MANDALA contract

## What this is

A real, working, miniature blockchain in plain Python (stdlib only) — plus
the MANDALA token as a contract living on it. Curtis's Crypto Page said it
first: the ledger is the public notebook glued page to page. This is that
notebook, with pages that check each other.

## The pieces

| File | What it does |
|---|---|
| `chain.py` | Blocks, SHA-256 hashing, proof-of-work mining, chain verification, save/load. Run `python3 chain.py` for the demo. |
| `mandala.py` | The MANDALA token contract: fixed supply cap, minter role, transfers, burns, locks. Every action is written to the chain. Run `python3 mandala.py` for the demo. |
| `test_chain.py` | 24 tests, all passing. Run `python3 test_chain.py`. |

## How the chain works (plain words)

1. **Block** — one page. Holds transactions, a timestamp, the hash of the
   previous page, and a nonce.
2. **Hash** — the glue. SHA-256 fingerprints the whole page. Change one
   letter anywhere and the fingerprint changes.
3. **Mining** — sealing a page. The program hunts for a nonce that makes the
   page's fingerprint start with zeros (difficulty 2 here, so it runs fast).
   That hunt is real work, which is what makes rewriting history expensive.
4. **Verify** — re-checking the glue. `verify_chain()` recomputes every
   fingerprint, confirms every link, confirms every seal. Tamper with any
   page and it reports exactly which page broke.

## How the mandala contract works (plain words)

- **Cap:** total supply can never exceed `CAP` (assumed 1,000,000 — Curtis
  sets the real number). The minter cannot print past it, ever.
- **Mint:** only the minter address creates mandalas, and only under the cap.
- **Transfer:** holder to holder. No negative amounts, no spending what you
  do not hold — overspending is refused, which is the classroom version of
  double-spend protection.
- **Burn:** destroy mandalas on purpose. This is the flywheel's burn line,
  as code.
- **Lock:** lock mandalas for 4, 12, or 52 weeks (the vault's shelves).
  Locked funds cannot move until released. This is the flywheel's lock line,
  as code. The vault (`~/workspace/mandala-vault/`) keeps the richer policy
  (rewards, early-exit rules); the contract is the on-chain record of what
  moved. The mapping is documented at the top of `mandala.py`.

## The honest limits

- This chain runs on **one machine**. Real blockchains are many computers
  agreeing; this one has nobody to agree with. It teaches the *mechanics*,
  not the *network*.
- Proof-of-work here is tiny (difficulty 2). Real networks use enormous
  difficulty and enormous energy. The principle is the same; the scale is not.
- Nothing here has value, promises value, or should be treated as money.
  It is a classroom.

## What would make it real (later, his call)

Many independent nodes running the same rules, agreeing on new pages —
that is what turns a notebook into a network. The rules in `mandala.py`
are written so they *could* travel: cap, mint, transfer, burn, lock are
the same rules any real contract would enforce. The classroom comes first;
the network is a decision, not an accident.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
