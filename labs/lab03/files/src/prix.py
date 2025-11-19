"""Calculs de prix de la boutique en ligne."""

TAUX_TVA = 0.20


def prix_ttc(prix_ht, taux=TAUX_TVA):
    """Prix toutes taxes comprises, arrondi au centime."""
    if prix_ht < 0:
        raise ValueError("Le prix HT doit être positif")
    return round(prix_ht * (1 + taux), 2)


def appliquer_remise(prix, pourcentage):
    """Applique une remise en pourcentage (0 à 100)."""
    if not 0 <= pourcentage <= 100:
        raise ValueError("La remise doit être comprise entre 0 et 100")
    return round(prix * (1 - pourcentage / 100), 2)


def total_panier(articles):
    """Total TTC d'un panier : liste de couples (prix_ht, quantite)."""
    total = 0
    for prix_ht, quantite in articles:
        if quantite <= 0:
            raise ValueError("Quantité invalide")
        print("DEBUG panier", prix_ht, quantite)
        total += prix_ttc(prix_ht) * quantite
    return round(total, 2)
