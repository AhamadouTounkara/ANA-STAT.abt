"""Module Commerce — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Commerce": ["Commerce intérieur", "Commerce extérieur", "Importations", "Exportations", "Balance commerciale"],
    "Prix et ventes": ["Prix des produits", "Ventes par secteur", "Achats par secteur", "Chiffre d'affaires"],
    "Acteurs": ["Entreprises", "PME/PMI", "Marchés"],
    "Logistique": ["Stocks commerciaux", "Flux commerciaux"],
}

INDICATEURS_CONFIG = {
    "Commerce intérieur": {"colonnes": ["Catégorie", "Commerce intérieur"], "famille": "classement",
                            "mots_cles": {"Commerce intérieur": ["commerce interieur", "commerce intérieur"]}},
    "Commerce extérieur": {"colonnes": ["Catégorie", "Commerce extérieur"], "famille": "classement",
                            "mots_cles": {"Commerce extérieur": ["commerce exterieur", "commerce extérieur"]}},
    "Importations": {"colonnes": ["Catégorie", "Importations"], "famille": "classement",
                      "mots_cles": {"Importations": ["importation"]}},
    "Exportations": {"colonnes": ["Catégorie", "Exportations"], "famille": "classement",
                      "mots_cles": {"Exportations": ["exportation"]}},
    "Balance commerciale": {"colonnes": ["Catégorie", "Exportations", "Importations"], "famille": "solde",
                             "nom_resultat": "Balance commerciale",
                             "mots_cles": {"Exportations": ["exportation"], "Importations": ["importation"]}},
    "Prix des produits": {"colonnes": ["Produit", "Prix"], "famille": "classement",
                           "mots_cles": {"Prix": ["prix"]}},
    "Ventes par secteur": {"colonnes": ["Secteur", "Ventes"], "famille": "classement",
                            "mots_cles": {"Ventes": ["vente"]}},
    "Achats par secteur": {"colonnes": ["Secteur", "Achats"], "famille": "classement",
                            "mots_cles": {"Achats": ["achat"]}},
    "Chiffre d'affaires": {"colonnes": ["Catégorie", "Chiffre d'affaires"], "famille": "classement",
                            "mots_cles": {"Chiffre d'affaires": ["chiffre d'affaires", "chiffre affaires", "ca"]}},
    "Entreprises": {"colonnes": ["Catégorie", "Entreprises"], "famille": "classement",
                     "mots_cles": {"Entreprises": ["entreprise"]}},
    "PME/PMI": {"colonnes": ["Catégorie", "PME/PMI"], "famille": "classement",
                "mots_cles": {"PME/PMI": ["pme", "pmi"]}},
    "Marchés": {"colonnes": ["Catégorie", "Marchés"], "famille": "classement",
                "mots_cles": {"Marchés": ["marche", "marché"]}},
    "Stocks commerciaux": {"colonnes": ["Catégorie", "Stocks"], "famille": "classement",
                            "mots_cles": {"Stocks": ["stock"]}},
    "Flux commerciaux": {"colonnes": ["Catégorie", "Flux"], "famille": "classement",
                          "mots_cles": {"Flux": ["flux"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Douanes", "Entreprises", "Marchés", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Cercle": ["cercle"], "Commune": ["commune"], "Marché": ["marche", "marché"],
    "Entreprise": ["entreprise"], "Secteur": ["secteur"], "Produit": ["produit"], "Année": ["annee", "année"],
    "Trimestre": ["trimestre"], "Mois": ["mois", "month"], "Période": ["periode", "période"],
}


def creer_page_commerce(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Commerce, avec la même structure que Démographie."""
    return creer_page_module(
        "Commerce", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )