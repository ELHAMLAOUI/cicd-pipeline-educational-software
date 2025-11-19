# Lab 05 — Branches : ne déployer que depuis main

**Durée indicative :** 35 min
**Objectifs :** adapter le pipeline à la branche (intégration continue sur toutes les branches, déploiement depuis `main` uniquement), travailler sur une branche de fonctionnalité puis la fusionner.

## Contexte
Aujourd'hui, **n'importe quelle branche** est déployée en staging, y compris un travail en cours. L'équipe veut :
- sur toutes les branches : build et tests (intégration continue) ;
- sur `main` uniquement : déploiement en staging.

## Étapes

1. `./pipectl start 05`, puis `cd workspace/lab05`.
2. Dans `pipeline.yml`, ajoutez à l'étape `deploy-staging` la condition :
   ```yaml
       when: branch == main
   ```
   Commitez sur `main`.
3. Créez une branche de fonctionnalité :
   ```bash
   git switch -c feature/remise-fidelite
   ```
4. Ajoutez dans `src/prix.py` la fonction `remise_fidelite(prix, annees)` : 1 % de remise par année d'ancienneté, **plafonnée à 10 %**, avec un résultat arrondi au centime. Par exemple, `remise_fidelite(100, 3)` renvoie `97.0` et `remise_fidelite(100, 20)` renvoie `90.0`. Ajoutez les tests correspondants.
5. Commitez sur la branche : le pipeline exécute build et test, mais **ignore le déploiement**.
6. Fusionnez dans `main` :
   ```bash
   git switch main
   git merge feature/remise-fidelite
   ```
   La fusion déclenche le pipeline sur `main`, qui déploie cette fois en staging.
7. `../../pipectl check 05`

## Questions de réflexion
1. Pourquoi exécuter les tests sur toutes les branches, et pas seulement sur `main` ?
2. Que faudrait-il pour imposer qu'une branche ne soit fusionnée que si son pipeline est vert ?
