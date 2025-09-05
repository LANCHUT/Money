"""
Operation model for the Money application.
"""

from bson import ObjectId


class Operation:
    """Represents a financial operation."""

    def __init__(self, date, type, type_tier, tier, moyen_paiement, categorie, 
                 sous_categorie, debit, credit, notes, compte_id, num_cheque=None, 
                 compte_associe=None, solde=None, _id=None, bq=False, 
                 type_beneficiaire="", beneficiaire="", link=None):
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id
        self.type = type
        self.compte_associe = compte_associe
        self.type_tier = type_tier
        self.tier = tier
        self.moyen_paiement = moyen_paiement
        self.num_cheque = num_cheque
        self.categorie = categorie
        self.sous_categorie = sous_categorie
        self.date = date
        self.debit = debit
        self.credit = credit
        self.notes = notes
        self.compte_id = compte_id
        self.solde = solde
        self.bq = bq
        self.type_beneficiaire = type_beneficiaire
        self.beneficiaire = beneficiaire
        self.link = link
