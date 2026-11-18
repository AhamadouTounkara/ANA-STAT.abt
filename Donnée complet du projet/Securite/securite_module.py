"""Module Sécurité — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Accidents et sécurité routière": ["Accidents de la route", "Sécurité routière"],
    "Criminalité": ["Criminalité", "Vols", "Cambriolages"],
    "Incidents et catastrophes": ["Incendies", "Catastrophes naturelles", "Gestion des risques"],
    "Interventions": ["Interventions des services de secours", "Statistiques des interventions"],
    "Analyse": ["Cartographie des incidents", "Tendances des incidents"],
}

INDICATEURS_CONFIG = {
    "Accidents de la route": {"colonnes": ["Catégorie", "Accidents"], "famille": "classement",
                               "mots_cles": {"Accidents": ["accident"]}},
    "Sécurité routière": {"colonnes": ["Catégorie", "Indicateur"], "famille": "classement",
                           "mots_cles": {"Indicateur": ["securite routiere", "sécurité routière"]}},
    "Criminalité": {"colonnes": ["Catégorie", "Cas"], "famille": "classement",
                     "mots_cles": {"Cas": ["criminalite", "criminalité", "crime"]}},
    "Vols": {"colonnes": ["Catégorie", "Vols"], "famille": "classement",
             "mots_cles": {"Vols": ["vol"]}},
    "Cambriolages": {"colonnes": ["Catégorie", "Cambriolages"], "famille": "classement",
                      "mots_cles": {"Cambriolages": ["cambriolage"]}},
    "Incendies": {"colonnes": ["Catégorie", "Incendies"], "famille": "classement",
                   "mots_cles": {"Incendies": ["incendie"]}},
    "Catastrophes naturelles": {"colonnes": ["Catégorie", "Catastrophes"], "famille": "classement",
                                 "mots_cles": {"Catastrophes": ["catastrophe"]}},
    "Gestion des risques": {"colonnes": ["Catégorie", "Indice de risque"], "famille": "classement",
                             "mots_cles": {"Indice de risque": ["risque"]}},
    "Interventions des services de secours": {"colonnes": ["Catégorie", "Interventions"], "famille": "classement",
                                                "mots_cles": {"Interventions": ["intervention"]}},
    "Statistiques des interventions": {"colonnes": ["Catégorie", "Interventions"], "famille": "classement",
                                        "mots_cles": {"Interventions": ["intervention"]}},
    "Cartographie des incidents": {"colonnes": ["Catégorie", "Incidents"], "famille": "classement",
                                    "mots_cles": {"Incidents": ["incident"]}},
    "Tendances des incidents": {"colonnes": ["Catégorie", "Incidents"], "famille": "classement",
                                 "mots_cles": {"Incidents": ["incident"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Police", "Gendarmerie", "Protection civile", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Cercle": ["cercle"], "Commune": ["commune"], "Quartier": ["quartier"],
    "Type d'incident": ["type d'incident"], "Année": ["annee", "année"], "Mois": ["mois", "month"],
    "Heure": ["heure"], "Période": ["periode", "période"],
}


def creer_page_securite(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Sécurité, avec la même structure que Démographie."""
    return creer_page_module(
        "Sécurité", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )