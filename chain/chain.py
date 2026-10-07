# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — a classroom blockchain, not a production network.
# One machine, one chain, no peers. It teaches how blocks, hashes, mining,
# and validation work. It claims no decentralization, no security, no value.
# ============================================================================
"""chain.py -- a minimal, real, working blockchain in plain Python (stdlib only).

Curtis's Crypto Page said it best: the ledger is the public notebook glued
page to page. Here is that notebook, built for real:

  - Each BLOCK is one page. It holds transactions, a timestamp, and the
    hash of the page before it.
  - The HASH is the glue. SHA-256 fingerprints the whole page; change one
    letter on an old page and its fingerprint changes, which breaks the
    glue on every page after it.
  - MINING is the work of sealing a page: find a number (the nonce) that
    makes the page's fingerprint start with a chosen number of zeros.
    That takes real (small) effort, which is what makes rewriting history
    expensive.
  - VERIFYING is anyone re-checking the glue: recompute every fingerprint,
    confirm every link, confirm every seal. verify_chain() does exactly
    that, and it catches any tampering.

Run the demo at the bottom: `python3 chain.py`
"""

import hashlib
import json
import time

DIFFICULTY = 2  # leading zeros a block hash must start with; low = classroom-fast


class Block:
    """One page of the notebook."""

    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions  # list of plain dicts, e.g. {"type": "transfer", ...}
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """The fingerprint of this page: SHA-256 over its canonical contents."""
        page = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        return hashlib.sha256(json.dumps(page, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["index"], d["timestamp"], d["transactions"],
                   d["previous_hash"], d["nonce"])


class Chain:
    """The notebook itself: an ordered list of sealed pages."""

    def __init__(self, difficulty=DIFFICULTY):
        self.difficulty = difficulty
        self.blocks = [self._genesis()]

    def _genesis(self):
        """Page zero. Every chain starts with an agreed-upon first page."""
        genesis = Block(0, 0.0, [{"type": "genesis",
                                  "note": "the first page of the mandala notebook"}],
                        "0" * 64)
        genesis.nonce = self._mine_nonce(genesis)
        return genesis

    def _mine_nonce(self, block):
        """Seal the page: hunt for a nonce whose fingerprint has the zeros."""
        target = "0" * self.difficulty
        nonce = 0
        while True:
            block.nonce = nonce
            if block.compute_hash().startswith(target):
                return nonce
            nonce += 1

    def add_block(self, transactions, timestamp=None):
        """Write and seal the next page of the notebook."""
        prev = self.blocks[-1]
        block = Block(prev.index + 1,
                      time.time() if timestamp is None else timestamp,
                      transactions,
                      prev.compute_hash())
        block.nonce = self._mine_nonce(block)
        self.blocks.append(block)
        return block

    def verify_chain(self):
        """Re-check every page: fingerprints, links, and seals.

        Returns (ok, reason). ok is False the moment any page is wrong.
        """
        target = "0" * self.difficulty
        for i, block in enumerate(self.blocks):
            fingerprint = block.compute_hash()
            if not fingerprint.startswith(target):
                return False, f"block {i}: seal broken (hash lacks {self.difficulty} leading zeros)"
            if i == 0:
                if block.previous_hash != "0" * 64:
                    return False, "genesis block: bad previous hash"
            else:
                if block.previous_hash != self.blocks[i - 1].compute_hash():
                    return False, f"block {i}: glue broken (previous hash mismatch)"
        return True, "chain valid"

    # -- persistence: the notebook saved to disk and read back ---------------

    def save(self, path):
        with open(path, "w") as f:
            json.dump({"difficulty": self.difficulty,
                       "blocks": [b.to_dict() for b in self.blocks]}, f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        chain = cls(difficulty=data["difficulty"])
        chain.blocks = [Block.from_dict(d) for d in data["blocks"]]
        return chain


def demo():
    print("MANDALA CHAIN -- classroom demo")
    chain = Chain()
    chain.add_block([{"type": "note", "text": "Curtis wrote the first real page"}])
    chain.add_block([{"type": "note", "text": "the glue held"}])
    ok, reason = chain.verify_chain()
    print(f"pages: {len(chain.blocks)} | verify: {reason}")
    for b in chain.blocks:
        print(f"  page {b.index}: {b.compute_hash()[:16]}... (nonce {b.nonce})")


if __name__ == "__main__":
    demo()
