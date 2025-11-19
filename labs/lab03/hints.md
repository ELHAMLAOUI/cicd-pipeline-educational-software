# Indices — Lab 03
1. Une étape s'écrit ainsi :
   ```yaml
     - name: lint
       run: python tools/lint.py src
   ```
2. Elle doit être le premier élément de la liste `stages`.
3. Le linter indique le fichier et le numéro de ligne de chaque problème.
