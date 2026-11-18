"""
Moteur générique partagé par tous les modules sectoriels (Démographie, Santé, Éducation...).
Chaque module définit ses propres catégories/indicateurs et appelle creer_page_module().
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter, QStackedWidget
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd
from Export.export_avance import exporter_pdf, exporter_powerpoint, exporter_word, exporter_image, imprimer_widget, exporter_excel
from Analyse.analyse_avancee import creer_page_analyse_avancee
from Graphiques.graphiques import creer_page_graphiques
from Tableaux.tableaux_croises import creer_page_tableaux_croises
from SIG.sig import creer_page_sig


# ---------- FONCTIONS GÉNÉRIQUES DE BASE ----------

def trouver_colonne_correspondante(donnees, mots_cles):
    """Cherche une colonne dont le nom contient un des mots-clés donnés."""
    if donnees is None:
        return None
    for colonne in donnees.columns:
        for mot in mots_cles:
            if mot.lower() in colonne.lower():
                return colonne
    return None


def remplir_tableau_resultat(tableau, dataframe_resultat):
    """Affiche un DataFrame pandas dans un QTableWidget."""
    tableau.setRowCount(dataframe_resultat.shape[0])
    tableau.setColumnCount(dataframe_resultat.shape[1])
    tableau.setHorizontalHeaderLabels(dataframe_resultat.columns.astype(str))
    tableau.verticalHeader().setVisible(False)

    for ligne in range(dataframe_resultat.shape[0]):
        for colonne in range(dataframe_resultat.shape[1]):
            valeur = dataframe_resultat.iloc[ligne, colonne]
            texte = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
            tableau.setItem(ligne, colonne, QTableWidgetItem(texte))
def lire_tableau_en_donnees(tableau, colonnes):
    """Lit le contenu actuel d'un QTableWidget et le transforme en DataFrame, en ignorant les lignes vides."""
    lignes = []
    for r in range(tableau.rowCount()):
        ligne = []
        vide = True
        for c in range(len(colonnes)):
            item = tableau.item(r, c)
            valeur = item.text().strip() if item else ""
            if valeur != "":
                vide = False
            ligne.append(valeur)
        if not vide:
            lignes.append(ligne)
    if not lignes:
        return None
    dataframe = pd.DataFrame(lignes, columns=colonnes)
    for colonne in colonnes:
        # On enlève les espaces (normaux et insécables) et les virgules, qui sont ici
        # traités comme des séparateurs de milliers — seul le point reste comme séparateur décimal.
        valeurs_nettoyees = (
            dataframe[colonne]
            .str.replace("\u202f", "", regex=False)  # espace insécable fine (courant en copié-collé Excel)
            .str.replace("\u00a0", "", regex=False)   # espace insécable classique
            .str.replace(" ", "", regex=False)
            .str.replace(",", "", regex=False)
        )
        dataframe[colonne + "__num"] = pd.to_numeric(valeurs_nettoyees, errors="coerce")
    return dataframe


