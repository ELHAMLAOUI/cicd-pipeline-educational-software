import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prix import appliquer_remise, prix_ttc  # noqa: E402


class TestPrixTTC(unittest.TestCase):
    def test_tva_20(self):
        self.assertEqual(prix_ttc(100), 120.0)

    def test_arrondi(self):
        self.assertEqual(prix_ttc(9.99), 11.99)

    def test_prix_negatif(self):
        with self.assertRaises(ValueError):
            prix_ttc(-1)


class TestRemise(unittest.TestCase):
    def test_remise_10(self):
        self.assertEqual(appliquer_remise(200, 10), 180.0)

    def test_remise_hors_bornes(self):
        with self.assertRaises(ValueError):
            appliquer_remise(100, 120)


if __name__ == "__main__":
    unittest.main()
