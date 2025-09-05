"""
Account model for the Money application.
"""

from datetime import date
from bson import ObjectId
from loguru import logger


class Compte:
    """Represents a financial account."""

    def __init__(self, nom, solde, type, nom_banque, _id=None):
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id
        self.nom = nom
        self.solde = solde
        self.type = type
        self.nom_banque = nom_banque

    def addOperation(self, operation):
        """Add an operation to this account."""
        from database.gestion_bd import (
            UpdateSoldeCompte, UpdateDoneOperation, UpdateDatePaiementTier,
            InsertOperation, UpdateSoldeJour, UpdateListeOperationCompte
        )
        
        if operation.type == "Débit":
            if operation.date <= date.today():            
                try:
                    self.solde -= operation.montant
                    InsertOperation(operation)
                    UpdateSoldeCompte(self.nom, self.solde)
                    UpdateDoneOperation(operation)
                    UpdateDatePaiementTier(operation)
                    self.operations.append(operation)
                    UpdateListeOperationCompte(self, self.operations)
                    logger.success(f"Insertion de l'opération {operation._id} réussie")
                except Exception as e:
                    logger.error(f"Echec de l'insertion de l'opération {operation._id} \n Cause : {repr(e)}")

            else:
                try:
                    self.solde_jour -= operation.montant
                    InsertOperation(operation)
                    UpdateSoldeJour(self)
                    UpdateDatePaiementTier(operation)
                    self.operations.append(operation)
                    UpdateListeOperationCompte(self, self.operations)
                    logger.success(f"Insertion de l'opération {operation._id} réussie")
                except Exception as e:
                    logger.error(f"Echec de l'insertion de l'opération {operation._id} \n Cause : {repr(e)}")
                    
        else:
            try:
                self.solde += operation.montant
                UpdateSoldeCompte(self.nom, self.solde)
                UpdateDoneOperation(operation)
                logger.success(f"Insertion de l'opération {operation._id} réussie")
            except Exception as e:
                logger.error(f"Echec de l'insertion de l'opération {operation._id} \n Cause : {repr(e)}")
