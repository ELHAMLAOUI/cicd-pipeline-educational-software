#!/usr/bin/env bash
# Solution du lab 06 — à exécuter dans workspace/lab06
set -e
python3 - <<'PY'
p = "pipeline.yml"; s = open(p, encoding="utf-8").read()
s = s.replace("    deploy: production\n", "    deploy: production\n    on_failure: rollback\n", 1)
open(p, "w", encoding="utf-8").write(s)
PY
git commit -q -am "Active le rollback automatique en production"
sed -i.bak 's/"devise"/"currency"/' config/production.json && rm -f config/production.json.bak
git commit -q -am "Release 2 : clé currency dans la configuration de production" || true   # rollback : attendu
printf '{\n  "devise": "MAD",\n  "currency": "MAD",\n  "tva": 0.2\n}\n' > config/production.json
git commit -q -am "Rétablit la clé devise utilisée par l'application (garde currency)"
