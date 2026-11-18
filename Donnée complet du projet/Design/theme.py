"""Génération et application de la feuille de style Qt (QSS) d'ANA-STAT.abt."""

from .couleurs import (
    COULEURS_CLAIR,
    COULEURS_SOMBRE,
    MODE_PAR_DEFAUT,
    POLICE,
    RAYON_COINS,
    obtenir_couleur_statut,
    obtenir_palette,
)


def generer_feuille_style(mode=MODE_PAR_DEFAUT):
    """Génère la feuille de style Qt (QSS) complète pour le mode demandé ('clair' ou 'sombre')."""
    c = obtenir_palette(mode)

    return f"""
    /* ---- Base ---- */
    QWidget {{
        background-color: {c['fond']};
        color: {c['texte']};
        font-family: "{POLICE}";
        font-size: 10.5pt;
    }}

    QMainWindow {{
        background-color: {c['fond']};
    }}

    /* ---- Titres de section ---- */
    QLabel#titreSection {{
        font-weight: bold;
        font-size: 13px;
    }}

    /* ---- Boutons ---- */
    QPushButton {{
        background-color: {c['bleu_action']};
        color: white;
        border: none;
        border-radius: {RAYON_COINS};
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        background-color: {c['bleu_action_survol']};
    }}
    QPushButton:disabled {{
        background-color: {c['bordure']};
        color: {c['texte_secondaire']};
    }}

    /* Boutons du menu latéral : bleu nuit, look "navigation" distinct des boutons d'action */
    QPushButton#boutonMenuLateral {{
        background-color: {c['bleu_nuit']};
        color: white;
        text-align: left;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 2px 4px;
    }}
    QPushButton#boutonMenuLateral:hover {{
        background-color: {c['bleu_action']};
    }}
    QPushButton#boutonMenuLateral:disabled {{
        background-color: transparent;
        color: {c['texte_secondaire']};
    }}

    /* ---- Onglets ---- */
    QTabWidget::pane {{
        border: 1px solid {c['bordure']};
        border-radius: {RAYON_COINS};
        background-color: {c['fond_widget']};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {c['fond']};
        color: {c['texte_secondaire']};
        padding: 7px 16px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['fond_widget']};
        color: {c['bleu_action']};
        font-weight: bold;
        border: 1px solid {c['bordure']};
        border-bottom: none;
    }}

    /* ---- Cadres, groupes ---- */
    QGroupBox {{
        background-color: {c['fond_widget']};
        border: 1px solid {c['bordure']};
        border-radius: {RAYON_COINS};
        margin-top: 12px;
        padding-top: 10px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {c['bleu_nuit']};
    }}
    QFrame {{
        border-radius: {RAYON_COINS};
    }}

    /* ---- Champs de saisie ---- */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {c['fond_widget']};
        border: 1px solid {c['bordure']};
        border-radius: 6px;
        padding: 4px 8px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {c['bleu_action']};
    }}

    /* ---- Tableaux et arborescences ---- */
    QTableWidget, QTreeWidget {{
        background-color: {c['fond_widget']};
        alternate-background-color: {c['fond']};
        border: 1px solid {c['bordure']};
        border-radius: 6px;
        gridline-color: {c['bordure']};
    }}
    QHeaderView::section {{
        background-color: {c['bleu_nuit']};
        color: white;
        padding: 5px;
        border: none;
    }}

    /* ---- Barres de défilement ---- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['bordure']};
        border-radius: 5px;
        min-height: 20px;
    }}

    /* ---- Boîtes de dialogue ---- */
    QDialog {{
        background-color: {c['fond']};
    }}
    QMessageBox {{
        background-color: {c['fond_widget']};
    }}
    """


def appliquer_theme(app, mode=MODE_PAR_DEFAUT):
    """Applique la feuille de style à une QApplication (ou à l'instance courante)."""
    if app is not None:
        app.setStyleSheet(generer_feuille_style(mode))
