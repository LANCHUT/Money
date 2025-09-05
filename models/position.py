"""
Position model for the Money application.
"""

from bson import ObjectId


class Position:
    """Represents an investment position."""

    def __init__(self, date, type, nom_placement, nb_part, val_part, frais, 
                 interets, notes, compte_id, montant_investit, compte_associe=None, 
                 _id=None, bq=0):
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id
        self.type = type
        self.nom_placement = nom_placement
        self.nb_part = nb_part
        self.val_part = val_part
        self.frais = frais
        self.interets = interets
        self.compte_associe = compte_associe
        self.date = date
        self.notes = notes
        self.compte_id = compte_id
        self.montant_investit = montant_investit
        self.bq = bq
