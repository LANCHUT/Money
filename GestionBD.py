import sqlite3
from Datas import *
from PyQt6.QtWidgets import QMessageBox
import datetime

DB_PATH = "money_manager.db"  # Ton fichier de base de données

# Fonction pour se connecter à la base de données SQLite
def connect_db():
    return sqlite3.connect(DB_PATH)

# Créer les tables si elles n'existent pas
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    

    # Table comptes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comptes (
        id TEXT PRIMARY KEY,
        nom TEXT,
        solde REAL,
        solde_initial REAl,
        type TEXT,
        nom_banque TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moyen_paiement (
        nom TEXT,
        PRIMARY KEY (nom)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS type_beneficiaire (
    nom TEXT,
    PRIMARY KEY (nom)        
    )
    ''')

    # Table opérations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            id TEXT PRIMARY KEY,
            date INTEGER,
            type TEXT,
            compte_associe TEXT,
            type_tier TEXT,
            tier TEXT,
            moyen_paiement TEXT,
            num_cheque INTEGER,
            categorie TEXT,
            sous_categorie TEXT,
            debit REAL,
            credit REAL,
            note TEXT,
            solde_compte REAL,
            compte_id TEXT,
            bq INT,
            type_beneficiaire TEXT,
            beneficiaire TEXT,
            FOREIGN KEY (compte_id) REFERENCES comptes(id) ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (moyen_paiement) REFERENCES moyen_paiement(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (tier) REFERENCES tiers(id) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_tier) REFERENCES type_tier(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (categorie) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_beneficiaire) REFERENCES type_beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (beneficiaire) REFERENCES beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS echeancier (
            id TEXT PRIMARY KEY,
            frequence TEXT,
            echeance_1 INTEGER,
            prochaine_echeance INTEGER,
            compte_id TEXT,
            type TEXT,
            compte_associe TEXT,
            type_tier TEXT,
            tier TEXT,
            categorie TEXT,
            sous_categorie TEXT,
            debit REAL,
            credit REAL,
            nb_part REAL,
            val_part REAL,
            frais REAL,
            interets REAL,
            note TEXT,
            type_beneficiaire TEXT,
            beneficiaire TEXT,
            FOREIGN KEY (compte_id) REFERENCES comptes(id) ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (tier) REFERENCES tiers(id) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_tier) REFERENCES type_tier(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (categorie) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_beneficiaire) REFERENCES type_beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (beneficiaire) REFERENCES beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL
        )
    """)

    # Table tiers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tiers (
        id TEXT PRIMARY KEY,
        nom TEXT,
        type TEXT,
        categorie TEXT,
        sous_categorie TEXT,
        moy_paiement TEXT,
        est_actif INTEGER,
        FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL,
        FOREIGN KEY (categorie) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL,
        FOREIGN KEY (type) REFERENCES type_tier(nom) ON UPDATE CASCADE ON DELETE SET NULL,
        FOREIGN KEY (moy_paiement) REFERENCES moyen_paiement(nom) ON UPDATE CASCADE ON DELETE SET NULL
    )
    ''')

    # Table catégories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categorie (
    nom TEXT PRIMARY KEY        
    )
    ''')

    # Table sous-catégories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sous_categorie (
        nom TEXT,
        categorie_parent TEXT,
        PRIMARY KEY (nom),
        FOREIGN KEY (categorie_parent) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS beneficiaire (
        nom TEXT,
        type_beneficiaire TEXT,
        PRIMARY KEY (nom),
        FOREIGN KEY (type_beneficiaire) REFERENCES type_beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL
    )
    ''')

    # Table catégories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS type_tier (
    nom TEXT PRIMARY KEY        
    )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_placement (
            nom TEXT,
            type TEXT,
            date INTEGER,
            valeur_actualise REAL,
            origine TEXT,    
            PRIMARY KEY (nom,date)
            FOREIGN KEY (nom) REFERENCES placement(nom) ON UPDATE CASCADE ON DELETE CASCADE
        )
                   
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_pointage (
            compte_id TEXT,
            date INTEGER,
            solde REAL,   
            PRIMARY KEY (compte_id,date)
            FOREIGN KEY (compte_id) REFERENCES comptes(id) ON UPDATE CASCADE ON DELETE CASCADE
        )
                   
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement (
            nom TEXT,
            type TEXT,    
            PRIMARY KEY (nom)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS position (
            id TEXT PRIMARY KEY,
            compte_id TEXT,
            type TEXT,
            nom_placement TEXT,
            nb_part REAL,
            val_part REAL,
            frais REAl,
            interets REAL,
            date INTEGER,
            notes TEXT,
            compte_associe TEXT,
            montant_investit REAL,
            FOREIGN KEY (nom_placement) REFERENCES placement(nom) ON UPDATE CASCADE ON DELETE CASCADE            
            
        )
    ''')

    # Vérifie si l'initialisation a déjà été faite
    cursor.execute("SELECT value FROM meta WHERE key = 'initialized'")
    init_done = cursor.fetchone()

    if not init_done:
    # === INSÉRER LES VALEURS PAR DÉFAUT ===

        cursor.execute('''
            INSERT OR IGNORE INTO categorie (nom) VALUES 
            ('Alimentation'), ('Automobile'), ('Banque'), ('Equipement'),
            ('Frais Professionnel'), ('Habillement'), ('Habitation'), ('Impots'),
            ('Informatique'), ('Loisirs'), ('Revenus'), ('Santé'),
            ('Téléphonie / Internet'), ('Tiers'), ('Vacances')
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO type_tier (nom) VALUES 
            ('Association'), ('Assurance'), ('Banque'), ('Carburant'), ('Energie'),
            ('Entreprise'), ('Hotel'), ('Hyper'), ('Magasin'), ('Organisme'),
            ('Particulier'), ('Restaurant'), ('Santé'), ('Site Internet'), ('Téléphonie')
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO moyen_paiement (nom) VALUES 
            ('Carte de crédit'), ('Chèque'), ('Prélèvement'), ('Virement'), ('Espèces')
        ''')

        # Marquer l'initialisation comme terminée
        cursor.execute("INSERT INTO meta (key, value) VALUES ('initialized', 'true')")

    conn.commit()
    conn.close()

# Insérer une opération
def InsertOperation(operation: Operation):
    conn = connect_db()
    cursor = conn.cursor()

    compte = GetCompte(str(operation.compte_id))
    compte.solde += operation.debit
    compte.solde += operation.credit
    operation.solde = compte.solde
    UpdateSoldeCompte(str(compte._id),compte.solde)

    cursor.execute('''
    INSERT INTO operations (id, date, type, compte_associe, type_tier, tier, moyen_paiement, num_cheque, categorie,sous_categorie, debit, credit, note, solde_compte, compte_id, bq, type_beneficiaire,beneficiaire)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(operation._id),
        operation.date,
        operation.type,
        operation.compte_associe,
        operation.type_tier,
        operation.tier,
        operation.moyen_paiement,
        operation.num_cheque,
        operation.categorie,
        operation.sous_categorie,
        float(operation.debit),
        float(operation.credit),
        operation.notes,
        compte.solde,
        str(operation.compte_id),
        operation.bq,
        operation.type_beneficiaire,
        operation.beneficiaire

    ))

    conn.commit()
    conn.close()


