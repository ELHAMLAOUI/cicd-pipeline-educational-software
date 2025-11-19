"""Vérification automatique du lab 06 — Production et rollback."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs, stage  # noqa: E402

lab = Lab("06", "Production : contrôle de santé et rollback automatique")


def rollback_configure():
    st = lab.stage_cfg("deploy-production") or {}
    return st.get("on_failure") == "rollback", f"on_failure = {st.get('on_failure')!r} sur deploy-production"


def rollbacks():
    out = []
    for r in commit_runs(lab.runs()):
        s = stage(r, "deploy-production")
        if s and s["status"] == "failed" and s.get("rollback"):
            out.append(s)
    return out


def rollback_effectue():
    return bool(rollbacks()), "aucun déploiement en production n'a déclenché de rollback"


def service_preserve():
    rb = rollbacks()
    if not rb:
        return False, "pas de rollback"
    s = rb[-1]
    return s.get("previous") and s.get("current_after") == s["previous"], \
        f"après l'incident, la production servait {s.get('current_after')} au lieu de {s.get('previous')}"


def dernier_vert_prod():
    runs = commit_runs(lab.runs())
    if not runs:
        return False, "aucun pipeline"
    r = runs[-1]
    st = {s["name"]: s["status"] for s in r["stages"]}
    ok = r["status"] == "success" and st.get("deploy-production") == "success" and r["commit"] == lab.head()
    return ok, f"dernier pipeline #{r['id']} : {st}"


def prod_saine_et_a_jour():
    cur = lab.current("production")
    if lab.head() == lab.meta().get("initial"):
        return False, "aucun commit depuis la version initiale"
    if cur != lab.head()[:7]:
        return False, f"production sert {cur}, dernier commit {lab.head()[:7]}"
    rel = os.path.join(lab.ws, ".pipeline", "env", "production", "releases", cur)
    r = subprocess.run([sys.executable, "healthcheck.py", ".", "production"], cwd=rel, capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip()


def config_release2():
    with open(os.path.join(lab.ws, "config", "production.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    return "devise" in cfg and "currency" in cfg, f"clés présentes : {sorted(cfg)} (attendu devise ET currency)"


lab.check(3, "Le déploiement en production a on_failure: rollback", "Ajoutez on_failure: rollback à deploy-production.",
          rollback_configure)
lab.check(3, "Un déploiement en échec a déclenché un rollback", "Commitez la release 2 (devise -> currency) APRÈS le filet.",
          rollback_effectue)
lab.check(2, "Pendant l'incident, la production servait la version précédente", "Le rollback restaure la version précédente.",
          service_preserve)
lab.check(3, "Dernier pipeline vert jusqu'en production", "Corrigez la configuration puis commitez.", dernier_vert_prod)
lab.check(2, "La production sert le dernier commit et son contrôle de santé est OK", "../../pipectl status 06",
          prod_saine_et_a_jour)
lab.check(2, "La release 2 est livrée : config avec devise ET currency", "Gardez les deux clés dans config/production.json.",
          config_release2)
lab.run()
