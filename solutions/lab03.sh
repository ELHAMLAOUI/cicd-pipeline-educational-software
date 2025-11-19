#!/usr/bin/env bash
# Solution du lab 03 — à exécuter dans workspace/lab03
set -e
python3 - <<'PY'
p = "pipeline.yml"; s = open(p, encoding="utf-8").read()
s = s.replace("stages:\n", "stages:\n  - name: lint\n    run: python tools/lint.py src\n", 1)
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Ajoute une étape de lint en tête du pipeline" || true   # le lint échoue : attendu
grep -v 'print("DEBUG panier"' src/prix.py > src/prix.tmp && mv src/prix.tmp src/prix.py
git commit -q -am "Supprime l'affichage de debug du calcul du panier"
