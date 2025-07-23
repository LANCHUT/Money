from PyQt6.QtWidgets import QApplication, QWidget, QDialog # Ou la classe de votre fenêtre principale
from PyQt6.QtCore import Qt # <--- C'EST CETTE LIGNE QUI EST CRUCIALE

# ... à l'intérieur de votre classe ou fonction où vous changez le curseur ...

class MaClassePrincipale: # Remplacez par le nom de votre classe principale
    def __init__(self):
        # ... autres initialisations ...
        pass

    def open_qif(self):
        # Simule l'ouverture d'un fichier QIF
        print("Ouverture du fichier QIF...")
        return "MoneyQIF.qif"

    def import_qif(self):
        input_path = self.open_qif()
        # Supposons que GetComptesHorsPlacement et ImportDialog existent
        # Si vous n'avez pas ces objets réels, ceci est un exemple conceptuel.
        comptes = [] # Remplacez par votre logique
        import_dialog = QDialog() # Remplacez par votre ImportDialog réelle
        import_dialog.exec()
        compte_id = 123 # Remplacez par la valeur réelle obtenue

        if compte_id: # On continue seulement si un compte a été sélectionné
            # 1. Changer le curseur pour toute l'application
            # C'est la méthode recommandée pour indiquer une opération longue à l'échelle de l'application.
            QApplication.setOverrideCursor(Qt.WaitCursor)

            try:
                # 2. Appeler votre fonction d'importation des données QIF
                print(f"Importation des données QIF depuis {input_path} pour le compte {compte_id}...")
                # Simule une opération qui prend du temps
                import time
                time.sleep(3) # C'est ici que votre import_qif_data serait appelé
                # import_qif_data(input_path, compte_id, self.current_db_path)
                print("Importation terminée avec succès.")

            except Exception as e:
                # 3. Gérer les erreurs
                print(f"Une erreur est survenue lors de l'importation : {e}")
            finally:
                # 4. Toujours restaurer le curseur dans le bloc 'finally'
                # Cela garantit que le curseur redevient normal même en cas d'erreur.
                QApplication.restoreOverrideCursor()

# Exemple d'exécution (si vous testez ce code)
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_instance = MaClassePrincipale()
    main_instance.import_qif()
    # Si vous aviez une fenêtre visible, vous feriez app.exec()
    # sys.exit(app.exec())