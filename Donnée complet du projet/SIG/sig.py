"""Module SIG — cartographie du Mali par région, cercle et commune.

Les contours administratifs sont stockés dans ``SIG/donnees_cartes`` :

- régions, cercles et limite du pays : OCHA COD Mali 2025 (HDX), CC BY-IGO ;
- communes : geoBoundaries gbOpen MLI ADM3 2023, CC BY 4.0.

Le module fonctionne même sans données importées : il affiche alors la carte
administrative du Mali. Dès qu'un fichier est importé, il détecte
automatiquement le niveau géographique, propose une variable numérique et
produit une carte choroplèthe. Les noms et les codes administratifs (p-code)
sont reconnus.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import pandas as pd
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.patheffects import withStroke
from matplotlib.textpath import TextPath
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ---------- CONFIGURATION DES CARTES ----------

DOSSIER_CARTES = Path(__file__).resolve().parent / "donnees_cartes"

NIVEAUX = {
    "Régions": {
        "fichier": "mali_adm1_2025.geojson",
        "singulier": "région",
        "pluriel": "régions",
    },
    "Cercles": {
        "fichier": "mali_adm2_2025.geojson",
        "singulier": "cercle",
        "pluriel": "cercles",
    },
    "Communes": {
        "fichier": "mali_adm3_2023.geojson",
        "singulier": "commune",
        "pluriel": "communes",
    },
    "Mali": {
        "fichier": "mali_adm0_2025.geojson",
        "singulier": "Mali",
        "pluriel": "Mali",
    },
}

ORDRE_NIVEAUX = ["Régions", "Cercles", "Communes", "Mali"]

PALETTES = {
    "Vert → rouge": "RdYlGn_r",
    "Jaune → rouge": "YlOrRd",
    "Bleus": "Blues",
    "Orange": "Oranges",
    "Spectral": "Spectral_r",
    "Viridis": "viridis",
}

FONCTIONS_AGREGATION = {
    "Somme": "sum",
    "Moyenne": "mean",
    "Médiane": "median",
    "Minimum": "min",
    "Maximum": "max",
    "Nombre de valeurs": "count",
}

# Corrections de noms fréquentes entre les fichiers importés et les contours.
ALIAS_NOMS = {
    "koulikouro": "koulikoro",
    "timbuktu": "tombouctou",
    "bafoulebe": "bafoulabe",
    "nioro du sahel": "nioro",
    "gourma rharous": "rharous",
    "taoudenit": "taoudenni",
}

# Noms affichés dans l'interface (les clés de correspondance restent inchangées).
NOMS_AFFICHAGE = {
    "Segou": "Ségou",
    "Taoudenni": "Taoudénit",
    "Timbuktu": "Tombouctou",
}

COULEUR_FOND_CARTE = "#FFFFFF"
COULEUR_ZONE_SANS_DONNEE = (0.90, 0.91, 0.93, 1.0)
COULEUR_BORDURE = "#374151"
COULEUR_SELECTION = "#DC2626"


# ---------- NORMALISATION DES NOMS ----------

def normaliser_nom(texte) -> str:
    """Normalise un nom pour comparer les libellés malgré accents, casse et tirets."""
    if texte is None:
        return ""

    try:
        if isinstance(texte, float) and math.isnan(texte):
            return ""
    except TypeError:
        pass

    texte = unicodedata.normalize("NFKD", str(texte))
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    texte = texte.lower().replace("’", " ").replace("'", " ")
    # Retire les préfixes du type « Commune de », « Cercle de », « Région de ».
    texte = re.sub(r"^\s*(commune|cercle|region|district)\s+(de\s+|d\s+)?", "", texte)
    # Retire les mots « commune », « cercle », etc. au milieu du nom.
    texte = re.sub(r"\b(commune|cercle|region|district)\b", " ", texte)
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return " ".join(texte.split())


def cle_canonique(texte) -> str:
    """Renvoie la clé de comparaison définitive d'un nom géographique."""
    cle = normaliser_nom(texte)
    return ALIAS_NOMS.get(cle, cle)


# ---------- CHARGEMENT DES CONTOURS ----------

def _extraire_parties(geometrie) -> tuple:
    """Extrait les anneaux extérieurs d'une géométrie GeoJSON (Polygon ou MultiPolygon)."""
    if not geometrie:
        return ()

    type_geometrie = geometrie.get("type")
    coordonnees = geometrie.get("coordinates")

    if type_geometrie == "Polygon":
        polygones = [coordonnees]
    elif type_geometrie == "MultiPolygon":
        polygones = coordonnees or []
    else:
        return ()

    parties = []
    for polygone in polygones:
        if not polygone:
            continue
        anneau = polygone[0]
        points = []
        for point in anneau:
            if point and len(point) >= 2:
                try:
                    points.append((float(point[0]), float(point[1])))
                except (TypeError, ValueError):
                    continue
        if len(points) >= 3:
            parties.append(tuple(points))
    return tuple(parties)


def _calculer_bbox(parties) -> tuple:
    """Calcule la boîte englobante (xmin, ymin, xmax, ymax) d'un ensemble d'anneaux."""
    xs = [point[0] for partie in parties for point in partie]
    ys = [point[1] for partie in parties for point in partie]
    return min(xs), min(ys), max(xs), max(ys)


def _aire_anneau(anneau) -> float:
    """Calcule l'aire d'un anneau par la formule du lacet (shoelace)."""
    aire = 0.0
    nombre = len(anneau)
    for index in range(nombre):
        x0, y0 = anneau[index]
        x1, y1 = anneau[(index + 1) % nombre]
        aire += x0 * y1 - x1 * y0
    return abs(aire) / 2.0


def _centroide(parties) -> tuple:
    """Calcule un centre approximatif : centroïde de la plus grande partie du polygone."""
    if not parties:
        return (0.0, 0.0)

    partie = max(parties, key=_aire_anneau)
    aire = 0.0
    cx = 0.0
    cy = 0.0
    nombre = len(partie)
    for index in range(nombre):
        x0, y0 = partie[index]
        x1, y1 = partie[(index + 1) % nombre]
        facteur = x0 * y1 - x1 * y0
        aire += facteur
        cx += (x0 + x1) * facteur
        cy += (y0 + y1) * facteur

    if abs(aire) < 1e-12:
        return (
            sum(point[0] for point in partie) / len(partie),
            sum(point[1] for point in partie) / len(partie),
        )

    aire /= 2.0
    return cx / (6.0 * aire), cy / (6.0 * aire)


@lru_cache(maxsize=None)
def charger_contours(niveau: str) -> tuple:
    """Charge et met en cache les contours d'un niveau administratif."""
    configuration = NIVEAUX[niveau]
    chemin = DOSSIER_CARTES / configuration["fichier"]

    with open(chemin, "r", encoding="utf-8") as fichier:
        donnees_geojson = json.load(fichier)

    resultat = []
    for entite in donnees_geojson.get("features", []):
        proprietes = entite.get("properties") or {}
        nom = (
            proprietes.get("shapeName")
            or proprietes.get("adm1_name1")
            or proprietes.get("adm2_name1")
            or proprietes.get("adm0_name1")
            or proprietes.get("adm1_name")
            or proprietes.get("adm2_name")
            or proprietes.get("adm0_name")
            or proprietes.get("name")
            or ""
        )
        code = (
            proprietes.get("shapeCode")
            or proprietes.get("adm1_pcode")
            or proprietes.get("adm2_pcode")
            or proprietes.get("adm0_pcode")
            or ""
        )
        parties = _extraire_parties(entite.get("geometry") or {})
        if not parties:
            continue
        nom_brut = str(nom)
        resultat.append(
            {
                "nom": NOMS_AFFICHAGE.get(nom_brut, nom_brut),
                "cle": cle_canonique(nom_brut),
                "code": str(code),
                "parties": parties,
                "bbox": _calculer_bbox(parties),
                "centre": _centroide(parties),
            }
        )

    resultat.sort(key=lambda entite: entite["nom"].lower())
    return tuple(resultat)


