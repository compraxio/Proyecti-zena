# ============================================================
# 1. IMPORTACIÓN DE LIBRERÍAS Y CONFIGURACIÓN INICIAL
# ============================================================

from flask import Flask, render_template, url_for, request, flash, redirect, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import io

# ============================================================
# 2. CONFIGURACIÓN DE LA APLICACIÓN Y EXTENSIONES
# ============================================================

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Clave secreta para sesiones y mensajes flash
app.secret_key = 'a94a8fe5cc5c2b0e5d8cb6e00392e5ed5557788983e1f915d2cdf697ec811b17'

# Configuración de Flask-Mail para envío de correos
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'  # Contraseña de aplicación de Gmail
mail = Mail(app)

# ============================================================
# 3. DEFINICIÓN DE MODELOS DE BASE DE DATOS
# ============================================================

class proveedores(db.Model):
    """
    Modelo para la tabla de proveedores.
    """
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(200), nullable=False)
    contacto = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    condiciones_de_pago = db.Column(db.String(200), nullable=False)
    ofrece = db.Column(db.String(300), nullable=False)
    precio = db.Column(db.String(100), nullable=False)
    tiempo_de_entrega = db.Column(db.String(100), nullable=False)
    imagen = db.Column(db.LargeBinary, nullable=True)  # Imagen almacenada en binario

class Usuarios(db.Model):
    """
    Modelo para la tabla de usuarios.
    """
    id = db.Column(db.Integer, primary_key=True)
    Usuario = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    contraseña = db.Column(db.String(200), nullable=False)

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

# ============================================================
# 4. RUTAS PRINCIPALES DE LA APLICACIÓN
# ============================================================
def login_required(f):
    """
    Decorador para proteger rutas que requieren autenticación.
    Redirige a la página de inicio de sesión si el usuario no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('comprobar_usuario'))
        return f(*args, **kwargs)
    return decorated_function
#us = "admin"
#corre = "luisangelacu10@gmail.com"
#contra = "M3ga42023"

#with app.app_context():
    #if not Usuarios.query.filter_by(Usuario=us).first():
        # Crear un usuario administrador si no existe
        #nuevo_usuario = Usuarios(
            #Usuario=us,
            #correo=corre,
            #contraseña=generate_password_hash(contra)
        #)
        #db.session.add(nuevo_usuario)
        #db.session.commit()
# ---------------------------
# Página de inicio y envío de correo
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/inicio', methods=['GET', 'POST'])
def index():
    """
    Página de inicio. Permite enviar un correo desde un formulario.
    """
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        try:
            msg = Message(
                "Nuevo mensaje del proyecto",
                sender=correo,
                recipients=["luisangelacu10@gmail.com", f"{correo}"]
            )
            msg.body = f"De: {nombre}\nCorreo: {correo}"
            mail.send(msg)
            flash(f'Correo enviado correctamente a: {correo}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            flash('Error al enviar el correo', 'danger')
            return redirect(url_for('index'))
    return render_template('Inicio.html')

# ---------------------------
# Rutas de navegación a otras secciones
# ---------------------------
@app.route('/prevencion_de_riesgos')
def prevencion_de_riesgos():
    """Página de prevención de riesgos."""
    return render_template('Prevención-de-riesgos.html')

@app.route('/gestion_de_productos')
def gestion_de_productos():
    """Página de gestión de productos."""
    return render_template('Gestion-de-productos.html')

@app.route('/control_de_inventario')
def control_de_inventario():
    """Página de control de inventario."""
    return render_template('Control-de-inventario.html')

@app.route('/optimizacion_de_rutas')
def optimizacion_de_rutas():
    """Página de optimización de rutas."""
    return render_template('Optimizacion-de-rutas.html')

@app.route('/gestion_de_vehiculos')
def gestion_de_vehiculos():
    """Página de gestión de vehículos."""
    return render_template('Gestion-de-vehiculos.html')

# ============================================================
# 5. RUTAS PARA GESTIÓN DE PROVEEDORES
# ============================================================
@app.route('/comprobar_usuario', methods=['GET', 'POST'])
def comprobar_usuario():
    if request.method == 'POST':
        User = request.form['usuario']
        corre = request.form['correo']
        contra = request.form['password']
        
        permitido = Usuarios.query.filter_by(Usuario=User, correo=corre).first()
        if permitido and check_password_hash(permitido.contraseña, contra):
            session['usuario'] = permitido.Usuario
            return redirect(url_for('proveedor'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('comprobar_usuario'))

    return render_template('comprovar.html')
@app.route('/cerrar_sesion')

def cerrar_sesion():
    """
    Cierra la sesión del usuario y redirige a la página de inicio.
    """
    session.pop('usuario', None)
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('comprobar_usuario'))

@app.route('/proveedor')
@login_required
def proveedor():
    """
    Muestra la lista de todos los proveedores.
    """
    empresarios = proveedores.query.all()
    return render_template('Proveedores.html', empresarios=empresarios)

@app.route('/añadir_proveedor', methods=['GET', 'POST'])
@login_required
def añadir_proveedor():
    """
    Permite añadir un nuevo proveedor mediante un formulario.
    """
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
            flash('Proveedor añadido correctamente.', 'success')
            return redirect("/proveedor")
        except Exception as e:
            print(f"Error al guardar: {e}")
            flash('Error al añadir el proveedor, verifique los datos.', 'danger')
            return redirect(url_for('proveedor'))
    return render_template('Añadir-proveedor.html')

@app.route('/editar_proveedor/<int:proveedor_id>', methods=['GET', 'POST'])
@login_required
def editar_proveedor(proveedor_id):
    """
    Permite editar los datos de un proveedor existente.
    """
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
            flash('Proveedor actualizado correctamente.', 'success')
            return redirect("/proveedor")
        except Exception as e:
            print(f"Error al actualizar: {e}")
            flash('Error al actualizar el proveedor, verifique los datos.', 'danger')
            return redirect(url_for('proveedor'))
    return render_template('Editar-proveedor.html', proveedor=proveedor)

@app.route('/eliminar_proveedor/<int:proveedor_id>', methods=['POST'])
@login_required
def eliminar_proveedor(proveedor_id):
    """
    Elimina un proveedor de la base de datos.
    """
    proveedor = proveedores.query.get_or_404(proveedor_id)
    try:
        db.session.delete(proveedor)
        db.session.commit()
        flash('Proveedor eliminado correctamente.', 'success')
    except Exception as e:
        print(f"Error al eliminar el proveedor: {e}")
        flash('Error al eliminar el proveedor.', 'danger')
    return redirect(url_for('proveedor'))

@app.route('/imagen_proveedor/<int:proveedor_id>')
def imagen_proveedor(proveedor_id):
    """
    Devuelve la imagen del proveedor o una imagen alternativa si no existe.
    """
    proveedor = proveedores.query.get_or_404(proveedor_id)
    if proveedor.imagen:
        return send_file(io.BytesIO(proveedor.imagen), mimetype='image/jpeg')
    else:
        return redirect(url_for('static', filename='img/proveedor-alternativo.png'))

# ============================================================
# 6. EJECUCIÓN DE LA APLICACIÓN
# ============================================================

if __name__ == '__main__':
    # Ejecuta el servidor Flask en modo debug
    app.run(debug=True)
