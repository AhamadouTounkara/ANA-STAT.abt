"""Palette de couleurs et constantes visuelles d'ANA-STAT.abt.

C'est la source unique des couleurs de l'application. Pour changer l'apparence
générale, il suffit de modifier les dictionnaires ci-dessous.
"""

COULEURS_CLAIR = {
    "bleu_nuit": "#14213D",       # navigation, éléments principaux
    "fond": "#F5F7FA",            # arrière-plan général
    "fond_widget": "#FFFFFF",     # fond des zones de contenu (cartes, tableaux...)
    "bleu_action": "#2563EB",     # boutons d'action principale
    "bleu_action_survol": "#1D4ED8",
    "vert_succes": "#16A34A",     # résultats / statistiques validés
    "orange_avertissement": "#F59E0B",
    "rouge_erreur": "#DC2626",
    "texte": "#1F2937",
    "texte_secondaire": "#6B7280",
    "bordure": "#E2E8F0",
}

COULEURS_SOMBRE = {
    "bleu_nuit": "#0B1220",
    "fond": "#111827",
    "fond_widget": "#1F2937",
    "bleu_action": "#3B82F6",
    "bleu_action_survol": "#60A5FA",
    "vert_succes": "#22C55E",
    "orange_avertissement": "#FBBF24",
    "rouge_erreur": "#F87171",
    "texte": "#E5E7EB",
    "texte_secondaire": "#9CA3AF",
    "bordure": "#374151",
}

POLICE = "Segoe UI"
RAYON_COINS = "9px"
MODE_PAR_DEFAUT = "clair"


def obtenir_palette(mode=MODE_PAR_DEFAUT):
    """Renvoie la palette de couleurs correspondant au mode demandé."""
    return COULEURS_SOMBRE if mode == "sombre" else COULEURS_CLAIR


def obtenir_couleur_statut(type_message, mode=MODE_PAR_DEFAUT):
    """Renvoie la couleur associée à un type de message (succès/avertissement/erreur)."""
    palette = obtenir_palette(mode)
    correspondance = {
        "succes": palette["vert_succes"],
        "avertissement": palette["orange_avertissement"],
        "erreur": palette["rouge_erreur"],
    }
    return correspondance.get(type_message, palette["texte"])
