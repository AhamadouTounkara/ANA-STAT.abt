"""Compatibilité : le thème visuel est désormais dans ``Design.theme``.

Ce module est conservé pour les anciens imports ``from Assets.theme import ...``.
Le code actif se trouve dans le dossier ``Design/``.
"""

from Design.couleurs import (  # noqa: F401
    COULEURS_CLAIR,
    COULEURS_SOMBRE,
    MODE_PAR_DEFAUT,
    POLICE,
    RAYON_COINS,
    obtenir_couleur_statut,
    obtenir_palette,
)
from Design.theme import appliquer_theme, generer_feuille_style  # noqa: F401

__all__ = [
    "COULEURS_CLAIR",
    "COULEURS_SOMBRE",
    "MODE_PAR_DEFAUT",
    "POLICE",
    "RAYON_COINS",
    "obtenir_couleur_statut",
    "obtenir_palette",
    "generer_feuille_style",
    "appliquer_theme",
]
