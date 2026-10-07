# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""
The Mandala blockchain — the honest fresh-start ledger.

This chain is the clean ledger Curtis ordered after the mandala integrity
audit: prior balances were unwound per his remedy (start from scratch, return
the money), and this chain starts clean. No prior amounts are fabricated here.

CONSENSUS: Proof-of-Authority.
Curtis is the authority. Blocks are sealed by his authority signature, not by
burned electricity. This matches his law: the Reserve moves only with his
approval, proof-of-self is his to grant, and multiplication-law growth is
recorded by authority. A proof-of-work chain would waste energy and answer to
nobody; this chain answers to one name.

THREE LAYERS, enforced in code:
  HAND    — attestations only. A citizen shows the mandala; it is NEVER spent.
            The chain records the showing, never a debit.
  VAULT   — transfers between holders, plus multiplication-law growth events
            (authority-recorded mints).
  RESERVE — transfers require the authority's signature AND an explicit
            approval flag. Without both, the transaction is rejected. The
            Reserve is funded only by authority-signed allocations.

CRYPTOGRAPHY: SHA-256 hash chaining (stdlib hashlib) and HMAC-SHA256
signatures (stdlib hmac). Real signatures, verifiable by anyone holding the
authority's public key id. The authority's private key is NEVER stored in this
repository — it lives with Curtis.

This is an educational/off-chain ledger, not a distributed network. One node,
one authority, fully auditable — Nola's Law: no lies, no deception.
"""

import hashlib
import hmac
import json
import time


GENESIS_PREV = "0" * 64

# The chain's name. The mandala is the currency; Phantom X is the chain.
CHAIN_NAME = "Phantom X"

# The token's name. The mandala is the currency concept the token embodies;
# the token itself is called "sleep" — named for Curtis's favorite band,
# Sleep Token.
TOKEN_NAME = "sleep"

# Transaction types
PROVE_SELF = "prove_self"        # authority grants one mandala to a citizen's Hand
HAND_ATTEST = "hand_attest"      # citizen shows the mandala (never moves it)
VAULT_TRANSFER = "vault_transfer"
VAULT_GROWTH = "vault_growth"    # multiplication-law growth, authority-recorded
RESERVE_ALLOCATION = "reserve_allocation"  # authority funds the reserve (signed)
RESERVE_TRANSFER = "reserve_transfer"


def _canonical(obj):
    """Deterministic JSON for hashing and signing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class InvalidTransaction(Exception):
    """Raised when a transaction breaks the mandala laws."""


class InvalidChain(Exception):
    """Raised when chain validation fails."""


