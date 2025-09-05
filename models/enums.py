"""
Enums for the Money application.
"""

from enum import Enum


class TypeOperation(Enum):
    Débit = "Débit"
    Crédit = "Crédit"
    TransfertV = "Transfert vers"
    TransfertD = "Transfert de"

    @classmethod
    def return_list(cls):
        return [operation.value for operation in cls]


class FrequenceEcheancier(Enum):    
    M = "Mensuelle"
    T = "Trimestrielle"    
    S = "Semestrielle"    
    A = "Annuelle"
    
    @classmethod
    def return_list(cls):
        return [frequence.value for frequence in cls]


class TypePlacement(Enum):
    Action = "Action"
    Fond = "Fond en euros"
    Mixte = "Mixte"
    Obligation = "Obligations"
    SCPI = "SCPI"
    UC = "Unités de compte"
    Immo = "Immobilier"

    @classmethod
    def return_list(cls):
        return [placement.value for placement in cls]


class TypePosition(Enum):
    Achat = "Achat"
    Don = "Don gratuit"
    Gain = "Gain de parts"
    Interet = "Intérêts"
    Perte = "Perte de parts"
    Vente = "Vente"

    @classmethod
    def return_list(cls):
        return [operation.value for operation in cls]


class TypeCompte(Enum):
    courant = "Courant"
    compte_placement = "Epargne"
    placement = "Placement"
    pret = "Prêt"

    @classmethod
    def return_list(cls):
        return [compte.value for compte in cls]
