"""
Payment method model for the Money application.
"""


class MoyenPaiement:
    """Represents a payment method."""

    def __init__(self, nom):
        self.nom = nom
