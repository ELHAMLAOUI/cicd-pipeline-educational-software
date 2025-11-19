#!/usr/bin/env bash
# Solution du lab 04 — à exécuter dans workspace/lab04
set -e
python3 - <<'PY'
p = "pipeline.yml"; s = open(p, encoding="utf-8").read()
s = s.replace("    run: python -m unittest discover -s tests -v\n",
              "    run: python -m unittest discover -s tests -v\n    coverage_min: 80\n", 1)
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Ajoute un seuil de couverture de 80 % (quality gate)" || true   # bloqué : attendu
python3 - <<'PY'
p = "tests/test_prix.py"; s = open(p, encoding="utf-8").read()
s = s.replace("from prix import appliquer_remise, prix_ttc", "from prix import appliquer_remise, prix_ttc, total_panier")
s = s.replace('\n\nif __name__', '''

class TestPanier(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total_panier([(10, 2), (5, 1)]), 30.0)

    def test_quantite_invalide(self):
        with self.assertRaises(ValueError):
            total_panier([(10, 0)])


if __name__''')
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Teste le calcul du total du panier"
