# Erreur typique : lint ajouté en DERNIER, code corrigé avant (le lint ne bloque jamais rien).
grep -v 'print("DEBUG panier"' src/prix.py > src/prix.tmp && mv src/prix.tmp src/prix.py
printf '  - name: lint\n    run: python tools/lint.py src\n' >> pipeline.yml
git commit -q -am "Ajoute le lint et nettoie le code"
