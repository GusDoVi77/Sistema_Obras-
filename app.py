from flask import Flask, render_template, request, redirect, url_for, send_file, Response
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
PDF_FOLDER = "pdfs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# ☁️ SIRV
CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "TU_CLIENT_SECRET"
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

        return f"{SIRV_DOMAIN}/obra/{filename}

    except:
        return "error_total"


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

                temp = os.path.join(UPLOAD_FOLDER, "temp.jpg")
                img.save(temp, optimize=True, quality=50)

                with open(temp, "rb") as f:
                    url_imagen = subir_a_sirv(f)

                os.remove(temp)

            except:
                url_imagen = "error_imagen"

        # 📄 PDF
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

        time.sleep(0.3)

        return redirect(url_for("success"))

    return render_template("form.html")


# ----------------------------
# SUCCESS
# ----------------------------
@app.route("/success")
def success():
    return render_template("success.html")


# ----------------------------
# ADMIN (PROTEGIDO)
# ----------------------------
def auth():
    return Response("Acceso restringido", 401,
                    {"WWW-Authenticate": 'Basic realm="Login"'})

def check_auth(user, password):
    return user == "admin" and password == "1234"


@app.route("/admin/reportes")
def reportes():
    auth_data = request.authorization
    if not auth_data or not check_auth(auth_data.username, auth_data.password):
        return auth()

    archivos = os.listdir(PDF_FOLDER)
    return render_template("admin.html", archivos=archivos)


@app.route("/admin/descargar/<filename>")
def descargar(filename):
    return send_file(os.path.join(PDF_FOLDER, filename), as_attachment=True)


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)