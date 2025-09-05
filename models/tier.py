"""
Tier model for the Money application.
"""

from bson import ObjectId


class TypeTier:
    """Represents a type of third party."""

    def __init__(self, nom):
        self.nom = nom


class Tier:
    """Represents a third party entity."""

    def __init__(self, nom, type, categorie, sous_categorie, moyen_paiement, 
                 _id=None, actif=True):
        if _id is None:            
            self._id = ObjectId()
        else:
            self._id = _id
        self.nom = nom
        self.type = type
        self.categorie = categorie
        self.sous_categorie = sous_categorie
        self.actif = actif
        self.moyen_paiement = moyen_paiement        

    def convertObjectoDict(self):
        """Convert the object to a dictionary."""
        return vars(self)
