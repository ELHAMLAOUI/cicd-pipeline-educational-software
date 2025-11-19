"""Vérification automatique du lab 02 — Casser et réparer."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs  # noqa: E402

lab = Lab("02", "Casser et réparer : le pipeline protège la production")


def remise_corrigee():
    got = lab.module().appliquer_remise(200, 10)
    return got == 180.0, f"appliquer_remise(200, 10) = {got} ; attendu 180.0"


def correctif_commit_distinct():
    bug = lab.meta().get("bug_commit")
    if not bug:
        return False, "commit du collègue introuvable (relancez ./pipectl reset 02)"
    if lab.head() == bug:
        return False, "aucun commit de correction après celui du collègue"
    return lab.git_ok("merge-base", "--is-ancestor", bug, "HEAD"), \
        "le commit du collègue a disparu de l'historique (amend / reset ?)"


def pipeline_vert_apres_echec():
    runs = commit_runs(lab.runs())
    fail = [r for r in runs if r["status"] == "failed"]
    ok_after = [r for r in runs if r["status"] == "success" and fail and r["id"] > fail[0]["id"]]
    return bool(ok_after), "aucun pipeline vert après le pipeline en échec"


def tests_intacts():
    initial = lab.meta().get("tests_initial")
    runs = commit_runs(lab.runs())
    if not runs or runs[-1]["status"] != "success":
        return False, "pas encore de pipeline vert"
    return lab.read("tests/test_prix.py") == initial, "tests/test_prix.py a été modifié"


def staging_corrige():
    cur = lab.current("staging")
    if cur != lab.head()[:7]:
        return False, f"staging sert {cur}, dernier commit {lab.head()[:7]}"
    got = lab.module(os.path.join(".pipeline", "env", "staging", "releases", cur, "src", "prix.py")).appliquer_remise(200, 10)
    return got == 180.0, f"la version servie en staging calcule appliquer_remise(200, 10) = {got}"


def message_explicite():
    bug = lab.meta().get("bug_commit")
    if not bug or lab.head() == bug:
        return False, "pas encore de commit de correction"
    msg = lab.git("log", "-1", "--format=%s").strip()
    vague = {"fix", "wip", "correction", "update", "maj", "test", "ok", "."}
    return len(msg) >= 15 and msg.lower() not in vague, f"message « {msg} » trop vague (15 caractères minimum)"


lab.check(3, "La remise est corrigée : appliquer_remise(200, 10) = 180.0", "Une remise de 10 % multiplie le prix par 0,90.",
          remise_corrigee)
lab.check(2, "Le correctif est un nouveau commit (historique non réécrit)", "Pas de --amend ni de reset : un nouveau commit.",
          correctif_commit_distinct)
lab.check(3, "Un pipeline vert a suivi le pipeline en échec", "Commitez votre correction : le pipeline se relance.",
          pipeline_vert_apres_echec)
lab.check(3, "La correction est dans le code, les tests sont intacts", "Ne modifiez pas tests/test_prix.py : ils ont raison.",
          tests_intacts)
lab.check(2, "Staging sert la version corrigée", "Le déploiement n'a lieu que si build et test réussissent.",
          staging_corrige)
lab.check(2, "Le message du commit de correction est explicite", "Décrivez ce qui est corrigé (15 caractères minimum).",
          message_explicite)
lab.run()
