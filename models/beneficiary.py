"""
Beneficiary models for the Money application.
"""


class TypeBeneficiaire:
    """Represents a type of beneficiary."""

    def __init__(self, nom):
        self.nom = nom


class Beneficiaire:
    """Represents a beneficiary."""

    def __init__(self, nom, type_beneficiaire):
        self.nom = nom
        self.type_beneficiaire = type_beneficiaire