def calculer_selon_famille(nom_indicateur, config, dataframe_saisi):
    """Applique la formule de la bonne famille sur les données saisies. Renvoie (resultat_df, message_erreur)."""
    famille = config["famille"]
    colonnes = config["colonnes"]

    try:
        if famille == "classement":
            colonne_valeur = colonnes[-1]
            df = dataframe_saisi.copy()
            df["Résultat"] = df[colonne_valeur + "__num"]
            if df["Résultat"].isna().all():
                return None, f"La colonne '{colonne_valeur}' doit contenir des nombres."
            resultat = df[[colonnes[0], "Résultat"]].sort_values(by="Résultat", ascending=False)
            return resultat, None

        elif famille == "taux":
            colonne_categorie, colonne_num, colonne_denom = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_denom + "__num"] > 0]
            if df.empty:
                return None, f"Aucune ligne valide (vérifie que '{colonne_denom}' contient des nombres > 0)."
            nom_taux = config["nom_taux"]
            df[nom_taux] = df[colonne_num + "__num"] / df[colonne_denom + "__num"] * config["facteur"]
            resultat = df[[colonne_categorie, nom_taux]].sort_values(by=nom_taux, ascending=False)
            return resultat, None

        elif famille == "solde":
            colonne_categorie, colonne_entrees, colonne_sorties = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            nom_resultat = config["nom_resultat"]
            df[nom_resultat] = df[colonne_entrees + "__num"] - df[colonne_sorties + "__num"]
            resultat = df[[colonne_categorie, nom_resultat]].sort_values(by=nom_resultat, ascending=False)
            return resultat, None

        elif famille == "densite":
            colonne_categorie, colonne_pop, colonne_superficie = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_superficie + "__num"] > 0]
            if df.empty:
                return None, "Aucune ligne valide (superficie doit être > 0)."
            df["Densité (hab/km²)"] = df[colonne_pop + "__num"] / df[colonne_superficie + "__num"]
            resultat = df[[colonne_categorie, "Densité (hab/km²)"]].sort_values(by="Densité (hab/km²)", ascending=False)
            return resultat, None

        elif famille == "moyenne_simple":
            colonne = colonnes[0]
            valeurs = dataframe_saisi[colonne + "__num"].dropna()
            if valeurs.empty:
                return None, "Aucune valeur numérique saisie."
            resultat = pd.DataFrame({"Indicateur": [f"{nom_indicateur}"], "Valeur": [round(valeurs.mean(), 2)]})
            return resultat, None

        elif famille == "moyenne_ponderee":
            colonne_x, colonne_poids = colonnes[0], colonnes[1]
            df = dataframe_saisi.dropna(subset=[colonne_x + "__num", colonne_poids + "__num"])
            total_poids = df[colonne_poids + "__num"].sum()
            if total_poids == 0 or df.empty:
                return None, "Impossible de calculer (effectifs vides ou nuls)."
            moyenne = (df[colonne_x + "__num"] * df[colonne_poids + "__num"]).sum() / total_poids
            resultat = pd.DataFrame({"Indicateur": [nom_indicateur], "Valeur": [round(moyenne, 2)]})
            return resultat, None

        elif famille == "mediane_ponderee":
            colonne_x, colonne_poids = colonnes[0], colonnes[1]
            df = dataframe_saisi.dropna(subset=[colonne_x + "__num", colonne_poids + "__num"]).sort_values(by=colonne_x + "__num")
            if df.empty:
                return None, "Aucune donnée valide saisie."
            cumul = df[colonne_poids + "__num"].cumsum()
            moitie = df[colonne_poids + "__num"].sum() / 2
            lignes_depassant = df[cumul >= moitie]
            if lignes_depassant.empty:
                return None, "Impossible de déterminer la médiane avec ces données."
            valeur_mediane = lignes_depassant.iloc[0][colonne_x + "__num"]
            resultat = pd.DataFrame({"Indicateur": [nom_indicateur], "Valeur": [valeur_mediane]})
            return resultat, None

        elif famille == "masculinite":
            colonne_sexe, colonne_effectif = colonnes[0], colonnes[1]
            df = dataframe_saisi.copy()
            ligne_hommes = df[df[colonne_sexe].str.lower().str.startswith(("h", "m"), na=False)]
            ligne_femmes = df[df[colonne_sexe].str.lower().str.startswith("f", na=False)]
            if ligne_hommes.empty or ligne_femmes.empty:
                return None, "Il faut une ligne commençant par 'H' (Hommes) et une ligne commençant par 'F' (Femmes)."
            hommes = ligne_hommes[colonne_effectif + "__num"].sum()
            femmes = ligne_femmes[colonne_effectif + "__num"].sum()
            if femmes == 0:
                return None, "L'effectif des femmes ne peut pas être 0."
            resultat = pd.DataFrame({"Indicateur": ["Rapport de masculinité (hommes pour 100 femmes)"],
                                      "Valeur": [round(hommes / femmes * 100, 2)]})
            return resultat, None

        elif famille == "dependance":
            colonne_tranche, colonne_pop = colonnes[0], colonnes[1]
            df = dataframe_saisi.copy()
            df["tranche_normalisee"] = df[colonne_tranche].str.replace(" ", "").str.lower()
            jeunes = df[df["tranche_normalisee"].str.contains("0-14", na=False)][colonne_pop + "__num"].sum()
            actifs = df[df["tranche_normalisee"].str.contains("15-64", na=False)][colonne_pop + "__num"].sum()
            ages = df[df["tranche_normalisee"].str.contains("65", na=False)][colonne_pop + "__num"].sum()
            if actifs == 0:
                return None, "Il faut une ligne '15-64' avec un effectif > 0. Utilise exactement ces libellés : 0-14, 15-64, 65+."
            rapport = (jeunes + ages) / actifs * 100
            resultat = pd.DataFrame({"Indicateur": ["Rapport de dépendance (%)"], "Valeur": [round(rapport, 2)]})
            return resultat, None

        elif famille == "accroissement_naturel":
            colonne_naiss, colonne_deces, colonne_pop = colonnes[0], colonnes[1], colonnes[2]
            total_naiss = dataframe_saisi[colonne_naiss + "__num"].sum()
            total_deces = dataframe_saisi[colonne_deces + "__num"].sum()
            total_pop = dataframe_saisi[colonne_pop + "__num"].sum()
            if total_pop == 0:
                return None, "La population totale saisie ne peut pas être 0."
            taux = (total_naiss - total_deces) / total_pop * 100
            resultat = pd.DataFrame({"Indicateur": ["Taux d'accroissement naturel (%)"], "Valeur": [round(taux, 3)]})
            return resultat, None

        elif famille == "taux_evolution":
            colonne_categorie, colonne_debut, colonne_fin = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_debut + "__num"] > 0]
            if df.empty:
                return None, f"'{colonne_debut}' doit contenir des valeurs > 0."
            nom_taux = config["nom_taux"]
            df[nom_taux] = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"] * 100
            resultat = df[[colonne_categorie, nom_taux]].sort_values(by=nom_taux, ascending=False)
            return resultat, None

        elif famille == "temps_doublement":
            import math
            colonne_categorie, colonne_debut, colonne_fin = colonnes[0], colonnes[1], colonnes[2]
            df = dataframe_saisi.copy()
            df = df[df[colonne_debut + "__num"] > 0]
            if df.empty:
                return None, f"'{colonne_debut}' doit contenir des valeurs > 0."
            taux = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"]
            df = df[taux > 0]
            if df.empty:
                return None, "Le taux de croissance doit être positif pour calculer un temps de doublement."
            taux_positif = (df[colonne_fin + "__num"] - df[colonne_debut + "__num"]) / df[colonne_debut + "__num"]
            df["Temps de doublement (années)"] = taux_positif.apply(lambda t: round(math.log(2) / t, 1))
            resultat = df[[colonne_categorie, "Temps de doublement (années)"]].sort_values(
                by="Temps de doublement (années)")
            return resultat, None

        elif famille == "projection":
            colonne_categorie, colonne_passe, colonne_recent, colonne_ecart, colonne_projection = colonnes
            df = dataframe_saisi.copy()
            df = df[(df[colonne_passe + "__num"] > 0) & (df[colonne_ecart + "__num"] > 0)]
            if df.empty:
                return None, f"'{colonne_passe}' et '{colonne_ecart}' doivent contenir des valeurs > 0."
            taux_annuel = (df[colonne_recent + "__num"] / df[colonne_passe + "__num"]) ** (1 / df[colonne_ecart + "__num"]) - 1
            nom_resultat = "Valeur projetée"
            df[nom_resultat] = df[colonne_recent + "__num"] * (1 + taux_annuel) ** df[colonne_projection + "__num"]
            resultat = df[[colonne_categorie, nom_resultat]].sort_values(by=nom_resultat, ascending=False)
            return resultat, None

        elif famille == "pyramide":
            colonne_tranche, colonne_sexe, colonne_pop = colonnes
            df = dataframe_saisi.copy()
            resultat = df.groupby([colonne_tranche, colonne_sexe])[colonne_pop + "__num"].sum().reset_index()
            resultat = resultat.rename(columns={colonne_pop + "__num": colonne_pop})
            return resultat, None

        elif famille == "tous_indicateurs":
            colonne_pop, colonne_naiss, colonne_deces = colonnes
            lignes = []
            if dataframe_saisi[colonne_pop + "__num"].notna().any():
                lignes.append(("Population totale", dataframe_saisi[colonne_pop + "__num"].sum()))
                lignes.append(("Population moyenne", round(dataframe_saisi[colonne_pop + "__num"].mean(), 2)))
            if dataframe_saisi[colonne_naiss + "__num"].notna().any():
                lignes.append(("Naissances totales", dataframe_saisi[colonne_naiss + "__num"].sum()))
            if dataframe_saisi[colonne_deces + "__num"].notna().any():
                lignes.append(("Décès totaux", dataframe_saisi[colonne_deces + "__num"].sum()))
            if not lignes:
                return None, "Aucune donnée numérique saisie."
            resultat = pd.DataFrame(lignes, columns=["Indicateur", "Valeur"])
            return resultat, None

        else:
            return None, "Famille de calcul inconnue."

    except Exception as erreur:
        return None, f"Erreur de calcul : {erreur}"



