"""
Category models for the Money application.
"""


class Categorie:
    """Represents a financial category."""

    def __init__(self, nom):
        self.nom = nom


class SousCategorie:
    """Represents a subcategory."""

    def __init__(self, nom, categorie_parent):
        self.nom = nom
        self.categorie_parent = categorie_parent
