"""Module Aide : guide d'utilisation intégré, organisé par thème."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QLineEdit
)
from PyQt6.QtCore import Qt

CONTENU_AIDE = {
    "Démarrage": {
        "Se connecter": (
            "Au lancement du logiciel, saisis ton nom d'utilisateur et ton mot de passe, puis clique "
            "sur 'Se connecter'. Si tu n'as pas encore de compte, clique sur 'Créer un compte'.\n\n"
            "Les nouveaux comptes créés depuis l'écran de connexion reçoivent automatiquement le rôle "
            "'visiteur' — un administrateur peut ensuite changer ton rôle depuis Administration."
        ),
        "Mot de passe oublié": (
            "Clique sur 'Mot de passe oublié ?' sur l'écran de connexion. Saisis ton nom d'utilisateur, "
            "réponds à ta question secrète (choisie à l'inscription), puis définis un nouveau mot de passe."
        ),
    },
    "Navigation générale": {
        "Le menu latéral": (
            "Le menu à gauche liste les modules disponibles. Cliquer sur un module l'ouvre dans un "
            "nouvel onglet en haut, comme dans un navigateur — les onglets ont un '×' pour les fermer, "
            "sauf 'Accueil' qui reste toujours ouvert."
        ),
        "Mode clair / sombre": (
            "Clique sur l'icône ⚙️ en haut à droite pour choisir entre le mode clair et le mode sombre."
        ),
    },
    "Modules sectoriels": {
        "Structure commune": (
            "Chaque module sectoriel (Démographie, Santé, Éducation...) partage la même organisation en "
            "onglets internes :\n\n"
            "• Accueil — cartes cliquables par catégorie d'indicateurs\n"
            "• Données — importer un fichier, filtres\n"
            "• Analyses — arborescence des indicateurs + tableau de saisie\n"
            "• Visualisations — graphique du dernier calcul\n"
            "• Analyse statistique — corrélation, régression, ANOVA, ACP...\n"
            "• Graphiques — laboratoire graphique complet\n"
            "• Tableaux croisés — générateur de tableaux\n"
            "• SIG — cartographie (si coordonnées disponibles)\n"
            "• Rapports — export du dernier résultat"
        ),
        "Lancer une analyse": (
            "Dans l'onglet Analyses, déplie une catégorie dans l'arborescence à gauche et clique sur "
            "l'indicateur voulu. Un tableau de saisie apparaît à droite, avec les colonnes exactes dont "
            "cet indicateur a besoin.\n\n"
            "Tu peux :\n"
            "• Coller des données (Ctrl+V) copiées depuis Excel ou un autre tableau du logiciel\n"
            "• Remplir les cases à la main\n"
            "• Cliquer sur 'Remplir depuis mes données importées' pour un remplissage automatique\n\n"
            "Clique ensuite sur 'Calculer'. Le résultat s'affiche avec un tableau, un graphique, "
            "la formule utilisée, et une interprétation automatique."
        ),
    },
    "Importer des données": {
        "Formats pris en charge": (
            "Excel (.xlsx, .xls), CSV, Stata (.dta), SPSS (.sav), SAS (.sas7bdat, .xpt), et bases SQL "
            "(SQLite, MySQL, PostgreSQL) via le bouton 'Base SQL'."
        ),
        "Réglages CSV/Excel": (
            "À l'import d'un fichier CSV ou Excel, une fenêtre te demande le séparateur de colonnes, "
            "le séparateur décimal et le séparateur de milliers. Choisis-les selon le format de ton "
            "fichier pour que les nombres soient importés correctement."
        ),
        "Éditer les données": (
            "Dans l'onglet 'Données', une barre d'outils permet de modifier les données importées :\n\n"
            "• Variables — ajouter, supprimer, renommer, recoder, convertir le type, créer une variable calculée\n"
            "• Observations — ajouter/supprimer des lignes\n"
            "• Organisation — filtrer, trier\n"
            "• Qualité — détecter valeurs manquantes et doublons\n"
            "• Combinaison — fusionner, joindre, agréger"
        ),
    },
    "Graphiques": {
        "Utilisation": (
            "Dans l'onglet Graphiques, choisis un type de graphique (histogramme, barres, secteurs, "
            "courbes, nuage de points, boxplot, pyramide des âges, courbe de Lorenz...), sélectionne "
            "les colonnes demandées, personnalise titre/légende/étiquettes, puis clique sur "
            "'Générer le graphique'. Exporte-le en PNG, JPG, SVG ou PDF."
        ),
    },
    "Tableaux croisés": {
        "Utilisation": (
            "Choisis une Variable (valeur numérique à résumer), un Indicateur (Effectif, Moyenne, "
            "Médiane, %, % en ligne, % en colonne, Total), une désagrégation en ligne, et optionnellement "
            "une désagrégation en colonne pour un vrai tableau croisé à deux dimensions."
        ),
    },
    "Rapports et export": {
        "Formats disponibles": (
            "Excel, PDF, Word et PowerPoint sont disponibles pour exporter un résultat d'analyse. "
            "Le Module IA peut aussi générer un rapport Word complet et structuré."
        ),
    },
    "Module IA": {
        "Ce qu'il peut faire": (
            "L'assistant répond à des questions par mots-clés (formules, guide d'utilisation), "
            "analyse automatiquement les données importées (valeurs manquantes, doublons, valeurs "
            "atypiques, corrélations), nettoie les doublons, impute les valeurs manquantes, détecte "
            "les problèmes, propose des prévisions avec une fourchette d'incertitude, et génère un "
            "rapport Word automatique.\n\n"
            "Il fonctionne actuellement en mode local (hors ligne), sans compréhension du langage libre."
        ),
    },
    "Administration": {
        "Rôles disponibles": (
            "administrateur — accès total, gestion des comptes\n"
            "analyste — accès complet aux analyses, pas de gestion des comptes\n"
            "agent_saisie — import et nettoyage des données uniquement\n"
            "visiteur — consultation uniquement (rôle par défaut à l'inscription)"
        ),
        "Gérer les comptes": (
            "Réservé aux administrateurs. Depuis l'onglet Administration : créer un compte, modifier le "
            "rôle d'un compte existant, réinitialiser un mot de passe, ou supprimer un compte."
        ),
    },
}


def creer_page_aide():
    """Assemble la page d'aide : arborescence de thèmes à gauche, contenu à droite."""
    page = QWidget()
    layout = QHBoxLayout()

    arbre = QTreeWidget()
    arbre.setHeaderLabel("Sommaire")
    arbre.setMinimumWidth(260)
    for theme, sous_pages in CONTENU_AIDE.items():
        item_theme = QTreeWidgetItem([theme])
        for sous_titre in sous_pages:
            item_theme.addChild(QTreeWidgetItem([sous_titre]))
        arbre.addTopLevelItem(item_theme)
    arbre.expandAll()

    panneau_droit = QWidget()
    layout_droit = QVBoxLayout()

    champ_recherche = QLineEdit()
    champ_recherche.setPlaceholderText("Rechercher dans l'aide...")

    label_titre = QLabel("Sélectionne un thème dans le sommaire à gauche.")
    label_titre.setStyleSheet("font-weight: bold; font-size: 14px;")

    zone_texte = QTextEdit()
    zone_texte.setReadOnly(True)

    layout_droit.addWidget(champ_recherche)
    layout_droit.addWidget(label_titre)
    layout_droit.addWidget(zone_texte)
    panneau_droit.setLayout(layout_droit)

    def gerer_selection(item, colonne):
        sous_titre = item.text(0)
        for theme, sous_pages in CONTENU_AIDE.items():
            if sous_titre in sous_pages:
                label_titre.setText(f"{theme} > {sous_titre}")
                zone_texte.setPlainText(sous_pages[sous_titre])
                return

    def gerer_recherche():
        terme = champ_recherche.text().strip().lower()
        if not terme:
            return
        for theme, sous_pages in CONTENU_AIDE.items():
            for sous_titre, texte in sous_pages.items():
                if terme in sous_titre.lower() or terme in texte.lower():
                    label_titre.setText(f"{theme} > {sous_titre}")
                    zone_texte.setPlainText(texte)
                    return
        label_titre.setText("Aucun résultat")
        zone_texte.setPlainText(f"Aucun résultat trouvé pour '{terme}'. Essaie un autre mot-clé.")

    arbre.itemClicked.connect(gerer_selection)
    champ_recherche.returnPressed.connect(gerer_recherche)

    diviseur = QSplitter(Qt.Orientation.Horizontal)
    diviseur.addWidget(arbre)
    diviseur.addWidget(panneau_droit)
    diviseur.setStretchFactor(1, 1)

    layout.addWidget(diviseur)
    page.setLayout(layout)
    return page
