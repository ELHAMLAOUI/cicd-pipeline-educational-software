# Indices — Lab 06
1. `on_failure: rollback` se place sous l'étape `deploy-production`, au même niveau que `deploy: production`.
2. Exemple de configuration finale :
   ```json
   { "devise": "MAD", "currency": "MAD", "tva": 0.2 }
   ```
3. Les versions déployées se trouvent dans `.pipeline/env/production/releases/`.
