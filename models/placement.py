"""
Placement models for the Money application.
"""


class HistoriquePlacement:
    """Represents historical placement data."""

    def __init__(self, nom, type, date, val_actualise, origine, ticker):
        self.type = type
        self.nom = nom
        self.val_actualise = val_actualise
        self.origine = origine
        self.date = date
        self.ticker = ticker


class Placement:
    """Represents a financial placement."""

    def __init__(self, nom, type, ticker=""):
        self.type = type
        self.nom = nom
        self.ticker = ticker
