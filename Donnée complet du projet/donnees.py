import pandas as pd
from PyQt6.QtWidgets import (
    QFileDialog, QTableWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QDialogButtonBox, QLabel, QMessageBox, QLineEdit, QWidget, QPushButton
)

SEUIL_GRANDES_DONNEES = 1000

# Mots-clés typiques de chaque domaine, utilisés pour deviner à quoi correspond un fichier importé.
MOTS_CLES_DOMAINES = {
    "Démographie": ["population", "naissance", "birth", "deces", "décès", "death",
                     "migration", "fecondite", "fécondité", "age", "âge", "sexe",
                     "mortalite", "mortalité", "natalite", "natalité", "menage", "ménage"],
    "Santé": ["maladie", "vaccination", "prevalence", "prévalence", "incidence",
              "nutrition", "sante", "santé", "epidemi", "épidémi", "clinique"],
    "Éducation": ["effectif", "inscription", "reussite", "réussite", "abandon",
                  "enseignant", "alphabetisation", "alphabétisation", "ecole", "école"],
    "Économie": ["pib", "inflation", "emploi", "chomage", "chômage", "revenu", "consommation"],
    "Agriculture": ["culture", "rendement", "elevage", "élevage", "peche", "pêche", "recolte", "récolte"],
    "Environnement": ["climat", "temperature", "température", "pluviometrie", "pluviométrie",
                       "pollution", "deforestation", "déforestation"],
    "Commerce": ["importation", "exportation", "prix", "entreprise", "investissement"],
    "Emploi et Social": ["chomage", "chômage", "pauvrete", "pauvreté", "protection sociale",
                          "retraite", "prestation", "inegalite", "inégalité", "handicap",
                          "salaire", "population active"],
    "Sécurité": ["accident", "criminalite", "criminalité", "crime", "vol", "cambriolage",
                 "incendie", "intervention", "victime", "incident"],
}


def detecter_domaine(donnees):
    """Devine le domaine probable d'un fichier en comptant les mots-clés trouvés dans ses colonnes."""
    if donnees is None:
        return None

    noms_colonnes = " ".join(donnees.columns.astype(str)).lower()
    scores = {}

    for domaine, mots_cles in MOTS_CLES_DOMAINES.items():
        score = sum(1 for mot in mots_cles if mot in noms_colonnes)
        if score > 0:
            scores[domaine] = score

    if not scores:
        return None

    return max(scores, key=scores.get)


def demander_options_import():
    """Ouvre une boîte de dialogue demandant les caractères de séparation à utiliser pour l'import.
    Renvoie un dictionnaire {separateur, decimal, milliers}, ou None si l'utilisateur annule."""
    dialogue = QDialog()
    dialogue.setWindowTitle("Options d'importation")
    layout = QVBoxLayout()

    label_info = QLabel(
        "Précise le format de ton fichier, pour que les nombres (comme les populations) "
        "soient importés correctement, et pas comme du texte."
    )
    label_info.setWordWrap(True)
    layout.addWidget(label_info)

    formulaire = QFormLayout()

    combo_separateur = QComboBox()
    combo_separateur.addItems(["Détection automatique", "Virgule (,)", "Point-virgule (;)", "Tabulation"])
    formulaire.addRow("Séparateur de colonnes (CSV) :", combo_separateur)

    combo_decimal = QComboBox()
    combo_decimal.addItems(["Point (.)", "Virgule (,)"])
    formulaire.addRow("Séparateur décimal :", combo_decimal)

    combo_milliers = QComboBox()
    combo_milliers.addItems(["Aucun", "Virgule (,)", "Espace", "Point (.)"])
    formulaire.addRow("Séparateur de milliers :", combo_milliers)

    layout.addLayout(formulaire)

    boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    boutons.accepted.connect(dialogue.accept)
    boutons.rejected.connect(dialogue.reject)
    layout.addWidget(boutons)

    dialogue.setLayout(layout)

    if dialogue.exec() != QDialog.DialogCode.Accepted:
        return None

    correspondance_separateur = {
        "Détection automatique": None, "Virgule (,)": ",", "Point-virgule (;)": ";", "Tabulation": "\t"
    }
    correspondance_decimal = {"Point (.)": ".", "Virgule (,)": ","}
    correspondance_milliers = {"Aucun": None, "Virgule (,)": ",", "Espace": " ", "Point (.)": "."}

    separateur = correspondance_separateur[combo_separateur.currentText()]
    decimal = correspondance_decimal[combo_decimal.currentText()]
    milliers = correspondance_milliers[combo_milliers.currentText()]

    if separateur == decimal or milliers == decimal:
        QMessageBox.warning(
            None, "Combinaison invalide",
            "Le séparateur de colonnes et le séparateur de milliers ne peuvent pas être "
            "identiques au séparateur décimal. Corrige tes choix et réessaie."
        )
        return demander_options_import()

    return {"separateur": separateur, "decimal": decimal, "milliers": milliers}


