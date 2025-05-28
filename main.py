# =============================================
# 1. IMPORTACIÓN DE LIBRERÍAS Y CONFIGURACIÓN
# =============================================

# Importa las herramientas necesarias de Flask:
# - Flask: para crear la app
# - render_template: para renderizar archivos HTML
# - url_for: para generar URLs dinámicamente
# - request: para manejar datos del formulario
# - flash: para mostrar mensajes temporales (notificaciones)
# - redirect: para redirigir después de enviar el formulario
from flask import Flask, render_template, url_for, request, flash, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import io

# Importa Flask-Mail:
# - Mail: para configurar el servidor de correos
# - Message: para crear y enviar correos
from flask_mail import Mail, Message

# ---------------------------
# Configuración de la app y correo
# ---------------------------

# Crea la instancia principal de la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class proveedores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(200), nullable=False)
    contacto = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    condiciones_de_pago = db.Column(db.String(200), nullable=False)
    ofrece = db.Column(db.String(300), nullable=False)  # Podría ser otro modelo
    precio = db.Column(db.String(100), nullable=False)  # Para cálculos
    tiempo_de_entrega = db.Column(db.String(100), nullable=False)
    imagen = db.Column(db.LargeBinary, nullable=True)  # Para almacenar la imagen en binario
    

with app.app_context():
    db.create_all()
# Clave secreta necesaria para usar "flash" y mantener la sesión segura
app.secret_key = 'a94a8fe5cc5c2b0e5d8cb6e00392e5ed5557788983e1f915d2cdf697ec811b17'

# Configura los parámetros necesarios para el envío de correos mediante Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'       # Servidor SMTP de Gmail
app.config['MAIL_PORT'] = 587                      # Puerto estándar con TLS
app.config['MAIL_USE_TLS'] = True                  # Activa la encriptación TLS
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'  # Correo que enviará los mensajes
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'        # Contraseña de aplicación (no la contraseña principal de Gmail)

# Inicializa Flask-Mail con la configuración anterior
mail = Mail(app)

# =============================================
# 2. RUTAS Y LÓGICA DE ENVÍO DE CORREO
# =============================================

# Define las rutas '/' e '/inicio' que aceptan los métodos GET y POST
@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/inicio', methods = ['GET', 'POST'])
def index():
    # Si se recibe un formulario enviado (POST)
    if request.method == 'POST':
        # Captura los datos del formulario HTML
        nombre = request.form['nombre']
        correo = request.form['correo']
        
        try:
            # Crea un objeto de tipo Message con los datos del formulario
            msg = Message(
                "Nuevo mensaje del proyecto",         # Asunto del correo
                sender=correo,                        # Correo del remitente (quien llenó el formulario)
                recipients=["luisangelacu10@gmail.com", f"{correo}"]  # Correos de destino (el tuyo y una copia al usuario)
            )

            # Define el cuerpo del mensaje
            msg.body = f"De: {nombre}\nCorreo: {correo}"

            # Envía el mensaje usando Flask-Mail
            mail.send(msg)

            # Muestra un mensaje de éxito en pantalla y redirige a la misma ruta
            flash(f'Correo enviado correctamente a: {correo}', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            # Si ocurre un error, lo muestra en consola y lanza un mensaje de error
            print(f"Error al enviar el correo: {e}")
            flash('Error al enviar el correo', 'danger')
            return redirect(url_for('index'))

    # Si la petición es GET (o tras redirección), se muestra la plantilla HTML
    return render_template('Inicio.html')

@app.route('/prevencion_de_riesgos')
def prevencion_de_riesgos():
    return render_template('Prevención-de-riesgos.html')

@app.route('/gestion_de_productos')
def gestion_de_productos():
    return render_template('Gestion-de-productos.html')

@app.route('/control_de_inventario')
def control_de_inventario():
    return render_template('Control-de-inventario.html')

@app.route('/optimizacion_de_rutas')
def optimizacion_de_rutas():
    return render_template('Optimizacion-de-rutas.html')

@app.route('/gestion_de_vehiculos')
def gestion_de_vehiculos():
    return render_template('Gestion-de-vehiculos.html')

@app.route('/imagen_proveedor/<int:proveedor_id>')
def imagen_proveedor(proveedor_id):
    proveedor = proveedores.query.get_or_404(proveedor_id)
    if proveedor.imagen:
        return send_file(io.BytesIO(proveedor.imagen), mimetype='image/jpeg')
    else:
        return redirect(url_for('static', filename='img/proveedor-alternativo.png'))

@app.route('/eliminar_proveedor/<int:proveedor_id>' , methods=['POST'])
def eliminar_proveedor(proveedor_id):
    proveedor = proveedores.query.get_or_404(proveedor_id)
    try:
        db.session.delete(proveedor)
        db.session.commit()
    except Exception as e:
        print(f"Error al eliminar el proveedor: {e}")
    return redirect(url_for('proveedor'))

@app.route('/proveedor')
def proveedor():
    empresarios = proveedores.query.all()  # Obtiene todos los proveedores de la base de datos
    return render_template('Proveedores.html' , empresarios=empresarios)

@app.route('/añadir_proveedor', methods=['GET', 'POST'])
def añadir_proveedor():
    if request.method == 'POST':
        imagen_file = request.files['imagen']
        imagen = imagen_file.read() if imagen_file else None
        proveedor = request.form['proveedor']
        Contacto = request.form['Contacto']
        Ubicacion = request.form['Ubicacion']
        Condicion = request.form['Condicion']
        ofrece = request.form['ofrece']
        Precio = request.form['Precio']
        tiempo = request.form['tiempo']
        try:
            NuevoProveedor = proveedores(
                identificacion=proveedor,
                contacto=Contacto,
                ubicacion=Ubicacion,
                condiciones_de_pago=Condicion,
                ofrece=ofrece,
                precio=Precio,
                tiempo_de_entrega=tiempo,
                imagen=imagen
            )
            db.session.add(NuevoProveedor)
            db.session.commit()
            return redirect("/proveedor")
        except Exception as e:
            print(f"Error al guardar: {e}")
            return redirect(url_for('proveedor'))
    return render_template('Añadir-proveedor.html')

@app.route('/editar_proveedor/<int:proveedor_id>', methods=['GET', 'POST'])
def editar_proveedor(proveedor_id):
    proveedor = proveedores.query.get_or_404(proveedor_id)
    if request.method == 'POST':
        imagen_file = request.files['imagen']
        proveedor.identificacion = request.form['proveedor']
        proveedor.contacto = request.form['Contacto']
        proveedor.ubicacion = request.form['Ubicacion']
        proveedor.condiciones_de_pago = request.form['Condicion']
        proveedor.ofrece = request.form['ofrece']
        proveedor.precio = request.form['Precio']
        proveedor.tiempo_de_entrega = request.form['tiempo']
        proveedor.imagen = imagen_file.read() if imagen_file else proveedor.imagen
        try:
            db.session.commit()
            return redirect("/proveedor")
        except Exception as e:
            print(f"Error al actualizar: {e}")
            return redirect(url_for('proveedor'))
    return render_template('Editar-proveedor.html', proveedor=proveedor)
# =============================================
# 3. EJECUCIÓN DE LA APLICACIÓN
# =============================================
# Si este archivo es el principal, ejecuta el servidor con debug activado
if __name__ == '__main__':
    app.run(debug=True)
