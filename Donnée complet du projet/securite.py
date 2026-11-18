import bcrypt
import time
import os
import json

FICHIER_JOURNAL = "journal_actions.txt"
DOSSIER_SAUVEGARDES = "sauvegardes_auto"
INTERVALLE_SAUVEGARDE = 300
DUREE_INACTIVITE_MAX = 300


# ---------- MOTS DE PASSE ----------

def hacher_mot_de_passe(mot_de_passe):
    """Transforme un mot de passe en clair en une version chiffrée (hachée)."""
    mot_de_passe_bytes = mot_de_passe.encode("utf-8")
    sel = bcrypt.gensalt()
    return bcrypt.hashpw(mot_de_passe_bytes, sel)


def verifier_mot_de_passe(mot_de_passe_saisi, mot_de_passe_hache):
    """Vérifie si le mot de passe saisi correspond au mot de passe haché stocké."""
    mot_de_passe_saisi_bytes = mot_de_passe_saisi.encode("utf-8")
    return bcrypt.checkpw(mot_de_passe_saisi_bytes, mot_de_passe_hache)


# ---------- BLOCAGE APRÈS TENTATIVES ----------

def initialiser_suivi_tentatives():
    """Crée un dictionnaire pour suivre les tentatives de chaque utilisateur."""
    return {}


def utilisateur_est_bloque(nom_utilisateur, suivi_tentatives, tentatives_max=3, duree_blocage=60):
    """Vérifie si un utilisateur est actuellement bloqué suite à trop d'échecs."""
    if nom_utilisateur not in suivi_tentatives:
        return False

    infos = suivi_tentatives[nom_utilisateur]

    if infos["echecs"] >= tentatives_max:
        temps_ecoule = time.time() - infos["dernier_echec"]
        if temps_ecoule < duree_blocage:
            return int(duree_blocage - temps_ecoule)
        else:
            suivi_tentatives[nom_utilisateur] = {"echecs": 0, "dernier_echec": 0}
            return False

    return False


def enregistrer_echec_connexion(nom_utilisateur, suivi_tentatives):
    """Enregistre une tentative de connexion échouée pour un utilisateur."""
    if nom_utilisateur not in suivi_tentatives:
        suivi_tentatives[nom_utilisateur] = {"echecs": 0, "dernier_echec": 0}

    suivi_tentatives[nom_utilisateur]["echecs"] += 1
    suivi_tentatives[nom_utilisateur]["dernier_echec"] = time.time()


def reinitialiser_tentatives(nom_utilisateur, suivi_tentatives):
    """Remet le compteur à zéro après une connexion réussie."""
    if nom_utilisateur in suivi_tentatives:
        suivi_tentatives[nom_utilisateur] = {"echecs": 0, "dernier_echec": 0}


# ---------- SESSIONS ----------

def demarrer_session(nom_utilisateur):
    """Crée une nouvelle session pour un utilisateur qui vient de se connecter."""
    return {
        "utilisateur": nom_utilisateur,
        "derniere_activite": time.time(),
        "active": True
    }


def mettre_a_jour_activite(session):
    """À appeler à chaque action de l'utilisateur pour dire 'je suis toujours là'."""
    session["derniere_activite"] = time.time()


def verifier_session_active(session):
    """Vérifie si la session a expiré à cause de l'inactivité."""
    if not session["active"]:
        return False

    temps_ecoule = time.time() - session["derniere_activite"]

    if temps_ecoule > DUREE_INACTIVITE_MAX:
        session["active"] = False
        return False

    return True


def deconnecter_session(session):
    """Termine manuellement une session."""
    session["active"] = False


# ---------- PERMISSIONS ----------

def definir_permissions():
    """Définit ce que chaque rôle a le droit de faire dans le logiciel."""
    return {
        "administrateur": [
            "importer", "nettoyer", "statistiques", "tests",
            "exporter", "gerer_comptes"
        ],
        "analyste": [
            "importer", "nettoyer", "statistiques", "tests", "exporter"
        ],
        "agent_saisie": [
            "importer", "nettoyer"
        ],
        "visiteur": [
            "consulter"
        ]
    }


def utilisateur_a_le_droit(role, action, permissions):
    """Vérifie si un rôle donné a le droit de faire une action précise."""
    if role not in permissions:
        return False
    return action in permissions[role]


# ---------- JOURNAL DES ACTIONS ----------

def enregistrer_action(nom_utilisateur, action):
    """Ajoute une ligne dans le journal à chaque action importante faite dans le logiciel."""
    horodatage = time.strftime("%Y-%m-%d %H:%M:%S")
    ligne = f"[{horodatage}] {nom_utilisateur} a fait : {action}\n"

    with open(FICHIER_JOURNAL, "a", encoding="utf-8") as fichier:
        fichier.write(ligne)


def lire_journal():
    """Lit et renvoie tout le contenu du journal."""
    if not os.path.exists(FICHIER_JOURNAL):
        return "Aucune action enregistrée pour le moment."

    with open(FICHIER_JOURNAL, "r", encoding="utf-8") as fichier:
        return fichier.read()


# ---------- SAUVEGARDE AUTOMATIQUE ----------

def initialiser_dossier_sauvegardes():
    """Crée le dossier de sauvegardes automatiques s'il n'existe pas encore."""
    if not os.path.exists(DOSSIER_SAUVEGARDES):
        os.makedirs(DOSSIER_SAUVEGARDES)


def sauvegarder_projet_auto(nom_utilisateur, donnees_projet):
    """Sauvegarde l'état actuel du projet dans un fichier horodaté."""
    initialiser_dossier_sauvegardes()
    horodatage = time.strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"{DOSSIER_SAUVEGARDES}/{nom_utilisateur}_{horodatage}.json"

    with open(nom_fichier, "w", encoding="utf-8") as fichier:
        json.dump(donnees_projet, fichier, ensure_ascii=False, indent=4)

    return nom_fichier


def temps_pour_sauvegarder(dernier_enregistrement):
    """Vérifie si le délai entre deux sauvegardes automatiques est écoulé."""
    temps_ecoule = time.time() - dernier_enregistrement
    return temps_ecoule >= INTERVALLE_SAUVEGARDE