def decoder_colonnes_texte(donnees):
    """Décode en texte lisible les colonnes qui arrivent en bytes (cas fréquent avec les fichiers SAS)."""
    for colonne in donnees.select_dtypes(include="object").columns:
        donnees[colonne] = donnees[colonne].apply(
            lambda v: v.decode("utf-8", errors="replace") if isinstance(v, bytes) else v
        )
    return donnees


def importer_depuis_sql(label_statut, tableau):
    """Ouvre une boîte de dialogue de connexion à une base SQL (SQLite, MySQL, PostgreSQL),
    liste ses tables, et importe celle choisie par l'utilisateur."""
    dialogue = QDialog()
    dialogue.setWindowTitle("Importer depuis une base SQL")
    layout = QVBoxLayout()

    combo_type = QComboBox()
    combo_type.addItems(["SQLite (fichier local)", "MySQL (serveur)", "PostgreSQL (serveur)"])
    layout.addWidget(QLabel("Type de base de données :"))
    layout.addWidget(combo_type)

    zone_sqlite = QWidget()
    layout_sqlite = QHBoxLayout()
    champ_chemin_sqlite = QLineEdit()
    champ_chemin_sqlite.setPlaceholderText("Aucun fichier choisi")
    champ_chemin_sqlite.setReadOnly(True)
    bouton_parcourir = QPushButton("Parcourir...")
    layout_sqlite.addWidget(champ_chemin_sqlite)
    layout_sqlite.addWidget(bouton_parcourir)
    zone_sqlite.setLayout(layout_sqlite)

    zone_serveur = QWidget()
    formulaire_serveur = QFormLayout()
    champ_hote = QLineEdit()
    champ_hote.setPlaceholderText("localhost")
    champ_port = QLineEdit()
    champ_port.setPlaceholderText("3306 (MySQL) / 5432 (PostgreSQL)")
    champ_utilisateur = QLineEdit()
    champ_mdp = QLineEdit()
    champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
    champ_base = QLineEdit()
    formulaire_serveur.addRow("Hôte :", champ_hote)
    formulaire_serveur.addRow("Port :", champ_port)
    formulaire_serveur.addRow("Utilisateur :", champ_utilisateur)
    formulaire_serveur.addRow("Mot de passe :", champ_mdp)
    formulaire_serveur.addRow("Nom de la base :", champ_base)
    zone_serveur.setLayout(formulaire_serveur)
    zone_serveur.setVisible(False)

    layout.addWidget(zone_sqlite)
    layout.addWidget(zone_serveur)

    bouton_connecter = QPushButton("Se connecter et lister les tables")
    combo_tables = QComboBox()
    combo_tables.setEnabled(False)
    layout.addWidget(bouton_connecter)
    layout.addWidget(QLabel("Table à importer :"))
    layout.addWidget(combo_tables)

    boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    boutons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    boutons.accepted.connect(dialogue.accept)
    boutons.rejected.connect(dialogue.reject)
    layout.addWidget(boutons)
    dialogue.setLayout(layout)

    connexion_actuelle = {"conn": None}

    def gerer_changement_type():
        est_sqlite = combo_type.currentIndex() == 0
        zone_sqlite.setVisible(est_sqlite)
        zone_serveur.setVisible(not est_sqlite)

    combo_type.currentIndexChanged.connect(gerer_changement_type)

    def gerer_parcourir():
        chemin, _ = QFileDialog.getOpenFileName(
            dialogue, "Choisir le fichier SQLite", "", "Bases SQLite (*.db *.sqlite *.sqlite3)"
        )
        if chemin:
            champ_chemin_sqlite.setText(chemin)

    bouton_parcourir.clicked.connect(gerer_parcourir)

    def gerer_connexion():
        import sqlite3
        type_base = combo_type.currentText()
        try:
            if type_base.startswith("SQLite"):
                if not champ_chemin_sqlite.text():
                    QMessageBox.warning(dialogue, "Erreur", "Choisis d'abord un fichier .db")
                    return
                conn = sqlite3.connect(champ_chemin_sqlite.text())
                tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                noms_tables = tables_df["name"].tolist()
                connexion_actuelle["conn"] = conn
            else:
                import sqlalchemy
                pilote = "mysql+pymysql" if type_base.startswith("MySQL") else "postgresql+psycopg2"
                port_defaut = "3306" if type_base.startswith("MySQL") else "5432"
                port = champ_port.text().strip() or port_defaut
                url = (f"{pilote}://{champ_utilisateur.text()}:{champ_mdp.text()}"
                       f"@{champ_hote.text() or 'localhost'}:{port}/{champ_base.text()}")
                moteur = sqlalchemy.create_engine(url)
                conn = moteur.connect()
                inspecteur = sqlalchemy.inspect(moteur)
                noms_tables = inspecteur.get_table_names()
                connexion_actuelle["conn"] = conn

            combo_tables.clear()
            combo_tables.addItems(noms_tables)
            combo_tables.setEnabled(True)
            boutons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(len(noms_tables) > 0)
            if not noms_tables:
                QMessageBox.information(dialogue, "Info", "Connexion réussie, mais aucune table trouvée.")

        except ImportError as erreur:
            QMessageBox.critical(
                dialogue, "Bibliothèque manquante",
                f"Il manque une bibliothèque pour ce type de connexion :\n{erreur}\n\n"
                "Pour MySQL : pip install sqlalchemy pymysql\n"
                "Pour PostgreSQL : pip install sqlalchemy psycopg2-binary"
            )
        except Exception as erreur:
            QMessageBox.critical(dialogue, "Erreur de connexion", f"Impossible de se connecter :\n{erreur}")

    bouton_connecter.clicked.connect(gerer_connexion)

    if dialogue.exec() != QDialog.DialogCode.Accepted:
        if connexion_actuelle["conn"]:
            try:
                connexion_actuelle["conn"].close()
            except Exception:
                pass
        return None

    table_choisie = combo_tables.currentText()
    if not table_choisie or connexion_actuelle["conn"] is None:
        return None

    try:
        donnees = pd.read_sql_query(f"SELECT * FROM {table_choisie}", connexion_actuelle["conn"])
    except Exception as erreur:
        QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer la table :\n{erreur}")
        return None
    finally:
        try:
            connexion_actuelle["conn"].close()
        except Exception:
            pass

    domaine_detecte = detecter_domaine(donnees)
    taille = "grandes données" if donnees.shape[0] >= SEUIL_GRANDES_DONNEES else "petites données"
    texte_domaine = domaine_detecte if domaine_detecte else "non déterminé"
    label_statut.setText(f"Table importée : {table_choisie} "
                          f"({donnees.shape[0]} lignes, {donnees.shape[1]} colonnes) — {taille} "
                          f"— Domaine détecté : {texte_domaine}")

    afficher_apercu(donnees, tableau)

    return donnees


