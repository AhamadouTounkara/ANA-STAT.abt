"""Module Agriculture — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Production": ["Productions agricoles", "Superficies cultivées", "Cultures", "Rendements"],
    "Élevage et pêche": ["Élevage", "Pêche"],
    "Cultures spécialisées": ["Maraîchage", "Arboriculture"],
    "Intrants": ["Utilisation des engrais", "Irrigation"],
    "Marché et sécurité alimentaire": ["Prix des produits agricoles", "Stocks alimentaires",
                                        "Sécurité alimentaire", "Prévisions des récoltes"],
}

INDICATEURS_CONFIG = {
    "Productions agricoles": {"colonnes": ["Catégorie", "Production"], "famille": "classement",
                               "mots_cles": {"Production": ["production"]}},
    "Superficies cultivées": {"colonnes": ["Catégorie", "Superficie"], "famille": "classement",
                               "mots_cles": {"Superficie": ["superficie", "area"]}},
    "Cultures": {"colonnes": ["Culture", "Production"], "famille": "classement",
                 "mots_cles": {"Production": ["culture", "production"]}},
    "Rendements": {"colonnes": ["Catégorie", "Production", "Superficie"], "famille": "densite",
                    "mots_cles": {"Production": ["production"], "Superficie": ["superficie", "area"]}},
    "Élevage": {"colonnes": ["Catégorie", "Cheptel"], "famille": "classement",
                "mots_cles": {"Cheptel": ["elevage", "élevage", "cheptel", "betail", "bétail"]}},
    "Pêche": {"colonnes": ["Catégorie", "Production halieutique"], "famille": "classement",
              "mots_cles": {"Production halieutique": ["peche", "pêche"]}},
    "Maraîchage": {"colonnes": ["Catégorie", "Production maraîchère"], "famille": "classement",
                    "mots_cles": {"Production maraîchère": ["maraichage", "maraîchage"]}},
    "Arboriculture": {"colonnes": ["Catégorie", "Production arboricole"], "famille": "classement",
                       "mots_cles": {"Production arboricole": ["arboriculture", "verger"]}},
    "Utilisation des engrais": {"colonnes": ["Catégorie", "Engrais utilisés"], "famille": "classement",
                                 "mots_cles": {"Engrais utilisés": ["engrais"]}},
    "Irrigation": {"colonnes": ["Catégorie", "Superficie irriguée"], "famille": "classement",
                    "mots_cles": {"Superficie irriguée": ["irrigation"]}},
    "Prix des produits agricoles": {"colonnes": ["Produit", "Prix"], "famille": "classement",
                                     "mots_cles": {"Prix": ["prix"]}},
    "Stocks alimentaires": {"colonnes": ["Catégorie", "Stocks"], "famille": "classement",
                             "mots_cles": {"Stocks": ["stock"]}},
    "Sécurité alimentaire": {"colonnes": ["Catégorie", "Indice de sécurité alimentaire"], "famille": "classement",
                              "mots_cles": {"Indice de sécurité alimentaire": ["securite alimentaire",
                                                                                "sécurité alimentaire"]}},
    "Prévisions des récoltes": {"colonnes": ["Catégorie", "Production passée", "Production récente",
                                              "Écart (années)", "Projection (+ années)"], "famille": "projection",
                                 "mots_cles": {"Production récente": ["production"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Coopératives", "Capteurs", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Cercle": ["cercle"], "Commune": ["commune"], "Village": ["village"],
    "Exploitation": ["exploitation"], "Culture": ["culture"], "Campagne agricole": ["campagne"],
    "Saison": ["saison"], "Année": ["annee", "année", "year"],
}


def creer_page_agriculture(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Agriculture, avec la même structure que Démographie."""
    return creer_page_module(
        "Agriculture", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )