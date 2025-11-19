"""Vérification automatique du lab 01 — Premier pipeline."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs  # noqa: E402

lab = Lab("01", "Premier pipeline : du commit au déploiement")


def nouveau_commit():
    n = int(lab.git("rev-list", "--count", "HEAD"))
    return n >= 2, f"{n} commit(s) dans l'historique : seul le commit initial existe"


def pipeline_par_commit():
    n = len(commit_runs(lab.runs()))
    return n >= 1, "aucun pipeline déclenché par un commit"


def fonction_correcte():
    m = lab.module()
    f = getattr(m, "prix_ht_depuis_ttc", None)
    if f is None:
        return False, "fonction prix_ht_depuis_ttc absente de src/prix.py"
    got = (f(120), f(11.99))
    return got == (100.0, 9.99), f"prix_ht_depuis_ttc(120), prix_ht_depuis_ttc(11.99) = {got} ; attendu (100.0, 9.99)"


def test_present():
    return "prix_ht_depuis_ttc" in lab.read("tests/test_prix.py"), "aucun test ne mentionne prix_ht_depuis_ttc"


def test_utile():
    if "prix_ht_depuis_ttc" not in lab.read("src/prix.py"):
        return False, "fonction absente"
    return lab.tests_fail_on_mutant(None, "def prix_ht_depuis_ttc(prix_ttc, taux=0.2):\n    return -1.0")


def dernier_vert():
    runs = commit_runs(lab.runs())
    if not runs:
        return False, "aucun pipeline"
    r = runs[-1]
    st = {s["name"]: s["status"] for s in r["stages"]}
    return r["status"] == "success" and r["commit"] == lab.head(), \
        f"dernier pipeline #{r['id']} : {st}" + ("" if r["commit"] == lab.head() else " (pas sur le dernier commit)")


def staging_a_jour():
    cur = lab.current("staging")
    return cur == lab.head()[:7], f"staging sert {cur}, dernier commit {lab.head()[:7]}"


lab.check(2, "Un nouveau commit a été créé", "git add -A puis git commit -m \"...\"", nouveau_commit)
lab.check(2, "Le commit a déclenché un pipeline", "Le hook post-commit lance le pipeline ; ne contournez pas Git.",
          pipeline_par_commit)
lab.check(3, "prix_ht_depuis_ttc est correcte (120 -> 100.0, 11.99 -> 9.99)", "round(prix_ttc / (1 + taux), 2)",
          fonction_correcte)
lab.check(2, "Un test mentionne prix_ht_depuis_ttc", "Ajoutez une méthode de test dans tests/test_prix.py",
          test_present)
lab.check(2, "Le test détecte une fonction fausse (test de mutation)", "Le test doit appeler la fonction et vérifier son résultat.",
          test_utile)
lab.check(2, "Le dernier pipeline (sur le dernier commit) est vert", "Consultez ../../pipectl status 01 --last",
          dernier_vert)
lab.check(2, "Staging sert la version du dernier commit", "L'étape deploy-staging doit avoir réussi sur ce commit.",
          staging_a_jour)
lab.run()
