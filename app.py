from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
from PIL import Image
import requests
import psycopg2

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = "fotos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ☁️ SIRV
CLIENT_ID = "8ARvedBbjChk50zgogeCBPtR5sN"
CLIENT_SECRET = "egU7oS4olUnvB0VrVXrEnhRquiVCRAJ86ZLDsFNsDq0z632VxpVJDdAJQPQ+fIrxlIT5QeWKjnsNE4c5zLSlHw=="
SIRV_DOMAIN = "https://gusdovi.sirv.com"

# 🗄️ DATABASE
DATABASE_URL = os.environ.get("DATABASE_URL")


# ----------------------------
# CONEXIÓN DB
# ----------------------------
def get_db():
    return psycopg2.connect(DATABASE_URL)


# ----------------------------
# CREAR TABLA
# ----------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reportes (
        id SERIAL PRIMARY KEY,
        obra TEXT,
        nombre TEXT,
        ubicacion TEXT,
        actividad TEXT,
        etapa TEXT,
        fecha TEXT,
        foto TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()


# ----------------------------
# SUBIR A SIRV
# ----------------------------
def subir_imagen(file):
    try:
        auth = requests.post(
            "https://api.sirv.com/v2/token",
            json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}
        )

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
            return "error"

        return f"{SIRV_DOMAIN}/obra/{filename}"

    except Exception as e:
        print("Error imagen:", e)
        return "error"


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
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 📷 imagen
        foto = request.files.get("foto")
        url_imagen = "sin_foto"

        if foto and foto.filename != "":
            url_imagen = subir_imagen(foto)

        # 🗄️ GUARDAR EN DB
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO reportes (obra, nombre, ubicacion, actividad, etapa, fecha, foto)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (obra, nombre, ubicacion, actividad, etapa, fecha, url_imagen))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print("Error DB:", e)

        return redirect(url_for("success"))

    return render_template("form.html")


# ----------------------------
# PANEL ADMIN
# ----------------------------
@app.route("/admin")
def admin():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM reportes ORDER BY id DESC")
    datos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin.html", datos=datos)


# ----------------------------
# SUCCESS
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