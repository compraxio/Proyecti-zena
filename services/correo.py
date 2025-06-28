from flask_mail import Mail, Message
from flask import Flask, render_template, url_for, request, flash, redirect, send_file, session, jsonify, Response
import pyotp
import qrcode
import os
from datetime import datetime, timedelta
app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'  # Contraseña de aplicación de Gmail
mail = Mail(app)

RUTA_TEMP = "templates/Optimizacion-de-rutas/temp"
LIMITE_TIEMPO = timedelta(hours=2)  # 2 horas
def correo_error(error):
    try:
        msg = Message(
            subject="Error detectado",
            sender="luisangelacu10@gmail.com",
            recipients=["luisangelacu10@gmail.com"]
        )
        msg.body = f"Se ha detectado el siguiente error:\n\n{error}"
        mail.send(msg)
    except Exception as e:
        print(f"Fallo al enviar el correo: {e}")

def qr(username, name_aplication):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    url = totp.provisioning_uri(username, issuer_name=name_aplication)
    img = qrcode.make(url)
    img.save(f"static/qr/{username}.png")
    return secret

def limpiar_archivos_expirados():
    ahora = datetime.now()
    eliminados = []

    if not os.path.exists(RUTA_TEMP):
        return eliminados  # Si no existe la carpeta, no hay nada que hacer

    for archivo in os.listdir(RUTA_TEMP):
        ruta = os.path.join(RUTA_TEMP, archivo)
        if os.path.isfile(ruta):
            tiempo_mod = datetime.fromtimestamp(os.path.getmtime(ruta))
            if ahora - tiempo_mod > LIMITE_TIEMPO:
                os.remove(ruta)
                eliminados.append(archivo)

    return eliminados