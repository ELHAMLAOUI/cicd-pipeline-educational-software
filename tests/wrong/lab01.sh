# Erreur typique : la fonction est ajoutée mais rien n'est commité ; pipeline lancé à la main.
cat >> src/prix.py <<'PY'


def prix_ht_depuis_ttc(prix_ttc, taux=TAUX_TVA):
    return round(prix_ttc / (1 + taux), 2)
PY
python3 ../../engine/pipectl.py run --workspace . >/dev/null 2>&1 || "$PIPECTL" run --workspace . >/dev/null
