from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os
from securite import lire_journal
from interface import creer_onglet_donnees, creer_onglet_statistiques
from donnees import importer_donnees, detecter_domaine, importer_depuis_sql
from statistiques import calculer_statistiques
# Les modules sectoriels sont importés à la demande (dans creer_fenetre_tableau_de_bord)
# pour accélérer le démarrage de l'application.
from Design.theme import appliquer_theme
from Design.composants import creer_pied_de_page, creer_titre_section

VERSION_LOGICIEL = "ANA-STAT.abt v1.0"

SECTIONS_MENU = [
    ("Accueil", True),
    ("Démographie", True),
    ("Santé", True),
    ("Éducation", True),
    ("Économie", True),
    ("Agriculture", True),
    ("Commerce", True),
    ("Environnement", True),
    ("Emploi et Social", True),
    ("Sécurité", True),
    ("Administration", True),
    ("Aide", True),
    ("Module IA", True),
]

# Sections qui ne peuvent jamais être fermées, comme l'onglet Accueil d'un navigateur.
SECTIONS_NON_FERMABLES = ["Accueil"]


# ---------- BARRE SUPÉRIEURE ----------

def creer_barre_superieure(nom_utilisateur, role):
    """Crée la barre supérieure : logo, titre, recherche, notifications, IA, paramètres, profil."""
    barre = QFrame()
    barre.setFixedHeight(50)
    layout = QHBoxLayout()
    layout.setContentsMargins(10, 5, 10, 5)

    logo = QLabel()
    chemin_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets", "logo.png")
    if os.path.exists(chemin_logo):
        pixmap_logo = QPixmap(chemin_logo).scaledToHeight(38, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap_logo)
    else:
        logo.setText("📊")  # repli si le fichier logo.png n'est pas trouvé
    titre = QLabel("ANA-STAT.abt")
    titre.setStyleSheet("font-weight: bold; font-size: 14px;")

    bouton_parametres = QPushButton("⚙️")
    bouton_parametres.setToolTip("Paramètres d'apparence")

    def gerer_ouverture_parametres():
        from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox
        dialogue = QDialog()
        dialogue.setWindowTitle("Paramètres — Apparence")
        layout_dialogue = QVBoxLayout()
        layout_dialogue.addWidget(QLabel("Choisis le thème du logiciel :"))

        bouton_clair = QRadioButton("Mode clair")
        bouton_sombre = QRadioButton("Mode sombre")
        bouton_clair.setChecked(True)
        layout_dialogue.addWidget(bouton_clair)
        layout_dialogue.addWidget(bouton_sombre)

        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.accepted.connect(dialogue.accept)
        boutons.rejected.connect(dialogue.reject)
        layout_dialogue.addWidget(boutons)
        dialogue.setLayout(layout_dialogue)

        if dialogue.exec() == QDialog.DialogCode.Accepted:
            mode = "sombre" if bouton_sombre.isChecked() else "clair"
            appliquer_theme(QApplication.instance(), mode)

    bouton_parametres.clicked.connect(gerer_ouverture_parametres)

    label_profil = QLabel(f"👤 {nom_utilisateur} ({role})")

    layout.addWidget(logo)
    layout.addWidget(titre)
    layout.addStretch()
    layout.addWidget(bouton_parametres)
    layout.addWidget(label_profil)

    barre.setLayout(layout)
    return barre


# ---------- MENU LATÉRAL ----------

def creer_menu_lateral(gerer_navigation):
    """Crée le menu latéral avec toutes les sections, avec défilement si la liste dépasse la hauteur visible."""
    contenu = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(5, 10, 5, 10)

    for nom_section, est_active in SECTIONS_MENU:
        bouton = QPushButton(nom_section)
        bouton.setObjectName("boutonMenuLateral")
        if est_active:
            bouton.clicked.connect(lambda checked, s=nom_section: gerer_navigation(s))
        else:
            bouton.setEnabled(False)
            bouton.setToolTip("Module à venir")
        layout.addWidget(bouton)

    layout.addStretch()
    contenu.setLayout(layout)

    menu = QScrollArea()
    menu.setFixedWidth(210)
    menu.setWidgetResizable(True)
    menu.setWidget(contenu)
    return menu


# ---------- PAGE ACCUEIL (zone centrale + panneau d'informations) ----------

