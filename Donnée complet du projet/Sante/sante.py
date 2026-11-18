"""Module Santé — utilise le moteur générique partagé (ModuleGenerique/module_generique.py)."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Morbidité et mortalité": ["Morbidité", "Mortalité", "Incidence", "Prévalence"],
    "Vaccination": ["Vaccination"],
    "Santé maternelle et infantile": ["Santé maternelle", "Santé infantile", "Nutrition"],
    "Maladies": ["Maladies transmissibles", "Maladies non transmissibles", "Épidémiologie"],
    "Services de santé": ["Hospitalisations", "Consultations"],
}

INDICATEURS_CONFIG = {
    "Morbidité": {"colonnes": ["Catégorie", "Cas", "Population"], "famille": "taux",
                  "facteur": 1000, "nom_taux": "Morbidité (‰)",
                  "mots_cles": {"Cas": ["cas", "morbidite", "morbidité"], "Population": ["population"]}},
    "Mortalité": {"colonnes": ["Catégorie", "Décès", "Population"], "famille": "taux",
                  "facteur": 1000, "nom_taux": "Mortalité (‰)",
                  "mots_cles": {"Décès": ["deces", "décès", "death"], "Population": ["population"]}},
    "Incidence": {"colonnes": ["Catégorie", "Nouveaux cas", "Population"], "famille": "taux",
                  "facteur": 1000, "nom_taux": "Incidence (‰)",
                  "mots_cles": {"Nouveaux cas": ["incidence"], "Population": ["population"]}},
    "Prévalence": {"colonnes": ["Catégorie", "Cas existants", "Population"], "famille": "taux",
                   "facteur": 1000, "nom_taux": "Prévalence (‰)",
                   "mots_cles": {"Cas existants": ["prevalence", "prévalence"], "Population": ["population"]}},
    "Vaccination": {"colonnes": ["Catégorie", "Vaccinés", "Population cible"], "famille": "taux",
                    "facteur": 100, "nom_taux": "Couverture vaccinale (%)",
                    "mots_cles": {"Vaccinés": ["vaccin"], "Population cible": ["population"]}},
    "Santé maternelle": {"colonnes": ["Catégorie", "Décès maternels", "Naissances vivantes"], "famille": "taux",
                          "facteur": 100000, "nom_taux": "Mortalité maternelle (pour 100 000)",
                          "mots_cles": {"Décès maternels": ["maternelle", "maternel"],
                                        "Naissances vivantes": ["naissance"]}},
    "Santé infantile": {"colonnes": ["Catégorie", "Décès infantiles", "Naissances vivantes"], "famille": "taux",
                         "facteur": 1000, "nom_taux": "Mortalité infantile (‰)",
                         "mots_cles": {"Décès infantiles": ["infantile", "nourrisson"],
                                       "Naissances vivantes": ["naissance"]}},
    "Nutrition": {"colonnes": ["Catégorie", "Cas de malnutrition", "Population cible"], "famille": "taux",
                  "facteur": 1000, "nom_taux": "Taux de malnutrition (‰)",
                  "mots_cles": {"Cas de malnutrition": ["nutrition", "malnutrition", "imc"],
                                "Population cible": ["population"]}},
    "Maladies transmissibles": {"colonnes": ["Catégorie", "Cas", "Population"], "famille": "taux",
                                 "facteur": 1000, "nom_taux": "Taux (‰)",
                                 "mots_cles": {"Cas": ["transmissible"], "Population": ["population"]}},
    "Maladies non transmissibles": {"colonnes": ["Catégorie", "Cas", "Population"], "famille": "taux",
                                     "facteur": 1000, "nom_taux": "Taux (‰)",
                                     "mots_cles": {"Cas": ["non transmissible", "chronique"],
                                                   "Population": ["population"]}},
    "Épidémiologie": {"colonnes": ["Catégorie", "Cas", "Population"], "famille": "taux",
                       "facteur": 1000, "nom_taux": "Taux (‰)",
                       "mots_cles": {"Cas": ["epidemi", "épidémi"], "Population": ["population"]}},
    "Hospitalisations": {"colonnes": ["Catégorie", "Hospitalisations", "Population"], "famille": "taux",
                          "facteur": 1000, "nom_taux": "Taux d'hospitalisation (‰)",
                          "mots_cles": {"Hospitalisations": ["hospitalisation", "hospitalise"],
                                        "Population": ["population"]}},
    "Consultations": {"colonnes": ["Catégorie", "Consultations", "Population"], "famille": "taux",
                       "facteur": 1000, "nom_taux": "Taux de consultation (‰)",
                       "mots_cles": {"Consultations": ["consultation"], "Population": ["population"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Hôpital", "Centre de santé", "Enquête", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "District": ["district"], "Commune": ["commune"],
    "Structure sanitaire": ["structure", "hopital", "hôpital"], "Sexe": ["sexe", "sex"],
    "Âge": ["age", "âge"], "Maladie": ["maladie", "disease"], "Année": ["annee", "année", "year"],
    "Mois": ["mois", "month"], "Période": ["periode", "période"],
}


def creer_page_sante(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Santé, avec la même structure que Démographie."""
    return creer_page_module(
        "Santé", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )