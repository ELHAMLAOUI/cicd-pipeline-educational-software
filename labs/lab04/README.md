# Lab 04 — Quality gate : un seuil de couverture de tests

**Durée indicative :** 30 min
**Objectifs :** mettre en place un *quality gate* (seuil de qualité bloquant), mesurer la couverture de code, écrire des tests qui vérifient vraiment le comportement.

## Contexte
Les tests passent, mais la fonction `total_panier` n'est **jamais testée**. Un pipeline vert ne garantit donc pas grand-chose. L'équipe décide d'exiger **au moins 80 % de couverture** du code par les tests.

> Prérequis : `pip install coverage`

## Étapes

1. `./pipectl start 04`, puis `cd workspace/lab04`.
2. Mesurez la couverture actuelle :
   ```bash
   python3 -m coverage run --source=src -m unittest discover -s tests
   python3 -m coverage report -m
   ```
   Quelles lignes ne sont jamais exécutées ?
3. Dans `pipeline.yml`, ajoutez à l'étape `test` la clé :
   ```yaml
       coverage_min: 80
   ```
4. Commitez : le pipeline doit échouer sur le quality gate.
5. Dans `tests/test_prix.py`, écrivez des tests pour `total_panier` :
   - le total d'un panier de plusieurs articles ;
   - le rejet d'une quantité invalide (`ValueError`).
6. Commitez : le pipeline repasse au vert et la couverture est affichée.
7. `../../pipectl check 04` vérifie aussi, par **test de mutation**, que vos tests détectent de vrais défauts.

## Questions de réflexion
1. 100 % de couverture garantit-il l'absence de bug ? Donnez un contre-exemple.
2. Pourquoi le seuil doit-il être **bloquant** pour être utile ?
