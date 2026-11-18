from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QScrollArea, QApplication, QGroupBox
)
from PyQt6.QtGui import QShortcut, QKeySequence
from donnees import importer_donnees, afficher_apercu, detecter_domaine
from statistiques import calculer_statistiques
from EditionDonnees.edition_donnees import (
    ajouter_variable, supprimer_variable, renommer_variable, convertir_type,
    recoder_variable, creer_variable_calculee, ajouter_observation, supprimer_observations,
    filtrer_donnees, trier_donnees, detecter_valeurs_manquantes, detecter_doublons,
    fusionner_fichiers, joindre_fichiers, agreger_donnees
)


def activer_copie_presse_papier(tableau):
    """Ajoute le raccourci Ctrl+C pour copier la sélection (une ou plusieurs cellules, une colonne entière...)."""

    def gerer_copie():
        selection = tableau.selectedRanges()
        if not selection:
            return
        lignes_texte = []
        plage = selection[0]
        for r in range(plage.topRow(), plage.bottomRow() + 1):
            valeurs_ligne = []
            for c in range(plage.leftColumn(), plage.rightColumn() + 1):
                item = tableau.item(r, c)
                valeurs_ligne.append(item.text() if item else "")
            lignes_texte.append("\t".join(valeurs_ligne))
        QApplication.clipboard().setText("\n".join(lignes_texte))

    raccourci = QShortcut(QKeySequence.StandardKey.Copy, tableau)
    raccourci.activated.connect(gerer_copie)


def creer_onglet_donnees(obtenir_donnees_actuelles=None, definir_donnees_actuelles=None):
    """Crée l'onglet d'import, d'édition et d'affichage des données.

    obtenir_donnees_actuelles / definir_donnees_actuelles : callbacks optionnels reliés à l'état
    partagé du logiciel. Sans eux, l'onglet fonctionne seulement en import/affichage simple.
    """
    onglet = QWidget()
    layout = QVBoxLayout()

    label_statut = QLabel("Aucun fichier chargé.")
    bouton_importer = QPushButton("Importer des données")
    tableau = QTableWidget()
    activer_copie_presse_papier(tableau)

    layout.addWidget(bouton_importer)
    layout.addWidget(label_statut)

    if obtenir_donnees_actuelles is not None and definir_donnees_actuelles is not None:
        def rafraichir_apres_edition(nouvelles_donnees):
            definir_donnees_actuelles(nouvelles_donnees)
            if nouvelles_donnees is not None:
                domaine = detecter_domaine(nouvelles_donnees)
                texte_domaine = domaine if domaine else "non déterminé"
                label_statut.setText(
                    f"{nouvelles_donnees.shape[0]} lignes, {nouvelles_donnees.shape[1]} colonnes — "
                    f"Domaine détecté : {texte_domaine}"
                )
                afficher_apercu(nouvelles_donnees, tableau)

        def creer_bouton_edition(texte, fonction_edition):
            bouton = QPushButton(texte)

            def gerer_clic():
                resultat = fonction_edition(obtenir_donnees_actuelles(), onglet)
                rafraichir_apres_edition(resultat)

            bouton.clicked.connect(gerer_clic)
            return bouton

        def gerer_suppression_observations():
            lignes_selectionnees = sorted({index.row() for index in tableau.selectedIndexes()})
            if not lignes_selectionnees:
                return
            resultat = supprimer_observations(obtenir_donnees_actuelles(), lignes_selectionnees, onglet)
            rafraichir_apres_edition(resultat)

        groupe_variables = QGroupBox("Variables")
        layout_variables = QHBoxLayout()
        layout_variables.addWidget(creer_bouton_edition("Ajouter", ajouter_variable))
        layout_variables.addWidget(creer_bouton_edition("Supprimer", supprimer_variable))
        layout_variables.addWidget(creer_bouton_edition("Renommer", renommer_variable))
        layout_variables.addWidget(creer_bouton_edition("Recoder", recoder_variable))
        layout_variables.addWidget(creer_bouton_edition("Convertir le type", convertir_type))
        layout_variables.addWidget(creer_bouton_edition("Variable calculée", creer_variable_calculee))
        groupe_variables.setLayout(layout_variables)

        groupe_observations = QGroupBox("Observations")
        layout_observations = QHBoxLayout()
        layout_observations.addWidget(creer_bouton_edition("Ajouter une ligne", ajouter_observation))
        bouton_suppr_lignes = QPushButton("Supprimer les lignes sélectionnées")
        bouton_suppr_lignes.clicked.connect(gerer_suppression_observations)
        layout_observations.addWidget(bouton_suppr_lignes)
        groupe_observations.setLayout(layout_observations)

        groupe_organisation = QGroupBox("Organisation")
        layout_organisation = QHBoxLayout()
        layout_organisation.addWidget(creer_bouton_edition("Filtrer", filtrer_donnees))
        layout_organisation.addWidget(creer_bouton_edition("Trier", trier_donnees))
        groupe_organisation.setLayout(layout_organisation)

        groupe_qualite = QGroupBox("Qualité des données")
        layout_qualite = QHBoxLayout()

        def gerer_valeurs_manquantes():
            detecter_valeurs_manquantes(obtenir_donnees_actuelles(), onglet)

        def gerer_doublons():
            detecter_doublons(obtenir_donnees_actuelles(), onglet)

        bouton_manquants = QPushButton("Détecter les valeurs manquantes")
        bouton_manquants.clicked.connect(gerer_valeurs_manquantes)
        bouton_doublons = QPushButton("Détecter les doublons")
        bouton_doublons.clicked.connect(gerer_doublons)
        layout_qualite.addWidget(bouton_manquants)
        layout_qualite.addWidget(bouton_doublons)
        groupe_qualite.setLayout(layout_qualite)

        groupe_combinaison = QGroupBox("Combinaison")
        layout_combinaison = QHBoxLayout()
        layout_combinaison.addWidget(creer_bouton_edition("Fusionner (empiler)", fusionner_fichiers))
        layout_combinaison.addWidget(creer_bouton_edition("Joindre", joindre_fichiers))
        layout_combinaison.addWidget(creer_bouton_edition("Agréger", agreger_donnees))
        groupe_combinaison.setLayout(layout_combinaison)

        layout.addWidget(groupe_variables)
        layout.addWidget(groupe_observations)
        layout.addWidget(groupe_organisation)
        layout.addWidget(groupe_qualite)
        layout.addWidget(groupe_combinaison)

    layout.addWidget(tableau)
    onglet.setLayout(layout)

    return onglet, bouton_importer, label_statut, tableau


def creer_onglet_statistiques():
    """Crée l'onglet des statistiques descriptives, avec défilement."""
    onglet = QWidget()
    layout = QVBoxLayout()

    bouton_stats = QPushButton("Calculer les statistiques")

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    conteneur_stats = QWidget()
    conteneur_stats.setLayout(QVBoxLayout())
    zone_defilement.setWidget(conteneur_stats)

    layout.addWidget(bouton_stats)
    layout.addWidget(zone_defilement)
    onglet.setLayout(layout)

    return onglet, bouton_stats, conteneur_stats
