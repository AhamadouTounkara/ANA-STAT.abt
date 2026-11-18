"""Composants d'interface réutilisables d'ANA-STAT.abt.

Ces widgets sont partagés par les différentes fenêtres du logiciel. Ils ne
contiennent pas de logique métier : uniquement de la présentation.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


def creer_pied_de_page(version, mode_test=False):
    """Crée le pied de page commun : version, licence, support et état de connexion.

    mode_test=True affiche « Mode test — sans connexion » au lieu de l'état
    normal, pour distinguer clairement le lancement par ABT.py.
    """
    pied = QFrame()
    pied.setFixedHeight(25)
    layout = QHBoxLayout()
    layout.setContentsMargins(10, 0, 10, 0)

    label_version = QLabel(version)
    label_licence = QLabel("Licence : usage personnel")
    label_support = QLabel("Support : à venir")
    texte_connexion = (
        "🟢 Mode test — sans connexion" if mode_test else "🟢 Connecté en local"
    )
    label_connexion = QLabel(texte_connexion)

    layout.addWidget(label_version)
    layout.addWidget(label_licence)
    layout.addWidget(label_support)
    layout.addStretch()
    layout.addWidget(label_connexion)

    pied.setLayout(layout)
    return pied


def creer_titre_section(texte):
    """Crée un titre de section avec le style visuel commun."""
    titre = QLabel(texte)
    titre.setObjectName("titreSection")
    return titre