def creer_page_accueil():
    """Crée la page d'accueil avec zone centrale (activités récentes) et panneau d'informations."""
    page = QWidget()
    layout = QHBoxLayout()

    # Zone centrale : activités récentes issues du vrai journal des actions
    zone_centrale = QWidget()
    layout_centrale = QVBoxLayout()
    titre_centrale = creer_titre_section("Activités récentes")
    texte_activites = QLabel(lire_journal())
    texte_activites.setWordWrap(True)
    texte_activites.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout_centrale.addWidget(titre_centrale)
    layout_centrale.addWidget(texte_activites)
    layout_centrale.addStretch()
    zone_centrale.setLayout(layout_centrale)

    # Panneau d'informations : structure prête, contenu simple pour l'instant
    panneau = QFrame()
    panneau.setFixedWidth(220)
    layout_panneau = QVBoxLayout()
    layout_panneau.addWidget(QLabel("Alertes"))
    liste_alertes = QListWidget()
    liste_alertes.addItem("Aucune alerte pour le moment")
    layout_panneau.addWidget(liste_alertes)

    layout_panneau.addWidget(QLabel("Tâches en attente"))
    liste_taches = QListWidget()
    liste_taches.addItem("Aucune tâche en attente")
    layout_panneau.addWidget(liste_taches)
    panneau.setLayout(layout_panneau)

    layout.addWidget(zone_centrale)
    layout.addWidget(panneau)
    page.setLayout(layout)
    return page


# ---------- PIED DE PAGE ----------
# Le pied de page est fourni par Design.composants.creer_pied_de_page


# ---------- GESTION DES ONGLETS DE DOMAINES (fermables, comme un navigateur) ----------

def creer_gestionnaire_onglets(pages_disponibles):
    """Crée le QTabWidget principal et les fonctions pour ouvrir/fermer des onglets de domaines.

    pages_disponibles : dictionnaire {nom_section: widget_page_deja_cree}
    """
    onglets = QTabWidget()
    onglets.setTabsClosable(True)
    onglets.setMovable(True)

    onglets_ouverts = {}  # {nom_section: index_dans_le_tabwidget}

    def gerer_fermeture_onglet(index):
        """Ferme l'onglet à cet index, sauf s'il fait partie des onglets non fermables."""
        for nom_section, index_ouvert in list(onglets_ouverts.items()):
            if index_ouvert == index:
                if nom_section in SECTIONS_NON_FERMABLES:
                    return
                onglets.removeTab(index)
                del onglets_ouverts[nom_section]
                # Les index des onglets suivants se décalent d'un cran vers la gauche
                for autre_nom, autre_index in onglets_ouverts.items():
                    if autre_index > index:
                        onglets_ouverts[autre_nom] = autre_index - 1
                return

    onglets.tabCloseRequested.connect(gerer_fermeture_onglet)

    def ouvrir_onglet(nom_section):
        """Ouvre l'onglet du domaine demandé, ou le ramène au premier plan s'il est déjà ouvert."""
        if nom_section in onglets_ouverts:
            onglets.setCurrentIndex(onglets_ouverts[nom_section])
            return

        widget_page = pages_disponibles.get(nom_section)
        if widget_page is None:
            return

        index = onglets.addTab(widget_page, nom_section)
        onglets_ouverts[nom_section] = index
        onglets.setCurrentIndex(index)

        if nom_section in SECTIONS_NON_FERMABLES:
            onglets.tabBar().setTabButton(index, onglets.tabBar().ButtonPosition.RightSide, None)

    return onglets, ouvrir_onglet


# ---------- FENÊTRE TABLEAU DE BORD (assemble tout) ----------

