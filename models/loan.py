"""
Loan model for the Money application.
"""

from datetime import date


class Loan:
    """Represents a loan."""

    def __init__(self,
                 nom: str,
                 montant_initial: float,
                 date_debut: date,
                 duree_ans: int,
                 taux_annuel_initial: float,
                 frequence_paiement: str,
                 assurance_par_periode: float = 0.0,
                 taux_variables: list = None,
                 compte_id: str = None,
                 compte_associe: str = None
                 ):
        self.compte_id = compte_id
        self.compte_associe = compte_associe
        self.nom = nom
        self.montant_initial = montant_initial
        self.date_debut = date_debut
        self.duree_ans = duree_ans
        self.taux_annuel_initial = taux_annuel_initial
        self.frequence_paiement = frequence_paiement
        self.assurance_par_periode = assurance_par_periode
        self.taux_variables = taux_variables if taux_variables is not None else []
