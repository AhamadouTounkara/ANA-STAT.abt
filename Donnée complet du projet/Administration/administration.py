"""Module Administration : gestion des comptes utilisateurs (réservé au rôle administrateur)."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QComboBox, QLineEdit, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from authentification import charger_utilisateurs, sauvegarder_utilisateurs, reinitialiser_mot_de_passe
from securite import lire_journal, hacher_mot_de_passe

ROLES_DISPONIBLES = ["administrateur", "analyste", "agent_saisie", "visiteur"]


def creer_page_administration(nom_utilisateur_connecte, role_utilisateur_connecte):
    """Assemble la page Administration. Réservée au rôle 'administrateur'."""
    page = QWidget()
    layout = QVBoxLayout()

    if role_utilisateur_connecte != "administrateur":
        label_refus = QLabel(
            "Accès réservé aux administrateurs.\n"
            f"Tu es actuellement connecté en tant que '{role_utilisateur_connecte}'."
        )
        label_refus.setStyleSheet("color: #DC2626; font-weight: bold; padding: 20px;")
        layout.addWidget(label_refus)
        layout.addStretch()
        page.setLayout(layout)
        return page

    titre = QLabel("Administration — Gestion des comptes")
    titre.setStyleSheet("font-size: 15px; font-weight: bold;")
    layout.addWidget(titre)

    groupe_comptes = QGroupBox("Comptes utilisateurs")
    layout_comptes = QVBoxLayout()

    tableau = QTableWidget()
    tableau.setColumnCount(2)
    tableau.setHorizontalHeaderLabels(["Nom d'utilisateur", "Rôle"])
    tableau.verticalHeader().setVisible(False)

    layout_boutons_comptes = QHBoxLayout()
    bouton_creer = QPushButton("Créer un compte")
    bouton_modifier_role = QPushButton("Modifier le rôle du compte sélectionné")
    bouton_reinitialiser_mdp = QPushButton("Réinitialiser le mot de passe du compte sélectionné")
    bouton_supprimer = QPushButton("Supprimer le compte sélectionné")
    for bouton in (bouton_creer, bouton_modifier_role, bouton_reinitialiser_mdp, bouton_supprimer):
        layout_boutons_comptes.addWidget(bouton)

    layout_comptes.addWidget(tableau)
    layout_comptes.addLayout(layout_boutons_comptes)
    groupe_comptes.setLayout(layout_comptes)

    groupe_journal = QGroupBox("Journal des actions")
    layout_journal = QVBoxLayout()
    label_journal = QLabel(lire_journal())
    label_journal.setWordWrap(True)
    label_journal.setStyleSheet("font-family: monospace; font-size: 9pt;")
    bouton_actualiser_journal = QPushButton("Actualiser le journal")
    layout_journal.addWidget(bouton_actualiser_journal)
    layout_journal.addWidget(label_journal)
    groupe_journal.setLayout(layout_journal)

    layout.addWidget(groupe_comptes)
    layout.addWidget(groupe_journal)
    page.setLayout(layout)

    def rafraichir_tableau():
        utilisateurs = charger_utilisateurs()
        noms = list(utilisateurs.keys())
        tableau.setRowCount(len(noms))
        for i, nom in enumerate(noms):
            tableau.setItem(i, 0, QTableWidgetItem(nom))
            tableau.setItem(i, 1, QTableWidgetItem(utilisateurs[nom].get("role", "visiteur")))

    def obtenir_compte_selectionne():
        lignes = tableau.selectionModel().selectedRows()
        if not lignes:
            QMessageBox.information(page, "Info", "Sélectionne d'abord un compte dans le tableau.")
            return None
        return tableau.item(lignes[0].row(), 0).text()

    def gerer_creation_compte():
        dialogue = QDialog(page)
        dialogue.setWindowTitle("Créer un compte")
        formulaire = QFormLayout()
        champ_nom = QLineEdit()
        champ_mdp = QLineEdit()
        champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        combo_role = QComboBox()
        combo_role.addItems(ROLES_DISPONIBLES)
        formulaire.addRow("Nom d'utilisateur :", champ_nom)
        formulaire.addRow("Mot de passe initial :", champ_mdp)
        formulaire.addRow("Rôle :", combo_role)
        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.accepted.connect(dialogue.accept)
        boutons.rejected.connect(dialogue.reject)
        formulaire.addWidget(boutons)
        dialogue.setLayout(formulaire)

        if dialogue.exec() != QDialog.DialogCode.Accepted:
            return

        nom, mdp, role = champ_nom.text().strip(), champ_mdp.text(), combo_role.currentText()
        if not nom or not mdp:
            QMessageBox.warning(page, "Erreur", "Le nom d'utilisateur et le mot de passe sont obligatoires.")
            return

        utilisateurs = charger_utilisateurs()
        if nom in utilisateurs:
            QMessageBox.warning(page, "Erreur", "Ce nom d'utilisateur existe déjà.")
            return

        mdp_hache = hacher_mot_de_passe(mdp)
        utilisateurs[nom] = {
            "mot_de_passe_hache": mdp_hache.decode("utf-8"),
            "role": role,
            "question_secrete": "Définie par l'administrateur",
            "reponse_secrete_hachee": hacher_mot_de_passe("admin").decode("utf-8"),
        }
        sauvegarder_utilisateurs(utilisateurs)
        QMessageBox.information(page, "Compte créé", f"Le compte '{nom}' a été créé avec le rôle '{role}'.")
        rafraichir_tableau()

    def gerer_modification_role():
        nom = obtenir_compte_selectionne()
        if nom is None:
            return
        utilisateurs = charger_utilisateurs()

        dialogue = QDialog(page)
        dialogue.setWindowTitle(f"Modifier le rôle de '{nom}'")
        formulaire = QFormLayout()
        combo_role = QComboBox()
        combo_role.addItems(ROLES_DISPONIBLES)
        combo_role.setCurrentText(utilisateurs[nom].get("role", "visiteur"))
        formulaire.addRow("Nouveau rôle :", combo_role)
        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.accepted.connect(dialogue.accept)
        boutons.rejected.connect(dialogue.reject)
        formulaire.addWidget(boutons)
        dialogue.setLayout(formulaire)

        if dialogue.exec() != QDialog.DialogCode.Accepted:
            return

        utilisateurs[nom]["role"] = combo_role.currentText()
        sauvegarder_utilisateurs(utilisateurs)
        QMessageBox.information(page, "Rôle modifié", f"'{nom}' a maintenant le rôle '{combo_role.currentText()}'.")
        rafraichir_tableau()

    def gerer_reinitialisation_mdp():
        nom = obtenir_compte_selectionne()
        if nom is None:
            return
        nouveau_mdp, ok = QDialog(), None
        from PyQt6.QtWidgets import QInputDialog
        nouveau_mdp, ok = QInputDialog.getText(page, "Réinitialiser le mot de passe",
                                                f"Nouveau mot de passe pour '{nom}' :",
                                                QLineEdit.EchoMode.Password)
        if not ok or not nouveau_mdp:
            return
        utilisateurs = charger_utilisateurs()
        reinitialiser_mot_de_passe(utilisateurs, nom, nouveau_mdp)
        QMessageBox.information(page, "Mot de passe réinitialisé", f"Le mot de passe de '{nom}' a été changé.")

    def gerer_suppression_compte():
        nom = obtenir_compte_selectionne()
        if nom is None:
            return
        if nom == nom_utilisateur_connecte:
            QMessageBox.warning(page, "Erreur", "Tu ne peux pas supprimer ton propre compte.")
            return
        reponse = QMessageBox.question(
            page, "Confirmer la suppression", f"Supprimer définitivement le compte '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reponse != QMessageBox.StandardButton.Yes:
            return
        utilisateurs = charger_utilisateurs()
        del utilisateurs[nom]
        sauvegarder_utilisateurs(utilisateurs)
        QMessageBox.information(page, "Compte supprimé", f"Le compte '{nom}' a été supprimé.")
        rafraichir_tableau()

    def gerer_actualisation_journal():
        label_journal.setText(lire_journal())

    bouton_creer.clicked.connect(gerer_creation_compte)
    bouton_modifier_role.clicked.connect(gerer_modification_role)
    bouton_reinitialiser_mdp.clicked.connect(gerer_reinitialisation_mdp)
    bouton_supprimer.clicked.connect(gerer_suppression_compte)
    bouton_actualiser_journal.clicked.connect(gerer_actualisation_journal)

    rafraichir_tableau()

    return page
