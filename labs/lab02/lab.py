TITLE = "Casser et réparer : le pipeline protège la production"


def setup(ctx):
    """Un collègue pousse une « remise de fin d'année » boguée : le pipeline doit passer au rouge."""
    ctx.save_meta(tests_initial=ctx.read("tests/test_prix.py"))
    ctx.replace("src/prix.py", "return round(prix * (1 - pourcentage / 100), 2)",
                "return round(prix * (1 - pourcentage / 10), 2)")
    print("\nUn collègue vient de commiter une modification de la remise...")
    bug = ctx.commit("Remise de fin d'année : optimisation du calcul")
    ctx.save_meta(bug_commit=bug)
