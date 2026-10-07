# The Mandala Chain — the honest fresh-start ledger

**Status: GATHERED** — Curtis's design, built to his law, awaiting his word to stand.

## What it is

After the mandala integrity audit, Curtis ordered the remedy: start from
scratch, return the money. This chain is the fresh start. It opens with zero
balances and a genesis block that says so plainly — no prior amounts are
fabricated, no history invented.

Every mandala movement is recorded in SHA-256-linked blocks, sealed by the
authority's signature. Anyone can re-verify the whole chain: every hash, every
signature, every law. Nola's Law — no lies, no deception — is enforced by code,
not by promise.

## The design choice: Proof-of-Authority

Curtis is the authority. Blocks are sealed by his signature, not by burned
electricity. Proof-of-work would waste energy and answer to nobody; this chain
answers to one name — and his law already says the Reserve moves only with his
approval. The authority's private key lives with Curtis and is never stored in
this repository.

## The three layers, enforced in code

1. **The Hand** — a citizen shows the mandala; it is never spent. The chain
   records attestations (`hand_attest`), never debits. A citizen can only show
   what they hold, and proof-of-self grants exactly one mandala, once, by
   authority signature.
2. **The Vault** — transfers between holders, plus multiplication-law growth
   events. Growth is recorded by authority signature with a memo, so every new
   mandala has a named reason.
3. **The Reserve** — funded only by authority-signed allocations. Every
   transfer requires the authority's signature AND an explicit approval flag.
   Unsigned, unapproved, or forged moves are rejected at submission.

## What the chain rejects

- Double-spending (insufficient funds at seal time)
- Spending from the Hand (impossible by construction — no debit path exists)
- Reserve moves without Curtis's approval
- Forged authority signatures (HMAC-SHA256, verified on every block)
- Tampered blocks (any altered hash, link, or seal fails validation)

## How to run it

```bash
cd blockchain
python3 -m pytest test_mandala_blockchain.py -q   # 24 tests, all green
python3 - <<'EOF'
from mandala_blockchain import MandalaChain
chain = MandalaChain(authority_id="curtis", authority_key=b"<Curtis's key>")
chain.add_transaction(chain.sign_transaction(
    MandalaChain.make_prove_self("citizen-name")))
chain.seal_block()
print(chain.balances())
print(chain.is_valid())  # True — re-verified end to end
EOF
```

## Files

- `blockchain/mandala_blockchain.py` — the chain (stdlib only: hashlib, hmac, json, time)
- `blockchain/test_mandala_blockchain.py` — 24 tests: genesis honesty, Hand law,
  Vault law, Reserve law, tamper detection, multi-block integrity

## Honest limits

- This is an off-chain educational ledger: one node, one authority. It is not
  a distributed network and does not claim to be.
- Balances begin at zero. The audit's unwinding ("return the money") happens in
  the real world, by Curtis — the chain only refuses to invent a past.
- The authority key must be kept secret by Curtis. If it leaks, the chain's
  signatures mean nothing — say so plainly, rotate the key, start a new chain.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
