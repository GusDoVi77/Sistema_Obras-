from flask import Flask, render_template, request, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from PIL import Image
import requests
import time

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = "fotos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ☁️ SIRV
CLIENT_ID = "8ARvedBbjChk50zgogeCBPtR5sN"
CLIENT_SECRET = "egU7oS4olUnvB0VrVXrEnhRquiVCRAJ86ZLDsFNsDq0z632VxpVJDdAJQPQ+fIrxlIT5QeWKjnsNE4c5zLSlHw=="
SIRV_DOMAIN = "https://gusdovi.sirv.com"


# ----------------------------
# SUBIR IMAGEN A SIRV
# ----------------------------
def subir_a_sirv(file):
    try:
        auth = requests.post(
            "https://api.sirv.com/v2/token",
            json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}
        )

        if auth.status_code != 200:
            return "error_auth"

        token = auth.json().get("token")

        filename = f"{datetime.now().timestamp()}.jpg"
        upload_url = f"https://api.sirv.com/v2/files/upload?filename=/obra/{filename}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }

        file.seek(0)
        response = requests.post(upload_url, headers=headers, data=file.read())

        if response.status_code != 200:
            return "error_upload"

        return f"{SIRV_DOMAIN}/obra/{filename}"

    except Exception as e:
        print("Error imagen:", e)
        return "error_total"


# ----------------------------
# SUBIR PDF A SIRV
# ----------------------------
def subir_pdf_a_sirv(pdf_path):
    try:
        auth = requests.post(
            "https://api.sirv.com/v2/token",
            json={
                "clientId": CLIENT_ID,
                "clientSecret": CLIENT_SECRET
            }
        )

        if auth.status_code != 200:
            return "error_auth"

        token = auth.json().get("token")

        filename = f"{datetime.now().timestamp()}.pdf"
        upload_url = f"https://api.sirv.com/v2/files/upload?filename=/reportes/{filename}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }

        with open(pdf_path, "rb") as f:
            response = requests.post(upload_url, headers=headers, data=f.read())

        if response.status_code != 200:
            return "error_upload"

        return f"{SIRV_DOMAIN}/reportes/{filename}"

    except Exception as e:
        print("Error PDF:", e)
        return "error_pdf"


# ----------------------------
# FORMULARIO
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":

        obra = request.form["obra"]
        nombre = request.form["nombre"]
        actividad = request.form["actividad"]
        etapa = request.form["etapa"]
        ubicacion = request.form["ubicacion"]
        cantidad = request.form["cantidad"]
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        foto = request.files.get("foto")
        url_imagen = "sin_foto"

        if foto and foto.filename != "":
            try:
                img = Image.open(foto)

                if img.mode != "RGB":
                    img = img.convert("RGB")

                img.thumbnail((600, 600))

                temp_path = os.path.join(UPLOAD_FOLDER, "temp.jpg")
                img.save(temp_path, optimize=True, quality=50)

                with open(temp_path, "rb") as f:
                    url_imagen = subir_a_sirv(f)

                os.remove(temp_path)

            except Exception as e:
                print("Error imagen:", e)
                url_imagen = "error_imagen"

        # 📄 GENERAR PDF (temporal)
        pdf_name = f"reporte_{datetime.now().timestamp()}.pdf"

        c = canvas.Canvas(pdf_name, pagesize=letter)
        c.drawString(100, 750, f"Obra: {obra}")
        c.drawString(100, 730, f"Obrero: {nombre}")
        c.drawString(100, 710, f"Ubicación: {ubicacion}")
        c.drawString(100, 690, f"Actividad: {actividad}")
        c.drawString(100, 670, f"Etapa: {etapa}")
        c.drawString(100, 650, f"Cantidad: {cantidad}")
        c.drawString(100, 630, f"Fecha: {fecha}")
        c.drawString(100, 610, f"Foto: {url_imagen}")
        c.save()

        time.sleep(0.3)

        # ☁️ SUBIR PDF
        url_pdf = subir_pdf_a_sirv(pdf_name)

        # 🧹 borrar archivo local
        os.remove(pdf_name)

        return f"""
        <h2>Reporte generado correctamente ✅</h2>
        <p><a href="{url_pdf}" target="_blank">Ver PDF</a></p>
        """

    return render_template("form.html")


# ----------------------------
# SUCCESS (opcional)
# ----------------------------
@app.route("/success")
def success():
    return render_template("success.html")


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)