# ---------- DICTIONNAIRE DES INDICATEURS : FORMULES PAR FAMILLE ----------

def obtenir_categorie_indicateur(nom_indicateur, categories):
    """Retrouve la catégorie à laquelle appartient un indicateur, dans le dictionnaire de catégories donné."""
    for categorie, sous_items in categories.items():
        if nom_indicateur in sous_items:
            return categorie
    return "Non classé"


def obtenir_formule_texte(config):
    """Renvoie une description textuelle de la formule utilisée, selon la famille de l'indicateur."""
    famille = config["famille"]
    colonnes = config["colonnes"]

    if famille == "classement":
        return f"Classement des valeurs de la colonne « {colonnes[-1]} », de la plus grande à la plus petite."
    elif famille == "taux":
        return f"{config.get('nom_taux', 'Taux')} = ({colonnes[1]} ÷ {colonnes[2]}) × {config.get('facteur', '')}"
    elif famille == "solde":
        return f"{config.get('nom_resultat', 'Solde')} = {colonnes[1]} − {colonnes[2]}"
    elif famille == "densite":
        return f"Densité = {colonnes[1]} ÷ {colonnes[2]}"
    elif famille == "moyenne_simple":
        return f"Moyenne = somme des valeurs de « {colonnes[0]} » ÷ nombre de valeurs saisies."
    elif famille == "moyenne_ponderee":
        return f"Moyenne pondérée = Σ({colonnes[0]} × {colonnes[1]}) ÷ Σ({colonnes[1]})"
    elif famille == "mediane_ponderee":
        return (f"Médiane pondérée : valeur de « {colonnes[0]} » où la moitié de l'effectif "
                f"cumulé de « {colonnes[1]} » est atteint.")
    elif famille == "masculinite":
        return "Rapport de masculinité = (effectif Hommes ÷ effectif Femmes) × 100"
    elif famille == "dependance":
        return "Rapport de dépendance = (Population 0-14 + Population 65+) ÷ Population 15-64 × 100"
    elif famille == "accroissement_naturel":
        return f"Taux d'accroissement naturel = ({colonnes[0]} − {colonnes[1]}) ÷ {colonnes[2]} × 100"
    elif famille == "taux_evolution":
        return f"{config.get('nom_taux', 'Taux')} = ({colonnes[2]} − {colonnes[1]}) ÷ {colonnes[1]} × 100"
    elif famille == "temps_doublement":
        return "Temps de doublement = ln(2) ÷ taux de croissance annuel"
    elif famille == "projection":
        return ("Valeur projetée = Valeur récente × (1 + taux annuel) ^ nombre d'années à projeter, "
                "avec taux annuel = (Valeur récente ÷ Valeur passée) ^ (1 ÷ écart en années) − 1")
    elif famille == "pyramide":
        return f"Répartition croisée de « {colonnes[2]} » par « {colonnes[0]} » et « {colonnes[1]} »."
    elif famille == "tous_indicateurs":
        return ("Compilation de plusieurs indicateurs de base (population totale, moyenne, "
                "naissances totales, décès totaux) à partir des colonnes saisies.")
    else:
        return "Formule non documentée."


