from collections import defaultdict
from qifparse.parser import QifParser
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

# Utilisation
clean_qif_file("MoneyQIF.qif", "MoneyQIF_cleaned.qif")

with open("MoneyQIF_cleaned.qif", "r", encoding="windows-1252", errors="ignore") as f:
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
    InsertCategorie(c)

# Insertion des sous-catégories
for sous_categorie, categories_parente in subcategories.items():
    for cat in categories_parente:
        sc = SousCategorie(sous_categorie, cat)
        InsertSousCategorie(sc)

# Insertion des tiers avec leur catégorie/sous-catégorie
tiers_id = {}
for tier_nom, (cat, subcat) in tiers_cat_map.items():
    t = Tier(tier_nom,"",cat,subcat,"")  # adapte ce constructeur à ta classe
    InsertTier(t)
    tiers_id[tier_nom] = str(t._id)
tiers_id[None] = ""
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
    o = Operation(date_operation,type,"",tiers_id[payee] if tiers_id[payee] else None,"",cat if cat is not None else "",subcat if subcat is not None else "",debit,credit,memo,'683acc0e0bc36d2a2149d832',bq = 1)

    InsertOperation(o)





