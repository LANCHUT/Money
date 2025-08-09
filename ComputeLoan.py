from datetime import date, timedelta

def calculer_echeancier_pret_avec_assurance(
    montant_pret: float,
    taux_annuel_initial: float,
    duree_ans: int,
    assurance_par_periode: float = 0.0,
    frequence_paiement: str = 'mensuelle',
    date_debut: date = date.today(),
    taux_variables: list = None
) -> list:
    """
    Calcule un échéancier de prêt pour un taux fixe ou variable, en incluant une assurance fixe par période.

    Args:
        montant_pret (float): Montant total du prêt.
        taux_annuel_initial (float): Taux d'intérêt annuelle initial (ex: 0.05 pour 5%).
        duree_ans (int): Durée du prêt en années.
        assurance_par_periode (float): Montant fixe de l'assurance à ajouter à chaque paiement.
        frequence_paiement (str): Fréquence des paiements ('mensuelle', 'trimestrielle', 'semestrielle', 'annuelle').
        date_debut (date): Date de début du prêt.
        taux_variables (list): Optionnel. Liste de tuples (date_application, nouveau_taux_annuel)
                                pour les prêts à taux variable. La date doit être au format datetime.date.

    Returns:
        list: Une liste de dictionnaires, chaque dictionnaire représentant une échéance.
    """

    if frequence_paiement == 'mensuelle':
        paiements_par_an = 12
    elif frequence_paiement == 'trimestrielle':
        paiements_par_an = 4
    elif frequence_paiement == 'semestrielle':
        paiements_par_an = 2
    elif frequence_paiement == 'annuelle':
        paiements_par_an = 1
    else:
        raise ValueError("La fréquence de paiement doit être 'mensuelle', 'trimestrielle', 'semestrielle' ou 'annuelle'.")

    nombre_total_paiements = duree_ans * paiements_par_an
    solde_restant = montant_pret
    echeancier = []
    taux_annuel_actuel = taux_annuel_initial

    if taux_variables:
        taux_variables = sorted(taux_variables, key=lambda x: x[0])

    prochain_changement_taux_index = 0

    for i in range(1, nombre_total_paiements + 1):
        date_paiement = date_debut

        if frequence_paiement == 'mensuelle':
            mois_a_ajouter = i
            annee_sup = (date_debut.month + mois_a_ajouter - 1) // 12
            mois_paiement = (date_debut.month + mois_a_ajouter - 1) % 12 + 1
            annee_paiement = date_debut.year + annee_sup
            
            try:
                date_paiement = date(annee_paiement, mois_paiement, date_debut.day)
            except ValueError:
                import calendar
                dernier_jour_du_mois = calendar.monthrange(annee_paiement, mois_paiement)[1]
                date_paiement = date(annee_paiement, mois_paiement, dernier_jour_du_mois)

        elif frequence_paiement == 'trimestrielle':
            date_paiement = date_debut + timedelta(days=i * 365.25 / paiements_par_an)
        elif frequence_paiement == 'semestrielle':
            date_paiement = date_debut + timedelta(days=i * 365.25 / paiements_par_an)
        elif frequence_paiement == 'annuelle':
            date_paiement = date(date_debut.year + i, date_debut.month, date_debut.day)
        
        if taux_variables and prochain_changement_taux_index < len(taux_variables):
            date_changement, nouveau_taux = taux_variables[prochain_changement_taux_index]
            if date_paiement >= date_changement:
                taux_annuel_actuel = nouveau_taux
                prochain_changement_taux_index += 1
                while prochain_changement_taux_index < len(taux_variables) and \
                      date_paiement >= taux_variables[prochain_changement_taux_index][0]:
                    taux_annuel_actuel = taux_variables[prochain_changement_taux_index][1]
                    prochain_changement_taux_index += 1

        taux_periodique = taux_annuel_actuel / paiements_par_an

        if solde_restant <= 0:
            annuite_hors_assurance = 0
            interet = 0
            principal = 0
            solde_final = 0
        else:
            if taux_periodique == 0:
                annuite_hors_assurance = solde_restant / (nombre_total_paiements - (i - 1))
            else:
                annuite_hors_assurance = (solde_restant * taux_periodique) / (1 - (1 + taux_periodique)**(-(nombre_total_paiements - (i - 1))))

            interet = solde_restant * taux_periodique
            principal = annuite_hors_assurance - interet
            
            if principal > solde_restant:
                principal = solde_restant
                annuite_hors_assurance = principal + interet
            
            solde_final = solde_restant - principal
        
        loyer_total = annuite_hors_assurance + assurance_par_periode

        echeancier.append({
            'numéro_echeance': i,
            'date': date_paiement,
            'taux_annuel_applique': round(taux_annuel_actuel*100, 3),
            'taux_periode': round(taux_periodique*100,3),
            'capital_restant_du': round(solde_restant, 2),
            'intérêts': round(interet, 2),
            'capital': round(principal, 2),
            'assurance': round(assurance_par_periode, 2),
            'mensualite': round(loyer_total, 2)
        })

        solde_restant = solde_final
        if solde_restant < 0.01 and solde_restant > -0.01:
            solde_restant = 0      
    return echeancier