# Lab 03 — Ajouter une étape : le lint comme garde-fou

**Durée indicative :** 25 min
**Objectifs :** modifier la définition d'un pipeline, comprendre l'intérêt d'échouer tôt (*fail fast*), faire respecter des règles de qualité de code automatiquement.

## Contexte
L'équipe adopte des règles de code, vérifiées par `tools/lint.py` :
- pas de tabulation ;
- 100 caractères au plus par ligne ;
- pas d'appel à `print()` dans le code applicatif.

Aujourd'hui, rien n'empêche de livrer du code qui viole ces règles.

## Étapes

1. `./pipectl start 03`, puis `cd workspace/lab03`.
2. Lancez le linter à la main : `python3 tools/lint.py src`. Que trouve-t-il ?
3. Dans `pipeline.yml`, ajoutez une étape nommée **`lint`**, placée **en premier**, qui exécute :
   ```
   python tools/lint.py src
   ```
4. Commitez **sans corriger le code** et observez : le lint échoue et les étapes suivantes ne s'exécutent pas.
5. Corrigez le code en supprimant l'appel à `print()`, puis commitez : le pipeline doit repasser au vert.
6. `../../pipectl check 03`

## Questions de réflexion
1. Pourquoi placer le lint **avant** le build et les tests ?
2. Quelles autres vérifications automatiques ajouteriez-vous à ce stade (sécurité, dépendances, formatage) ?
