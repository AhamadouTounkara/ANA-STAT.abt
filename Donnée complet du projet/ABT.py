"""ANA-STAT.abt — point d'entrée de TEST (mode sans connexion).

Ce fichier ouvre directement le tableau de bord, sans aucune authentification.
Le lancement normal, avec écran de connexion, se fait par main.py.
Ne pas supprimer : il sert à tester l'interface et les modules.

Le code d'interface est partagé avec tableau_bord.py (paramètre mode_test).
"""

import os
import sys
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

import traceback
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt

from tableau_bord import creer_fenetre_tableau_de_bord, VERSION_LOGICIEL, appliquer_theme


def lancer_application():
    """Lance uniquement l'interface de l'application, sans aucune authentification."""
    print("=" * 64)
    print("ANA-STAT.abt — MODE TEST SANS CONNEXION (ABT.py)")
    print("Aucune authentification : accès direct au tableau de bord.")
    print("Pour le parcours normal avec connexion, lancer main.py.")
    print("=" * 64)

    app = QApplication(sys.argv)
    app.setApplicationName("ANA-STAT.abt — test sans connexion")
    appliquer_theme(app, "clair")

    # Écran de chargement (les modules lourds se chargent pendant ce temps)
    pixmap = QPixmap(420, 160)
    pixmap.fill(QColor("#F5F7FA"))
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.showMessage("Chargement des modules…", Qt.AlignmentFlag.AlignCenter, QColor("#1F2937"))
    splash.show()
    app.processEvents()

    fenetre = creer_fenetre_tableau_de_bord("Utilisateur", "Administrateur", mode_test=True)
    splash.finish(fenetre)
    fenetre.show()

    try:
        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Erreur",
            "L'application a rencontré une erreur et a été fermée."
        )
        sys.exit(1)


if __name__ == "__main__":
    lancer_application()
