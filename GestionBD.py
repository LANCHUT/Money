import sqlite3
from Datas import *
from PyQt6.QtWidgets import QMessageBox
import datetime

# DB_PATH ne sera plus une constante ici, mais sera défini dynamiquement
# Initialisez-le à None ou à une valeur par défaut, ou supprimez-le si vous le passez toujours.
DB_PATH = None

# Fonction pour se connecter à la base de données SQLite
def connect_db(db_path=None):
    """
    Connecte à la base de données SQLite.
    Utilise le db_path global si aucun n'est fourni.
    """
    global DB_PATH
    if db_path:
        DB_PATH = db_path
    if not DB_PATH:
        raise ValueError("Le chemin de la base de données n'est pas défini. Utilisez connect_db(chemin_du_fichier.db) ou définissez DB_PATH.")
    return sqlite3.connect(DB_PATH)

# Modifiez toutes les fonctions qui appellent connect_db() pour passer le chemin
# ou assurez-vous que DB_PATH est défini avant leur appel.

# Exemple pour create_tables:
def  create_tables(db_path=None):
    conn = connect_db(db_path) # Passez le chemin ici
    cursor = conn.cursor()

    # ... (le reste de votre code create_tables reste inchangé) ...
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
            FOREIGN KEY (beneficiaire,type_beneficiaire) REFERENCES beneficiaire(nom,type_beneficiaire) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (categorie, sous_categorie) REFERENCES sous_categorie(categorie_parent, nom) ON UPDATE CASCADE ON DELETE SET NULL
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
            moyen_paiement TEXT,
            is_position INTEGER,
            FOREIGN KEY (compte_id) REFERENCES comptes(id) ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (moyen_paiement) REFERENCES moyen_paiement(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (tier) REFERENCES tiers(id) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_tier) REFERENCES type_tier(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (categorie) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (type_beneficiaire) REFERENCES type_beneficiaire(nom) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (beneficiaire,type_beneficiaire) REFERENCES beneficiaire(nom,type_beneficiaire) ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (categorie, sous_categorie) REFERENCES sous_categorie(categorie_parent, nom) ON UPDATE CASCADE ON DELETE SET NULL
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
        FOREIGN KEY (categorie, sous_categorie) REFERENCES sous_categorie(categorie_parent, nom) ON UPDATE CASCADE ON DELETE SET NULL,
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
        PRIMARY KEY (nom, categorie_parent),
        FOREIGN KEY (categorie_parent) REFERENCES categorie(nom) ON UPDATE CASCADE ON DELETE SET NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS beneficiaire (
        nom TEXT,
        type_beneficiaire TEXT,
        PRIMARY KEY (nom,type_beneficiaire),
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
def InsertOperation(operation, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    compte = GetCompte(str(operation.compte_id), conn)
    compte.solde += operation.debit
    compte.solde += operation.credit
    operation.solde = compte.solde
    UpdateSoldeCompte(str(compte._id),compte.solde, conn)

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


def InsertEcheance(echeance, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO echeancier (id, frequence, echeance_1, prochaine_echeance, compte_id, type,compte_associe, type_tier, tier, categorie,sous_categorie, debit, credit, nb_part,val_part,frais,interets,note,type_beneficiaire,beneficiaire,moyen_paiement,is_position)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        echeance.beneficiaire,
        echeance.moyen_paiement,
        echeance.is_position

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
        val_part = 0 if val_part is None else val_part
        valo_placement = val_part*nb_part
        valo += valo_placement
    compte = GetCompte(compte_id,conn)
    compte.solde = valo
    UpdateSoldeCompte(compte_id,compte.solde,conn)
    if was_none:
        conn.close()


def InsertPosition(position:Position, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    montant_investit = 0
    if position.type == "Achat":
        montant_investit = round((position.val_part*position.nb_part + position.frais),2)
    position.montant_investit = montant_investit

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
def InsertCompte(compte, parent = None, db_path=None) -> bool:
    conn = connect_db(db_path)
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

def UpdateTier(tier, db_path=None):
    conn = connect_db(db_path)
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
    
    cursor.execute('''
    UPDATE operations
    set type_tier = ?, moyen_paiement = ?, categorie = ?, sous_categorie = ?
    where tier = ?
    ''',(tier.type, tier.moyen_paiement,tier.categorie,tier.sous_categorie,str(tier._id)))

    conn.commit()
    conn.close()

def UpdateBqOperation(operation_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
    UPDATE operations
    SET bq = 1
    WHERE id = ?
    ''', (operation_id,))

    conn.commit()
    conn.close()

def UpdateSousCategorie(sous_categorie,old_nom:str,old_categorie:str, parent=None,db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        cursor.execute('''
        UPDATE sous_categorie
        SET nom = ?, categorie_parent = ?
        WHERE nom = ? and categorie_parent = ?
        ''', (sous_categorie.nom,
            sous_categorie.categorie_parent,
            old_nom,
            old_categorie))
        
    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Mise à jour impossible",
            f"La sous-catégorie {sous_categorie.nom}/{sous_categorie.categorie_parent} existe déjà."
        )
        return False
    
    

    conn.commit()
    conn.close()
    return True

def UpdateBeneficiaire(beneficiaire,old_nom:str, old_type_beneficiaire:str,parent = None,db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        cursor.execute('''
        UPDATE beneficiaire
        SET nom = ?, type_beneficiaire = ?
        WHERE nom = ? and type_beneficiaire = ?
        ''', (beneficiaire.nom,
            beneficiaire.type_beneficiaire,
            old_nom,
            old_type_beneficiaire))

    except sqlite3.IntegrityError:
        QMessageBox.warning(
            parent,
            "Mise à jour impossible",
            f"La sous-catégorie {beneficiaire.nom}/{beneficiaire.type_beneficiaire} existe déjà."
        )
        return False
    
    

    conn.commit()
    conn.close()

def UpdateCategorie(categorie,old_nom:str, db_path=None):
    conn = connect_db(db_path)
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

def UpdateTypeBeneficiaire(type_beneficiaire,old_nom:str, db_path=None):
    conn = connect_db(db_path)
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


def UpdateTypeTypeTier(type_tier,old_nom:str, db_path=None):
    conn = connect_db(db_path)
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

def UpdatePlacement(placement,old_nom:str, db_path=None):
    conn = connect_db(db_path)
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

def UpdateMoyenPaiement(moyen_paiement,old_nom:str, db_path=None):
    conn = connect_db(db_path)
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

def UpdateCompte(compte, db_path=None):
    conn = connect_db(db_path)
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

def GetTierName(tier_id: str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT nom
    FROM tiers
    WHERE id = ?
    """, (tier_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def GetInitialSolde(compte_id: str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT solde_initial
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def GetNextNumCheque(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
SELECT COALESCE(MAX(CAST(num_cheque AS INTEGER)), 0) + 1
FROM operations
    """)

    result = cursor.fetchone()
    conn.close()

    return str(result[0]) if result else None


def GetCompteName(compte_id: str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT nom
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def GetCompteType(compte_id: str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT type
    FROM comptes
    WHERE id = ?
    """, (compte_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def GetSousCategorie(categorie:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select nom from sous_categorie where categorie_parent = ? order by categorie_parent,nom asc",(categorie,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories: # Assuming SousCategorie and ObjectId are defined in Datas.py
        sous_categorie = SousCategorie(row[0],categorie)
        result.append(sous_categorie)

    return result

def GetSousCategorieFiltre(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select distinct nom from sous_categorie order by nom asc")
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        sous_categorie = SousCategorie(row[0],None)
        result.append(sous_categorie)

    return result

def GetLastValueForPlacement(nom_placement: str,conn = None):
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

def GetHistoriquePlacement(nom:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,date,valeur_actualise,origine from historique_placement where nom = '{nom}'")
    historique_placement = cursor.fetchall()

    conn.close()

    result = []
    for row in historique_placement:
        placement = HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])
        result.append(placement)

    return result

def GetHistoriquePlacementByDate(nom:str,date:int, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,date,valeur_actualise,origine from historique_placement where nom = '{nom}' and date = {date}")
    row = cursor.fetchone()

    conn.close()
    return HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])


def GetAllSousCategorie(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from sous_categorie order by categorie_parent,nom")
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        sous_categorie = SousCategorie(row[0],row[1])
        result.append(sous_categorie)

    return result

def DeleteEcheance(echeance_id:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM echeancier WHERE id = ?", (str(echeance_id),))
    conn.commit()

    conn.close()

def UpdateEcheance(echeance, db_path=None):
    DeleteEcheance(echeance._id, db_path)
    InsertEcheance(echeance, db_path)

def GetEcheance(echeance_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from echeancier where id = '{echeance_id}'")
    row = cursor.fetchone()

    conn.close()
    echeance = Echeance(row[1],row[2],row[3],row[5],row[7],row[8],row[9],row[10],row[11],row[12],row[17],row[4],row[13],row[14],row[15],row[16],row[20],row[21],row[6],row[17],row[18],row[0])

    return echeance


def GetAllEcheance(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from echeancier")
    echeances = cursor.fetchall()

    conn.close()

    result = []
    for row in echeances:
        echeance = Echeance(row[1],row[2],row[3],row[5],row[7],row[8],row[9],row[10],row[11],row[12],row[17],row[4],row[13],row[14],row[15],row[16],row[20],row[21],row[6],row[17],row[18],row[0])
        result.append(echeance)

    return result

def GetAllBeneficiaire(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from beneficiaire order by nom asc")
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        beneficiaire = Beneficiaire(row[0],row[1])
        result.append(beneficiaire)

    return result

def GetBeneficiairesByType(type_beneficiaire : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from beneficiaire where type_beneficiaire = ?",(type_beneficiaire,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        beneficiaire = Beneficiaire(row[0],row[1])
        result.append(beneficiaire)

    return result

def GetMoyenPaiement(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from moyen_paiement order by nom asc")
    moyen_paiements = cursor.fetchall()

    conn.close()

    result = []
    for row in moyen_paiements:
        moyen_paiement = MoyenPaiement(row[0])
        result.append(moyen_paiement)

    return result

def GetCategorie(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from categorie order by nom asc")
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        categorie = Categorie(row[0])
        result.append(categorie)

    return result


def GetTypeBeneficiaire(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select * from type_beneficiaire order by nom asc")
    types_beneficiaire = cursor.fetchall()

    conn.close()

    result = []
    for row in types_beneficiaire:
        type_beneficiaire = TypeBeneficiaire(row[0])
        result.append(type_beneficiaire)

    return result


def GetLastPlacement(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select nom,type,max(date),valeur_actualise,origine from historique_placement group by nom")
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        placement = HistoriquePlacement(row[0],row[1],row[2],row[3],row[4])
        result.append(placement)

    return result

def GetTierRelatedOperations(tier_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where tier = '{tier_id}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetSousCategorieRelatedOperations(nom_sous_categorie : str,categorie_parent:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where sous_categorie = '{nom_sous_categorie}' and categorie = '{categorie_parent}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetCategorieRelatedOperations(nom_categorie : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where categorie = '{nom_categorie}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]


def GetTypeBeneficiaireRelatedOperations(type_beneficiaire : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where type_beneficiaire = '{type_beneficiaire}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetBeneficiaireRelatedOperations(beneficiaire : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where beneficiaire = '{beneficiaire}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetTypeTierRelatedOperations(nom_type_tier : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where type_tier = '{nom_type_tier}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def GetMoyenPaiementRelatedOperations(nom_moyen_paiement : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"select count(*) from operations where moyen_paiement = '{nom_moyen_paiement}'")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def DeleteTier(tier_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM tiers WHERE id = ?", (tier_id,))
    conn.commit()

    conn.close()

def DeleteOperation(operation,old_credit:float,old_debit:float, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    compte = GetCompte(str(operation.compte_id), conn)
    compte.solde -= old_credit
    compte.solde -= old_debit
    operation.solde = compte.solde
    UpdateSoldeCompte(str(compte._id),compte.solde, conn)
    cursor.execute("DELETE FROM operations WHERE id = ?", (str(operation._id),))
    conn.commit()

    conn.close()

def DeletePosition(position:Position, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    compte = GetCompte(str(position.compte_id), conn)
    compte.solde -= round((position.nb_part*position.val_part),2)
    UpdateSoldeCompte(str(compte._id),compte.solde, conn)
    cursor.execute("DELETE FROM position WHERE id = ?", (str(position._id),))
    conn.commit()

    conn.close()

def DeleteCompte(compte_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM comptes WHERE id = ?", (compte_id,))
    conn.commit()

    conn.close()

def DeletePlacement(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    SetPlacementTo0(nom,conn)
    for compte_id in GetComptePlacement(nom, conn):
        GetLastValueForPlacement(nom,conn)
        UpdateValoComptePlacement(compte_id,conn)
    cursor.execute("DELETE FROM placement WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteHistoriquePlacement(nom : str, date : int, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historique_placement WHERE nom = ? and date = ?", (nom,date,))
    conn.commit()
    for compte_id in GetComptePlacement(nom,conn):
            UpdateValoComptePlacement(compte_id,conn)

    conn.close()

def DeleteSousCategorie(nom : str,categorie_parent:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM sous_categorie WHERE nom = ? and categorie_parent = ?", (nom,categorie_parent))
    conn.commit()

    conn.close()

def DeleteCategorie(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM categorie WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()
def DeleteTypeTier(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM type_tier WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteTypeBeneficiaire(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM type_beneficiaire WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

def DeleteBeneficiaire(nom : str,type_beneficiaire:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM beneficiaire WHERE nom = ? and type_beneficiaire = ?", (nom,type_beneficiaire))
    conn.commit()

    conn.close()

def DeleteMoyenPaiement(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM moyen_paiement WHERE nom = ?", (nom,))
    conn.commit()

    conn.close()

# Obtenir tous les comptes
def GetComptes(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, nom, solde, type, nom_banque FROM comptes order by nom asc')
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes: # Assuming Compte and ObjectId are defined in Datas.py
        c = Compte(row[1], row[2], row[3], row[4], ObjectId(row[0]))
        result.append(c)

    return result

def GetComptesHorsPlacement(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, nom, solde, type, nom_banque FROM comptes where type == "Courant" OR type == "Epargne"')
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes: # Assuming Compte and ObjectId are defined in Datas.py
        c = Compte(row[1], row[2], row[3], row[4], ObjectId(row[0]))
        result.append(c)

    return result

# Obtenir tous les comptes sauf l'actuel
def GetComptesExceptCurrent(compte_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, nom, solde, type, nom_banque FROM comptes where id != '{compte_id}'")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        c = Compte(row[1], row[2], row[3], row[4], ObjectId(row[0]))
        result.append(c)

    return result


def GetDerniereValeurPointe(compte_id:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""SELECT solde,date FROM historique_pointage
        WHERE compte_id = ? 
        ORDER BY date DESC LIMIT 1""",(compte_id,))
    val_pointe = cursor.fetchone()

    conn.close()
    return (val_pointe[0],val_pointe[1])

# Obtenir tous les comptes
def GetOperations(compte_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where compte_id = '{compte_id}' order by date asc")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        operation = Operation(row[1], row[2], row[4], row[5], row[6], row[8], row[9], row[10], row[11], row[12],compte_id, row[7],row[3],row[13],row[0],row[15],row[16],row[17])
        result.append(operation)

    return result


def GetFilteredOperations(date_debut, date_fin, categories=None, sous_categories=None, tiers=None, comptes=None, bq=None, type_tiers = None, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    categories = categories or []
    sous_categories = sous_categories or []
    tiers = tiers or []
    type_tiers = type_tiers or []
    comptes = comptes or []

    def placeholders(values, prefix):
        return ','.join(f':{prefix}{i}' for i in range(len(values)))

    query = f"""
    SELECT * FROM operations
    WHERE date >= :date_debut AND date <= :date_fin
      AND (:categories_empty OR categorie IN ({placeholders(categories, 'cat')}))
      AND (:sous_categories_empty OR sous_categorie IN ({placeholders(sous_categories, 'sous')}))
      AND (:tiers_empty OR tier IN ({placeholders(tiers, 'tier')}))
      AND (:type_tiers_empty OR type_tier IN ({placeholders(type_tiers,'type_tiers')}))
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
        'tiers_empty': not tiers,
        'type_tiers_empty': not type_tiers
    }

    for i, val in enumerate(categories):
        params[f'cat{i}'] = val
    for i, val in enumerate(sous_categories):
        params[f'sous{i}'] = val
    for i, val in enumerate(tiers):
        params[f'tier{i}'] = val
    for i, val in enumerate(type_tiers):
        params[f'type_tiers{i}'] = val
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


def GetOperationsNotBq(compte_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where compte_id = '{compte_id}' and bq = 0 order by date asc")
    comptes = cursor.fetchall()

    conn.close()

    result = []
    for row in comptes:
        operation = Operation(row[1], row[2], row[4], row[5], row[6], row[8], row[9], row[10], row[11], row[12],compte_id, row[7],row[3],row[13],row[0],row[15],row[16],row[17])
        result.append(operation)

    return result

def GetOperation(operation_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM operations where id = '{operation_id}'")
    operation_bd = cursor.fetchone()

    conn.close()

    operation = Operation(operation_bd[1], operation_bd[2], operation_bd[4], operation_bd[5], operation_bd[6], operation_bd[8], operation_bd[9], operation_bd[10], operation_bd[11], operation_bd[12],operation_bd[14], operation_bd[7],operation_bd[3],operation_bd[13],operation_bd[0],operation_bd[15],operation_bd[16],operation_bd[17])

    # return operation
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
def UpdateDoneOperation(operation, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE operations
    SET done = 1
    WHERE id = ?
    ''', (str(operation._id),))

    conn.commit()
    conn.close()

# Mettre à jour la date du dernier paiement d'un tiers
def UpdateDatePaiementTier(operation, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE tiers
    SET date_dernier_paiement = ?
    WHERE nom = ?
    ''', (operation.date.isoformat(), operation.tier['nom']))

    conn.commit()
    conn.close()

# Récupérer tous les tiers
def GetTiers(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers order by type,nom asc')
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5],ObjectId(row[0]),row[6])
        result.append(t)

    return result

def GetTierById(tier_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers where id = ?',(tier_id,))
    t = cursor.fetchone()

    conn.close()

    tier = Tier(t[1],t[2],t[3],t[4],t[5],ObjectId(t[0]),t[6])
    return tier

def GetTiersActif(db_path=None):
    conn = connect_db(db_path)
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

def GetTierActif(tier_id : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tiers where est_actif = 1 and id = ?',(tier_id,))
    t = cursor.fetchone()

    conn.close()
    if t is not None:
        tier = Tier(t[1],t[2],t[3],t[4],t[5],actif=t[6])
        tier._id = ObjectId(t[0])
        return tier
    return

def GetTiersActifByType(type_tier: str, db_path=None):
    conn = connect_db(db_path)
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

def GetTiersByType(type_tier: str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM tiers where type = '{type_tier}' order by nom asc")
    tiers = cursor.fetchall()

    conn.close()

    result = []
    for row in tiers:
        t = Tier(row[1],row[2],row[3],row[4],row[5])
        t._id = ObjectId(row[0])
        result.append(t)

    return result

def GetTiersActifByTypeExceptCurrent(type_tier: str, current_tier_id: str, db_path=None):
    conn = connect_db(db_path)
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

def GetSousCategorieByCategorieParentExceptCurrent(nom : str, categorie_parent : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM sous_categorie where categorie_parent = ? and nom != ? ",(categorie_parent,nom,))
    sous_categories = cursor.fetchall()

    conn.close()

    result = []
    for row in sous_categories:
        s = SousCategorie(row[0],row[1])
        result.append(s)

    return result

def GetCategorieExceptCurrent(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM categorie where nom != ? ",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        s = Categorie(row[0])
        result.append(s)

    return result


def GetTypeBeneficiaireExceptCurrent(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM type_beneficiaire where nom != ? ",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        s = TypeBeneficiaire(row[0])
        result.append(s)

    return result

def GetTypeTierExceptCurrent(nom : str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM type_tier where nom != ? order by nom asc",(nom,))
    categories = cursor.fetchall()

    conn.close()

    result = []
    for row in categories:
        t = TypeTier(row[0])
        result.append(t)

    return result

def GetMoyenPaiementExceptCurrent(nom : str, db_path=None):
    conn = connect_db(db_path)
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
def InsertTier(tier,parent=None, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    for tiers in GetTiers():
        if tier.nom.lower() == tiers.nom.lower() and tier.type == tiers.type:
            QMessageBox.warning(parent,"Insertion impossible",f"Le tiers '{tier.nom.lower()}' existe déjà pour le type de tiers {tier.type}.")
            conn.close()
            return False

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
    return True

# Insérer une catégorie de tiers
def InsertCategorieTiers(categorie,parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
def InsertPlacement(placement,parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
def InsertHistoriquePlacement(historique_placement,parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO historique_placement (nom, type,date,valeur_actualise,origine)
        VALUES (?, ?, ?, ?, ?)
        ''', (historique_placement.nom, historique_placement.type,historique_placement.date,historique_placement.val_actualise,historique_placement.origine))

        conn.commit()
        for compte_id in GetComptePlacement(historique_placement.nom, conn):
            UpdateValoComptePlacement(compte_id,conn)

        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def InsertHistoriquePointage(compte_id,date,solde, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO historique_pointage (compte_id, date,solde)
    VALUES (?, ?, ?)
    ''', (compte_id, date,solde))

    conn.commit()
    conn.close()

# Insérer une sous-catégorie
def InsertSousCategorie(sous_categorie, parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
            f"La sous-categorie '{sous_categorie.nom}' existe déjà pour la catégorie {sous_categorie.categorie_parent}."
        )
        return False
    finally:
        conn.close()


def InsertBeneficiaire(beneficiaire, parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
            f"Le bénéficiaire '{beneficiaire.nom}' existe déjà pour le type de bénéficiaire {beneficiaire.type_beneficiaire}."
        )
        return False
    finally:
        conn.close()

def InsertCategorie(categorie, parent = None, db_path=None) -> bool:
    conn = connect_db(db_path)
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


def InsertTypeBeneficiaire(type_beneficiaire, parent = None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
            f"Le type bénéficiaire '{type_beneficiaire.nom}' existe déjà."
        )
        return False
    finally:
        conn.close()

def InsertMoyenPaiement(moyen_paiement, parent = None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
def GetNomBanque(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT nom_banque FROM comptes')
    banques = cursor.fetchall()

    conn.close()

    return [row[0] for row in banques]

# Mettre à jour le solde jour du compte
def UpdateSoldeJour(compte, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE comptes
    SET solde_jour = ?
    WHERE id = ?
    ''', (compte.solde_jour, str(compte._id)))

    conn.commit()
    conn.close()

# Obtenir un compte par nom et banque
def GetCompte(compte_id:str,conn = None) :
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


def GetPositions(compte_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT date,type,nom_placement,nb_part,val_part,frais,interets,notes,compte_id,montant_investit,compte_associe,id FROM position where compte_id = '{compte_id}' order by date asc")
    positions = cursor.fetchall()

    conn.close()

    result = []
    for row in positions:
        position = Position(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11])
        result.append(position)

    return result


def GetPosition(position_id:str, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT date,type,nom_placement,nb_part,val_part,frais,interets,notes,compte_id,montant_investit,compte_associe,id FROM position where id = '{position_id}' order by date asc ")
    row = cursor.fetchone()

    conn.close()
    position = Position(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11])
    return position

def GetPlacements(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT nom,type FROM placement")
    placements = cursor.fetchall()

    conn.close()

    result = []
    for row in placements:
        placement = Placement(row[0],row[1])
        result.append(placement)

    return result

def InsertTypeTier(typeTier, parent=None, db_path=None) -> bool:
    conn = connect_db(db_path)
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
    
def GetTypeTier(db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM type_tier order by nom asc")
    types_tier = cursor.fetchall()

    result = []
    for row in types_tier:
        type_tier = TypeTier(row[0])
        result.append(type_tier)

    return result

def GetTypePlacement(nom_placement, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM placement where nom = ?",(nom_placement,))
    result = cursor.fetchone()

    return result[0]

def UpdateTierInOperations(old_tier_id, new_tier_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET tier = ?
        WHERE tier = ?
    """, (new_tier_id, old_tier_id))
    conn.commit()
    conn.close()


def UpdateTypeBeneficiaireInOperations(old_type_beneficiaire, new_type_beneficiaire, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_beneficiaire = ?
        WHERE type_beneficiaire = ?
    """, (old_type_beneficiaire, new_type_beneficiaire))
    conn.commit()
    conn.close()

def UpdateBeneficiaireInOperations(old_beneficiaire, new_beneficiaire, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_beneficiaire = ?
        WHERE type_beneficiaire = ?
    """, (old_beneficiaire, new_beneficiaire))
    conn.commit()
    conn.close()

def UpdateSousCategorieInOperations(old_sous_categorie, new_sous_categorie,categorie, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET sous_categorie = ?
        WHERE sous_categorie = ?
        AND categorie = ?
    """, (new_sous_categorie, old_sous_categorie,categorie))
    conn.commit()
    conn.close()


def UpdateTypeTierInOperations(old_type_tier, new_type_tier, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET type_tier = ?
        WHERE type_tier = ?
    """, (new_type_tier, old_type_tier))
    conn.commit()
    conn.close()

def UpdateMoyenPaiementInOperations(old_moyen_paiement, new_moyen_paiement, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET moyen_paiement = ?
        WHERE moyen_paiement = ?
    """, (new_moyen_paiement, old_moyen_paiement))
    conn.commit()
    conn.close()

def UpdateCategorieInOperations(old_categorie, new_categorie, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operations
        SET categorie = ?
        WHERE categorie = ?
    """, (new_categorie, old_categorie))
    conn.commit()
    conn.close()

def UpdateSousCategorieTier(old_sous_categorie, new_sous_categorie,categorie, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET sous_categorie = ?
        WHERE sous_categorie = ?
        AND categorie = ?
    """, (new_sous_categorie, old_sous_categorie,categorie))
    conn.commit()
    conn.close()

def UpdateTypeTier(old_type_tier, new_type_tier, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET type = ?
        WHERE type = ?
    """, (new_type_tier, old_type_tier))
    conn.commit()
    conn.close()

def UpdateMoyenPaiementTier(old_moyen_paiement, new_moyen_paiement, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET moy_paiement = ?
        WHERE moy_paiement = ?
    """, (new_moyen_paiement, old_moyen_paiement))
    conn.commit()
    conn.close()

def UpdateCategorieTier(old_categorie, new_categorie, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tiers
        SET categorie = ?
        WHERE categorie = ?
    """, (new_categorie, old_categorie))
    conn.commit()
    conn.close()

def GetPerformanceGlobaleData(compte_id: str, db_path=None):
    conn = connect_db(db_path)
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
    montant_frais = 0
    last_values = {}

    for p in positions:
        type_op, nb_part, nom_placement, montant_investit, val_part, interets, frais = p
        montant_frais += frais
        # Récupération de la valeur du placement avec caching
        if nom_placement not in last_values:
            last_values[nom_placement] = GetLastValueForPlacement(nom_placement, conn) # Pass conn
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
        "frais" : round(montant_frais),
        "perf": round(perf, 2)
    }


def GetBilanByCategorie(date_debut:int,date_fin:int, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        select c.nom, c.id, o.categorie,o.sous_categorie,(sum(o.debit)+sum(o.credit)) as somme
        from operations o
        inner join comptes c on o.compte_id = c.id
        where o.date >= ? and o.date <= ?
        group by o.compte_id,o.categorie,o.sous_categorie
    """,(date_debut,date_fin,))
    rows = cursor.fetchall()
    result = []
    hierarchy_level = ["type_flux","compte","categorie","sous_cat"]
    negative_treatment = {
    "column_to_update": "type_flux",
    "negative_label": "Dépenses",
    "positive_label": "Revenus"
}

    for row in rows:
        result.append({"compte": row[0], "compte_id": row[1], "categorie": row[2], "sous_cat": row[3], "montant": row[4]})
    
    return result,hierarchy_level,negative_treatment

def GetBilanByTiers(date_debut:int,date_fin:int, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        select c.nom,c.id,t.type,t.nom,t.id,(sum(o.debit)+sum(o.credit)) as somme
        from operations o
        inner join comptes c on o.compte_id = c.id
        inner join tiers t  on o.tier = t.id
        where o.date >= ? and o.date <= ?
        group by o.compte_id,o.tier
    """,(date_debut,date_fin,))
    rows = cursor.fetchall()
    result = []
    hierarchy_level = ["type_flux","compte","type_tiers","tiers"]
    negative_treatment = {
    "column_to_update": "type_flux",
    "negative_label": "Dépenses",
    "positive_label": "Revenus"
}

    for row in rows:
        result.append({"compte": row[0], "compte_id": row[1], "type_tiers": row[2], "tiers": row[3],"tiers_id" : row[4], "montant": row[5]})
    
    return result,hierarchy_level,negative_treatment



def GetPerformanceByPlacement(compte_id: str, db_path=None):
    conn = connect_db(db_path)
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
        val_part = GetLastValueForPlacement(nom_placement, conn) # Pass conn
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

def GetEcheanceToday(current_date = int((datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y%m%d')), db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    # Récupération groupée par nom_placement
    cursor.execute("""
        SELECT *
        FROM echeancier
        WHERE prochaine_echeance <=  ?
    """, (current_date,))
    echeances = cursor.fetchall()
    return int(datetime.date.today().strftime('%Y%m%d')),echeances

def GetEcheanceForce(echeance_date,echeance_id, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    # Récupération groupée par nom_placement
    cursor.execute("""
        SELECT *
        FROM echeancier
        WHERE id = ?
    """, (echeance_id,))
    echeances = cursor.fetchall()
    return echeance_date,echeances

def UpdateProchaineEcheance(id,next_date, db_path=None):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE echeancier
    SET prochaine_echeance = ?
    WHERE id = ?
    ''', (next_date,
          id))

    conn.commit()
    conn.close()


def RunEcheance(current_date,echeances, db_path=None):
    from Main import get_next_echeance
    for row in echeances:
        if row[21]:
            montant_investit = round(row[13]*row[14] + row[15])
            position = Position(current_date,row[5],row[8],row[13],row[14],row[15],row[16],row[17],row[4],montant_investit,row[6])
            InsertPosition(position, db_path)
            if position.type == "Achat":
                InsertOperation(Operation(position.date,TypeOperation.TransfertV.value,"","","","","",round((position.nb_part*position.val_part * -1) - position.frais),0,f"Achat de {position.nb_part} parts de {position.nom_placement} à {position.val_part} €",position.compte_associe,compte_associe=position.compte_id), db_path)
            elif position.type == "Vente":
                InsertOperation(Operation(position.date,TypeOperation.TransfertD.value,"","","","","",0,round((position.nb_part*position.val_part * -1) - position.frais),f"Vente de {position.nb_part * -1} parts de {position.nom_placement} à {position.val_part} €",position.compte_associe,compte_associe=position.compte_id), db_path)
            pass
        else:
            operation = Operation(current_date,row[5],row[7],row[8],row[20],row[9],row[10],row[11],row[12],row[17],row[4],"",row[6],type_beneficiaire=row[18],beneficiaire=row[19])
            InsertOperation(operation, db_path)
            pass

        UpdateProchaineEcheance(row[0],get_next_echeance(current_date,row[1]), db_path)