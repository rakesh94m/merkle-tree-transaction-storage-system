import unittest

from merkle_tree_code import (
    build_merkle_proof,
    build_merkle_tree,
    verify_merkle_proof,
)


class MerkleProofTests(unittest.TestCase):
    def setUp(self):
        self.transactions = [
            "T1| Alice| Bob| 10.0| 2026-08-22 10:00:00",
            "T2| Carol| Dave| 20.0| 2026-08-22 10:01:00",
            "T3| Eve| Frank| 30.0| 2026-08-22 10:02:00",
            "T4| Grace| Heidi| 40.0| 2026-08-22 10:03:00",
        ]
        self.root = build_merkle_tree(self.transactions)["root"]
        self.proofs = [
            build_merkle_proof(self.transactions, index)
            for index in range(len(self.transactions))
        ]

    def test_unmodified_transaction_proof_remains_valid(self):
        self.assertTrue(
            verify_merkle_proof(self.transactions[2], self.proofs[2], self.root)
        )

    def test_tampered_transaction_fails_against_original_root(self):
        tampered_transaction = self.transactions[0].replace("10.0", "999.0")
        self.assertFalse(
            verify_merkle_proof(tampered_transaction, self.proofs[0], self.root)
        )

    def test_tampering_changes_root(self):
        tampered_transactions = self.transactions.copy()
        tampered_transactions[0] = tampered_transactions[0].replace("10.0", "999.0")
        tampered_root = build_merkle_tree(tampered_transactions)["root"]
        self.assertNotEqual(self.root, tampered_root)


if __name__ == "__main__":
    unittest.main()
