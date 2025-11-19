# Lab 06 — Production : contrôle de santé et rollback automatique

**Durée indicative :** 35 min
**Objectifs :** comprendre le déploiement continu jusqu'en production, le rôle du contrôle de santé (*healthcheck*) et du retour arrière automatique (*rollback*), gérer un incident sans interrompre le service.

## Contexte
Le pipeline déploie en **staging** puis en **production**. Après chaque déploiement, `healthcheck.py` vérifie que le service fonctionne : calcul de prix et configuration de l'environnement. La version initiale est déjà en production.

## Étapes

1. `./pipectl start 06`, puis `cd workspace/lab06`. Repérez la version servie en production : `../../pipectl status 06`.
2. **Filet de sécurité.** Dans `pipeline.yml`, ajoutez à l'étape `deploy-production` :
   ```yaml
       on_failure: rollback
   ```
   Commitez, puis vérifiez que la production sert ce nouveau commit.
3. **Release 2.** Le service marketing demande d'utiliser la clé anglaise `currency` dans `config/production.json`. Renommez `devise` en `currency`, puis commitez.
4. Observez : les tests passent et staging est déployé, mais le contrôle de santé de **production** échoue. Le rollback remet en service la version précédente. Lisez le journal : `../../pipectl status 06 --last`
5. **Correctif.** L'application lit encore la clé `devise` : gardez **les deux clés**, `devise` et `currency`, puis commitez. Le pipeline doit repasser au vert jusqu'en production.
6. `../../pipectl check 06`

## Questions de réflexion
1. Pourquoi les tests n'ont-ils pas détecté le problème ? Qu'est-ce qui différait entre staging et production ?
2. Sans `on_failure: rollback`, dans quel état aurait été la production après l'étape 3 ?
3. Quelles sont les limites d'un rollback, par exemple en cas de migration de base de données ?
