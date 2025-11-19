# Lab 01 — Premier pipeline : du commit au déploiement

**Durée indicative :** 25 min
**Objectifs :** comprendre qu'un commit déclenche un pipeline, lire ses étapes (build, test, déploiement) et suivre une modification jusqu'à l'environnement de staging.

## Contexte
L'espace de travail `workspace/lab01` est un dépôt Git qui contient l'application « boutique » (calculs de prix) et son pipeline `pipeline.yml`. Un hook Git exécute le pipeline **après chaque commit**.

## Étapes

1. Préparez le lab, puis placez-vous dans l'espace de travail :
   ```bash
   ./pipectl start 01
   cd workspace/lab01
   ```
2. Lisez `pipeline.yml` : quelles étapes seront exécutées, et dans quel ordre ?
3. Ouvrez la page de suivi dans votre navigateur. Elle se met à jour toute seule :
   ```bash
   ../../pipectl open 01
   ```
4. **Nouvelle fonctionnalité.** Dans `src/prix.py`, ajoutez la fonction
   `prix_ht_depuis_ttc(prix_ttc, taux=TAUX_TVA)`, qui retrouve le prix HT arrondi au centime.
   Par exemple, `prix_ht_depuis_ttc(120)` doit renvoyer `100.0`.
5. Ajoutez un test pour cette fonction dans `tests/test_prix.py`.
6. Commitez, puis **observez le pipeline se déclencher** dans le terminal et sur la page de suivi :
   ```bash
   git add -A
   git commit -m "Ajoute le calcul du prix HT depuis le TTC"
   ```
7. Vérifiez votre travail : `../../pipectl check 01`

## Questions de réflexion
1. Quelle version de l'application sert l'environnement de staging ? Quelle commande permet de le savoir ?
2. Pourquoi les tests passent-ils **avant** le déploiement ?
