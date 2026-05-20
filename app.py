from flask import Flask, render_template, request, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from PIL import Image
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "fotos"
PDF_FOLDER = "pdfs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

CLIENT_ID = "UM9DzKb3TmN1Fbi5sRewrscfCnD"
CLIENT_SECRET = "0m3aoJdhRPEygjmKdXMWaaihmgf0FM1V2UNes9nLf89VkrsvUeMvsj+D52af1n140YkiXpUPSYdpyaKph97N9g=="
SIRV_DOMAIN = "https://gusdovi.sirv.com"

# 🚀 FUNCIÓN CORREGIDA
def subir_a_sirv(file):
    try:
        auth = requests.post(
            "https://api.sirv.com/v2/token",
            json={
                "clientId": CLIENT_ID,
                "clientSecret": CLIENT_SECRET
            }
        )

        if auth.status_code != 200:
            print("Auth error:", auth.text)
            return "error_auth"

        token = auth.json().get("token")

        filename = f"{datetime.now().timestamp()}.jpg"

        upload_url = f"https://api.sirv.com/v2/files/upload?filename=/obra/{filename}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }

        # 🔥 FIX CLAVE
        file.seek(0)
        data = file.read()

        response = requests.post(upload_url, headers=headers, data=data)

        if response.status_code != 200:
            print("Upload error:", response.text)
            return "error_upload"

        return f"{SIRV_DOMAIN}/obra/{filename}"

    except Exception as e:
        print("ERROR SIRV:", e)
        return "error_total"


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

                # 🔥 ABRIR BIEN EL ARCHIVO
                with open(temp_path, "rb") as f:
                    url_imagen = subir_a_sirv(f)

                os.remove(temp_path)

            except Exception as e:
                print("Error imagen:", e)
                url_imagen = "error_imagen"

        pdf_name = f"{PDF_FOLDER}/reporte_{nombre}_{datetime.now().timestamp()}.pdf"
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

        return redirect(url_for("success"))

    return render_template("form.html")


@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)