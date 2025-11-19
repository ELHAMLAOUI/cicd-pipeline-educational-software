#!/usr/bin/env bash
# Solution du lab 05 — à exécuter dans workspace/lab05
set -e
python3 - <<'PY'
p = "pipeline.yml"; s = open(p, encoding="utf-8").read()
s = s.replace("    deploy: staging\n", "    deploy: staging\n    when: branch == main\n", 1)
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Ne déploie en staging que depuis main"
git switch -q -c feature/remise-fidelite
python3 - <<'PY'
p = "src/prix.py"; s = open(p, encoding="utf-8").read()
s += '''

def remise_fidelite(prix, annees):
    """1 % de remise par année d'ancienneté, plafonnée à 10 %."""
    return appliquer_remise(prix, min(annees, 10))
'''
open(p, "w", encoding="utf-8").write(s)
p = "tests/test_prix.py"; s = open(p, encoding="utf-8").read()
s = s.replace("from prix import appliquer_remise, prix_ttc, total_panier",
              "from prix import appliquer_remise, prix_ttc, remise_fidelite, total_panier")
s = s.replace('\n\nif __name__', '''

class TestFidelite(unittest.TestCase):
    def test_trois_ans(self):
        self.assertEqual(remise_fidelite(100, 3), 97.0)

    def test_plafond(self):
        self.assertEqual(remise_fidelite(100, 20), 90.0)


if __name__''')
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Ajoute la remise de fidélité (1 % par an, plafond 10 %)"
git switch -q main
git merge -q feature/remise-fidelite
