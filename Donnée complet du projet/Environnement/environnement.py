"""Module Environnement — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Climat": ["Température", "Pluviométrie", "Humidité"],
    "Qualité": ["Qualité de l'air", "Qualité de l'eau"],
    "Ressources naturelles": ["Déforestation", "Reboisement", "Biodiversité", "Désertification", "Érosion des sols"],
    "Pollution et risques": ["Gestion des déchets", "Émissions de gaz à effet de serre",
                              "Catastrophes naturelles", "Changements climatiques"],
}

INDICATEURS_CONFIG = {
    "Température": {"colonnes": ["Catégorie", "Température (°C)"], "famille": "classement",
                     "mots_cles": {"Température (°C)": ["temperature", "température"]}},
    "Pluviométrie": {"colonnes": ["Catégorie", "Précipitations (mm)"], "famille": "classement",
                      "mots_cles": {"Précipitations (mm)": ["pluviometrie", "pluviométrie", "pluie"]}},
    "Humidité": {"colonnes": ["Catégorie", "Humidité (%)"], "famille": "classement",
                 "mots_cles": {"Humidité (%)": ["humidite", "humidité"]}},
    "Qualité de l'air": {"colonnes": ["Catégorie", "Indice de qualité de l'air"], "famille": "classement",
                          "mots_cles": {"Indice de qualité de l'air": ["qualite de l'air", "qualité de l'air"]}},
    "Qualité de l'eau": {"colonnes": ["Catégorie", "Indice de qualité de l'eau"], "famille": "classement",
                          "mots_cles": {"Indice de qualité de l'eau": ["qualite de l'eau", "qualité de l'eau"]}},
    "Déforestation": {"colonnes": ["Catégorie", "Surface déforestée (ha)"], "famille": "classement",
                       "mots_cles": {"Surface déforestée (ha)": ["deforestation", "déforestation"]}},
    "Reboisement": {"colonnes": ["Catégorie", "Surface reboisée (ha)"], "famille": "classement",
                     "mots_cles": {"Surface reboisée (ha)": ["reboisement"]}},
    "Biodiversité": {"colonnes": ["Catégorie", "Indice de biodiversité"], "famille": "classement",
                      "mots_cles": {"Indice de biodiversité": ["biodiversite", "biodiversité"]}},
    "Désertification": {"colonnes": ["Catégorie", "Surface touchée (ha)"], "famille": "classement",
                         "mots_cles": {"Surface touchée (ha)": ["desertification", "désertification"]}},
    "Érosion des sols": {"colonnes": ["Catégorie", "Surface érodée (ha)"], "famille": "classement",
                          "mots_cles": {"Surface érodée (ha)": ["erosion", "érosion"]}},
    "Gestion des déchets": {"colonnes": ["Catégorie", "Déchets (tonnes)"], "famille": "classement",
                             "mots_cles": {"Déchets (tonnes)": ["dechet", "déchet"]}},
    "Émissions de gaz à effet de serre": {"colonnes": ["Catégorie", "Émissions (tonnes CO2)"],
                                           "famille": "classement",
                                           "mots_cles": {"Émissions (tonnes CO2)": ["emission", "émission", "co2"]}},
    "Catastrophes naturelles": {"colonnes": ["Catégorie", "Catastrophes"], "famille": "classement",
                                 "mots_cles": {"Catastrophes": ["catastrophe"]}},
    "Changements climatiques": {"colonnes": ["Catégorie", "Indice climatique"], "famille": "classement",
                                 "mots_cles": {"Indice climatique": ["climat"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Stations météo", "Capteurs", "Satellite", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Cercle": ["cercle"], "Commune": ["commune"], "Site": ["site"],
    "Écosystème": ["ecosysteme", "écosystème"], "Année": ["annee", "année", "year"],
    "Mois": ["mois", "month"], "Période": ["periode", "période"],
}


def creer_page_environnement(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Environnement, avec la même structure que Démographie."""
    return creer_page_module(
        "Environnement", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )