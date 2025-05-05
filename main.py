# =============================================
# 1. IMPORTACIÓN DE LIBRERÍAS Y CONFIGURACIÓN
# =============================================
# Importa los módulos esenciales de Flask para crear rutas, renderizar plantillas y manejar peticiones.
from flask import Flask, render_template, url_for, request, flash, redirect
from flask_mail import Mail, Message

# ---------------------------
# Configuración de la app y correo
# ---------------------------
# Crea la instancia principal de la aplicación Flask.
app = Flask(__name__)
app.secret_key = 'a94a8fe5cc5c2b0e5d8cb6e00392e5ed5557788983e1f915d2cdf697ec811b17'

# Configuración de los parámetros para el envío de correos
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'
mail = Mail(app)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/inicio', methods = ['GET', 'POST'])
def index():
    if request.method =='POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        
        try:
            msg = Message("Nuevo mensaje del proyecto", 
                        sender=correo, 
                        recipients=["luisangelacu10@gmail.com", f"{correo}"])
            msg.body = f"De: {nombre}\nCorreo: {correo}"
            mail.send(msg)
            flash(f'Correo enviado correctamente a: {correo}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            flash('Error al enviar el correo', 'danger')
            return redirect(url_for('index'))
    return render_template('Inicio.html')

if __name__ == '__main__':
    app.run(debug=True)
