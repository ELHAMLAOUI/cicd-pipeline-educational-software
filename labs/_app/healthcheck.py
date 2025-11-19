"""Contrôle de santé exécuté après chaque déploiement.

Usage : python healthcheck.py <dossier de la version déployée> <environnement>
Code retour 0 = service sain ; autre = service en panne (rollback possible).
"""
import importlib.util
import json
import os
import sys

release, env = sys.argv[1], sys.argv[2]
try:
    spec = importlib.util.spec_from_file_location("prix", os.path.join(release, "src", "prix.py"))
    prix = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prix)
    assert prix.prix_ttc(100) == 120.0, "prix_ttc(100) devrait valoir 120.0"
    cfg_file = os.path.join(release, "config", f"{env}.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding="utf-8") as fh:
            cfg = json.load(fh)
        assert "devise" in cfg, f"clé « devise » absente de config/{env}.json"
except Exception as e:  # noqa: BLE001
    print(f"KO — {e}")
    sys.exit(1)
print("OK — service opérationnel")
