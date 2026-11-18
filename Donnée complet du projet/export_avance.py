from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from pptx import Presentation
from pptx.util import Inches, Pt
from docx import Document
from datetime import datetime


def exporter_excel(dataframe, chemin_fichier):
    """Exporte un DataFrame pandas dans un fichier Excel."""
    dataframe.to_excel(chemin_fichier, index=False)


def exporter_word(dataframe, titre, chemin_fichier):
    """Exporte un DataFrame pandas dans un fichier Word avec un titre et un tableau."""
    document = Document()
    document.add_heading(titre, level=1)
    document.add_paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — ANA-STAT.abt")

    dataframe_affiche = dataframe.head(200)

    table = document.add_table(rows=1, cols=dataframe_affiche.shape[1])
    table.style = "Light Grid Accent 1"
    cellules_entete = table.rows[0].cells
    for i, colonne in enumerate(dataframe_affiche.columns):
        cellules_entete[i].text = str(colonne)

    for _, ligne in dataframe_affiche.iterrows():
        cellules = table.add_row().cells
        for i, valeur in enumerate(ligne):
            cellules[i].text = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)

    if dataframe.shape[0] > 200:
        document.add_paragraph(
            f"Remarque : seules les 200 premières lignes sur {dataframe.shape[0]} sont affichées ici."
        )

    document.save(chemin_fichier)


def exporter_image(figure, chemin_fichier):
    """Exporte le graphique matplotlib actuellement affiché en fichier image."""
    figure.savefig(chemin_fichier, dpi=150, bbox_inches="tight")


def imprimer_widget(widget_parent, widget_a_imprimer):
    """Ouvre la boîte de dialogue d'impression du système et imprime le contenu du widget donné."""
    from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
    from PyQt6.QtGui import QPainter

    imprimante = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialogue = QPrintDialog(imprimante, widget_parent)
    if dialogue.exec() == QPrintDialog.DialogCode.Accepted:
        peintre = QPainter(imprimante)
        widget_a_imprimer.render(peintre)
        peintre.end()
        return True
    return False


def exporter_pdf(dataframe, titre, chemin_fichier):
    """Exporte un DataFrame pandas dans un fichier PDF avec un titre et un tableau."""
    document = SimpleDocTemplate(chemin_fichier, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(titre, styles["Title"]))
    elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — ANA-STAT.abt",
                               styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Limite raisonnable pour ne pas produire un PDF illisible avec des milliers de lignes
    dataframe_affiche = dataframe.head(200)

    donnees_tableau = [list(dataframe_affiche.columns)]
    for _, ligne in dataframe_affiche.iterrows():
        donnees_tableau.append([
            f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur) for valeur in ligne
        ])

    tableau = Table(donnees_tableau, repeatRows=1)
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    elements.append(tableau)

    if dataframe.shape[0] > 200:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            f"Remarque : seules les 200 premières lignes sur {dataframe.shape[0]} sont affichées dans ce PDF.",
            styles["Italic"]
        ))

    document.build(elements)


def exporter_powerpoint(dataframe, titre, chemin_fichier, chemin_image_graphique=None):
    """Exporte un DataFrame pandas et, si fourni, un graphique déjà enregistré en image, dans un PowerPoint."""
    presentation = Presentation()

    # Diapositive de titre
    diapo_titre = presentation.slides.add_slide(presentation.slide_layouts[0])
    diapo_titre.shapes.title.text = titre
    diapo_titre.placeholders[1].text = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — ANA-STAT.abt"

    # Diapositive tableau (limité aux 15 premières lignes pour rester lisible)
    diapo_tableau = presentation.slides.add_slide(presentation.slide_layouts[5])
    diapo_tableau.shapes.title.text = "Tableau de résultats"

    dataframe_affiche = dataframe.head(15)
    nb_lignes = dataframe_affiche.shape[0] + 1
    nb_colonnes = dataframe_affiche.shape[1]

    tableau_forme = diapo_tableau.shapes.add_table(
        nb_lignes, nb_colonnes, Inches(0.5), Inches(1.5), Inches(9), Inches(0.4 * nb_lignes)
    ).table

    for j, colonne in enumerate(dataframe_affiche.columns):
        tableau_forme.cell(0, j).text = str(colonne)

    for i in range(dataframe_affiche.shape[0]):
        for j in range(nb_colonnes):
            valeur = dataframe_affiche.iloc[i, j]
            texte = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
            tableau_forme.cell(i + 1, j).text = texte

    # Diapositive graphique, si une image a été fournie
    if chemin_image_graphique:
        diapo_graphique = presentation.slides.add_slide(presentation.slide_layouts[5])
        diapo_graphique.shapes.title.text = "Graphique"
        diapo_graphique.shapes.add_picture(chemin_image_graphique, Inches(1), Inches(1.3), width=Inches(8))

    presentation.save(chemin_fichier)