def InsertEcheance(echeance: Echeance):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO echeancier (id, frequence, echeance_1, prochaine_echeance, compte_id, type,compte_associe, type_tier, tier, categorie,sous_categorie, debit, credit, nb_part,val_part,frais,interets,note,type_beneficiaire,beneficiaire)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(echeance._id),
        echeance.frequence,
        echeance.echeance1,
        echeance.prochaine_echeance,
        str(echeance.compte_id),
        echeance.type,
        echeance.compte_associe,
        echeance.type_tier,
        echeance.tier,
        echeance.categorie,
        echeance.sous_categorie,
        float(echeance.debit),
        float(echeance.credit),
        echeance.nb_part,
        echeance.val_part,
        echeance.frais,
        echeance.interets,
        echeance.notes,
        echeance.type_beneficiaire,
        echeance.beneficiaire

    ))

    conn.commit()
    conn.close()

def UpdateValoComptePlacement(compte_id : str,conn = None):
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT nom_placement,sum(nb_part) from position
    WHERE compte_id = ?
    group by nom_placement
    ''',(compte_id,))

    placements = cursor.fetchall()
    valo = 0
    for nom_placement,nb_part in placements:
        val_part = GetLastValueForPlacement(nom_placement,conn)
        valo_placement = val_part*nb_part
        valo += valo_placement
    compte = GetCompte(compte_id,conn)
    compte.solde = valo
    UpdateSoldeCompte(compte_id,compte.solde,conn)
    if was_none:
        conn.close()


def InsertPosition(position: Position):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO position (id, compte_id, type, nom_placement, nb_part, val_part, frais, interets, date,notes, compte_associe, montant_investit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(position._id),
        position.compte_id,
        position.type,
        position.nom_placement,
        float(position.nb_part),
        float(position.val_part),
        float(position.frais),
        float(position.interets),
        position.date,
        position.notes,
        position.compte_associe,
        position.montant_investit

    ))

    UpdateValoComptePlacement(position.compte_id,conn)
    conn.commit()
    conn.close()




# Insérer un compte
def InsertCompte(compte: Compte, parent = None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO comptes (id, nom, solde,solde_initial, type, nom_banque)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(compte._id),
            compte.nom,
            compte.solde,
            compte.solde,
            compte.type,
            compte.nom_banque
        ))

        cursor.execute('''
        INSERT INTO historique_pointage (compte_id, date, solde)
        VALUES (?, ?, ?)
        ''', (
            str(compte._id),
            int(datetime.date.today().strftime('%Y%m%d')),
            compte.solde,
        ))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"Le compte numero '{compte._id}' existe déjà."
        )
        return False
    finally:
        conn.close()

def UpdateTier(tier: Tier):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE tiers
    SET nom = ?, type = ?, categorie = ?, sous_categorie = ?, moy_paiement = ?, est_actif = ?
    WHERE id = ?
    ''', (tier.nom,
          tier.type,
          tier.categorie,
          tier.sous_categorie,
          tier.moyen_paiement,
          tier.actif,
          str(tier._id)))

    conn.commit()
    conn.close()

