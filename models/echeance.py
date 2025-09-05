"""
Echeance model for the Money application.
"""

from bson import ObjectId


class Echeance:
    """Represents a scheduled payment."""

    def __init__(self, frequence, echeance1, prochaine_echeance, type, type_tier, 
                 tier, categorie, sous_categorie, debit, credit, notes, compte_id, 
                 nb_part, val_part, frais, interets, moyen_paiement, is_position, 
                 compte_associe=None, type_beneficiaire="", beneficiaire="", _id=None):
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id
        self.frequence = frequence
        self.echeance1 = echeance1
        self.prochaine_echeance = prochaine_echeance
        self.type = type
        self.compte_associe = compte_associe
        self.type_tier = type_tier
        self.tier = tier
        self.categorie = categorie
        self.sous_categorie = sous_categorie
        self.debit = debit
        self.credit = credit
        self.notes = notes
        self.compte_id = compte_id
        self.type_beneficiaire = type_beneficiaire
        self.beneficiaire = beneficiaire
        self.nb_part = nb_part
        self.val_part = val_part
        self.frais = frais
        self.interets = interets
        self.moyen_paiement = moyen_paiement
        self.is_position = is_position
