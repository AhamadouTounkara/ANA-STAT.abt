import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
)

QUESTIONS_SECRETES = [
    "Quel est le nom de ta ville natale ?",
    "Quel est le prénom de ton premier enseignant ?",
    "Quel est ton plat préféré ?",
    "Quel est le nom de ton animal préféré ?"
]
from securite import (
    hacher_mot_de_passe, verifier_mot_de_passe,
    initialiser_suivi_tentatives, utilisateur_est_bloque,
    enregistrer_echec_connexion, reinitialiser_tentatives,
    enregistrer_action
)

FICHIER_UTILISATEURS = "utilisateurs.json"


# ---------- GESTION DES COMPTES ----------

def charger_utilisateurs():
    """Charge la liste des comptes depuis le fichier JSON, ou en crée une vide."""
    if not os.path.exists(FICHIER_UTILISATEURS):
        return {}
    with open(FICHIER_UTILISATEURS, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def sauvegarder_utilisateurs(utilisateurs):
    """Enregistre la liste des comptes dans le fichier JSON."""
    with open(FICHIER_UTILISATEURS, "w", encoding="utf-8") as fichier:
        json.dump(utilisateurs, fichier, ensure_ascii=False, indent=4)


def creer_compte_si_absent(utilisateurs, nom, mot_de_passe, role):
    """Crée un compte de test s'il n'existe pas déjà."""
    if nom not in utilisateurs:
        mdp_hache = hacher_mot_de_passe(mot_de_passe)
        reponse_hachee = hacher_mot_de_passe("bamako")
        utilisateurs[nom] = {
            "mot_de_passe_hache": mdp_hache.decode("utf-8"),
            "role": role,
            "question_secrete": "Quel est le nom de ta ville natale ?",
            "reponse_secrete_hachee": reponse_hachee.decode("utf-8")
        }
        sauvegarder_utilisateurs(utilisateurs)


def compte_existe_deja(utilisateurs, nom):
    """Vérifie si un nom d'utilisateur est déjà pris."""
    return nom in utilisateurs


def creer_nouveau_compte(utilisateurs, nom, mot_de_passe, role, question_secrete, reponse_secrete):
    """Crée un nouveau compte utilisateur avec mot de passe haché, et sauvegarde."""
    mdp_hache = hacher_mot_de_passe(mot_de_passe)
    reponse_hachee = hacher_mot_de_passe(reponse_secrete.lower().strip())
    utilisateurs[nom] = {
        "mot_de_passe_hache": mdp_hache.decode("utf-8"),
        "role": role,
        "question_secrete": question_secrete,
        "reponse_secrete_hachee": reponse_hachee.decode("utf-8")
    }
    sauvegarder_utilisateurs(utilisateurs)


def obtenir_question_secrete(utilisateurs, nom):
    """Renvoie la question secrète d'un utilisateur, ou None s'il n'existe pas."""
    if nom not in utilisateurs:
        return None
    return utilisateurs[nom].get("question_secrete")


def verifier_reponse_secrete(utilisateurs, nom, reponse_saisie):
    """Vérifie si la réponse saisie correspond à la réponse secrète enregistrée."""
    if nom not in utilisateurs:
        return False
    reponse_hachee_stockee = utilisateurs[nom]["reponse_secrete_hachee"].encode("utf-8")
    return verifier_mot_de_passe(reponse_saisie.lower().strip(), reponse_hachee_stockee)


def reinitialiser_mot_de_passe(utilisateurs, nom, nouveau_mot_de_passe):
    """Remplace le mot de passe d'un utilisateur par un nouveau, après vérification de la réponse secrète."""
    nouveau_hache = hacher_mot_de_passe(nouveau_mot_de_passe)
    utilisateurs[nom]["mot_de_passe_hache"] = nouveau_hache.decode("utf-8")
    sauvegarder_utilisateurs(utilisateurs)


def tenter_connexion(nom, mot_de_passe_saisi, utilisateurs, suivi_tentatives):
    """Vérifie les identifiants en tenant compte du blocage après tentatives échouées."""
    if nom not in utilisateurs:
        return False, "Utilisateur inconnu."

    blocage = utilisateur_est_bloque(nom, suivi_tentatives)
    if blocage:
        return False, f"Compte bloqué, réessaie dans {blocage} secondes."

    mdp_hache_stocke = utilisateurs[nom]["mot_de_passe_hache"].encode("utf-8")

    if verifier_mot_de_passe(mot_de_passe_saisi, mdp_hache_stocke):
        reinitialiser_tentatives(nom, suivi_tentatives)
        enregistrer_action(nom, "connexion réussie")
        return True, utilisateurs[nom]["role"]
    else:
        enregistrer_echec_connexion(nom, suivi_tentatives)
        enregistrer_action(nom, "tentative de connexion échouée")
        return False, "Mot de passe incorrect."


# ---------- FENÊTRE D'INSCRIPTION ----------

def creer_fenetre_inscription(utilisateurs, on_compte_cree):
    """Crée la fenêtre d'inscription pour un nouveau compte."""
    fenetre = QWidget()
    fenetre.setWindowTitle("ANA-STAT.abt - Créer un compte")
    fenetre.setFixedSize(350, 280)

    layout = QVBoxLayout()

    titre = QLabel("Créer un compte")
    champ_nom = QLineEdit()
    champ_nom.setPlaceholderText("Nom d'utilisateur")
    champ_mdp = QLineEdit()
    champ_mdp.setPlaceholderText("Mot de passe")
    champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
    champ_mdp_confirmation = QLineEdit()
    champ_mdp_confirmation.setPlaceholderText("Confirmer le mot de passe")
    champ_mdp_confirmation.setEchoMode(QLineEdit.EchoMode.Password)
    liste_question = QComboBox()
    liste_question.addItems(QUESTIONS_SECRETES)
    champ_reponse = QLineEdit()
    champ_reponse.setPlaceholderText("Réponse à la question secrète")
    bouton_creer = QPushButton("Créer le compte")

    def gerer_creation():
        nom = champ_nom.text().strip()
        mdp = champ_mdp.text()
        mdp_confirmation = champ_mdp_confirmation.text()
        question = liste_question.currentText()
        reponse = champ_reponse.text().strip()

        if nom == "" or mdp == "" or reponse == "":
            QMessageBox.warning(fenetre, "Erreur", "Tous les champs sont obligatoires, y compris la réponse secrète.")
            return

        if compte_existe_deja(utilisateurs, nom):
            QMessageBox.warning(fenetre, "Erreur", "Ce nom d'utilisateur existe déjà.")
            return

        if mdp != mdp_confirmation:
            QMessageBox.warning(fenetre, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        if len(mdp) < 6:
            QMessageBox.warning(fenetre, "Erreur", "Le mot de passe doit contenir au moins 6 caractères.")
            return

        creer_nouveau_compte(utilisateurs, nom, mdp, "visiteur", question, reponse)
        enregistrer_action(nom, "création de compte")
        QMessageBox.information(fenetre, "Compte créé", f"Le compte '{nom}' a été créé avec succès.")
        fenetre.close()
        on_compte_cree()

    bouton_creer.clicked.connect(gerer_creation)

    layout.addWidget(titre)
    layout.addWidget(champ_nom)
    layout.addWidget(champ_mdp)
    layout.addWidget(champ_mdp_confirmation)
    layout.addWidget(QLabel("Question secrète (pour récupérer ton compte plus tard) :"))
    layout.addWidget(liste_question)
    layout.addWidget(champ_reponse)
    layout.addWidget(bouton_creer)
    fenetre.setLayout(layout)

    return fenetre


# ---------- FENÊTRE MOT DE PASSE OUBLIÉ ----------

def creer_fenetre_recuperation(utilisateurs):
    """Crée la fenêtre en 2 étapes pour récupérer l'accès à un compte via la question secrète."""
    fenetre = QWidget()
    fenetre.setWindowTitle("ANA-STAT.abt - Mot de passe oublié")
    fenetre.setFixedSize(350, 250)

    layout = QVBoxLayout()

    titre = QLabel("Récupération de compte")
    champ_nom = QLineEdit()
    champ_nom.setPlaceholderText("Nom d'utilisateur")
    bouton_valider_nom = QPushButton("Continuer")

    label_question = QLabel("")
    label_question.setVisible(False)
    champ_reponse = QLineEdit()
    champ_reponse.setPlaceholderText("Ta réponse")
    champ_reponse.setVisible(False)
    champ_nouveau_mdp = QLineEdit()
    champ_nouveau_mdp.setPlaceholderText("Nouveau mot de passe")
    champ_nouveau_mdp.setEchoMode(QLineEdit.EchoMode.Password)
    champ_nouveau_mdp.setVisible(False)
    bouton_reinitialiser = QPushButton("Réinitialiser le mot de passe")
    bouton_reinitialiser.setVisible(False)

    def gerer_validation_nom():
        nom = champ_nom.text().strip()
        question = obtenir_question_secrete(utilisateurs, nom)

        if question is None:
            QMessageBox.warning(fenetre, "Erreur", "Utilisateur inconnu.")
            return

        label_question.setText(question)
        label_question.setVisible(True)
        champ_reponse.setVisible(True)
        champ_nouveau_mdp.setVisible(True)
        bouton_reinitialiser.setVisible(True)
        champ_nom.setEnabled(False)
        bouton_valider_nom.setEnabled(False)

    def gerer_reinitialisation():
        nom = champ_nom.text().strip()
        reponse = champ_reponse.text()
        nouveau_mdp = champ_nouveau_mdp.text()

        if not verifier_reponse_secrete(utilisateurs, nom, reponse):
            QMessageBox.warning(fenetre, "Erreur", "Réponse incorrecte.")
            return

        if len(nouveau_mdp) < 6:
            QMessageBox.warning(fenetre, "Erreur", "Le nouveau mot de passe doit contenir au moins 6 caractères.")
            return

        reinitialiser_mot_de_passe(utilisateurs, nom, nouveau_mdp)
        enregistrer_action(nom, "réinitialisation du mot de passe")
        QMessageBox.information(fenetre, "Succès", "Mot de passe réinitialisé. Tu peux te reconnecter.")
        fenetre.close()

    bouton_valider_nom.clicked.connect(gerer_validation_nom)
    bouton_reinitialiser.clicked.connect(gerer_reinitialisation)

    layout.addWidget(titre)
    layout.addWidget(champ_nom)
    layout.addWidget(bouton_valider_nom)
    layout.addWidget(label_question)
    layout.addWidget(champ_reponse)
    layout.addWidget(champ_nouveau_mdp)
    layout.addWidget(bouton_reinitialiser)
    fenetre.setLayout(layout)

    return fenetre


# ---------- FENÊTRE DE CONNEXION ----------

def creer_fenetre_connexion(on_connexion_reussie):
    """Crée la fenêtre de connexion. on_connexion_reussie est appelée avec (nom, role) si ça marche."""
    utilisateurs = charger_utilisateurs()
    creer_compte_si_absent(utilisateurs, "ahamadou", "Bamako2026", "administrateur")
    suivi_tentatives = initialiser_suivi_tentatives()

    fenetre = QWidget()
    fenetre.setWindowTitle("ANA-STAT.abt - Connexion")
    fenetre.setFixedSize(350, 300)

    layout = QVBoxLayout()

    titre = QLabel("Connexion à ANA-STAT.abt")
    champ_nom = QLineEdit()
    champ_nom.setPlaceholderText("Nom d'utilisateur")
    champ_mdp = QLineEdit()
    champ_mdp.setPlaceholderText("Mot de passe")
    champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
    bouton_connexion = QPushButton("Se connecter")
    bouton_inscription = QPushButton("Créer un compte")
    bouton_mdp_oublie = QPushButton("Mot de passe oublié ?")

    def gerer_clic():
        nom = champ_nom.text()
        mdp = champ_mdp.text()
        succes, resultat = tenter_connexion(nom, mdp, utilisateurs, suivi_tentatives)

        if succes:
            fenetre.close()
            on_connexion_reussie(nom, resultat)
        else:
            QMessageBox.warning(fenetre, "Échec de connexion", resultat)

    def gerer_ouverture_inscription():
        def apres_creation_compte():
            utilisateurs.update(charger_utilisateurs())

        fenetre_inscription = creer_fenetre_inscription(utilisateurs, apres_creation_compte)
        fenetre_inscription.show()
        fenetre.fenetre_inscription_ouverte = fenetre_inscription

    def gerer_ouverture_recuperation():
        fenetre_recuperation = creer_fenetre_recuperation(utilisateurs)
        fenetre_recuperation.show()
        fenetre.fenetre_recuperation_ouverte = fenetre_recuperation

    bouton_connexion.clicked.connect(gerer_clic)
    bouton_inscription.clicked.connect(gerer_ouverture_inscription)
    bouton_mdp_oublie.clicked.connect(gerer_ouverture_recuperation)

    layout.addWidget(titre)
    layout.addWidget(champ_nom)
    layout.addWidget(champ_mdp)
    layout.addWidget(bouton_connexion)
    layout.addWidget(bouton_inscription)
    layout.addWidget(bouton_mdp_oublie)
    fenetre.setLayout(layout)

    return fenetre