@lru_cache(maxsize=None)
def index_libelles(niveau: str) -> dict:
    """Construit la correspondance entre noms / codes administratifs et zones.

    Les clés sont soit le nom normalisé, soit le p-code normalisé ; les valeurs
    sont toujours la clé canonique de la zone.
    """
    index = {}
    for entite in charger_contours(niveau):
        index.setdefault(entite["cle"], entite["cle"])
    for entite in charger_contours(niveau):
        code = normaliser_nom(entite.get("code") or "")
        if code:
            index.setdefault(code, entite["cle"])
    return index


def associer_libelle(valeur, index: dict) -> str | None:
    """Retrouve la clé d'une zone à partir d'un nom ou d'un p-code."""
    if valeur is None:
        return None
    try:
        if isinstance(valeur, float) and math.isnan(valeur):
            return None
    except TypeError:
        pass

    texte = str(valeur).strip()
    if not texte:
        return None

    cle = index.get(cle_canonique(texte))
    if cle:
        return cle
    return index.get(normaliser_nom(texte))


# ---------- DÉTECTION DES COLONNES ----------

def colonnes_texte(donnees) -> list:
    """Renvoie les colonnes utilisables comme libellés géographiques."""
    resultat = []
    if donnees is None:
        return resultat

    for colonne in donnees.columns:
        serie = donnees[colonne]
        if (
            pd.api.types.is_numeric_dtype(serie)
            or pd.api.types.is_bool_dtype(serie)
            or pd.api.types.is_datetime64_any_dtype(serie)
        ):
            continue
        resultat.append(colonne)
    return resultat


def _taux_correspondance(serie, index_libelles_niveau) -> float:
    """Renvoie la proportion de valeurs d'une colonne qui correspondent à une zone connue."""
    valeurs = serie.dropna().astype(str).unique()
    if len(valeurs) == 0:
        return 0.0
    correspondances = sum(
        1 for valeur in valeurs if associer_libelle(valeur, index_libelles_niveau) is not None
    )
    return correspondances / len(valeurs)


def _niveau_du_libelle_colonne(colonne) -> str | None:
    """Déduit un niveau administratif à partir du nom d'une colonne."""
    texte = unicodedata.normalize("NFKD", str(colonne))
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    nom = " ".join(re.sub(r"[^a-z0-9]+", " ", texte.lower()).split())
    if "commune" in nom:
        return "Communes"
    if "cercle" in nom:
        return "Cercles"
    if "region" in nom or "district" in nom:
        return "Régions"
    return None


def detecter_niveau(donnees) -> tuple:
    """Devine le niveau administratif le plus probable pour un jeu de données.

    Renvoie ``(niveau, colonne, taux_de_correspondance)``.

    La priorité est donnée aux colonnes explicitement nommées « Région »,
    « Cercle » ou « Commune », car un même nom peut exister à plusieurs
    niveaux (le cercle de Kayes et la commune de Kayes, par exemple). À défaut,
    le niveau dont les valeurs correspondent le mieux est retenu.
    """
    if donnees is None or donnees.empty:
        return "Régions", None, 0.0

    colonnes = colonnes_texte(donnees)

    # 1. Colonnes explicitement nommées : on prend le niveau le plus fin.
    for niveau in ("Communes", "Cercles", "Régions"):
        index_niveau = index_libelles(niveau)
        meilleure_colonne = None
        meilleur_taux = 0.0
        for colonne in colonnes:
            if _niveau_du_libelle_colonne(colonne) != niveau:
                continue
            taux = _taux_correspondance(donnees[colonne], index_niveau)
            if taux > meilleur_taux:
                meilleure_colonne = colonne
                meilleur_taux = taux
        if meilleure_colonne is not None and meilleur_taux >= 0.5:
            return niveau, meilleure_colonne, meilleur_taux

    # 2. Aucun libellé explicite : meilleur taux, en préférant le niveau le
    #    moins fin en cas d'égalité (les noms de régions sont plus stables).
    meilleur = ("Régions", None, 0.0)
    for niveau in ("Régions", "Cercles", "Communes"):
        index_niveau = index_libelles(niveau)
        for colonne in colonnes:
            taux = _taux_correspondance(donnees[colonne], index_niveau)
            if taux > meilleur[2]:
                meilleur = (niveau, colonne, taux)

    return meilleur


def detecter_colonne_nom(donnees, niveau: str) -> tuple:
    """Cherche la colonne qui correspond le mieux au niveau choisi."""
    if donnees is None or donnees.empty:
        return None, 0.0

    index_niveau = index_libelles(niveau)
    meilleur = (None, 0.0)
    for colonne in colonnes_texte(donnees):
        taux = _taux_correspondance(donnees[colonne], index_niveau)
        if taux > meilleur[1]:
            meilleur = (colonne, taux)
    return meilleur


def convertir_serie_nombre(serie) -> pd.Series:
    """Convertit une série en nombres, en acceptant les formats français et anglais."""
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")

    texte = (
        serie.astype(str)
        .str.replace("\u202f", "", regex=False)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    candidats = [pd.to_numeric(texte, errors="coerce")]

    # Format français : 1 234,56
    francais = texte.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    candidats.append(pd.to_numeric(francais, errors="coerce"))

    # Format anglais : 1,234.56
    anglais = texte.str.replace(",", "", regex=False)
    candidats.append(pd.to_numeric(anglais, errors="coerce"))

    return max(candidats, key=lambda candidate: candidate.notna().sum())


def colonnes_numeriques(donnees) -> list:
    """Renvoie les colonnes numériques, y compris celles stockées sous forme de texte."""
    if donnees is None:
        return []

    resultat = list(donnees.select_dtypes(include="number").columns)
    for colonne in donnees.columns:
        if colonne in resultat:
            continue
        if pd.api.types.is_datetime64_any_dtype(donnees[colonne]):
            continue
        converti = convertir_serie_nombre(donnees[colonne])
        if converti.notna().mean() >= 0.8:
            resultat.append(colonne)
    return resultat


def choisir_colonne_valeur(colonnes) -> str | None:
    """Choisit une variable numérique pertinente par défaut."""
    priorites = [
        "population", "effectif", "total", "valeur", "nombre", "cas",
        "taux", "montant", "production", "rendement", "incidence",
    ]
    for mot in priorites:
        for colonne in colonnes:
            if mot in normaliser_nom(colonne):
                return colonne
    return colonnes[0] if colonnes else None


def trouver_colonnes_coordonnees(donnees) -> tuple:
    """Cherche des colonnes latitude/longitude dans le fichier importé."""
    if donnees is None:
        return None, None

    colonne_lat, colonne_lon = None, None
    for colonne in donnees.columns:
        nom = normaliser_nom(colonne)
        if colonne_lat is None and ("latitude" in nom or nom == "lat"):
            colonne_lat = colonne
        if colonne_lon is None and ("longitude" in nom or nom == "lon" or nom == "lng"):
            colonne_lon = colonne
    return colonne_lat, colonne_lon


def agreger_valeurs(donnees, colonne_geo, colonne_valeur, methode, index_niveau):
    """Agrège une variable numérique par zone géographique.

    ``index_niveau`` est la correspondance renvoyée par :func:`index_libelles`.
    Renvoie (valeurs_par_cle, libellés_inconnus).
    """
    if (
        donnees is None
        or colonne_geo not in donnees.columns
        or colonne_valeur not in donnees.columns
    ):
        return {}, []

    libelles = donnees[colonne_geo]
    cles = libelles.map(lambda valeur: associer_libelle(valeur, index_niveau))
    valeurs = convertir_serie_nombre(donnees[colonne_valeur])

    tableau = pd.DataFrame({"cle": cles, "valeur": valeurs})
    tableau = tableau[tableau["cle"].notna() & tableau["valeur"].notna()]

    if tableau.empty:
        return {}, []

    fonction = FONCTIONS_AGREGATION.get(methode, "sum")
    try:
        groupe = tableau.groupby("cle")["valeur"].agg(fonction)
    except (TypeError, ValueError):
        return {}, []

    valeurs_par_cle = {str(cle): float(valeur) for cle, valeur in groupe.items()}
    inconnues = sorted(
        {
            str(libelle)
            for libelle, cle in zip(libelles, cles)
            if cle is None and libelle is not None and str(libelle).strip()
        }
    )
    return valeurs_par_cle, inconnues


def formater_nombre(valeur) -> str:
    """Affiche un nombre avec un format lisible en français."""
    if valeur is None:
        return "—"
    try:
        nombre = float(valeur)
    except (TypeError, ValueError):
        return str(valeur)

    if math.isnan(nombre) or math.isinf(nombre):
        return "—"
    if abs(nombre) >= 1000:
        return f"{nombre:,.0f}".replace(",", " ")
    if abs(nombre) >= 100:
        return f"{nombre:.0f}"
    if abs(nombre) >= 10:
        return f"{nombre:.1f}".replace(".", ",")
    return f"{nombre:.2f}".replace(".", ",")


def point_dans_anneau(x, y, anneau) -> bool:
    """Teste si un point est à l'intérieur d'un anneau (algorithme du rayon)."""
    interieur = False
    nombre = len(anneau)
    j = nombre - 1
    for i in range(nombre):
        xi, yi = anneau[i]
        xj, yj = anneau[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            interieur = not interieur
        j = i
    return interieur


def _luminance(couleur) -> float:
    """Calcule la luminance d'une couleur RGBA pour choisir un texte clair ou sombre."""
    try:
        rouge, vert, bleu = couleur[:3]
    except (TypeError, ValueError):
        return 0.5
    return 0.299 * rouge + 0.587 * vert + 0.114 * bleu


def _chevauchement(box_a, box_b) -> bool:
    """Indique si deux rectangles (xmin, ymin, xmax, ymax) se chevauchent."""
    return not (
        box_a[2] <= box_b[0]
        or box_a[0] >= box_b[2]
        or box_a[3] <= box_b[1]
        or box_a[1] >= box_b[3]
    )


def _placer_etiquettes(ax, figure, etiquettes, limites, taille):
    """Place les noms des zones en évitant les chevauchements.

    Les grandes zones sont servies en premier. Quand une étiquette doit être
    déplacée hors de sa zone, un trait de rappel relie le nom au centroïde.
    """
    if not etiquettes:
        return

    # Met à jour les transformations sans refaire un rendu complet.
    try:
        figure.draw_without_rendering()
    except Exception:
        figure.canvas.draw()

    transformation = ax.transData
    origine = transformation.transform((0.0, 0.0))
    pixels_x = transformation.transform((1.0, 0.0))[0] - origine[0]
    pixels_y = transformation.transform((0.0, 1.0))[1] - origine[1]
    if pixels_x == 0 or pixels_y == 0:
        return

    unite_x_par_point = abs((1.0 / pixels_x) * (figure.dpi / 72.0))
    unite_y_par_point = abs((1.0 / pixels_y) * (figure.dpi / 72.0))

    propriete_police = FontProperties(size=taille)
    xmin, ymin, xmax, ymax = limites
    boites_placees = []

    for etiquette in sorted(etiquettes, key=lambda element: element["aire"], reverse=True):
        chemin = TextPath((0.0, 0.0), etiquette["nom"], prop=propriete_police)
        bornes = chemin.get_extents()
        demi_largeur = max(bornes.width, 1.0) * unite_x_par_point / 2.0
        demi_hauteur = max(bornes.height, 1.0) * unite_y_par_point / 2.0

        marge_x = 2.0 * unite_x_par_point
        marge_y = 2.0 * unite_y_par_point
        pas_x = demi_largeur + marge_x
        pas_y = demi_hauteur + marge_y

        centre_x, centre_y = etiquette["centre"]
        candidats = [(0.0, 0.0)]
        for rayon in (1.0, 1.8, 2.8, 4.0, 5.4):
            for angle in range(0, 360, 30):
                radians = math.radians(angle)
                candidats.append(
                    (
                        rayon * pas_x * math.cos(radians),
                        rayon * pas_y * math.sin(radians),
                    )
                )

        position = None
        for decalage_x, decalage_y in candidats:
            x = centre_x + decalage_x
            y = centre_y + decalage_y
            boite = (
                x - demi_largeur - marge_x,
                y - demi_hauteur - marge_y,
                x + demi_largeur + marge_x,
                y + demi_hauteur + marge_y,
            )
            if boite[0] < xmin or boite[1] < ymin or boite[2] > xmax or boite[3] > ymax:
                continue
            if any(_chevauchement(boite, autre) for autre in boites_placees):
                continue
            position = (x, y, boite)
            break

        if position is None:
            # Aucun emplacement lisible : on masque l'étiquette plutôt que
            # d'afficher un texte illisible par-dessus ses voisins.
            continue

        x, y, boite = position
        boites_placees.append(boite)

        # Trait de rappel si l'étiquette a quitté sa propre zone.
        dans_sa_zone = any(
            point_dans_anneau(x, y, partie) for partie in etiquette["parties"]
        )
        if not dans_sa_zone:
            ax.plot(
                [centre_x, x],
                [centre_y, y],
                color="#6B7280",
                linewidth=0.8,
                zorder=7.5,
            )
            ax.plot(
                [centre_x],
                [centre_y],
                marker="o",
                markersize=2.2,
                color="#374151",
                zorder=7.5,
            )

        couleur_texte = "#FFFFFF" if _luminance(etiquette["couleur"]) < 0.45 else "#111827"
        couleur_contour = "#111827" if couleur_texte == "#FFFFFF" else "#FFFFFF"

        ax.text(
            x,
            y,
            etiquette["nom"],
            fontsize=taille,
            ha="center",
            va="center",
            color=couleur_texte,
            zorder=8,
            path_effects=[withStroke(linewidth=2.8, foreground=couleur_contour)],
        )


# ---------- PAGE SIG ----------

class PageSIG(QWidget):
    """Page complète de cartographie du Mali."""

    def __init__(self, obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import):
        super().__init__()
        self.obtenir_donnees_actuelles = obtenir_donnees_actuelles
        self.obtenir_domaine_actuel = obtenir_domaine_actuel
        self.fonction_import = fonction_import

        self.donnees = None
        self.features = ()
        self.index_features = {}
        self.valeurs = {}
        self.inconnues = []
        self.selection = None
        self.colonnes_geo = []
        self.colonnes_valeurs = []
        self._empreinte_donnees = object()
        self._deja_affichee = False
        self._colorbar = None
        self._ax = None

        self._construire_interface()
        self.actualiser_donnees()

    # ---- Construction de l'interface ----

    def _construire_interface(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(12, 12, 12, 12)
        layout_principal.setSpacing(10)

        # En-tête
        entete = QHBoxLayout()
        textes_entete = QVBoxLayout()
        titre = QLabel("Carte du Mali")
        titre.setStyleSheet("font-size: 18px; font-weight: bold;")
        sous_titre = QLabel(
            "Cartographie par région, cercle et commune — colorée selon les données importées."
        )
        sous_titre.setStyleSheet("color: #6B7280;")
        sous_titre.setWordWrap(True)
        textes_entete.addWidget(titre)
        textes_entete.addWidget(sous_titre)

        badge_source = QLabel("Contours : OCHA COD 2025 · geoBoundaries 2023")
        badge_source.setStyleSheet("color: #6B7280; font-size: 9pt;")
        badge_source.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        entete.addLayout(textes_entete, 1)
        entete.addWidget(badge_source)
        layout_principal.addLayout(entete)

        # Séparateur principal
        separateur = QSplitter(Qt.Orientation.Horizontal)
        separateur.setChildrenCollapsible(False)

        # ---- Panneau gauche ----
        panneau_gauche = QWidget()
        layout_gauche = QVBoxLayout(panneau_gauche)
        layout_gauche.setContentsMargins(0, 0, 8, 0)
        layout_gauche.setSpacing(10)

        groupe_carte = QGroupBox("Carte thématique")
        grille = QGridLayout()
        grille.setColumnStretch(1, 1)

        self.combo_niveau = QComboBox()
        self.combo_niveau.addItems(ORDRE_NIVEAUX)
        self.combo_niveau.setToolTip("Choisissez le découpage administratif à afficher.")

        self.combo_geo = QComboBox()
        self.combo_geo.addItem("Aucune colonne")
        self.combo_geo.setToolTip(
            "Colonne du fichier qui contient les noms de régions, de cercles ou de communes."
        )

        self.combo_valeur = QComboBox()
        self.combo_valeur.addItem("Aucune (carte vide)")
        self.combo_valeur.setToolTip("Variable numérique utilisée pour colorer les zones.")

        self.combo_agregation = QComboBox()
        self.combo_agregation.addItems(list(FONCTIONS_AGREGATION))
        self.combo_agregation.setToolTip(
            "Comment résumer plusieurs lignes rattachées à la même zone."
        )

        self.combo_palette = QComboBox()
        self.combo_palette.addItems(list(PALETTES))

        self.case_noms = QCheckBox("Afficher les noms")
        self.case_noms.setChecked(True)
        self.case_noms.setToolTip(
            "Les noms sont affichés automatiquement jusqu'à 80 zones, pour rester lisibles."
        )

        self.case_points = QCheckBox("Afficher les points GPS")
        self.case_points.setChecked(False)
        self.case_points.setToolTip(
            "Affiche les points des colonnes latitude/longitude du fichier importé."
        )

        ligne_niveau = QLabel("Niveau administratif")
        ligne_geo = QLabel("Colonne géographique")
        ligne_valeur = QLabel("Variable à cartographier")
        ligne_agregation = QLabel("Agrégation")
        ligne_palette = QLabel("Palette")

        grille.addWidget(ligne_niveau, 0, 0)
        grille.addWidget(self.combo_niveau, 0, 1)
        grille.addWidget(ligne_geo, 1, 0)
        grille.addWidget(self.combo_geo, 1, 1)
        grille.addWidget(ligne_valeur, 2, 0)
        grille.addWidget(self.combo_valeur, 2, 1)
        grille.addWidget(ligne_agregation, 3, 0)
        grille.addWidget(self.combo_agregation, 3, 1)
        grille.addWidget(ligne_palette, 4, 0)
        grille.addWidget(self.combo_palette, 4, 1)
        grille.addWidget(self.case_noms, 5, 0, 1, 2)
        grille.addWidget(self.case_points, 6, 0, 1, 2)
        groupe_carte.setLayout(grille)

        self.bouton_afficher = QPushButton("Afficher la carte")
        self.bouton_afficher.setMinimumHeight(36)
        self.bouton_actualiser = QPushButton("Actualiser les données")
        self.bouton_actualiser.setToolTip(
            "Relit les données importées et redétecte automatiquement les colonnes."
        )

        groupe_donnees = QGroupBox("Données")
        layout_donnees = QVBoxLayout()
        self.bouton_importer = QPushButton("Importer un fichier (Excel / CSV)")
        self.label_import = QLabel("Aucune donnée importée. La carte administrative s'affiche seule.")
        self.label_import.setWordWrap(True)
        self.label_import.setStyleSheet("color: #6B7280; font-size: 9pt;")
        layout_donnees.addWidget(self.bouton_importer)
        layout_donnees.addWidget(self.label_import)
        groupe_donnees.setLayout(layout_donnees)

        groupe_export = QGroupBox("Exportation")
        layout_export = QGridLayout()
        self.bouton_png = QPushButton("Carte PNG")
        self.bouton_pdf = QPushButton("Carte PDF")
        self.bouton_csv = QPushButton("Tableau CSV")
        self.bouton_excel = QPushButton("Tableau Excel")
        layout_export.addWidget(self.bouton_png, 0, 0)
        layout_export.addWidget(self.bouton_pdf, 0, 1)
        layout_export.addWidget(self.bouton_csv, 1, 0)
        layout_export.addWidget(self.bouton_excel, 1, 1)
        groupe_export.setLayout(layout_export)

        astuce = QLabel(
            "Astuce : importez un fichier contenant une colonne « Région », « Cercle » "
            "ou « Commune », puis choisissez la variable à représenter."
        )
        astuce.setWordWrap(True)
        astuce.setStyleSheet("color: #6B7280; font-size: 9pt;")

        layout_gauche.addWidget(groupe_carte)
        layout_gauche.addWidget(self.bouton_afficher)
        layout_gauche.addWidget(self.bouton_actualiser)
        layout_gauche.addWidget(groupe_donnees)
        layout_gauche.addWidget(groupe_export)

        groupe_analyse_avancee = QGroupBox("Analyse avancée")
        layout_analyse_avancee = QVBoxLayout()
        self.bouton_top5 = QPushButton("Top 5 zones")
        self.bouton_stats_sig = QPushButton("Statistiques spatiales")
        self.bouton_risque = QPushButton("Zones à risque (top 25 %)")
        layout_analyse_avancee.addWidget(self.bouton_top5)
        layout_analyse_avancee.addWidget(self.bouton_stats_sig)
        layout_analyse_avancee.addWidget(self.bouton_risque)
        groupe_analyse_avancee.setLayout(layout_analyse_avancee)

        layout_gauche.addWidget(groupe_analyse_avancee)
        layout_gauche.addWidget(astuce)
        layout_gauche.addStretch()

        zone_gauche = QScrollArea()
        zone_gauche.setWidgetResizable(True)
        zone_gauche.setWidget(panneau_gauche)
        zone_gauche.setMinimumWidth(310)
        zone_gauche.setMaximumWidth(380)
        zone_gauche.setFrameShape(QScrollArea.Shape.NoFrame)
        separateur.addWidget(zone_gauche)

        # ---- Panneau droit : carte + tableau ----
        separateur_droit = QSplitter(Qt.Orientation.Vertical)
        separateur_droit.setChildrenCollapsible(False)

        self.figure = Figure(figsize=(7.2, 5.2), dpi=100, facecolor=COULEUR_FOND_CARTE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(360)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._ax = self.figure.add_subplot(111)

        groupe_carte_droite = QGroupBox("Carte interactive")
        layout_carte = QVBoxLayout()
        barre_outils = NavigationToolbar2QT(self.canvas, self)
        layout_carte.addWidget(barre_outils)
        layout_carte.addWidget(self.canvas, 1)

        self.label_selection = QLabel("Cliquez sur une zone de la carte pour voir son détail.")
        self.label_selection.setWordWrap(True)
        self.label_selection.setStyleSheet("color: #374151;")
        layout_carte.addWidget(self.label_selection)
        groupe_carte_droite.setLayout(layout_carte)

        groupe_resultats = QGroupBox("Tableau des valeurs")
        layout_resultats = QVBoxLayout()
        ligne_resultats = QHBoxLayout()
        self.champ_recherche = QLineEdit()
        self.champ_recherche.setPlaceholderText("Rechercher une zone...")
        self.label_resume = QLabel("")
        self.label_resume.setStyleSheet("color: #6B7280; font-size: 9pt;")
        ligne_resultats.addWidget(self.champ_recherche, 1)
        ligne_resultats.addWidget(self.label_resume)
        layout_resultats.addLayout(ligne_resultats)

        self.tableau = QTableWidget(0, 3)
        self.tableau.setHorizontalHeaderLabels(["Nom", "Valeur", "Rang"])
        self.tableau.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tableau.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tableau.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tableau.verticalHeader().setVisible(False)
        self.tableau.setAlternatingRowColors(True)
        self.tableau.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableau.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableau.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout_resultats.addWidget(self.tableau, 1)
        groupe_resultats.setLayout(layout_resultats)

        separateur_droit.addWidget(groupe_carte_droite)
        separateur_droit.addWidget(groupe_resultats)
        separateur_droit.setStretchFactor(0, 4)
        separateur_droit.setStretchFactor(1, 2)
        separateur_droit.setSizes([520, 230])
        separateur.addWidget(separateur_droit)

        separateur.setStretchFactor(0, 0)
        separateur.setStretchFactor(1, 1)
        separateur.setSizes([330, 850])
        layout_principal.addWidget(separateur, 1)

        pied = QLabel(
            "Contours : OCHA COD 2025 (CC BY-IGO) pour les régions et cercles ; "
            "geoBoundaries 2023 (CC BY 4.0) pour les communes · "
            "19 régions + district de Bamako, 160 cercles, 701 communes. "
            "Les noms de communes identiques dans plusieurs cercles sont regroupés."
        )
        pied.setStyleSheet("color: #6B7280; font-size: 8.5pt;")
        pied.setWordWrap(True)
        layout_principal.addWidget(pied)

        # ---- Connexions ----
        self.combo_niveau.currentTextChanged.connect(self._changer_niveau)
        self.combo_geo.currentTextChanged.connect(self._redessiner)
        self.combo_valeur.currentTextChanged.connect(self._redessiner)
        self.combo_agregation.currentTextChanged.connect(self._redessiner)
        self.combo_palette.currentTextChanged.connect(self._redessiner)
        self.case_noms.stateChanged.connect(self._redessiner)
        self.case_points.stateChanged.connect(self._redessiner)

        self.bouton_afficher.clicked.connect(self._redessiner)
        self.bouton_actualiser.clicked.connect(lambda: self.actualiser_donnees(force=True, message=True))
        self.bouton_importer.clicked.connect(self._importer)

        self.bouton_png.clicked.connect(lambda: self._exporter_carte("PNG"))
        self.bouton_pdf.clicked.connect(lambda: self._exporter_carte("PDF"))
        self.bouton_csv.clicked.connect(lambda: self._exporter_tableau("CSV"))
        self.bouton_excel.clicked.connect(lambda: self._exporter_tableau("Excel"))

        self.bouton_top5.clicked.connect(self._afficher_top5)
        self.bouton_stats_sig.clicked.connect(self._afficher_statistiques)
        self.bouton_risque.clicked.connect(self._afficher_zones_risque)

        self.canvas.mpl_connect("button_press_event", self._clic_carte)
        self.tableau.itemSelectionChanged.connect(self._selection_tableau)
        self.champ_recherche.textChanged.connect(self._filtrer_tableau)
        self.champ_recherche.returnPressed.connect(self._selectionner_premier_visible)

    # ---- Données ----

    @contextmanager
    def _sans_signaux(self, *widgets):
        """Bloque temporairement les signaux de plusieurs widgets."""
        for widget in widgets:
            widget.blockSignals(True)
        try:
            yield
        finally:
            for widget in widgets:
                widget.blockSignals(False)

    def _empreinte(self, donnees):
        if donnees is None:
            return None
        try:
            return (id(donnees), donnees.shape, tuple(str(colonne) for colonne in donnees.columns))
        except Exception:
            return id(donnees)

    def _charger_niveau(self):
        """Charge les contours du niveau actuellement sélectionné."""
        self.niveau_courant = self.combo_niveau.currentText()
        self.features = charger_contours(self.niveau_courant)
        self.index_features = {}
        for entite in self.features:
            self.index_features.setdefault(entite["cle"], []).append(entite)

        noms_possibles = len(self.features) <= 80
        self.case_noms.setEnabled(noms_possibles)
        if noms_possibles:
            self.case_noms.setToolTip(
                "Les noms sont affichés automatiquement jusqu'à 80 zones, pour rester lisibles."
            )
        else:
            self.case_noms.setToolTip(
                "Trop de zones à ce niveau pour afficher les noms lisiblement "
                "(maximum 80). Utilisez le tableau ou la recherche."
            )

    def _remplir_colonnes(self):
        """Met à jour les listes de colonnes proposées dans les menus."""
        self.colonnes_geo = colonnes_texte(self.donnees)
        self.colonnes_valeurs = colonnes_numeriques(self.donnees)

        with self._sans_signaux(self.combo_geo, self.combo_valeur):
            self.combo_geo.clear()
            if self.colonnes_geo:
                self.combo_geo.addItems(self.colonnes_geo)
            else:
                self.combo_geo.addItem("Aucune colonne")

            self.combo_valeur.clear()
            self.combo_valeur.addItem("Aucune (carte vide)")
            if self.colonnes_valeurs:
                self.combo_valeur.addItems(self.colonnes_valeurs)

        self.combo_geo.setEnabled(bool(self.colonnes_geo))
        self.combo_valeur.setEnabled(bool(self.colonnes_valeurs))

        colonne_lat, colonne_lon = trouver_colonnes_coordonnees(self.donnees)
        coordonnees_disponibles = bool(colonne_lat and colonne_lon)
        self.case_points.setEnabled(coordonnees_disponibles)
        if not coordonnees_disponibles:
            self.case_points.setChecked(False)

    def actualiser_donnees(self, force=False, message=False):
        """Relit les données importées et met à jour la carte.

        Si les données n'ont pas changé, les choix de l'utilisateur sont
        conservés. ``force=True`` relance la détection automatique.
        """
        donnees = self.obtenir_donnees_actuelles()
        self.donnees = donnees if isinstance(donnees, pd.DataFrame) else None

        nouvelle_donnee = self._empreinte(self.donnees) != self._empreinte_donnees
        if force or nouvelle_donnee:
            self._empreinte_donnees = self._empreinte(self.donnees)

        ancien_geo = self.combo_geo.currentText()
        ancienne_valeur = self.combo_valeur.currentText()

        self._remplir_colonnes()

        if self.donnees is not None and not self.donnees.empty:
            niveau, colonne_geo_detectee, taux = detecter_niveau(self.donnees)

            if force or nouvelle_donnee:
                with self._sans_signaux(self.combo_niveau):
                    index = self.combo_niveau.findText(niveau)
                    if index >= 0:
                        self.combo_niveau.setCurrentIndex(index)
                self._charger_niveau()

                if colonne_geo_detectee:
                    with self._sans_signaux(self.combo_geo):
                        self.combo_geo.setCurrentText(colonne_geo_detectee)
                else:
                    colonne_geo, _ = detecter_colonne_nom(self.donnees, self.niveau_courant)
                    if colonne_geo:
                        with self._sans_signaux(self.combo_geo):
                            self.combo_geo.setCurrentText(colonne_geo)

                valeur_choisie = choisir_colonne_valeur(self.colonnes_valeurs)
                if valeur_choisie:
                    with self._sans_signaux(self.combo_valeur):
                        self.combo_valeur.setCurrentText(valeur_choisie)

                avertissement = (
                    " — correspondance faible, vérifiez la colonne géographique."
                    if taux < 0.8
                    else "."
                )
                self.label_import.setText(
                    f"{len(self.donnees)} lignes · {len(self.donnees.columns)} colonnes · "
                    f"niveau détecté : {niveau} · correspondance {taux:.0%}{avertissement}"
                )
            else:
                # Même jeu de données : on conserve les choix précédents.
                if ancien_geo in self.colonnes_geo:
                    with self._sans_signaux(self.combo_geo):
                        self.combo_geo.setCurrentText(ancien_geo)
                if ancienne_valeur in (["Aucune (carte vide)"] + self.colonnes_valeurs):
                    with self._sans_signaux(self.combo_valeur):
                        self.combo_valeur.setCurrentText(ancienne_valeur)

            if not self.features:
                self._charger_niveau()
        else:
            self._charger_niveau()
            self.label_import.setText(
                "Aucune donnée importée. La carte administrative s'affiche seule."
            )

        self.selection = None
        self._redessiner()

        if message:
            self.label_selection.setText("Carte actualisée.")

    def _changer_niveau(self, niveau=None):
        """Change le niveau administratif et redétecte la colonne géographique."""
        self._charger_niveau()
        self.selection = None

        if self.donnees is not None and not self.donnees.empty:
            colonne, taux = detecter_colonne_nom(self.donnees, self.niveau_courant)
            if colonne:
                with self._sans_signaux(self.combo_geo):
                    self.combo_geo.setCurrentText(colonne)
            avertissement = (
                " — correspondance faible, vérifiez la colonne géographique."
                if taux < 0.8
                else "."
            )
            self.label_import.setText(
                f"{len(self.donnees)} lignes · niveau {self.niveau_courant} · "
                f"correspondance {taux:.0%}{avertissement}"
            )
        else:
            self.label_import.setText(
                "Aucune donnée importée. La carte administrative s'affiche seule."
            )

        self._redessiner()

    def _importer(self):
        """Ouvre l'import de fichier puis rafraîchit la carte."""
        try:
            self.fonction_import()
        except Exception as erreur:  # pragma: no cover - dépend de l'interface
            QMessageBox.critical(self, "Erreur d'import", f"L'import a échoué :\n\n{erreur}")
            return
        self.actualiser_donnees(force=True, message=True)

    # ---- Dessin de la carte ----

    def _redessiner(self):
        """Recalcule les valeurs et redessine la carte et le tableau."""
        if not hasattr(self, "figure"):
            return

        if not self.features:
            self._charger_niveau()

        self.niveau_courant = self.combo_niveau.currentText()
        colonne_geo = self.combo_geo.currentText()
        colonne_valeur = self.combo_valeur.currentText()

        self.valeurs = {}
        self.inconnues = []

        if (
            self.donnees is not None
            and not self.donnees.empty
            and colonne_geo not in ("", "Aucune colonne")
            and colonne_valeur != "Aucune (carte vide)"
        ):
            self.valeurs, self.inconnues = agreger_valeurs(
                self.donnees,
                colonne_geo,
                colonne_valeur,
                self.combo_agregation.currentText(),
                index_libelles(self.niveau_courant),
            )

        self._dessiner_carte()
        self._remplir_tableau()
        self._maj_resume()

    def _dessiner_carte(self):
        """Dessine la carte choroplèthe dans la figure matplotlib."""
        if self._ax is None:
            self._ax = self.figure.add_subplot(111)

        if self._colorbar is not None:
            try:
                self._colorbar.remove()
            except Exception:
                pass
            self._colorbar = None

        ax = self._ax
        ax.clear()
        ax.set_facecolor(COULEUR_FOND_CARTE)

        nom_palette = PALETTES.get(self.combo_palette.currentText(), "YlOrRd")
        cmap = colormaps.get_cmap(nom_palette)

        valeurs_valides = [
            valeur
            for valeur in self.valeurs.values()
            if valeur is not None and math.isfinite(valeur)
        ]

        if valeurs_valides:
            minimum = min(valeurs_valides)
            maximum = max(valeurs_valides)
            if math.isclose(minimum, maximum):
                minimum -= 1.0
                maximum += 1.0
            norme = Normalize(vmin=minimum, vmax=maximum)
        else:
            norme = None

        polygones = []
        couleurs = []
        couleurs_par_cle = {}
        for entite in self.features:
            valeur = self.valeurs.get(entite["cle"])
            if norme is not None and valeur is not None and math.isfinite(valeur):
                couleur = cmap(norme(valeur))
            else:
                couleur = COULEUR_ZONE_SANS_DONNEE

            couleurs_par_cle[entite["cle"]] = couleur
            for partie in entite["parties"]:
                polygones.append(partie)
                couleurs.append(couleur)

        if polygones:
            collection = PolyCollection(
                polygones,
                facecolors=couleurs,
                edgecolors="white",
                linewidths=0.45,
                zorder=2,
            )
            ax.add_collection(collection)

        # Contour du pays, pour garder une limite nette.
        for entite in charger_contours("Mali"):
            for partie in entite["parties"]:
                xs = [point[0] for point in partie]
                ys = [point[1] for point in partie]
                ax.plot(xs, ys, color=COULEUR_BORDURE, linewidth=1.1, zorder=3)

        # Zone sélectionnée.
        if self.selection:
            for entite in self.index_features.get(self.selection, []):
                for partie in entite["parties"]:
                    xs = [point[0] for point in partie]
                    ys = [point[1] for point in partie]
                    ax.fill(xs, ys, facecolor="none", edgecolor=COULEUR_SELECTION, linewidth=2.2, zorder=6)

        # Points GPS.
        if self.case_points.isChecked() and self.donnees is not None:
            colonne_lat, colonne_lon = trouver_colonnes_coordonnees(self.donnees)
            if colonne_lat and colonne_lon:
                latitudes = convertir_serie_nombre(self.donnees[colonne_lat])
                longitudes = convertir_serie_nombre(self.donnees[colonne_lon])
                points = pd.DataFrame({"lat": latitudes, "lon": longitudes}).dropna()
                if not points.empty:
                    ax.scatter(
                        points["lon"],
                        points["lat"],
                        s=22,
                        c=COULEUR_SELECTION,
                        edgecolors="white",
                        linewidths=0.6,
                        zorder=7,
                    )

        # Cadrage sur le Mali.
        contours_mali = charger_contours("Mali")
        if contours_mali:
            xmin, ymin, xmax, ymax = contours_mali[0]["bbox"]
            marge = 0.35
            ax.set_xlim(xmin - marge, xmax + marge)
            ax.set_ylim(ymin - marge, ymax + marge)
        ax.set_aspect(1.0 / math.cos(math.radians(17.5)))
        ax.axis("off")
        limites_x = ax.get_xlim()
        limites_y = ax.get_ylim()
        limites = (limites_x[0], limites_y[0], limites_x[1], limites_y[1])

        # Titre.
        nom_variable = self.combo_valeur.currentText()
        if self.valeurs:
            titre = f"{nom_variable} par {self.niveau_courant.lower()}"
        else:
            titre = f"Carte administrative du Mali — {self.niveau_courant.lower()}"
        ax.set_title(titre, fontsize=12, fontweight="bold", pad=10)

        # Barre de couleurs.
        if norme is not None:
            mappable = ScalarMappable(norm=norme, cmap=cmap)
            mappable.set_array([])
            self._colorbar = self.figure.colorbar(
                mappable,
                ax=ax,
                fraction=0.032,
                pad=0.02,
                shrink=0.82,
            )
            self._colorbar.set_label(
                f"{nom_variable} ({self.combo_agregation.currentText().lower()})",
                fontsize=8,
            )
            self._colorbar.ax.tick_params(labelsize=7)

        ax.text(
            0.01,
            0.01,
            "Sources : OCHA COD 2025 · geoBoundaries 2023",
            transform=ax.transAxes,
            fontsize=7,
            color="#6B7280",
        )

        try:
            self.figure.tight_layout()
        except Exception:
            pass

        # Noms des zones, placés après la mise en page pour éviter les chevauchements.
        if self.case_noms.isChecked() and len(self.features) <= 80:
            if self.niveau_courant == "Régions":
                taille = 8.5
            elif self.niveau_courant == "Cercles":
                taille = 5.8
            else:
                taille = 4.5

            etiquettes = [
                {
                    "nom": entite["nom"],
                    "centre": entite["centre"],
                    "parties": entite["parties"],
                    "aire": sum(_aire_anneau(partie) for partie in entite["parties"]),
                    "couleur": couleurs_par_cle.get(entite["cle"], COULEUR_ZONE_SANS_DONNEE),
                }
                for entite in self.features
            ]
            _placer_etiquettes(ax, self.figure, etiquettes, limites, taille)

        self.canvas.draw_idle()

    # ---- Tableau et résumé ----

    def _remplir_tableau(self):
        """Remplit le tableau des valeurs par zone."""
        self.tableau.blockSignals(True)
        self.tableau.setRowCount(0)

        lignes = [(entite["nom"], self.valeurs.get(entite["cle"]), entite["cle"]) for entite in self.features]

        def cle_tri(ligne):
            valeur = ligne[1]
            manquante = valeur is None or not math.isfinite(valeur)
            return (manquante, -(valeur if not manquante else 0.0), ligne[0].lower())

        lignes.sort(key=cle_tri)
        self.tableau.setRowCount(len(lignes))

        rang = 0
        for index, (nom, valeur, cle) in enumerate(lignes):
            item_nom = QTableWidgetItem(nom)
            item_nom.setData(Qt.ItemDataRole.UserRole, cle)
            self.tableau.setItem(index, 0, item_nom)

            if valeur is not None and math.isfinite(valeur):
                rang += 1
                item_valeur = QTableWidgetItem(formater_nombre(valeur))
                item_rang = QTableWidgetItem(str(rang))
            else:
                item_valeur = QTableWidgetItem("—")
                item_valeur.setForeground(QColor("#9CA3AF"))
                item_rang = QTableWidgetItem("—")
                item_rang.setForeground(QColor("#9CA3AF"))

            self.tableau.setItem(index, 1, item_valeur)
            self.tableau.setItem(index, 2, item_rang)

        self.tableau.blockSignals(False)
        self._filtrer_tableau(self.champ_recherche.text())

    def _maj_resume(self):
        """Met à jour le résumé affiché au-dessus du tableau."""
        nombre = len(self.features)
        renseignees = sum(
            1
            for entite in self.features
            if entite["cle"] in self.valeurs and math.isfinite(self.valeurs[entite["cle"]])
        )

        texte = f"{nombre} entités · {renseignees} renseignées · {nombre - renseignees} sans donnée"
        if self.inconnues:
            texte += f" · {len(self.inconnues)} nom(s) non reconnu(s)"

        self.label_resume.setText(texte)
        if self.inconnues:
            exemples = ", ".join(self.inconnues[:5])
            if len(self.inconnues) > 5:
                exemples += "…"
            self.label_resume.setToolTip(
                "Ces libellés du fichier ne correspondent à aucune zone du niveau choisi :\n"
                + exemples
            )
        else:
            self.label_resume.setToolTip("")

    def _filtrer_tableau(self, texte):
        """Masque les lignes du tableau qui ne correspondent pas à la recherche."""
        terme = normaliser_nom(texte)
        for ligne in range(self.tableau.rowCount()):
            item = self.tableau.item(ligne, 0)
            nom = normaliser_nom(item.text()) if item else ""
            self.tableau.setRowHidden(ligne, bool(terme) and terme not in nom)

    def _selectionner_premier_visible(self):
        """Sélectionne la première ligne visible après une recherche."""
        for ligne in range(self.tableau.rowCount()):
            if not self.tableau.isRowHidden(ligne):
                self.tableau.selectRow(ligne)
                self.tableau.scrollToItem(self.tableau.item(ligne, 0))
                return

    # ---- Sélection ----

    def _selectionner_cle(self, cle):
        """Sélectionne une zone et met à jour le tableau et le libellé de détail."""
        self.selection = cle
        self._dessiner_carte()
        self._maj_selection()

        for ligne in range(self.tableau.rowCount()):
            item = self.tableau.item(ligne, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == cle:
                self.tableau.blockSignals(True)
                self.tableau.selectRow(ligne)
                self.tableau.scrollToItem(item)
                self.tableau.blockSignals(False)
                return

    def _selection_tableau(self):
        """Applique la sélection d'une ligne du tableau à la carte."""
        lignes = self.tableau.selectionModel().selectedRows()
        if not lignes:
            return
        item = self.tableau.item(lignes[0].row(), 0)
        if item:
            cle = item.data(Qt.ItemDataRole.UserRole)
            if cle and cle != self.selection:
                self.selection = cle
                self._dessiner_carte()
                self._maj_selection()

    def _maj_selection(self):
        """Affiche le détail de la zone sélectionnée."""
        if not self.selection:
            self.label_selection.setText("Cliquez sur une zone de la carte pour voir son détail.")
            return

        entites = self.index_features.get(self.selection, [])
        if not entites:
            return

        noms = " / ".join(entite["nom"] for entite in entites)
        if len(entites) > 1:
            noms += f" ({len(entites)} zones portent ce nom)"
        valeur = self.valeurs.get(self.selection)
        if valeur is None or not math.isfinite(valeur):
            self.label_selection.setText(f"{noms} — aucune donnée pour ce niveau.")
        else:
            self.label_selection.setText(
                f"{noms} — {formater_nombre(valeur)} "
                f"({self.combo_agregation.currentText().lower()})"
            )

    def _clic_carte(self, evenement):
        """Sélectionne la zone cliquée sur la carte."""
        if evenement.inaxes is not self._ax or evenement.xdata is None or evenement.ydata is None:
            return

        x = evenement.xdata
        y = evenement.ydata
        trouve = None

        for entite in self.features:
            xmin, ymin, xmax, ymax = entite["bbox"]
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            if any(point_dans_anneau(x, y, partie) for partie in entite["parties"]):
                trouve = entite["cle"]
                break

        if trouve:
            self._selectionner_cle(trouve)
        else:
            self.selection = None
            self._dessiner_carte()
            self.label_selection.setText("Cliquez sur une zone de la carte pour voir son détail.")

    # ---- Exports ----

    def _exporter_carte(self, format_export):
        """Exporte la carte en PNG ou PDF."""
        filtres = {
            "PNG": ("Image PNG (*.png)", "carte_mali.png"),
            "PDF": ("Document PDF (*.pdf)", "carte_mali.pdf"),
        }
        filtre, nom_defaut = filtres[format_export]
        chemin, _ = QFileDialog.getSaveFileName(self, f"Exporter la carte en {format_export}", nom_defaut, filtre)
        if not chemin:
            return

        try:
            self.figure.savefig(chemin, dpi=200, bbox_inches="tight")
        except Exception as erreur:
            QMessageBox.critical(self, "Erreur d'export", f"Impossible d'exporter la carte :\n\n{erreur}")
            return
        QMessageBox.information(self, "Export réussi", f"Carte exportée vers :\n{chemin}")

    def _exporter_tableau(self, format_export):
        """Exporte le tableau des valeurs en CSV ou Excel."""
        lignes = []
        for entite in self.features:
            valeur = self.valeurs.get(entite["cle"])
            lignes.append(
                {
                    "Nom": entite["nom"],
                    "Niveau": self.niveau_courant,
                    "Valeur": valeur,
                    "Agrégation": self.combo_agregation.currentText(),
                    "Variable": self.combo_valeur.currentText(),
                }
            )

        if not lignes:
            QMessageBox.information(self, "Info", "Aucune valeur à exporter.")
            return

        dataframe = pd.DataFrame(lignes)

        if format_export == "CSV":
            chemin, _ = QFileDialog.getSaveFileName(
                self, "Exporter le tableau en CSV", "valeurs_carte_mali.csv", "Fichier CSV (*.csv)"
            )
            if not chemin:
                return
            try:
                dataframe.to_csv(chemin, index=False, encoding="utf-8-sig")
            except Exception as erreur:
                QMessageBox.critical(self, "Erreur d'export", f"Impossible d'exporter le tableau :\n\n{erreur}")
                return
        else:
            chemin, _ = QFileDialog.getSaveFileName(
                self, "Exporter le tableau en Excel", "valeurs_carte_mali.xlsx", "Fichier Excel (*.xlsx)"
            )
            if not chemin:
                return
            try:
                dataframe.to_excel(chemin, index=False)
            except Exception as erreur:
                QMessageBox.critical(self, "Erreur d'export", f"Impossible d'exporter le tableau :\n\n{erreur}")
                return

        QMessageBox.information(self, "Export réussi", f"Tableau exporté vers :\n{chemin}")

    # ---- Analyse avancée ----

    def _nom_zone(self, cle):
        for entite in self.features:
            if entite["cle"] == cle:
                return entite["nom"]
        return str(cle)

    def _afficher_top5(self):
        if not self.valeurs:
            QMessageBox.information(self, "Top 5 zones", "Aucune donnée à afficher. Importez d'abord un fichier.")
            return
        items = sorted(
            self.valeurs.items(),
            key=lambda x: (x[1] if x[1] is not None and math.isfinite(x[1]) else float("-inf")),
            reverse=True,
        )
        top = items[:5]
        texte = "Top 5 zones par valeur :\n\n"
        for i, (cle, val) in enumerate(top, 1):
            texte += f"{i}. {self._nom_zone(cle)} : {formater_nombre(val)}\n"
        QMessageBox.information(self, "Top 5 zones", texte)

    def _afficher_statistiques(self):
        valeurs = [v for v in self.valeurs.values() if v is not None and math.isfinite(v)]
        if not valeurs:
            QMessageBox.information(self, "Statistiques spatiales", "Aucune donnée numérique.")
            return
        import statistics
        cle_max = max(self.valeurs, key=lambda k: self.valeurs[k] if (self.valeurs[k] is not None and math.isfinite(self.valeurs[k])) else float("-inf"))
        texte = (
            f"Nombre de zones : {len(valeurs)}\n"
            f"Moyenne : {formater_nombre(sum(valeurs) / len(valeurs))}\n"
            f"Médiane : {formater_nombre(statistics.median(valeurs))}\n"
            f"Minimum : {formater_nombre(min(valeurs))}\n"
            f"Maximum : {formater_nombre(max(valeurs))}\n"
            f"Écart-type : {formater_nombre(statistics.pstdev(valeurs))}\n\n"
            f"Zone la plus élevée : {self._nom_zone(cle_max)} ({formater_nombre(self.valeurs[cle_max])})"
        )
        QMessageBox.information(self, "Statistiques spatiales", texte)

    def _afficher_zones_risque(self):
        valeurs = [v for v in self.valeurs.values() if v is not None and math.isfinite(v)]
        if not valeurs:
            QMessageBox.information(self, "Zones à risque", "Aucune donnée numérique.")
            return
        seuil = sorted(valeurs)[int(0.75 * (len(valeurs) - 1))]
        zones = [(cle, v) for cle, v in self.valeurs.items() if v is not None and v >= seuil]
        zones.sort(key=lambda x: x[1], reverse=True)
        texte = f"Zones au-dessus du 75e percentile (seuil {formater_nombre(seuil)}) :\n\n"
        for cle, val in zones:
            texte += f"- {self._nom_zone(cle)} : {formater_nombre(val)}\n"
        if not zones:
            texte = "Aucune zone au-dessus du seuil."
        QMessageBox.information(self, "Zones à risque", texte)

    # ---- Rafraîchissement automatique ----

    def showEvent(self, evenement):
        """Rafraîchit la carte quand l'onglet SIG devient visible."""
        super().showEvent(evenement)
        if self._deja_affichee:
            self.actualiser_donnees()
        else:
            self._deja_affichee = True


def creer_page_sig(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import):
    """Crée la page SIG / cartographie du Mali."""
    return PageSIG(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import)