def creer_fenetre_tableau_de_bord(nom_utilisateur, role, mode_test=False):
    """Assemble la barre supérieure, le menu latéral, les onglets de domaines et le pied de page."""
    fenetre = QMainWindow()
    if mode_test:
        fenetre.setWindowTitle(f"ANA-STAT.abt — MODE TEST SANS CONNEXION — Tableau de bord ({nom_utilisateur})")
    else:
        fenetre.setWindowTitle(f"ANA-STAT.abt - Tableau de bord ({nom_utilisateur})")
    fenetre.setGeometry(80, 80, 1200, 750)

    # Imports paresseux des modules sectoriels (accélère le démarrage)
    from Demographie.demographie import creer_page_demographie
    from Sante.sante import creer_page_sante
    from Education.education import creer_page_education
    from Economie.economie import creer_page_economie
    from Agriculture.agriculture import creer_page_agriculture
    from Environnement.environnement import creer_page_environnement
    from Commerce.commerce import creer_page_commerce
    from Emploi_social.emploi_social import creer_page_emploi_social
    from Securite.securite_module import creer_page_securite
    from Administration.administration import creer_page_administration
    from Aide.aide import creer_page_aide

    widget_central = QWidget()
    layout_principal = QVBoxLayout()
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    barre_superieure = creer_barre_superieure(nom_utilisateur, role)

    zone_milieu = QWidget()
    layout_milieu = QHBoxLayout()
    layout_milieu.setContentsMargins(0, 0, 0, 0)

    # ---- Création de toutes les pages (une seule fois, réutilisées à chaque ouverture d'onglet) ----

    page_accueil = creer_page_accueil()

    donnees_actuelles = {"valeur": None, "domaine": None}

    def obtenir_donnees_actuelles_brut():
        return donnees_actuelles["valeur"]

    def definir_donnees_actuelles_brut(nouvelles_donnees):
        donnees_actuelles["valeur"] = nouvelles_donnees
        donnees_actuelles["domaine"] = detecter_domaine(nouvelles_donnees) if nouvelles_donnees is not None else None

    onglet_donnees, bouton_importer, label_statut, tableau = creer_onglet_donnees(
        obtenir_donnees_actuelles_brut, definir_donnees_actuelles_brut
    )
    onglet_stats, bouton_stats, conteneur_stats = creer_onglet_statistiques()

    def gerer_import():
        resultat = importer_donnees(label_statut, tableau)
        donnees_actuelles["valeur"] = resultat
        donnees_actuelles["domaine"] = detecter_domaine(resultat)

    def gerer_import_sql():
        resultat = importer_depuis_sql(label_statut, tableau)
        if resultat is not None:
            donnees_actuelles["valeur"] = resultat
            donnees_actuelles["domaine"] = detecter_domaine(resultat)

    def gerer_stats():
        calculer_statistiques(donnees_actuelles["valeur"], conteneur_stats)

    bouton_importer.clicked.connect(gerer_import)
    bouton_stats.clicked.connect(gerer_stats)

    def obtenir_donnees_actuelles():
        return donnees_actuelles["valeur"]

    def obtenir_domaine_actuel():
        return donnees_actuelles["domaine"]

    page_demographie = creer_page_demographie(
        obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql
    )
    page_sante = creer_page_sante(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_education = creer_page_education(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_economie = creer_page_economie(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_agriculture = creer_page_agriculture(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_environnement = creer_page_environnement(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_commerce = creer_page_commerce(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_emploi_social = creer_page_emploi_social(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)
    page_securite = creer_page_securite(obtenir_donnees_actuelles, obtenir_domaine_actuel, gerer_import, gerer_import_sql)

    page_administration = creer_page_administration(nom_utilisateur, role)
    page_aide = creer_page_aide()

    pages_disponibles = {
        "Accueil": page_accueil,
        "Démographie": page_demographie,
        "Santé": page_sante,
        "Éducation": page_education,
        "Économie": page_economie,
        "Agriculture": page_agriculture,
        "Environnement": page_environnement,
        "Commerce": page_commerce,
        "Emploi et Social": page_emploi_social,
        "Sécurité": page_securite,
        "Administration": page_administration,
        "Aide": page_aide,
    }

    onglets, ouvrir_onglet = creer_gestionnaire_onglets(pages_disponibles)

    # Le Module IA a besoin de gerer_navigation (ouvrir_onglet) pour rediriger vers les autres domaines
    from IA.module_ia import creer_page_module_ia
    page_ia = creer_page_module_ia(obtenir_donnees_actuelles, obtenir_domaine_actuel, ouvrir_onglet)
    pages_disponibles["Module IA"] = page_ia

    # L'onglet Accueil est toujours ouvert par défaut, non fermable
    ouvrir_onglet("Accueil")

    menu_lateral = creer_menu_lateral(ouvrir_onglet)

    layout_milieu.addWidget(menu_lateral)
    layout_milieu.addWidget(onglets)
    zone_milieu.setLayout(layout_milieu)

    pied_de_page = creer_pied_de_page(VERSION_LOGICIEL, mode_test=mode_test)

    layout_principal.addWidget(barre_superieure)
    layout_principal.addWidget(zone_milieu)
    layout_principal.addWidget(pied_de_page)

    widget_central.setLayout(layout_principal)
    fenetre.setCentralWidget(widget_central)

    return fenetre