def importer_donnees(label_statut, tableau):
    """Ouvre une boîte de dialogue pour choisir un fichier, demande le format si besoin, puis charge les données.
    Formats pris en charge : CSV, Excel, Stata (.dta), SPSS (.sav), SAS (.sas7bdat / .xpt)."""
    chemin_fichier, _ = QFileDialog.getOpenFileName(
        None,
        "Choisir un fichier de données",
        "",
        "Tous les formats pris en charge (*.csv *.xlsx *.xls *.dta *.sav *.sas7bdat *.xpt);;"
        "Fichiers CSV (*.csv);;Fichiers Excel (*.xlsx *.xls);;"
        "Fichiers Stata (*.dta);;Fichiers SPSS (*.sav);;Fichiers SAS (*.sas7bdat *.xpt)"
    )

    if chemin_fichier == "":
        return None

    extension = chemin_fichier.lower().rsplit(".", 1)[-1]

    if extension == "csv":
        options = demander_options_import()
        if options is None:
            return None  # l'utilisateur a annulé la boîte de dialogue de format
        parametres_lecture = {"engine": "python", "decimal": options["decimal"]}
        parametres_lecture["sep"] = options["separateur"] if options["separateur"] is not None else None
        if options["milliers"] is not None:
            parametres_lecture["thousands"] = options["milliers"]
        try:
            donnees = pd.read_csv(chemin_fichier, **parametres_lecture)
        except Exception as erreur:
            QMessageBox.critical(None, "Erreur d'importation",
                                  f"Impossible de lire le fichier avec ces réglages :\n{erreur}")
            return None

    elif extension in ("xlsx", "xls"):
        options = demander_options_import()
        if options is None:
            return None
        parametres_lecture = {"decimal": options["decimal"]}
        if options["milliers"] is not None:
            parametres_lecture["thousands"] = options["milliers"]
        try:
            donnees = pd.read_excel(chemin_fichier, **parametres_lecture)
        except Exception as erreur:
            QMessageBox.critical(None, "Erreur d'importation",
                                  f"Impossible de lire le fichier avec ces réglages :\n{erreur}")
            return None

    elif extension == "dta":
        try:
            donnees = pd.read_stata(chemin_fichier)
        except Exception as erreur:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible de lire ce fichier Stata :\n{erreur}")
            return None

    elif extension == "sav":
        try:
            donnees = pd.read_spss(chemin_fichier)
        except ImportError:
            QMessageBox.critical(
                None, "Bibliothèque manquante",
                "L'import de fichiers SPSS (.sav) nécessite le paquet 'pyreadstat'.\n"
                "Installe-le avec : pip install pyreadstat"
            )
            return None
        except Exception as erreur:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible de lire ce fichier SPSS :\n{erreur}")
            return None

    elif extension in ("sas7bdat", "xpt"):
        try:
            donnees = pd.read_sas(chemin_fichier)
            donnees = decoder_colonnes_texte(donnees)
        except Exception as erreur:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible de lire ce fichier SAS :\n{erreur}")
            return None

    else:
        QMessageBox.warning(None, "Format non reconnu",
                             f"L'extension '.{extension}' n'est pas prise en charge.")
        return None

    domaine_detecte = detecter_domaine(donnees)
    taille = "grandes données" if donnees.shape[0] >= SEUIL_GRANDES_DONNEES else "petites données"
    texte_domaine = domaine_detecte if domaine_detecte else "non déterminé"
    label_statut.setText(f"Fichier chargé : {chemin_fichier.split('/')[-1]} "
                          f"({donnees.shape[0]} lignes, {donnees.shape[1]} colonnes) — {taille} "
                          f"— Domaine détecté : {texte_domaine}")

    afficher_apercu(donnees, tableau)

    return donnees


def afficher_apercu(donnees, tableau):
    """Affiche toutes les données dans le tableau, sans la numérotation automatique."""
    tableau.setRowCount(donnees.shape[0])
    tableau.setColumnCount(donnees.shape[1])
    tableau.setHorizontalHeaderLabels(donnees.columns.astype(str))
    tableau.verticalHeader().setVisible(False)

    for ligne in range(donnees.shape[0]):
        for colonne in range(donnees.shape[1]):
            valeur = str(donnees.iloc[ligne, colonne])
            tableau.setItem(ligne, colonne, QTableWidgetItem(valeur))