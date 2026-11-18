"""ANA-STAT.abt — point d'entrée NORMAL (avec connexion).

Ce fichier affiche d'abord l'écran de connexion, puis le tableau de bord.
Pour tester sans connexion, lancer ABT.py.
"""

import os
import sys
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
from authentification import creer_fenetre_connexion
from tableau_bord import creer_fenetre_tableau_de_bord
from Design.theme import appliquer_theme


def gerer_erreur_non_prevue(type_erreur, valeur_erreur, trace):
    """Affiche toute erreur non prévue dans une fenêtre au lieu de fermer le programme silencieusement."""
    message_complet = "".join(traceback.format_exception(type_erreur, valeur_erreur, trace))
    print(message_complet)  # reste aussi visible dans le terminal, pour copier-coller facilement
    try:
        import os as _os
        with open(_os.path.join(_os.getcwd(), "erreur_ana_stat.log"), "w", encoding="utf-8") as _f:
            _f.write(message_complet)
    except Exception:
        pass
    boite = QMessageBox()
    boite.setIcon(QMessageBox.Icon.Critical)
    boite.setWindowTitle("Erreur inattendue")
    boite.setText(f"Une erreur est survenue :\n\n{valeur_erreur}")
    boite.setDetailedText(message_complet)
    boite.exec()


def lancer_application():
    """Lance l'application : d'abord la connexion, puis le tableau de bord si ça réussit."""
    sys.excepthook = gerer_erreur_non_prevue

    app = QApplication(sys.argv)
    appliquer_theme(app, "clair")

    fenetres = {"principale": None}

    def apres_connexion(nom, role):
        pixmap = QPixmap(420, 160)
        pixmap.fill(QColor("#F5F7FA"))
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.showMessage("Chargement des modules…", Qt.AlignmentFlag.AlignCenter, QColor("#1F2937"))
        splash.show()
        app.processEvents()

        fenetres["principale"] = creer_fenetre_tableau_de_bord(nom, role)
        splash.finish(fenetres["principale"])
        fenetres["principale"].show()

    fenetre_connexion = creer_fenetre_connexion(apres_connexion)
    fenetre_connexion.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    lancer_application()