def UpdateBqOperation(operation_id : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE operations
    SET bq = 1
    WHERE id = ?
    ''', (operation_id,))

    conn.commit()
    conn.close()

def UpdateSousCategorie(sous_categorie: SousCategorie,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE sous_categorie
    SET nom = ?, categorie_parent = ?
    WHERE nom = ?
    ''', (sous_categorie.nom,
          sous_categorie.categorie_parent,
          old_nom))

    conn.commit()
    conn.close()

def UpdateBeneficiaire(beneficiaire: Beneficiaire,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE beneficiaire
    SET nom = ?, type_beneficiaire = ?
    WHERE nom = ?
    ''', (beneficiaire.nom,
          beneficiaire.type_beneficiaire,
          old_nom))

    conn.commit()
    conn.close()

def UpdateCategorie(categorie: Categorie,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE categorie
    SET nom = ?
    WHERE nom = ?
    ''', (categorie.nom,
          old_nom))

    conn.commit()
    conn.close()

def UpdateTypeBeneficiaire(type_beneficiaire: TypeBeneficiaire,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE type_beneficiaire
    SET nom = ?
    WHERE nom = ?
    ''', (type_beneficiaire.nom,
          old_nom))

    conn.commit()
    conn.close()


def UpdateTypeTypeTier(type_tier: TypeTier,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE type_tier
    SET nom = ?
    WHERE nom = ?
    ''', (type_tier.nom,
          old_nom))

    conn.commit()
    conn.close()

def UpdatePlacement(placement: Placement,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE placement
    SET nom = ?
    WHERE nom = ?
    ''', (placement.nom,
          old_nom))

    conn.commit()
    conn.close()

def UpdateMoyenPaiement(moyen_paiement: MoyenPaiement,old_nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE moyen_paiement
    SET nom = ?
    WHERE nom = ?
    ''', (moyen_paiement.nom,
          old_nom))

    conn.commit()
    conn.close()

def UpdateCompte(compte: Compte):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE comptes
    SET nom = ?, type = ?, nom_banque = ?
    WHERE id = ?
    ''', (compte.nom,
          compte.type,
          compte.nom_banque,
          str(compte._id)))

    conn.commit()
    conn.close()

def GetTierName(tier_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT nom
    FROM tiers
    WHERE id = ?
    """, (tier_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def GetInitialSolde(compte_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT solde_initial
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def GetNextNumCheque():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
SELECT COALESCE(MAX(CAST(num_cheque AS INTEGER)), 0) + 1
FROM operations
    """)

    result = cursor.fetchone()
    conn.close()

    return str(result[0]) if result else None


def GetCompteName(compte_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT nom
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def GetCompteType(compte_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT type
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def GetSousCategorie(categorie:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select nom from sous_categorie where categorie_parent = ?",(categorie,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        sous_categorie = SousCategorie(row[0],categorie)
        result.append(sous_categorie)

    return result

def GetLastValueForPlacement(nom_placement: str,conn = None) -> float:
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT valeur_actualise FROM historique_placement 
        WHERE nom = ? 
        ORDER BY date DESC LIMIT 1
    """, (nom_placement,))
    row = cursor.fetchone()
    if was_none:
        conn.close()
    return row[0] if row else None


def SetPlacementTo0(nom_placement: str,conn = None):
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE historique_placement
        SET valeur_actualise = 0
        WHERE rowid = (
            SELECT rowid
            FROM historique_placement
            WHERE nom = ?
            ORDER BY date DESC
            LIMIT 1
        )
    """, (nom_placement,))
    conn.commit()
    if was_none:
        conn.close()

def GetHistoriquePlacement(nom:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,date,valeur_actualise,origine from historique_placement where nom = '{nom}'")
    historique_placement = cursor.fetchall()

    conn.close()

    result = []
    for row in historique_placement:
        placement = HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])
        result.append(placement)

    return result

def GetHistoriquePlacementByDate(nom:str,date:int):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,date,valeur_actualise,origine from historique_placement where nom = '{nom}' and date = {date}")
    row = cursor.fetchone()

    conn.close()
    return HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])


def GetAllSousCategorie():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from sous_categorie")
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        sous_categorie = SousCategorie(row[0],row[1])
        result.append(sous_categorie)

    return result

def GetAllBeneficiaire():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from beneficiaire")
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        beneficiaire = Beneficiaire(row[0],row[1])
        result.append(beneficiaire)

    return result

def GetBeneficiairesByType(type_beneficiaire : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from beneficiaire where type_beneficiaire = ?",(type_beneficiaire,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        beneficiaire = Beneficiaire(row[0],row[1])
        result.append(beneficiaire)

    return result

def GetMoyenPaiement():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from moyen_paiement")
    moyen_paiements = cursor.fetchall()

    conn.close()

    result = []
    for row in moyen_paiements:
        moyen_paiement = MoyenPaiement(row[0])
        result.append(moyen_paiement)

    return result

def GetCategorie():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from categorie")
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        categorie = Categorie(row[0])
        result.append(categorie)

    return result


def GetTypeBeneficiaire():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select * from type_beneficiaire")
    types_beneficiaire = cursor.fetchall()

    conn.close()

    result = []
    for row in types_beneficiaire:
        type_beneficiaire = TypeBeneficiaire(row[0])
        result.append(type_beneficiaire)

    return result


def GetLastPlacement():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,max(date),valeur_actualise,origine from historique_placement group by nom")
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        placement = HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])
        result.append(placement)

    return result

def GetTierRelatedOperations(tier_id : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where tier = '{tier_id}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetSousCategorieRelatedOperations(nom_sous_categorie : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where sous_categorie = '{nom_sous_categorie}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetCategorieRelatedOperations(nom_categorie : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where categorie = '{nom_categorie}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]


def GetTypeBeneficiaireRelatedOperations(type_beneficiaire : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where type_beneficiaire = '{type_beneficiaire}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetBeneficiaireRelatedOperations(beneficiaire : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where beneficiaire = '{beneficiaire}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetTypeTierRelatedOperations(nom_type_tier : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where type_tier = '{nom_type_tier}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetMoyenPaiementRelatedOperations(nom_moyen_paiement : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where moyen_paiement = '{nom_moyen_paiement}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def DeleteTier(tier_id : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM tiers WHERE id = ?", (tier_id,))
    conn.commit()

    conn.close()

def DeleteOperation(operation : Operation,old_credit:float,old_debit:float):
    conn = connect_db()
    cursor = conn.cursor()
    compte = GetCompte(str(operation.compte_id))
    compte.solde -= old_credit
    compte.solde -= old_debit
    operation.solde = compte.solde
    UpdateSoldeCompte(str(compte._id),compte.solde)
    cursor.execute("DELETE FROM operations WHERE id = ?", (str(operation._id),))
    conn.commit()

    conn.close()

def DeleteCompte(compte_id : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM comptes WHERE id = ?", (compte_id,))
    conn.commit()

    conn.close()

def DeletePlacement(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    SetPlacementTo0(nom,conn)
    for compte_id in GetComptePlacement(nom):
        GetLastValueForPlacement(nom,conn)
        UpdateValoComptePlacement(compte_id,conn)
    cursor.execute("DELETE FROM placement WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteHistoriquePlacement(nom : str, date : int):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historique_placement WHERE nom = ? and date = ?", (nom,date,))
    conn.commit()
    for compte_id in GetComptePlacement(nom,conn):
            UpdateValoComptePlacement(compte_id,conn)

    conn.close()

def DeleteSousCategorie(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM sous_categorie WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteCategorie(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM categorie WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteTypeTier(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM type_tier WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteTypeBeneficiaire(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM type_beneficiaire WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteBeneficiaire(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM beneficiaire WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteMoyenPaiement(nom : str):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM moyen_paiement WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

# Obtenir tous les comptes
def GetComptes():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id, nom, solde, type, nom_banque FROM comptes')
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        c = Compte(row[1], row[2], row[3], row[4], ObjectId(row[0]))
        result.append(c)

    return result

# Obtenir tous les comptes sauf l'actuel
def GetComptesExceptCurrent(compte_id : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, nom, solde, type, nom_banque FROM comptes where id != '{compte_id}'")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        c = Compte(row[1], row[2], row[3], row[4], ObjectId(row[0]))
        result.append(c)

    return result


def GetDerniereValeurPointe(compte_id:str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""SELECT solde,date FROM historique_pointage
        WHERE compte_id = ? 
        ORDER BY date DESC LIMIT 1""",(compte_id,))
    val_pointe = cursor.fetchone()

    conn.close()
    return (val_pointe[0],val_pointe[1])

# Obtenir tous les comptes
def GetOperations(compte_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where compte_id = '{compte_id}' order by date asc")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        operation = Operation(row[1], row[2], row[4], row[5], row[6], row[8], row[9], row[10], row[11], row[12],compte_id, row[7],row[3],row[13],row[0],row[15],row[16],row[17])
        result.append(operation)

    return result


def GetFilteredOperations(date_debut, date_fin, categories=None, sous_categories=None, tiers=None, comptes=None, bq=None):
    conn = connect_db()
    cursor = conn.cursor()

    categories = categories or []
    sous_categories = sous_categories or []
    tiers = tiers or []
    comptes = comptes or []

    def placeholders(values, prefix):
        return ','.join(f':{prefix}{i}' for i in range(len(values)))

    query = f"""
    SELECT * FROM operations
    WHERE date >= :date_debut AND date <= :date_fin
      AND (:categories_empty OR categorie IN ({placeholders(categories, 'cat')}))
      AND (:sous_categories_empty OR sous_categorie IN ({placeholders(sous_categories, 'sous')}))
      AND (:tiers_empty OR tier IN ({placeholders(tiers, 'tier')}))
    """

    if comptes:
        query += f" AND compte_id IN ({placeholders(comptes, 'compte')})"

    if bq is not None:
        query += " AND bq = :bq"

    query += " ORDER BY date ASC"

    # Paramètres
    params = {
        'date_debut': date_debut,
        'date_fin': date_fin,
        'categories_empty': not categories,
        'sous_categories_empty': not sous_categories,
        'tiers_empty': not tiers
    }

    for i, val in enumerate(categories):
        params[f'cat{i}'] = val
    for i, val in enumerate(sous_categories):
        params[f'sous{i}'] = val
    for i, val in enumerate(tiers):
        params[f'tier{i}'] = val
    for i, val in enumerate(comptes):
        params[f'compte{i}'] = val

    if bq is not None:
        params['bq'] = int(bq)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    operations = []
    for row in rows:
        operation = Operation(
            row[1], row[2], row[4], row[5], row[6], row[8], row[9], row[10],
            row[11], row[12], row[14], row[7], row[3], row[13], row[0], row[15], row[16], row[17]
        )
        operations.append(operation)

    return operations


def GetOperationsNotBq(compte_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where compte_id = '{compte_id}' and bq = 0 order by date asc")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        operation = Operation(row[1], row[2], row[4], row[5], row[6], row[8], row[9], row[10], row[11], row[12],compte_id, row[7],row[3],row[13],row[0],row[15],row[16],row[17])
        result.append(operation)

    return result

def GetOperation(operation_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where id = '{operation_id}'")
    operation_bd = cursor.fetchone()

    conn.close()

    operation = Operation(operation_bd[1], operation_bd[2], operation_bd[4], operation_bd[5], operation_bd[6], operation_bd[8], operation_bd[9], operation_bd[10], operation_bd[11], operation_bd[12],operation_bd[14], operation_bd[7],operation_bd[3],operation_bd[13],operation_bd[0],operation_bd[15],operation_bd[16],operation_bd[17])

    return operation

# Mise à jour du solde d'un compte
def UpdateSoldeCompte(compte_id: str, new_solde: float, conn=None):
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE comptes
    SET solde = ?
    WHERE id = ?
    ''', (new_solde, compte_id,))

    conn.commit()
    if was_none:
        conn.close()

# Mettre à jour l'état de l'opération (done = True)
def UpdateDoneOperation(operation: Operation):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE operations
    SET done = 1
    WHERE id = ?
    ''', (str(operation._id),))

    conn.commit()
    conn.close()

# Mettre à jour la date du dernier paiement d'un tiers
def UpdateDatePaiementTier(operation: Operation):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE tiers
    SET date_dernier_paiement = ?
    WHERE nom = ?
    ''', (operation.date.isoformat(), operation.tier['nom']))

    conn.commit()
    conn.close()

# Récupérer tous les tiers
def GetTiers():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers order by nom asc')
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5],ObjectId(row[0]),row[6])
        result.append(t)

    return result

def GetTierById(tier_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers where id = ?',(tier_id,))
    t = cursor.fetchone()

    conn.close()

    tier = Tier(t[1],t[2],t[3],t[4],t[5],ObjectId(t[0]),t[6])


    return tier

def GetTiersActif():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers where est_actif = 1')
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5])
        t._id = ObjectId(row[0])
        result.append(t)

    return result

def GetTierActif(tier_id : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers where est_actif = 1 and id = ?',(tier_id,))
    t = cursor.fetchone()

    conn.close()
    if t is not None:
        tier = Tier(t[1],t[2],t[3],t[4],t[5],actif=t[6])
        tier._id = ObjectId(t[0])

        return tier
    return


def GetTiersActifByType(type_tier: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM tiers where type = '{type_tier}' and est_actif = 1 order by nom asc")
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5])
        t._id = ObjectId(row[0])
        result.append(t)

    return result

def GetTiersActifByTypeExceptCurrent(type_tier: str, current_tier_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM tiers where type = ? and est_actif = 1 and id != ? ",(type_tier,current_tier_id,))
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5])
        t._id = ObjectId(row[0])
        result.append(t)

    return result

def GetSousCategorieByCategorieParentExceptCurrent(nom : str, categorie_parent : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM sous_categorie where categorie_parent = ? and nom != ? ",(categorie_parent,nom,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        s = SousCategorie(row[0],row[1])
        result.append(s)

    return result

def GetCategorieExceptCurrent(nom : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM categorie where nom != ? ",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        s = Categorie(row[0])
        result.append(s)

    return result


def GetTypeBeneficiaireExceptCurrent(nom : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM type_beneficiaire where nom != ? ",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        s = TypeBeneficiaire(row[0])
        result.append(s)

    return result

def GetTypeTierExceptCurrent(nom : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM type_tier where nom != ? ",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        t = TypeTier(row[0])
        result.append(t)

    return result

def GetMoyenPaiementExceptCurrent(nom : str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM moyen_paiement where nom != ? ",(nom,))
    moyens_paiement = cursor.fetchall()

    conn.close()

    result = []
    for row in moyens_paiement:
        m = MoyenPaiement(row[0])
        result.append(m)

    return result

# Insérer un tiers
def InsertTier(tier: Tier):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO tiers (id, nom, type, categorie, sous_categorie, moy_paiement, est_actif)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(tier._id),
        tier.nom,
        tier.type,
        tier.categorie,
        tier.sous_categorie,
        tier.moyen_paiement,
        tier.actif
    ))

    conn.commit()
    conn.close()

# Insérer une catégorie de tiers
def InsertCategorieTiers(categorie: Categorie,parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO categorie (id, nom)
        VALUES (?, ?)
        ''', (str(categorie._id), categorie.nom))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"La catégorie '{categorie.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

# Insérer une catégorie de tiers
def InsertPlacement(placement: Placement,parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO placement (nom, type)
        VALUES (?, ?)
        ''', (placement.nom, placement.type))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"Le placement '{placement.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

# Insérer une catégorie de tiers
def InsertHistoriquePlacement(historique_placement: HistoriquePlacement,parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO historique_placement (nom, type,date,valeur_actualise,origine)
        VALUES (?, ?, ?, ?, ?)
        ''', (historique_placement.nom, historique_placement.type,historique_placement.date,historique_placement.val_actualise,historique_placement.origine))

        conn.commit()
        for compte_id in GetComptePlacement(historique_placement.nom):
            UpdateValoComptePlacement(compte_id,conn)

        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def InsertHistoriquePointage(compte_id,date,solde):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO historique_pointage (compte_id, date,solde)
    VALUES (?, ?, ?)
    ''', (compte_id, date,solde))

    conn.commit()
    conn.close()

# Insérer une sous-catégorie
def InsertSousCategorie(sous_categorie: SousCategorie, parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO sous_categorie (nom, categorie_parent)
        VALUES ( ?, ?)
        ''', (sous_categorie.nom,sous_categorie.categorie_parent,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        if parent is None:
            return False
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"La sous-categorie '{sous_categorie.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()


def InsertBeneficiaire(beneficiaire: Beneficiaire, parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO beneficiaire (nom, type_beneficiaire)
        VALUES ( ?, ?)
        ''', (beneficiaire.nom,beneficiaire.type_beneficiaire,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        if parent is None:
            return False
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"Le bénéficiaire '{beneficiaire.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

def InsertCategorie(categorie: Categorie, parent = None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO categorie (nom)
        VALUES ( ?)
        ''', (categorie.nom,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        if parent is None:
            return False
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"La catégorie '{categorie.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()


def InsertTypeBeneficiaire(type_beneficiaire: TypeBeneficiaire, parent = None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO type_beneficiaire (nom)
        VALUES ( ?)
        ''', (type_beneficiaire.nom,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        if parent is None:
            return False
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"La catégorie '{type_beneficiaire.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

def InsertMoyenPaiement(moyen_paiement: MoyenPaiement, parent = None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO moyen_paiement (nom)
        VALUES ( ?)
        ''', (moyen_paiement.nom,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"Le moyen de paiement '{moyen_paiement.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

# Obtenir tous les comptes distincts
def GetNomBanque():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT nom_banque FROM comptes')
    banques = cursor.fetchall()

    conn.close()

    return [row[0] for row in banques]

# Mettre à jour le solde jour du compte
def UpdateSoldeJour(compte: Compte):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE comptes
    SET solde_jour = ?
    WHERE id = ?
    ''', (compte.solde_jour, str(compte._id)))

    conn.commit()
    conn.close()

# Obtenir un compte par nom et banque
def GetCompte(compte_id:str,conn = None) -> Compte:
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, nom, solde, type, nom_banque FROM comptes WHERE id = '{compte_id}'")

    result = cursor.fetchone()
    if was_none:
        conn.close()

    if result:
        c = Compte(result[1], result[2], result[3], result[4], ObjectId(result[0]))
        return c
    return None


def GetComptePlacement(nom_placement:str,conn = None) -> list:
    was_none = False
    if conn is None:
        was_none = True
        conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT distinct compte_id from position WHERE nom_placement  = '{nom_placement}'")

    comptes = cursor.fetchall()
    if was_none:
        conn.close()

    result = []
    for row in comptes:
        result.append(row[0])
    return result


def GetPositions(compte_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT date,type,nom_placement,nb_part,val_part,frais,interets,notes,compte_id,montant_investit,compte_associe,id FROM position where compte_id = '{compte_id}' order by date asc")
    positions = cursor.fetchall()

    conn.close()

    result = []
    for row in positions:
        position = Position(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11])
        result.append(position)

    return result

def GetPlacements():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT nom,type,date,valeur_actualise,origine FROM placement")
    placements = cursor.fetchall()

    conn.close()

    result = []
    for row in placements:
        placement = Placement(row[0],row[1],row[2],row[3],row[4])
        result.append(placement)

    return result

def InsertTypeTier(typeTier: TypeTier, parent=None) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO type_tier (nom) VALUES (?)''', (typeTier.nom,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Insertion impossible",
            f"Le type de tiers '{typeTier.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()
    
def GetTypeTier():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM type_tier")
    types_tier = cursor.fetchall()

    result = []
    for row in types_tier:
        type_tier = TypeTier(row[0])
        result.append(type_tier)

    return result

def GetTypePlacement(nom_placement):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM placement where nom = ?",(nom_placement,))
    result = cursor.fetchone()

    return result[0]

def UpdateTierInOperations(old_tier_id, new_tier_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET tier = ?
        WHERE tier = ?
    """, (new_tier_id, old_tier_id))
    conn.commit()
    conn.close()


def UpdateTypeBeneficiaireInOperations(old_type_beneficiaire, new_type_beneficiaire):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_beneficiaire = ?
        WHERE type_beneficiaire = ?
    """, (old_type_beneficiaire, new_type_beneficiaire))
    conn.commit()
    conn.close()

def UpdateBeneficiaireInOperations(old_beneficiaire, new_beneficiaire):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_beneficiaire = ?
        WHERE type_beneficiaire = ?
    """, (old_beneficiaire, new_beneficiaire))
    conn.commit()
    conn.close()

def UpdateSousCategorieInOperations(old_sous_categorie, new_sous_categorie):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET sous_categorie = ?
        WHERE sous_categorie = ?
    """, (new_sous_categorie, old_sous_categorie))
    conn.commit()
    conn.close()


def UpdateTypeTierInOperations(old_type_tier, new_type_tier):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_tier = ?
        WHERE type_tier = ?
    """, (new_type_tier, old_type_tier))
    conn.commit()
    conn.close()

def UpdateMoyenPaiementInOperations(old_moyen_paiement, new_moyen_paiement):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET moyen_paiement = ?
        WHERE moyen_paiement = ?
    """, (new_moyen_paiement, old_moyen_paiement))
    conn.commit()
    conn.close()

def UpdateCategorieInOperations(old_categorie, new_categorie):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET categorie = ?
        WHERE categorie = ?
    """, (new_categorie, old_categorie))
    conn.commit()
    conn.close()

def UpdateSousCategorieTier(old_sous_categorie, new_sous_categorie):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET sous_categorie = ?
        WHERE sous_categorie = ?
    """, (new_sous_categorie, old_sous_categorie))
    conn.commit()
    conn.close()

def UpdateTypeTier(old_type_tier, new_type_tier):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET type = ?
        WHERE type = ?
    """, (new_type_tier, old_type_tier))
    conn.commit()
    conn.close()

def UpdateMoyenPaiementTier(old_moyen_paiement, new_moyen_paiement):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET moy_paiement = ?
        WHERE moy_paiement = ?
    """, (new_moyen_paiement, old_moyen_paiement))
    conn.commit()
    conn.close()

def UpdateCategorieTier(old_categorie, new_categorie):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET categorie = ?
        WHERE categorie = ?
    """, (new_categorie, old_categorie))
    conn.commit()
    conn.close()

def GetPerformanceGlobaleData(compte_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    # Récupère toutes les positions nécessaires en une seule requête
    cursor.execute("""
        SELECT type, nb_part, nom_placement, montant_investit, val_part, interets, frais
        FROM position
        WHERE compte_id = ?
    """, (compte_id,))
    positions = cursor.fetchall()

    valo = 0
    montant_investissement = 0
    don = 0
    cumul_interet = 0
    montant_vente = 0
    montant_perte = 0
    last_values = {}

    for p in positions:
        type_op, nb_part, nom_placement, montant_investit, val_part, interets, frais = p

        # Récupération de la valeur du placement avec caching
        if nom_placement not in last_values:
            last_values[nom_placement] = GetLastValueForPlacement(nom_placement)
        valeur_part = last_values[nom_placement]

        if type_op in ['Achat', 'Gain de parts', 'Don gratuit']:
            valo += nb_part * valeur_part
            if type_op == 'Achat':
                montant_investissement += montant_investit

        elif type_op == 'Don gratuit':
            don += nb_part * val_part

        elif type_op == 'Intérêts':
            cumul_interet += interets

        elif type_op == 'Vente':
            valo += nb_part * val_part
            montant_vente += nb_part * val_part

        elif type_op == "Perte de parts":
            valo += nb_part * val_part
            montant_perte += nb_part * val_part
        else :
            valo += nb_part * valeur_part

    plus_value = valo - montant_investissement
    perf = (plus_value / montant_investissement * 100) if montant_investissement != 0 else 0

    conn.close()

    return {
        "valo": round(valo),
        "montant_investissement": round(montant_investissement),
        "don": round(don),
        "vente": round(montant_vente),
        "perte": round(montant_perte),
        "cumul_interet": round(cumul_interet),
        "plus-value": round(plus_value),
        "frais" : round(frais),
        "perf": round(perf, 2)
    }



def GetPerformanceByPlacement(compte_id: str):
    conn = connect_db()
    cursor = conn.cursor()

    # Récupération groupée par nom_placement
    cursor.execute("""
        SELECT nom_placement, SUM(nb_part), SUM(montant_investit), SUM(interets)
        FROM position
        WHERE compte_id = ?
        GROUP BY nom_placement
    """, (compte_id,))
    placements = cursor.fetchall()

    performance_data = []
    for nom_placement, nb_parts, montant_investi, interets in placements:
        val_part = GetLastValueForPlacement(nom_placement)
        valo = nb_parts * val_part
        plus_value = valo - montant_investi
        perf = (plus_value / montant_investi * 100) if montant_investi != 0 else 0

        performance_data.append({
            "nom": nom_placement,
            "nb_parts": round(nb_parts, 2),
            "val_part": round(val_part, 2),
            "investi": round(montant_investi, 2),
            "valorisation": round(valo, 2),
            "interet": round(interets, 2),
            "plus-value": round(plus_value, 2),
            "performance": round(perf, 2)
        })

    conn.close()
    return performance_data


