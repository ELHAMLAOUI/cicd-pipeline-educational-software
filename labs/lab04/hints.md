# Indices — Lab 04
1. L'étape test devient :
   ```yaml
     - name: test
       run: python -m unittest discover -s tests -v
       coverage_min: 80
   ```
2. Pensez à importer `total_panier` dans le fichier de test.
3. `with self.assertRaises(ValueError):` vérifie qu'une erreur est levée.
4. Panier exemple : `[(10, 2), (5, 1)]` donne 30.0 TTC.
