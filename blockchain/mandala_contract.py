# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""
The Mandala Contract, enforced in code.

MandalaContract is the law-enforcing facade over MandalaChain. It binds the
articles of MANDALA_CONTRACT.md to the ledger:

  Article III (The Hand)   — attest() records a showing. There is DELIBERATELY
                             no method that debits the Hand. The Hand cannot
                             be spent because no code path exists to spend it.
  Article IV (The Vault)   — transfer() and grow(); every movement carries a
                             memo (a named reason). The chain refuses
                             double-spends at seal time.
  Article V (The Reserve)  — reserve_move() requires the Authority's signature
                             AND an explicit approval flag. Unapproved moves
                             are refused before they touch the chain.
  Article VI (Proof of Self) — a fingerprint registry: one fingerprint, one
                             citizen, one mandala. issue() grants exactly one.

Deliberately NOT implemented: any treasury entry-fee path. The Declaration
says the mandala is shown, not consumed; a threshold design moves one
mandala to a treasury on entry. Curtis has NOT ruled between them
(MANDALA_CONTRACT.md Article X — AWAITING HIS RULING), so no code here moves
a mandala to any treasury on entry. The question stays open until his word
closes it.

Stdlib only. The authority's private key is never stored in this repository.
"""

from mandala_blockchain import (
    MandalaChain,
    InvalidTransaction,
)


class ContractViolation(Exception):
    """Raised when an action breaks the Mandala Contract."""


class MandalaContract:
    """The Mandala Contract bound to a MandalaChain. The Authority operates it."""

    def __init__(self, chain: MandalaChain):
        self.chain = chain
        self._fingerprints = {}  # fingerprint_id -> citizen
        self._citizen_prints = {}  # citizen -> fingerprint_id
        self._issued = set()  # citizens granted proof-of-self via this contract

    def _sealed_balances(self):
        return self.chain.balances()

    # ------------------------------------------------------------------ #
    # Article VI — proof of self
    # ------------------------------------------------------------------ #
    def register_fingerprint(self, citizen: str, fingerprint_id: str):
        """Bind one fingerprint to one citizen. Neither may repeat."""
        if not citizen or not fingerprint_id:
            raise ContractViolation("citizen and fingerprint_id are required")
        holder = self._fingerprints.get(fingerprint_id)
        if holder is not None and holder != citizen:
            raise ContractViolation(
                "fingerprint already carried by %r — one fingerprint, one citizen"
                % (holder,))
        existing = self._citizen_prints.get(citizen)
        if existing is not None and existing != fingerprint_id:
            raise ContractViolation(
                "citizen %r already proved with a different fingerprint" % (citizen,))
        self._fingerprints[fingerprint_id] = citizen
        self._citizen_prints[citizen] = fingerprint_id

    def issue(self, citizen: str, fingerprint_id: str):
        """Grant one mandala to one proven citizen's Hand. Once, ever."""
        if citizen in self._issued:
            raise ContractViolation(
                "proof-of-self already granted to %r — one mandala per citizen"
                % (citizen,))
        self.register_fingerprint(citizen, fingerprint_id)
        tx = self.chain.sign_transaction(MandalaChain.make_prove_self(citizen))
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        self._issued.add(citizen)
        return tx

    # ------------------------------------------------------------------ #
    # Article III — the Hand: attest only. No debit path exists. Ever.
    # ------------------------------------------------------------------ #
    def attest(self, citizen: str, where: str):
        """Record a showing of the mandala. Moves nothing — by construction."""
        if self._sealed_balances()["hand"].get(citizen, 0) < 1:
            raise ContractViolation(
                "hand attestation refused: %r holds no mandala to show"
                % (citizen,))
        tx = MandalaChain.make_hand_attest(citizen, where)
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        return tx

    # NOTE: there is intentionally no spend_hand(), debit_hand(), or
    # hand_transfer() method. The Hand is shown, never spent (Article III).

    # ------------------------------------------------------------------ #
    # Article IV — the Vault: transfers and approved growth, memo required
    # ------------------------------------------------------------------ #
    def transfer(self, sender: str, recipient: str, amount: int, memo: str):
        """Move Vault mandalas citizen to citizen. Memo is required."""
        if not memo or not memo.strip():
            raise ContractViolation(
                "vault transfer requires a memo — honest money names its reason")
        if not (isinstance(amount, int) and amount > 0):
            raise ContractViolation("amount must be a positive integer")
        # Count what's already promised in the mempool — a citizen cannot
        # promise the same mandala twice, even before sealing.
        pending_out = sum(t.get("amount", 0) for t in self.chain.mempool
                          if t.get("type") == "vault_transfer"
                          and t.get("sender") == sender)
        available = self._sealed_balances()["vault"].get(sender, 0) - pending_out
        if available < amount:
            raise ContractViolation(
                "vault transfer refused: insufficient funds (double-spend)")
        tx = MandalaChain.make_vault_transfer(sender, recipient, amount,
                                              memo=memo.strip())
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        return tx

    def grow(self, recipient: str, amount: int, reason: str):
        """Record multiplication-law growth. Authority-signed, reason named."""
        if not reason or not reason.strip():
            raise ContractViolation(
                "growth requires a named reason — every new mandala says why it exists")
        tx = self.chain.sign_transaction(
            MandalaChain.make_vault_growth(recipient, amount,
                                           memo=reason.strip()))
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        return tx

    # ------------------------------------------------------------------ #
    # Article V — the Reserve: approval or nothing
    # ------------------------------------------------------------------ #
    def fund_reserve(self, recipient: str, amount: int, memo: str):
        """Authority-signed allocation into the Reserve."""
        tx = self.chain.sign_transaction(
            MandalaChain.make_reserve_allocation(recipient, amount,
                                                memo=memo or ""))
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        return tx

    def reserve_move(self, sender: str, recipient: str, amount: int,
                     approved: bool, memo: str = ""):
        """Move Reserve funds. Requires explicit approval AND valid signature."""
        if not approved:
            raise ContractViolation(
                "reserve move refused: no authority approval — "
                "no signature, no approval, no movement")
        tx = self.chain.sign_transaction(
            MandalaChain.make_reserve_transfer(sender, recipient, amount,
                                               approved=True,
                                               memo=memo or ""))
        try:
            self.chain.add_transaction(tx)
        except InvalidTransaction as e:
            raise ContractViolation(str(e))
        return tx

    # ------------------------------------------------------------------ #
    # sealing + reading
    # ------------------------------------------------------------------ #
    def seal(self):
        """Seal pending contract actions into a block under the mandala laws."""
        try:
            return self.chain.seal_block()
        except InvalidTransaction as e:
            raise ContractViolation(str(e))

    def balances(self):
        return self.chain.balances()

    def validate(self):
        """Re-verify the whole chain. Nola's Law: no lies, no deception."""
        return self.chain.is_valid()
