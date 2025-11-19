#!/usr/bin/env bash
# Solution du lab 01 — à exécuter dans workspace/lab01
set -e
python3 - <<'PY'
p = "src/prix.py"; s = open(p, encoding="utf-8").read()
s += '''

def prix_ht_depuis_ttc(prix_ttc, taux=TAUX_TVA):
    """Prix hors taxes à partir du prix TTC, arrondi au centime."""
    return round(prix_ttc / (1 + taux), 2)
'''
open(p, "w", encoding="utf-8").write(s)
p = "tests/test_prix.py"; s = open(p, encoding="utf-8").read()
s = s.replace("from prix import appliquer_remise, prix_ttc, total_panier",
              "from prix import appliquer_remise, prix_ht_depuis_ttc, prix_ttc, total_panier")
s = s.replace('\n\nif __name__', '''

class TestPrixHT(unittest.TestCase):
    def test_inverse_du_ttc(self):
        self.assertEqual(prix_ht_depuis_ttc(120), 100.0)
        self.assertEqual(prix_ht_depuis_ttc(11.99), 9.99)


if __name__''')
open(p, "w", encoding="utf-8").write(s)
PY
git add -A
git commit -q -m "Ajoute le calcul du prix HT depuis le TTC"
