"""Vérification automatique du lab 05 — Branches."""
import fnmatch
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs, stage  # noqa: E402

lab = Lab("05", "Branches : ne déployer que depuis main")


def condition_main():
    st = lab.stage_cfg("deploy-staging") or {}
    cond = re.sub(r"\s+", " ", str(st.get("when", ""))).strip()
    return cond == "branch == main", f"when = {st.get('when')!r} sur deploy-staging (attendu « branch == main »)"


def pipeline_feature():
    for r in commit_runs(lab.runs()):
        if fnmatch.fnmatch(r["branch"], "feature/*"):
            b, t, d = stage(r, "build"), stage(r, "test"), stage(r, "deploy-staging")
            if b and t and d and b["status"] == t["status"] == "success" and d["status"] == "skipped":
                return True
    return False, "aucun pipeline sur une branche feature/* avec build et test réussis et déploiement ignoré"


def fonction_correcte():
    f = getattr(lab.module(), "remise_fidelite", None)
    if f is None:
        return False, "remise_fidelite absente de src/prix.py sur la branche courante"
    got = (f(100, 3), f(100, 20), f(80, 0))
    return got == (97.0, 90.0, 80.0), f"(100,3), (100,20), (80,0) -> {got} ; attendu (97.0, 90.0, 80.0)"


def fusionnee():
    branches = [b.strip().lstrip("* ") for b in lab.git("branch", "--list", "feature/*").splitlines()]
    if not branches:
        return False, "aucune branche feature/*"
    initial = lab.meta().get("initial")
    for b in branches:
        travail = int(lab.git("rev-list", "--count", f"{initial}..{b}") or 0) if initial else 1
        if travail >= 1 and lab.git_ok("merge-base", "--is-ancestor", b, "main"):
            return True
    return False, f"branche(s) {branches} sans commit ou non fusionnée(s) dans main"


def vert_sur_main_avec_deploy():
    for r in reversed(commit_runs(lab.runs())):
        if r["branch"] == "main":
            d = stage(r, "deploy-staging")
            ok = r["status"] == "success" and d and d["status"] == "success" and \
                "def remise_fidelite" in lab.git("show", f"{r['commit']}:src/prix.py")
            return bool(ok), f"dernier pipeline sur main #{r['id']} : {r['status']}" + \
                ("" if ok else " (sans la fonctionnalité fusionnée ou sans déploiement)")
    return False, "aucun pipeline sur main"


def staging_contient():
    cur = lab.current("staging")
    if not cur:
        return False, "rien n'est déployé en staging"
    p = os.path.join(lab.ws, ".pipeline", "env", "staging", "releases", cur, "src", "prix.py")
    with open(p, encoding="utf-8") as fh:
        return "def remise_fidelite" in fh.read(), f"la version {cur} servie en staging ne contient pas remise_fidelite"


lab.check(3, "deploy-staging ne s'exécute que sur main", "when: branch == main", condition_main)
lab.check(3, "Sur feature/* : build et test exécutés, déploiement ignoré",
          "Commitez sur une branche feature/... après avoir ajouté la condition.", pipeline_feature)
lab.check(2, "remise_fidelite est correcte (1 %/an, plafond 10 %)", "appliquer_remise(prix, min(annees, 10))",
          fonction_correcte)
lab.check(2, "La branche de fonctionnalité est fusionnée dans main", "git switch main && git merge feature/...",
          fusionnee)
lab.check(3, "Pipeline vert sur main après la fusion, avec déploiement", "La fusion déclenche le pipeline sur main.",
          vert_sur_main_avec_deploy)
lab.check(2, "Staging sert une version qui contient remise_fidelite", "Le déploiement doit suivre la fusion.",
          staging_contient)
lab.run()