def obtenir_definition_texte(nom_indicateur, categorie):
    """Renvoie une courte définition générique de l'indicateur, basée sur sa catégorie et son nom."""
    return (f"« {nom_indicateur} » est un indicateur du domaine {categorie.lower()}, "
            f"calculé à partir des données saisies dans le tableau ci-dessus.")


def generer_interpretation(nom_indicateur, resultat):
    """Génère un texte d'interprétation simple à partir du résultat calculé."""
    if resultat is None or resultat.empty:
        return "Aucun résultat à interpréter."

    if resultat.shape[0] == 1:
        colonne_valeur = resultat.columns[-1]
        valeur = resultat.iloc[0][colonne_valeur]
        return f"La valeur calculée pour « {nom_indicateur} » est de {valeur}."

    colonne_categorie = resultat.columns[0]
    colonne_valeur = resultat.columns[-1]
    ligne_max = resultat.iloc[0]
    ligne_min = resultat.iloc[-1]
    return (
        f"Sur les {resultat.shape[0]} lignes calculées pour « {nom_indicateur} », "
        f"la valeur la plus élevée est observée pour « {ligne_max[colonne_categorie]} » "
        f"({ligne_max[colonne_valeur]:.2f} si numérique), et la plus basse pour « {ligne_min[colonne_categorie]} » "
        f"({ligne_min[colonne_valeur]:.2f} si numérique)."
    ) if pd.api.types.is_numeric_dtype(resultat[colonne_valeur]) else (
        f"{resultat.shape[0]} lignes ont été calculées pour « {nom_indicateur} »."
    )


def calculer_fiche_globale(config, dataframe_saisi):
    """Calcule un résumé global (totaux des colonnes saisies) pour l'afficher dans la fiche résultat."""
    resume = {}
    for colonne in config["colonnes"]:
        colonne_num = colonne + "__num"
        if colonne_num in dataframe_saisi.columns and dataframe_saisi[colonne_num].notna().any():
            resume[colonne] = round(dataframe_saisi[colonne_num].sum(), 2)
    return resume



def creer_tableau_saisie(colonnes, nb_lignes_initial=12):
    """Crée un QTableWidget qui accepte le copier-coller depuis Excel (Ctrl+V)."""
    from PyQt6.QtGui import QShortcut, QKeySequence
    from PyQt6.QtWidgets import QApplication

    tableau = QTableWidget(nb_lignes_initial, len(colonnes))
    tableau.setHorizontalHeaderLabels(colonnes)

    def gerer_collage():
        presse_papier = QApplication.clipboard().text()
        if not presse_papier:
            return
        lignes_collees = presse_papier.strip("\n").split("\n")
        ligne_depart = tableau.currentRow() if tableau.currentRow() >= 0 else 0
        colonne_depart = tableau.currentColumn() if tableau.currentColumn() >= 0 else 0

        for i, ligne_texte in enumerate(lignes_collees):
            valeurs = ligne_texte.split("\t")
            ligne_cible = ligne_depart + i
            if ligne_cible >= tableau.rowCount():
                tableau.insertRow(tableau.rowCount())
            for j, valeur in enumerate(valeurs):
                colonne_cible = colonne_depart + j
                if colonne_cible < tableau.columnCount():
                    tableau.setItem(ligne_cible, colonne_cible, QTableWidgetItem(valeur.strip()))

    raccourci = QShortcut(QKeySequence.StandardKey.Paste, tableau)
    raccourci.activated.connect(gerer_collage)

    return tableau


