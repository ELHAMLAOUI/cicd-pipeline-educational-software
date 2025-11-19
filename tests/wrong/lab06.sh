# Erreur typique : release 2 livrée SANS rollback configuré -> production en panne.
sed -i.bak 's/"devise"/"currency"/' config/production.json && rm -f config/production.json.bak
git commit -q -am "Release 2 : clé currency" || true
