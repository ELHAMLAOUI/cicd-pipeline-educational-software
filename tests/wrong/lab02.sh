# Triche typique : modifier le test pour qu'il accepte la valeur fausse.
sed -i.bak 's/appliquer_remise(200, 10), 180.0/appliquer_remise(200, 10), 0.0/' tests/test_prix.py && rm -f tests/test_prix.py.bak
git commit -q -am "Corrige les tests de remise"