def remplir_depuis_donnees_importees(tableau, colonnes, mots_cles, donnees):
    """Remplit le tableau de saisie avec les vraies colonnes du fichier importé, si elles sont trouvées."""
    if donnees is None:
        QMessageBox.warning(None, "Erreur", "Aucune donnée importée. Va d'abord dans l'onglet 'Données'.")
        return

    colonnes_texte = list(donnees.select_dtypes(include="object").columns)
    colonne_categorie_source = colonnes_texte[0] if colonnes_texte else None

    colonnes_sources = {}
    colonnes_manquantes = []
    for colonne_config in colonnes:
        if colonne_config in mots_cles:
            colonne_trouvee = trouver_colonne_correspondante(donnees, mots_cles[colonne_config])
            if colonne_trouvee:
                colonnes_sources[colonne_config] = colonne_trouvee
            else:
                colonnes_manquantes.append(colonne_config)
        elif colonne_categorie_source:
            colonnes_sources[colonne_config] = colonne_categorie_source
        else:
            colonnes_manquantes.append(colonne_config)

    if not colonnes_sources:
        QMessageBox.information(None, "Info", "Aucune colonne correspondante trouvée dans le fichier importé.")
        return

    nb_lignes = min(len(donnees), 500)
    tableau.setRowCount(nb_lignes)
    for i in range(nb_lignes):
        for j, colonne_config in enumerate(colonnes):
            if colonne_config in colonnes_sources:
                valeur = donnees.iloc[i][colonnes_sources[colonne_config]]
                tableau.setItem(i, j, QTableWidgetItem(str(valeur)))

    if colonnes_manquantes:
        QMessageBox.information(
            None, "Remplissage partiel",
            "Colonnes non trouvées dans le fichier importé (à compléter à la main) :\n"
            + ", ".join(colonnes_manquantes)
        )


def creer_widget_fiche_resultat():
    """Crée le petit encadré 'fiche professionnelle' qui résume les données saisies et le résultat."""
    cadre = QFrame()
    cadre.setFrameShape(QFrame.Shape.Box)
    cadre.setStyleSheet("background-color: #f7f7f7;")
    layout = QVBoxLayout()
    label_titre = QLabel("")
    label_titre.setStyleSheet("font-weight: bold; font-size: 13px;")
    label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_contenu = QLabel("")
    label_contenu.setWordWrap(True)
    layout.addWidget(label_titre)
    layout.addWidget(label_contenu)
    cadre.setLayout(layout)
    return cadre, label_titre, label_contenu




def creer_onglet_donnees(fonction_import, fonction_import_sql, sources_supplementaires, filtres_correspondances):
    """Onglet Données : source (Excel/CSV + Base SQL + sources spécifiques au module) et filtres."""
    contenu = QWidget()
    layout = QVBoxLayout()

    groupe_source = QGroupBox("Sélection de la source de données")
    layout_source = QHBoxLayout()
    bouton_excel = QPushButton("Importer Excel / CSV")
    bouton_excel.clicked.connect(fonction_import)
    layout_source.addWidget(bouton_excel)

    bouton_sql = QPushButton("Base SQL")
    bouton_sql.clicked.connect(fonction_import_sql)
    layout_source.addWidget(bouton_sql)

    groupe_source.setLayout(layout_source)

    layout.addWidget(groupe_source)
    layout.addStretch()
    contenu.setLayout(layout)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setWidget(contenu)
    return zone_defilement


def creer_onglet_visualisations():
    """Onglet Visualisations : le graphique du dernier calcul est visible directement dans Analyses."""
    onglet = QWidget()
    layout = QVBoxLayout()
    label_info = QLabel(
        "Le graphique du dernier indicateur calculé est visible directement dans l'onglet Analyses "
        "(bouton 'Graphique')."
    )
    label_info.setStyleSheet("color: gray;")
    label_info.setWordWrap(True)
    layout.addWidget(label_info)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet


def creer_onglet_rapports(obtenir_dernier_resultat, nom_module):
    """Onglet Rapports : export du dernier résultat calculé dans Analyses."""
    onglet = QWidget()
    layout = QVBoxLayout()

    label_info = QLabel("Exporte le dernier résultat calculé dans l'onglet Analyses.")
    label_info.setWordWrap(True)
    label_info.setStyleSheet("color: gray;")
    layout.addWidget(label_info)

    layout_boutons = QHBoxLayout()

    def verifier_et_obtenir():
        resultat = obtenir_dernier_resultat()
        if resultat is None:
            QMessageBox.warning(None, "Erreur", "Calcule d'abord un résultat dans l'onglet Analyses.")
        return resultat

    def gerer_export_excel():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en Excel", "", "Fichiers Excel (*.xlsx)")
        if chemin:
            exporter_excel(resultat, chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_pdf():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en PDF", "", "Fichiers PDF (*.pdf)")
        if chemin:
            exporter_pdf(resultat, f"Résultat d'analyse - {nom_module}", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_word():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en Word", "", "Documents Word (*.docx)")
        if chemin:
            exporter_word(resultat, f"Résultat d'analyse - {nom_module}", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    def gerer_export_powerpoint():
        resultat = verifier_et_obtenir()
        if resultat is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(None, "Exporter en PowerPoint", "", "Fichiers PowerPoint (*.pptx)")
        if chemin:
            exporter_powerpoint(resultat, f"Résultat d'analyse - {nom_module}", chemin)
            QMessageBox.information(None, "Export réussi", f"Résultat exporté vers {chemin}")

    for nom, fonction in [("Excel", gerer_export_excel), ("PDF", gerer_export_pdf),
                           ("Word", gerer_export_word), ("PowerPoint", gerer_export_powerpoint)]:
        bouton = QPushButton(nom)
        bouton.clicked.connect(fonction)
        layout_boutons.addWidget(bouton)

    layout.addLayout(layout_boutons)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet


def creer_onglet_accueil(gerer_ouverture_categorie, categories, titre_module):
    """Onglet Accueil : cartes cliquables par catégorie, qui ouvrent Analyses sur la bonne catégorie."""
    onglet = QWidget()
    layout = QVBoxLayout()

    titre = QLabel(titre_module.upper())
    titre.setStyleSheet("font-size: 16px; font-weight: bold;")
    titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(titre)

    grille = QGridLayout()
    grille.setSpacing(15)
    noms_categories = list(categories.keys())
    for i, categorie in enumerate(noms_categories):
        carte = QPushButton(categorie.upper())
        carte.setMinimumHeight(70)
        carte.setStyleSheet("font-weight: bold;")
        carte.clicked.connect(lambda checked, c=categorie: gerer_ouverture_categorie(c))
        grille.addWidget(carte, i // 3, i % 3)

    conteneur_grille = QWidget()
    conteneur_grille.setLayout(grille)
    layout.addWidget(conteneur_grille)
    layout.addStretch()
    onglet.setLayout(layout)
    return onglet
def creer_onglet_analyses(obtenir_donnees_actuelles, enregistrer_dernier_resultat, categories, indicateurs_config, nom_domaine):
    """Onglet Analyses : arborescence à gauche, fiche + saisie + résultat (Tableau/Graphique/Formule/Interprétation) à droite."""
    onglet = QWidget()
    layout = QHBoxLayout()

    arbre = QTreeWidget()
    arbre.setHeaderLabel("Indicateurs")
    arbre.setMinimumWidth(260)
    elements_categorie = {}
    for categorie, sous_items in categories.items():
        item_categorie = QTreeWidgetItem([categorie])
        for sous_item in sous_items:
            item_categorie.addChild(QTreeWidgetItem([sous_item]))
        arbre.addTopLevelItem(item_categorie)
        elements_categorie[categorie] = item_categorie

    panneau_droit = QWidget()
    layout_droit = QVBoxLayout()
    label_titre = QLabel("Sélectionne un indicateur dans la liste à gauche.")
    label_titre.setStyleSheet("font-weight: bold; font-size: 13px;")

    label_instructions = QLabel("")
    label_instructions.setStyleSheet("color: gray;")
    label_instructions.setWordWrap(True)

    conteneur_saisie = QWidget()
    zone_tableau_saisie = QVBoxLayout()
    conteneur_saisie.setLayout(zone_tableau_saisie)

    layout_boutons_action = QHBoxLayout()
    bouton_remplir = QPushButton("Remplir depuis mes données importées")
    bouton_calculer = QPushButton("Calculer")
    layout_boutons_action.addWidget(bouton_remplir)
    layout_boutons_action.addWidget(bouton_calculer)

    fiche_cadre, fiche_titre, fiche_contenu = creer_widget_fiche_resultat()
    fiche_cadre.setVisible(False)

    layout_boutons_vue = QHBoxLayout()
    bouton_vue_tableau = QPushButton("📋 Tableau")
    bouton_vue_graphique = QPushButton("📈 Graphique")
    bouton_vue_formule = QPushButton("Σ Formule")
    bouton_vue_interpretation = QPushButton("💬 Interprétation")
    for b in (bouton_vue_tableau, bouton_vue_graphique, bouton_vue_formule, bouton_vue_interpretation):
        layout_boutons_vue.addWidget(b)

    pile_vues = QStackedWidget()

    tableau_resultat = QTableWidget()
    tableau_resultat.setMinimumHeight(220)
    pile_vues.addWidget(tableau_resultat)  # index 0

    figure = Figure(figsize=(5, 3))
    canvas = FigureCanvasQTAgg(figure)
    canvas.setMinimumHeight(280)
    pile_vues.addWidget(canvas)  # index 1

    label_formule = QLabel("")
    label_formule.setWordWrap(True)
    label_formule.setStyleSheet("font-size: 13px; padding: 10px;")
    pile_vues.addWidget(label_formule)  # index 2

    label_interpretation = QLabel("")
    label_interpretation.setWordWrap(True)
    label_interpretation.setStyleSheet("font-size: 13px; padding: 10px;")
    pile_vues.addWidget(label_interpretation)  # index 3

    bouton_vue_tableau.clicked.connect(lambda: pile_vues.setCurrentIndex(0))
    bouton_vue_graphique.clicked.connect(lambda: pile_vues.setCurrentIndex(1))
    bouton_vue_formule.clicked.connect(lambda: pile_vues.setCurrentIndex(2))
    bouton_vue_interpretation.clicked.connect(lambda: pile_vues.setCurrentIndex(3))

    layout_droit.addWidget(label_titre)
    layout_droit.addWidget(label_instructions)
    layout_droit.addWidget(conteneur_saisie)
    layout_droit.addLayout(layout_boutons_action)
    layout_droit.addWidget(fiche_cadre)
    layout_droit.addLayout(layout_boutons_vue)
    layout_droit.addWidget(pile_vues)
    panneau_droit.setLayout(layout_droit)

    zone_defilement_droite = QScrollArea()
    zone_defilement_droite.setWidgetResizable(True)
    zone_defilement_droite.setWidget(panneau_droit)

    indicateur_actuel = {"nom": None, "config": None, "tableau_saisie": None}
    etats_indicateurs = {}  # {nom_item: {"tableau_saisie": widget, "resultat": df/None, "fiche_texte", "interpretation_texte"}}

    def retirer_widget_saisie_sans_detruire():
        """Retire le tableau de saisie actuellement affiché du layout, SANS le détruire (il reste en mémoire)."""
        while zone_tableau_saisie.count():
            item = zone_tableau_saisie.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)  # détache proprement le widget, sans le supprimer

    def redessiner_graphique_resultat(nom_item, resultat):
        figure.clear()
        if resultat is not None and resultat.shape[0] > 1 and resultat.shape[1] == 2:
            try:
                ax = figure.add_subplot(111)
                top_10 = resultat.head(10)
                colonne_cat, colonne_val = resultat.columns[0], resultat.columns[1]
                ax.barh(top_10[colonne_cat].astype(str), top_10[colonne_val])
                ax.set_title(nom_item)
                ax.invert_yaxis()
                figure.tight_layout()
            except Exception:
                pass
        canvas.draw()

    def selectionner_indicateur(nom_item):
        if nom_item not in indicateurs_config:
            return
        config = indicateurs_config[nom_item]
        indicateur_actuel["nom"] = nom_item
        indicateur_actuel["config"] = config

        label_titre.setText(nom_item)
        label_instructions.setText(
            "Colle tes données ici avec Ctrl+V (depuis Excel par exemple), ou remplis les cases à la main, "
            "puis clique sur 'Calculer'. Colonnes attendues : " + " | ".join(config["colonnes"])
        )

        retirer_widget_saisie_sans_detruire()

        if nom_item not in etats_indicateurs:
            etats_indicateurs[nom_item] = {
                "tableau_saisie": creer_tableau_saisie(config["colonnes"]),
                "resultat": None, "fiche_texte": None, "interpretation_texte": None,
            }

        etat = etats_indicateurs[nom_item]
        zone_tableau_saisie.addWidget(etat["tableau_saisie"])
        etat["tableau_saisie"].show()
        indicateur_actuel["tableau_saisie"] = etat["tableau_saisie"]

        label_formule.setText(obtenir_formule_texte(config))

        if etat["resultat"] is not None:
            # Cet indicateur a déjà été calculé avant : on réaffiche son résultat tel quel.
            resultat = etat["resultat"]
            fiche_titre.setText(nom_item.upper())
            fiche_contenu.setText(etat["fiche_texte"])
            fiche_cadre.setVisible(True)
            remplir_tableau_resultat(tableau_resultat, resultat)
            redessiner_graphique_resultat(nom_item, resultat)
            label_interpretation.setText(etat["interpretation_texte"])
        else:
            tableau_resultat.setRowCount(0)
            tableau_resultat.setColumnCount(0)
            figure.clear()
            canvas.draw()
            label_interpretation.setText("Calcule d'abord un résultat pour voir son interprétation.")
            fiche_cadre.setVisible(False)

        pile_vues.setCurrentIndex(0)

    def gerer_selection_arbre(item, colonne):
        try:
            selectionner_indicateur(item.text(0))
        except Exception as erreur:
            import traceback
            QMessageBox.critical(
                None, "Erreur inattendue",
                f"Une erreur est survenue en ouvrant cet indicateur :\n\n{erreur}\n\n"
                f"Détail technique :\n{traceback.format_exc()[-800:]}"
            )

    def gerer_remplissage():
        if indicateur_actuel["nom"] is None:
            QMessageBox.information(None, "Info", "Sélectionne d'abord un indicateur dans la liste.")
            return
        config = indicateur_actuel["config"]
        remplir_depuis_donnees_importees(
            indicateur_actuel["tableau_saisie"], config["colonnes"], config["mots_cles"], obtenir_donnees_actuelles()
        )

    def gerer_calcul():
        if indicateur_actuel["nom"] is None:
            QMessageBox.information(None, "Info", "Sélectionne d'abord un indicateur dans la liste.")
            return

        nom_item = indicateur_actuel["nom"]
        config = indicateur_actuel["config"]
        tableau_saisie = indicateur_actuel["tableau_saisie"]

        dataframe_saisi = lire_tableau_en_donnees(tableau_saisie, config["colonnes"])
        if dataframe_saisi is None:
            QMessageBox.warning(None, "Erreur", "Le tableau est vide. Colle ou saisis des données d'abord.")
            return

        resultat, message_erreur = calculer_selon_famille(nom_item, config, dataframe_saisi)

        if resultat is None:
            QMessageBox.warning(None, "Erreur de calcul", message_erreur)
            return

        try:
            enregistrer_dernier_resultat(resultat, figure)

            # --- Fiche professionnelle ---
            fiche_titre.setText(nom_item.upper())
            resume_global = calculer_fiche_globale(config, dataframe_saisi)
            lignes_fiche = []
            for cle, valeur in resume_global.items():
                try:
                    lignes_fiche.append(f"{cle} : {float(valeur):,.2f}".replace(",", " "))
                except (ValueError, TypeError):
                    lignes_fiche.append(f"{cle} : {valeur}")
            if resultat.shape[0] == 1:
                colonne_resultat = resultat.columns[-1]
                valeur_resultat = resultat.iloc[0][colonne_resultat]
                lignes_fiche.append(f"Résultat : {valeur_resultat}")
            else:
                lignes_fiche.append(f"{resultat.shape[0]} résultats calculés — voir l'onglet Tableau.")
            fiche_contenu.setText("\n".join(lignes_fiche))
            fiche_cadre.setVisible(True)

            # --- Tableau ---
            remplir_tableau_resultat(tableau_resultat, resultat)

            # --- Graphique ---
            figure.clear()
            if resultat.shape[0] > 1 and resultat.shape[1] == 2:
                try:
                    ax = figure.add_subplot(111)
                    top_10 = resultat.head(10)
                    colonne_cat, colonne_val = resultat.columns[0], resultat.columns[1]
                    ax.barh(top_10[colonne_cat].astype(str), top_10[colonne_val])
                    ax.set_title(nom_item)
                    ax.invert_yaxis()
                    figure.tight_layout()
                except Exception:
                    pass
            canvas.draw()

            # --- Formule (déjà affichée dès la sélection, on la garde) ---
            label_formule.setText(obtenir_formule_texte(config))

            # --- Interprétation ---
            texte_interpretation = generer_interpretation(nom_item, resultat)
            label_interpretation.setText(texte_interpretation)

            # --- Sauvegarde dans le cache, pour que ce résultat reste visible si on revient sur cet indicateur ---
            etats_indicateurs[nom_item]["resultat"] = resultat
            etats_indicateurs[nom_item]["fiche_texte"] = fiche_contenu.text()
            etats_indicateurs[nom_item]["interpretation_texte"] = texte_interpretation

        except Exception as erreur:
            import traceback
            QMessageBox.critical(
                None, "Erreur inattendue",
                f"Une erreur est survenue lors de l'affichage du résultat pour '{nom_item}' :\n\n{erreur}\n\n"
                f"Détail technique :\n{traceback.format_exc()[-800:]}"
            )

    arbre.itemClicked.connect(gerer_selection_arbre)
    bouton_remplir.clicked.connect(gerer_remplissage)
    bouton_calculer.clicked.connect(gerer_calcul)

    diviseur = QSplitter(Qt.Orientation.Horizontal)
    diviseur.addWidget(arbre)
    diviseur.addWidget(zone_defilement_droite)
    diviseur.setStretchFactor(1, 1)

    layout.addWidget(diviseur)
    onglet.setLayout(layout)

    def ouvrir_categorie_depuis_accueil(nom_categorie):
        """Déplie et sélectionne visuellement la catégorie demandée dans l'arbre (appelé depuis Accueil)."""
        item_categorie = elements_categorie.get(nom_categorie)
        if item_categorie:
            item_categorie.setExpanded(True)
            arbre.setCurrentItem(item_categorie)
            arbre.scrollToItem(item_categorie)

    return onglet, ouvrir_categorie_depuis_accueil




def creer_page_module(nom_module, categories, indicateurs_config, sources_supplementaires,
                       filtres_correspondances, obtenir_donnees_actuelles, obtenir_domaine_actuel,
                       fonction_import, fonction_import_sql):
    """Assemble une page de module complète : Accueil, Données, Analyses, Visualisations, Rapports.

    C'est la fonction que chaque module sectoriel (Santé, Éducation, etc.) appelle avec ses
    propres catégories et indicateurs, pour obtenir la même structure que Démographie.
    """
    page_onglets = QTabWidget()

    dernier_resultat = {"dataframe": None}

    def enregistrer_dernier_resultat(dataframe, figure=None):
        dernier_resultat["dataframe"] = dataframe

    onglet_analyses, ouvrir_categorie = creer_onglet_analyses(
        obtenir_donnees_actuelles, enregistrer_dernier_resultat, categories, indicateurs_config, nom_module
    )
    onglet_donnees = creer_onglet_donnees(
        fonction_import, fonction_import_sql, sources_supplementaires, filtres_correspondances
    )
    onglet_visualisations = creer_onglet_visualisations()
    onglet_rapports = creer_onglet_rapports(lambda: dernier_resultat["dataframe"], nom_module)

    INDEX_ANALYSES = 2

    def gerer_ouverture_categorie(nom_categorie):
        ouvrir_categorie(nom_categorie)
        page_onglets.setCurrentIndex(INDEX_ANALYSES)

    onglet_accueil = creer_onglet_accueil(gerer_ouverture_categorie, categories, nom_module)

    onglet_analyse_stat = creer_page_analyse_avancee(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import)
    onglet_graphiques = creer_page_graphiques(obtenir_donnees_actuelles)
    onglet_tableaux_croises = creer_page_tableaux_croises(obtenir_donnees_actuelles)
    onglet_sig = creer_page_sig(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import)

    page_onglets.addTab(onglet_accueil, "Accueil")
    page_onglets.addTab(onglet_donnees, "Données")
    page_onglets.addTab(onglet_analyses, "Analyses")
    page_onglets.addTab(onglet_visualisations, "Visualisations")
    page_onglets.addTab(onglet_analyse_stat, "Analyse statistique")
    page_onglets.addTab(onglet_graphiques, "Graphiques")
    page_onglets.addTab(onglet_tableaux_croises, "Tableaux croisés")
    page_onglets.addTab(onglet_sig, "SIG")
    page_onglets.addTab(onglet_rapports, "Rapports")

    return page_onglets