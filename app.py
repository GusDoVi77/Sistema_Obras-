from flask import Flask, render_template, request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "fotos"
PDF_FOLDER = "pdfs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        obra = request.form["obra"]
        nombre = request.form["nombre"]
        actividad = request.form["actividad"]
        cantidad = request.form["cantidad"]
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        foto = request.files["foto"]
        foto_path = os.path.join(UPLOAD_FOLDER, foto.filename)
        foto.save(foto_path)

        pdf_name = f"{PDF_FOLDER}/reporte_{nombre}_{datetime.now().timestamp()}.pdf"
        c = canvas.Canvas(pdf_name, pagesize=letter)

        c.drawString(100, 750, f"Obra: {obra}")
        c.drawString(100, 730, f"Obrero: {nombre}")
        c.drawString(100, 710, f"Actividad: {actividad}")
        c.drawString(100, 690, f"Cantidad: {cantidad}")
        c.drawString(100, 670, f"Fecha: {fecha}")
        c.drawString(100, 650, f"Foto: {foto.filename}")

        c.save()

        return "✅ PDF generado correctamente"

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)