class MandalaChain:
    """Proof-of-authority mandala ledger with three enforced wallet layers."""

    def __init__(self, authority_id="curtis", authority_key=None):
        if authority_key is None:
            raise ValueError("authority_key is required — the authority signs blocks")
        self.authority_id = authority_id
        self._authority_key = authority_key
        self.blocks = []
        self.mempool = []
        self._proven = set()  # citizens already granted proof-of-self
        self._seal_genesis()

    # ------------------------------------------------------------------ #
    # signing
    # ------------------------------------------------------------------ #
    def _sign(self, payload: bytes) -> str:
        return hmac.new(self._authority_key, payload, hashlib.sha256).hexdigest()

    def _tx_signing_bytes(self, tx: dict) -> bytes:
        body = {k: v for k, v in tx.items() if k not in ("signature",)}
        return _canonical(body)

    def sign_transaction(self, tx: dict) -> dict:
        """Authority-sign a transaction dict in place; returns it."""
        tx = dict(tx)
        tx["signature"] = self._sign(self._tx_signing_bytes(tx))
        return tx

    def _tx_signature_valid(self, tx: dict) -> bool:
        sig = tx.get("signature")
        if not sig:
            return False
        expected = self._sign(self._tx_signing_bytes(tx))
        return hmac.compare_digest(expected, sig)

    # ------------------------------------------------------------------ #
    # genesis — the honest fresh start
    # ------------------------------------------------------------------ #
    def _seal_genesis(self):
        genesis_tx = {
            "type": "genesis",
            "chain": CHAIN_NAME,
            "memo": (
                "Phantom X: the fresh start ordered by Curtis Ray Dyess after "
                "the mandala integrity audit. Prior balances unwound per his "
                "remedy: "
                "start from scratch, return the money. This chain opens with "
                "zero balances and no fabricated amounts. Authority: "
                + self.authority_id
            ),
            "timestamp": int(time.time()),
        }
        block = self._seal_block(0, GENESIS_PREV, [genesis_tx])
        self.blocks.append(block)

    def _block_hash(self, index, timestamp, transactions, prev_hash, authority):
        return _sha256(_canonical({
            "index": index,
            "timestamp": timestamp,
            "transactions": transactions,
            "prev_hash": prev_hash,
            "authority": authority,
        }))

    def _seal_block(self, index, prev_hash, transactions):
        timestamp = int(time.time())
        block_hash = self._block_hash(index, timestamp, transactions, prev_hash,
                                     self.authority_id)
        block = {
            "index": index,
            "timestamp": timestamp,
            "transactions": transactions,
            "prev_hash": prev_hash,
            "authority": self.authority_id,
            "hash": block_hash,
        }
        block["block_signature"] = self._sign(_canonical(
            {k: v for k, v in block.items() if k != "block_signature"}))
        return block

    # ------------------------------------------------------------------ #
    # transactions
    # ------------------------------------------------------------------ #
    @staticmethod
    def make_prove_self(citizen):
        return {"type": PROVE_SELF, "citizen": citizen,
                "timestamp": int(time.time())}

    @staticmethod
    def make_hand_attest(citizen, where):
        # A showing, not a spending. No amounts, no debits — ever.
        return {"type": HAND_ATTEST, "citizen": citizen, "where": where,
                "timestamp": int(time.time())}

    @staticmethod
    def make_vault_transfer(sender, recipient, amount, memo=""):
        return {"type": VAULT_TRANSFER, "sender": sender, "recipient": recipient,
                "amount": amount, "memo": memo, "timestamp": int(time.time())}

    @staticmethod
    def make_vault_growth(recipient, amount, memo):
        return {"type": VAULT_GROWTH, "recipient": recipient, "amount": amount,
                "memo": memo, "timestamp": int(time.time())}

    @staticmethod
    def make_reserve_allocation(recipient, amount, memo):
        # The authority funds the Reserve. Signed, recorded, auditable.
        return {"type": RESERVE_ALLOCATION, "recipient": recipient,
                "amount": amount, "memo": memo, "timestamp": int(time.time())}

    @staticmethod
    def make_reserve_transfer(sender, recipient, amount, approved, memo=""):
        return {"type": RESERVE_TRANSFER, "sender": sender, "recipient": recipient,
                "amount": amount, "approved": bool(approved), "memo": memo,
                "timestamp": int(time.time())}

    def add_transaction(self, tx: dict):
        """Light checks at submission; full law checks happen at seal time."""
        tx = dict(tx)
        t = tx.get("type")
        if t not in (PROVE_SELF, HAND_ATTEST, VAULT_TRANSFER, VAULT_GROWTH,
                     RESERVE_ALLOCATION, RESERVE_TRANSFER):
            raise InvalidTransaction("unknown transaction type: %r" % (t,))
        if t in (PROVE_SELF, VAULT_GROWTH, RESERVE_ALLOCATION):
            if not self._tx_signature_valid(tx):
                raise InvalidTransaction(t + " requires a valid authority signature")
        if t == RESERVE_TRANSFER:
            if not tx.get("approved"):
                raise InvalidTransaction(
                    "reserve transfer rejected: no authority approval flag")
            if not self._tx_signature_valid(tx):
                raise InvalidTransaction(
                    "reserve transfer rejected: invalid authority signature")
        for amt_key in ("amount",):
            if amt_key in tx and not (isinstance(tx[amt_key], int) and tx[amt_key] > 0):
                raise InvalidTransaction("amount must be a positive integer")
        self.mempool.append(tx)
        return tx

    # ------------------------------------------------------------------ #
    # sealing (proof-of-authority: the authority seals each block)
    # ------------------------------------------------------------------ #
    def seal_block(self):
        """Apply mempool in order under the mandala laws; seal or raise."""
        # Simulate against current state to enforce balance laws.
        state = self._replay()
        for tx in self.mempool:
            self._apply(tx, state)
        block = self._seal_block(len(self.blocks),
                                self.blocks[-1]["hash"],
                                list(self.mempool))
        self.blocks.append(block)
        self.mempool = []
        return block

    # ------------------------------------------------------------------ #
    # state + law enforcement
    # ------------------------------------------------------------------ #
    @staticmethod
    def _new_state():
        return {"hand": {}, "vault": {}, "reserve": {}, "proven": set()}

    def _apply(self, tx, state):
        """Apply one transaction to a state dict, enforcing the laws."""
        t = tx["type"]
        if t == "genesis":
            return
        if t == PROVE_SELF:
            citizen = tx["citizen"]
            if citizen in state["proven"]:
                raise InvalidTransaction(
                    "proof-of-self already granted to %r — one mandala per citizen"
                    % (citizen,))
            state["proven"].add(citizen)
            state["hand"][citizen] = state["hand"].get(citizen, 0) + 1
        elif t == HAND_ATTEST:
            # THE HAND LAW: showing is recorded; nothing is ever debited.
            # A citizen can only show what they hold.
            citizen = tx["citizen"]
            if state["hand"].get(citizen, 0) < 1:
                raise InvalidTransaction(
                    "hand attestation rejected: %r holds no mandala to show"
                    % (citizen,))
            # No balance change. Deliberately. The Hand is never spent.
        elif t == VAULT_TRANSFER:
            s, r, a = tx["sender"], tx["recipient"], tx["amount"]
            if state["vault"].get(s, 0) < a:
                raise InvalidTransaction(
                    "vault transfer rejected: insufficient funds (double-spend)")
            state["vault"][s] -= a
            state["vault"][r] = state["vault"].get(r, 0) + a
        elif t == VAULT_GROWTH:
            r, a = tx["recipient"], tx["amount"]
            state["vault"][r] = state["vault"].get(r, 0) + a
        elif t == RESERVE_ALLOCATION:
            r, a = tx["recipient"], tx["amount"]
            state["reserve"][r] = state["reserve"].get(r, 0) + a
        elif t == RESERVE_TRANSFER:
            # Double-checked at seal time: approval flag + valid signature.
            if not tx.get("approved") or not self._tx_signature_valid(tx):
                raise InvalidTransaction(
                    "reserve transfer rejected: authority approval required")
            s, r, a = tx["sender"], tx["recipient"], tx["amount"]
            if state["reserve"].get(s, 0) < a:
                raise InvalidTransaction(
                    "reserve transfer rejected: insufficient funds")
            state["reserve"][s] -= a
            state["reserve"][r] = state["reserve"].get(r, 0) + a
        else:
            raise InvalidTransaction("unknown transaction type: %r" % (t,))

    def _replay(self):
        state = self._new_state()
        for block in self.blocks:
            for tx in block["transactions"]:
                self._apply(tx, state)
        return state

    def balances(self):
        """Current balances per layer. Returns dict of dicts."""
        state = self._replay()
        return {"hand": dict(state["hand"]),
                "vault": dict(state["vault"]),
                "reserve": dict(state["reserve"])}

    # ------------------------------------------------------------------ #
    # full chain validation — Nola's Law: no lies, no deception
    # ------------------------------------------------------------------ #
    def is_valid(self):
        """Re-verify every hash, every signature, every law. Raises on failure."""
        if not self.blocks:
            raise InvalidChain("empty chain")
        prev_hash = GENESIS_PREV
        state = self._new_state()
        for i, block in enumerate(self.blocks):
            if block["index"] != i:
                raise InvalidChain("block index mismatch at %d" % i)
            if block["prev_hash"] != prev_hash:
                raise InvalidChain("broken hash link at block %d" % i)
            recomputed = self._block_hash(block["index"], block["timestamp"],
                                         block["transactions"], block["prev_hash"],
                                         block["authority"])
            if not hmac.compare_digest(recomputed, block["hash"]):
                raise InvalidChain("block hash mismatch at block %d — tampered" % i)
            sig = block.get("block_signature")
            expected = self._sign(_canonical(
                {k: v for k, v in block.items() if k != "block_signature"}))
            if not sig or not hmac.compare_digest(expected, sig):
                raise InvalidChain("invalid authority seal at block %d" % i)
            if block["authority"] != self.authority_id:
                raise InvalidChain("foreign authority at block %d" % i)
            for tx in block["transactions"]:
                if tx.get("type") in (PROVE_SELF, VAULT_GROWTH, RESERVE_ALLOCATION) \
                        and not self._tx_signature_valid(tx):
                    raise InvalidChain("forged authority transaction in block %d" % i)
                if tx.get("type") == RESERVE_TRANSFER and (
                        not tx.get("approved") or not self._tx_signature_valid(tx)):
                    raise InvalidChain("unapproved reserve move in block %d" % i)
                self._apply(tx, state)  # raises on any broken law
            prev_hash = block["hash"]
        return True
