# Erreur typique : pas de condition de branche ; la branche de travail est déployée en staging.
git switch -q -c feature/remise-fidelite
cat >> src/prix.py <<'PY'


def remise_fidelite(prix, annees):
    return appliquer_remise(prix, annees)
PY
git commit -q -am "Ajoute la remise de fidélité"
