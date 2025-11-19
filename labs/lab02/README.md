# Lab 02 — Casser et réparer : le pipeline protège la production

**Durée indicative :** 25 min
**Objectifs :** lire le journal d'un pipeline en échec, comprendre pourquoi le déploiement est bloqué, corriger dans le code (et non dans les tests) par un nouveau commit.

## Situation de départ
Au lab 01, l'application était saine. Ici, **un collègue vient de commiter une « optimisation » de la remise** : le pipeline est passé au rouge et le déploiement en staging n'a pas eu lieu.

## Étapes

1. `./pipectl start 02`, puis `cd workspace/lab02`.
2. Observez le pipeline en échec :
   ```bash
   ../../pipectl status 02 --last
   ```
   Quelle étape a échoué ? Quel test, et avec quelles valeurs ? Que sont devenues les étapes suivantes ?
3. Retrouvez la modification fautive : `git log --oneline` puis `git show HEAD`.
4. Corrigez **le code** de `src/prix.py`. Ne modifiez pas les tests : ils ont raison.
5. Commitez votre correctif avec un message explicite. Ne réécrivez pas l'historique : pas de `git commit --amend`, pas de `git reset`.
6. Vérifiez que le pipeline repasse au vert et que staging sert votre correctif : `../../pipectl status 02`
7. `../../pipectl check 02`

## Questions de réflexion
1. Que se serait-il passé sans l'étape de test ?
2. Pourquoi est-il préférable de corriger par un nouveau commit plutôt que de réécrire l'historique ?
