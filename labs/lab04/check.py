"""Vérification automatique du lab 04 — Quality gate de couverture."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from checks import Lab, commit_runs, stage  # noqa: E402

lab = Lab("04", "Quality gate : un seuil de couverture de tests")


def seuil_configure():
    st = lab.stage_cfg("test") or {}
    v = st.get("coverage_min")
    try:
        return float(v) >= 80, f"coverage_min = {v!r} sur l'étape test (attendu au moins 80)"
    except (TypeError, ValueError):
        return False, "coverage_min absent de l'étape test"


def gate_a_bloque():
    for r in commit_runs(lab.runs()):
        s = stage(r, "test")
        if s and s["status"] == "failed" and "coverage" in s and s["coverage"] < s.get("coverage_min", 0):
            return True
    return False, "aucun pipeline bloqué par le seuil de couverture"


def mutant_tva():
    return lab.tests_fail_on_mutant("total += prix_ttc(prix_ht) * quantite", "total += prix_ht * quantite")


def mutant_quantite():
    return lab.tests_fail_on_mutant("if quantite <= 0:", "if quantite < 0:")


def dernier_vert_couverture():
    runs = commit_runs(lab.runs())
    if not runs:
        return False, "aucun pipeline"
    r = runs[-1]
    s = stage(r, "test") or {}
    cov = s.get("coverage")
    ok = r["status"] == "success" and cov is not None and cov >= 80 and r["commit"] == lab.head()
    return ok, f"dernier pipeline #{r['id']} : {r['status']}, couverture {cov}"


def staging_a_jour():
    cur = lab.current("staging")
    return cur == lab.head()[:7], f"staging sert {cur}, dernier commit {lab.head()[:7]}"


lab.check(3, "Un seuil coverage_min d'au moins 80 est configuré sur l'étape test", "Ajoutez coverage_min: 80 à l'étape test.",
          seuil_configure)
lab.check(2, "Le quality gate a bloqué au moins un pipeline", "Commitez le seuil AVANT d'écrire les nouveaux tests.",
          gate_a_bloque)
lab.check(3, "Les tests détectent un total calculé sans TVA (mutation)", "Testez la valeur du total d'un panier.",
          mutant_tva)
lab.check(2, "Les tests détectent l'acceptation d'une quantité nulle (mutation)",
          "Testez total_panier([(10, 0)]) avec assertRaises(ValueError).", mutant_quantite)
lab.check(3, "Dernier pipeline vert avec une couverture d'au moins 80 %", "Ajoutez des tests puis commitez.",
          dernier_vert_couverture)
lab.check(2, "Staging sert la version du dernier commit", "Le déploiement suit un pipeline vert.", staging_a_jour)
lab.run()
