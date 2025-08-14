from datetime import datetime,date
from enum import Enum
from bson import ObjectId
from loguru import logger



class Compte():

    def __init__(self,nom,solde,type,nom_banque,_id = None) -> None:
        if _id is None:
            self._id = ObjectId()
        else:
            self._id = _id
        self.nom = nom
        self.solde = solde
        self.type = type
        self.nom_banque = nom_banque

    def addOperation(self,operation):
        from GestionBD import UpdateSoldeCompte
        from GestionBD import UpdateDoneOperation
        from GestionBD import UpdateDatePaiementTier
        from GestionBD import InsertOperation, UpdateSoldeJour
        from GestionBD import UpdateListeOperationCompte
        if operation.type == "Débit":
            if operation.date <= date.today():            
                try:
                    self.solde -= operation.montant
                    InsertOperation(operation)
                    UpdateSoldeCompte(self.nom,self.solde)
                    UpdateDoneOperation(operation)
                    UpdateDatePaiementTier(operation)
                    self.operations.append(operation)
                    UpdateListeOperationCompte(self,self.operations)
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
                    UpdateListeOperationCompte(self,self.operations)
                    logger.succes(f"Insertion de l'opération {operation._id} réussie")
                except Exception as e:
                    logger.error(f"Echec de l'insertion de l'opération {operation._id} \n Cause : {repr(e)}")
                    
        else:
            try:
                self.solde += operation.montant
                UpdateSoldeCompte(self.nom,self.solde)
                UpdateDoneOperation(operation)
                logger.success(f"Insertion de l'opération {operation._id} réussie")
            except Exception as e:
                logger.error(f"Echec de l'insertion de l'opération {operation._id} \n Cause : {repr(e)}")
    


class Operation():

    def __init__(self,date,type,type_tier,tier,moyen_paiement,categorie,sous_categorie,debit,credit,notes,compte_id, num_cheque = None,compte_associe = None, solde=None, _id = None, bq = False, type_beneficiaire = "",beneficiaire = "") -> None:
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

class Position():

    def __init__(self,date,type,nom_placement,nb_part,val_part,frais,interets,notes,compte_id,montant_investit,compte_associe = None, _id = None):
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

class HistoriquePlacement():

    def __init__(self,nom,type,date,val_actualise,origine) -> None:
        self.type = type
        self.nom = nom
        self.val_actualise = val_actualise
        self.origine = origine
        self.date = date

class Placement():

    def __init__(self,nom,type) -> None:
        self.type = type
        self.nom = nom


class TypeOperation(Enum):
    Débit = "Débit"
    Crédit = "Crédit"
    TransfertV = "Transfert vers"
    TransfertD = "Transfert de"

    @classmethod
    def return_list(self):
        return[operation.value for operation in self]
    
class FrequenceEcheancier(Enum):
    A = "Annuelle"
    S = "Semestrielle"
    T = "Trimestrielle"
    M = "Mensuelle"

    @classmethod
    def return_list(self):
        return[frequence.value for frequence in self]

class TypePlacement(Enum):
    Action = "Action"
    Fond = "Fond en euros"
    Mixte = "Mixte"
    Obligation = "Obligations"
    SCPI = "SCPI"
    UC = "Unités de comptes"

    @classmethod
    def return_list(self):
        return[placement.value for placement in self]


class TypePosition(Enum):
    Achat = "Achat"
    Don = "Don gratuit"
    Gain = "Gain de parts"
    Interet = "Intérêts"
    Perte = "Perte de parts"
    Vente = "Vente"

    @classmethod
    def return_list(self):
        return[operation.value for operation in self]

class TypeCompte(Enum):
    courant = "Courant"
    compte_placement = "Epargne"
    placement = "Placement"
    pret = "Prêt"

    @classmethod
    def return_list(self):
        return [compte.value for compte in self]

class TypeTier():
    def __init__(self,nom):
        self.nom = nom
    
class MoyenPaiement():
    def __init__(self,nom) -> None:
        self.nom = nom
    
class Categorie():
    def __init__(self,nom) -> None:
        self.nom = nom

class TypeBeneficiaire():
    def __init__(self,nom) -> None:
        self.nom = nom


class Tier():
    def __init__(self,nom,type,categorie,sous_categorie,moyen_paiement,_id = None,actif=True) -> None:
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
        return vars(self)


class SousCategorie():
    def __init__(self,nom,categorie_parent) -> None:
        self.nom = nom
        self.categorie_parent = categorie_parent

class Beneficiaire():
    def __init__(self,nom,type_beneficiaire) -> None:
        self.nom = nom
        self.type_beneficiaire = type_beneficiaire

class Echeance():
    def __init__(self,frequence,echeance1,prochaine_echeance,type,type_tier,tier,categorie,sous_categorie,debit,credit,notes,compte_id,nb_part,val_part,frais,interets,moyen_paiement,is_position,compte_associe = None, type_beneficiaire = "",beneficiaire = "",_id = None) -> None:
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

class Loan:
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
                 compte_associe:str = None
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