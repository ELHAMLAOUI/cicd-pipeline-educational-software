TITLE = "Production : contrôle de santé et rollback automatique"


def setup(ctx):
    """La version initiale est déjà en production."""
    print("\nMise en production de la version initiale...")
    ctx.run_pipeline(trigger="manual")
