"""Linter minimal de la boutique.

Règles : pas de tabulation, lignes de 100 caractères au plus,
pas d'appel à print() dans le code applicatif (utiliser un logger).
Usage : python tools/lint.py <dossier>
"""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "src"
problems = []
for dirpath, _, files in os.walk(root):
    for name in sorted(files):
        if not name.endswith(".py"):
            continue
        path = os.path.join(dirpath, name)
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if "\t" in line:
                    problems.append(f"{path}:{n}: tabulation interdite")
                if len(line.rstrip("\n")) > 100:
                    problems.append(f"{path}:{n}: ligne de plus de 100 caractères")
                if re.search(r"(^|[^\w.])print\(", line.split("#")[0]):
                    problems.append(f"{path}:{n}: print() interdit dans le code applicatif")
for p in problems:
    print(p)
print(f"{len(problems)} problème(s) trouvé(s)" if problems else "Lint OK")
sys.exit(1 if problems else 0)
