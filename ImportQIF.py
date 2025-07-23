from collections import defaultdict
import os
from qifparse.parser import QifParser
from PyQt6.QtWidgets import QFileDialog
from GestionBD import *


def clean_qif_file(input_path, output_path):
    with open(input_path, 'r', encoding='windows-1252', errors='ignore') as infile:
        lines = infile.readlines()

    cleaned_lines = []
    for line in lines:
        # Remplace les caractères non imprimables comme les espaces insécables (\xa0)
        line = line.replace('\xa0', '').replace('\u202f', '')  # juste au cas où

        # Nettoyage des montants (ligne commençant par 'T')
        if line.startswith('T'):
            line = 'T' + line[1:].replace(',', '')  # enlever les , dans les montants

        cleaned_lines.append(line)

    with open(output_path, 'w', encoding='windows-1252') as outfile:
        outfile.writelines(cleaned_lines)

def import_qif_data(input_path:str,compte_id:str, db_path: str):

    outputpath = input_path.replace(".qif","_cleaned.qif")

        # Utilisation
    clean_qif_file(input_path, outputpath)

    with open(outputpath, "r", encoding="windows-1252", errors="ignore") as f:
        qif = QifParser.parse(f)

    categories = set()
    subcategories = defaultdict(set)
    tiers_cat_map = {}  # tier → (cat, subcat)

    # Transactions
    for txn in qif.get_transactions()[0]:  # [0] = premier compte
        cat, subcat = None, None
        if txn.category:
            if ':' in txn.category:
                cat, subcat = txn.category.split(':', 1)
                cat = cat.strip()
                subcat = subcat.strip()
                categories.add(cat)
                subcategories[subcat].add(cat)
            else:
                cat = txn.category.strip()
                subcat = None
                categories.add(cat)

        if txn.payee:
            payee = txn.payee.strip()
            if payee not in tiers_cat_map:  # tier unique : on ne l'écrase pas s'il existe déjà
                tiers_cat_map[payee] = (cat, subcat)

    # Insertion des catégories
    for categorie_nom in categories:
        c = Categorie(categorie_nom)
        InsertCategorie(c,db_path=db_path)

    # Insertion des sous-catégories
    for sous_categorie, categories_parente in subcategories.items():
        for cat in categories_parente:
            sc = SousCategorie(sous_categorie, cat)
            InsertSousCategorie(sc,db_path=db_path)

    # Charger les tiers connus depuis la base
    known_tiers_from_db = GetTiers(db_path=db_path)

    # Créer un dictionnaire de lookup pour les noms de tiers existants
    known_tier_names = {tier.nom: str(tier._id) for tier in known_tiers_from_db}

    tiers_id = {}
    tiers_list = []

    # Construire les nouveaux tiers à insérer
    for tier_nom, (cat, subcat) in tiers_cat_map.items():
        if tier_nom in known_tier_names:
            tiers_id[tier_nom] = known_tier_names[tier_nom]
        else:
            t = Tier(tier_nom, "", cat, subcat, "")
            tiers_list.append(t)
            tiers_id[tier_nom] = str(t._id)

    # Associer None à une chaîne vide dans le dictionnaire tiers_id
    tiers_id[None] = ""

    # Insérer les nouveaux tiers dans la base
    for tier in tiers_list:
        InsertTier(tier, db_path=db_path)
                
    for txn in qif.get_transactions()[0]:  # [0] = premier compte
        # Extraction des champs
        date_operation = txn.date
        date_operation = int(date_operation.strftime("%Y%m%d"))
        montant = txn.amount
        if montant < 0 :
            debit = montant
            credit = 0
            type = "Débit"
        else :
            credit = montant
            debit = 0
            type = "Crédit"
        payee = txn.payee.strip() if txn.payee else None
        memo = txn.memo.strip() if txn.memo else None

        # Catégorie et sous-catégorie
        cat, subcat = None, None
        if txn.category:
            if ':' in txn.category:
                cat, subcat = txn.category.split(':', 1)
                cat = cat.strip()
                subcat = subcat.strip()
            else:
                cat = txn.category.strip()

        # Création et insertion de la transaction
        o = Operation(date_operation,type,"",tiers_id[payee] if tiers_id[payee] else None,"",cat if cat is not None else "",subcat if subcat is not None else "",debit,credit,memo,compte_id,bq = 1,beneficiaire='',type_beneficiaire="")

        InsertOperation(o,db_path=db_path)
    os.remove(outputpath)
if __name__ == "__main__":
    import_qif_data("687eaebb18a3c01464677aaa")




