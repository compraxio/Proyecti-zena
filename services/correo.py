from flask_mail import Mail, Message
from flask import Flask, render_template, url_for, request, flash, redirect, send_file, session, jsonify, Response

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'  # Contraseña de aplicación de Gmail
mail = Mail(app)

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
