"""Vérification automatique du lab 03 — Étape de lint."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs, stage  # noqa: E402

lab = Lab("03", "Ajouter une étape : le lint comme garde-fou")


def etape_lint():
    return lab.stage_cfg("lint") is not None, "aucune étape nommée « lint » dans pipeline.yml"


def lint_en_premier():
    names = [s["name"] for s in lab.config()["stages"]]
    return names[:1] == ["lint"], f"ordre des étapes : {names}"


def lint_commande():
    st = lab.stage_cfg("lint") or {}
    return "tools/lint.py" in str(st.get("run", "")), f"commande de l'étape lint : {st.get('run')!r}"


def lint_a_bloque():
    for r in commit_runs(lab.runs()):
        s = stage(r, "lint")
        if s and s["status"] == "failed" and all(x["status"] == "skipped" for x in r["stages"][1:]):
            return True
    return False, "aucun pipeline où le lint a échoué et bloqué les étapes suivantes"


def code_conforme():
    r = subprocess.run([sys.executable, "tools/lint.py", "src"], cwd=lab.ws, capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip().splitlines()[0] if r.stdout.strip() else "lint en échec"


def dernier_vert_avec_lint():
    runs = commit_runs(lab.runs())
    if not runs:
        return False, "aucun pipeline"
    r = runs[-1]
    s = stage(r, "lint")
    return r["status"] == "success" and s is not None and s["status"] == "success" and r["commit"] == lab.head(), \
        f"dernier pipeline #{r['id']} : {r['status']}, lint {'absent' if s is None else s['status']}"


lab.check(3, "pipeline.yml contient une étape lint", "Ajoutez « - name: lint » à la liste stages.", etape_lint)
lab.check(2, "L'étape lint est la première", "Placez lint en tête de la liste stages.", lint_en_premier)
lab.check(2, "L'étape lint exécute tools/lint.py", "run: python tools/lint.py src", lint_commande)
lab.check(2, "Le lint a bloqué au moins un pipeline (fail fast)",
          "Commitez la nouvelle étape AVANT de corriger le code, et observez.", lint_a_bloque)
lab.check(3, "Le code respecte les règles du lint", "Supprimez l'appel à print() de src/prix.py.", code_conforme)
lab.check(3, "Dernier pipeline vert, lint compris", "Commitez la correction et vérifiez avec ../../pipectl status 03.",
          dernier_vert_avec_lint)
lab.run()
