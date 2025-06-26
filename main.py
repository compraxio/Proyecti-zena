# ============================================================
# 1. IMPORTACIÓN DE LIBRERÍAS Y CONFIGURACIÓN INICIAL
# ============================================================

#librerias para ruta
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import great_circle
import folium  # <- NUEVO
import time
from networkx.algorithms import approximation as approx
import gpxpy
import gpxpy.gpx
import geopandas as gpd
import csv
from pathlib import Path

# Librerías de Google Gemini y SerpApi para IA y búsquedas web
from google import genai
from google.genai import types
from google.genai.types import  Tool, GenerateContentConfig, GoogleSearch
from serpapi import GoogleSearch as Gg

# Librerías de Flask para la creación de la aplicación web y manejo de peticiones
from flask import Flask, render_template, url_for, request, flash, redirect, send_file, session, jsonify, Response

# SQLAlchemy para ORM y manejo de base de datos SQLite
from flask_sqlalchemy import SQLAlchemy

# Flask-Mail para envío de correos electrónicos
from flask_mail import Mail, Message

# Werkzeug para manejo seguro de contraseñas
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
# Función wraps para crear decoradores personalizados
from functools import wraps

# Librería estándar para manejo de archivos binarios
import io

from services.correo import correo_error, qr
from services.Ruta import *

# ============================================================
# 2. CONFIGURACIÓN DE LA APLICACIÓN Y EXTENSIONES
# ============================================================

# Inicialización de la aplicación Flask
app = Flask(__name__)

#qr("correo","nombre de aplicacion")

# Cliente de Google Gemini para IA (requiere API Key)
client = genai.Client(api_key="AIzaSyBGxDkqcairULlOIvMycALEvclJn3-e-_o")
#Key de api google
Clav = "AIzaSyBi_IAVJo42jH0ziRi72nO5XrU9DM7dFcE"


# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuración de la API de SerpApi para búsquedas en Google
key = "c4ea6b07cbade43b7a7c7955016ffc9463975b858b0ccb50863bdc57e40bf1c8"  # Clave de API de SerpApi

# Clave secreta para sesiones y mensajes flash
app.secret_key = 'a94a8fe5cc5c2b0e5d8cb6e00392e5ed5557788983e1f915d2cdf697ec811b17'

# Configuración de Flask-Mail para envío de correos electrónicos
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
    Almacena información relevante de cada proveedor, incluyendo datos de contacto, condiciones y una imagen.
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
    Almacena usuarios registrados con su correo y contraseña encriptada.
    """
    id = db.Column(db.Integer, primary_key=True)
    Usuario = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    contraseña = db.Column(db.String(200), nullable=False)

# Crear las tablas si no existen al iniciar la aplicación
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

# ---------------------------
# Página de inicio y envío de correo
# ---------------------------

@app.route('/usuario/<key>', methods=['GET', 'POST'])
def usuario(key):
    
    SECRET_TOTP = "MILH6SJUVAPI6UFEDZ633CTNPRVJULV5"
    totp = pyotp.TOTP(SECRET_TOTP)
    
    if totp.verify(str(key), valid_window=1):
        try:
            if request.method == 'POST':
                user = Usuarios(
                    Usuario = request.form['User'],
                    correo = request.form['Email'],
                    contraseña = generate_password_hash(request.form['Pas'])
                )
                db.session.add(user)
                db.session.commit()
                flash('Usuario registrado exitosamente', 'success')
                return redirect(url_for('comprobar_usuario'))
        except Exception as e:
            correo_error(e)
            print(f"Fallo al ingresar: {e}")
            return redirect(url_for('inicio'))
        return render_template('usuario.html')
    else:
        flash('Código inválido o expirado.', 'danger')
        return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/inicio', methods=['GET', 'POST'])
def index():
    """
    Página de inicio. Permite enviar un correo desde un formulario.
    Si el método es POST, procesa el formulario y envía un correo.
    """
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        mensaje = request.form['Mensage']
        try:
            msg = Message(
                "Nuevo mensaje del proyecto",
                sender=correo,
                recipients=["luisangelacu10@gmail.com", f"{correo}"]
            )
            msg.body = f"De: {nombre}\nCorreo: {correo}\n\nMensaje:\n{mensaje}"
            mail.send(msg)
            flash(f'Correo enviado correctamente a: {correo}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            correo_error(e)
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

@app.route('/optimizacion_de_rutas/<valor1>')
@app.route('/optimizacion_de_rutas/<valor1>/<valor2>')
def optimizacion_de_rutas(valor1, valor2=None):
    valor_bool1 = valor1.lower() == 'true'
    if valor2 is None:
        valor_bool2 = False
    else:
        valor_bool2 = valor2.lower() == 'true'
    return render_template('Optimizacion-de-rutas.html', valor_1=valor_bool1, valor_2=valor_bool2)

@app.route('/gestion_de_vehiculos')
def gestion_de_vehiculos():
    """Página de gestión de vehículos."""
    return render_template('Gestion-de-vehiculos.html')

# ============================================================
# 5. RUTAS PARA GESTIÓN DE PROVEEDORES Y USUARIOS
# ============================================================

@app.route('/comprobar_usuario', methods=['GET', 'POST'])
def comprobar_usuario():
    """
    Ruta para inicio de sesión de usuarios.
    Verifica usuario, correo y contraseña. Si es correcto, inicia sesión.
    """
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

    return render_template('proveedores/comprovar.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    """
    Cierra la sesión del usuario y redirige a la página de inicio de sesión.
    """
    session.pop('usuario', None)
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('comprobar_usuario'))

@app.route('/proveedor')
@login_required
def proveedor():
    """
    Muestra la lista de todos los proveedores registrados en la base de datos.
    Solo accesible para usuarios autenticados.
    """
    empresarios = proveedores.query.all()
    return render_template('proveedores/Proveedores.html', empresarios=empresarios)

@app.route('/añadir_proveedor', methods=['GET', 'POST'])
@login_required
def añadir_proveedor():
    """
    Permite añadir un nuevo proveedor mediante un formulario.
    Procesa la imagen y los datos enviados por el usuario.
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
            correo_error(e)
            flash('Error al añadir el proveedor, verifique los datos.', 'danger')
            return redirect(url_for('proveedor'))
    return render_template('proveedores/Añadir-proveedor.html')

@app.route('/editar_proveedor/<int:proveedor_id>', methods=['GET', 'POST'])
@login_required
def editar_proveedor(proveedor_id):
    """
    Permite editar los datos de un proveedor existente.
    Si se envía una nueva imagen, la actualiza; si no, mantiene la anterior.
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
        if imagen_file and imagen_file.filename:
            proveedor.imagen = imagen_file.read()
        try:
            db.session.commit()
            flash('Proveedor actualizado correctamente.', 'success')
            return redirect("/proveedor")
        except Exception as e:
            print(f"Error al actualizar: {e}")
            correo_error(e)
            flash('Error al actualizar el proveedor, verifique los datos.', 'danger')
            return redirect(url_for('proveedor'))
    return render_template('proveedores/Editar-proveedor.html', proveedor=proveedor)

@app.route('/eliminar_proveedor/<int:proveedor_id>', methods=['POST'])
@login_required
def eliminar_proveedor(proveedor_id):
    """
    Elimina un proveedor de la base de datos.
    Solo accesible para usuarios autenticados.
    """
    proveedor = proveedores.query.get_or_404(proveedor_id)
    try:
        db.session.delete(proveedor)
        db.session.commit()
        flash('Proveedor eliminado correctamente.', 'success')
    except Exception as e:
        print(f"Error al eliminar el proveedor: {e}")
        correo_error(e)
        flash('Error al eliminar el proveedor.', 'danger')
    return redirect(url_for('proveedor'))

@app.route('/imagen_proveedor/<int:proveedor_id>')
def imagen_proveedor(proveedor_id):
    """
    Devuelve la imagen del proveedor en formato binario.
    Si no existe imagen, redirige a una imagen alternativa por defecto.
    """
    proveedor = proveedores.query.get_or_404(proveedor_id)
    if proveedor.imagen:
        return send_file(io.BytesIO(proveedor.imagen), mimetype='image/jpeg')
    else:
        return redirect(url_for('static', filename='img/proveedor-alternativo.png'))

# ============================================================
# 6. RUTAS DE INTELIGENCIA ARTIFICIAL (IA)
# ============================================================

@app.route('/IA')
@login_required
def IA():
    """
    Página principal de la sección de IA.
    Solo accesible para usuarios autenticados.
    """
    return render_template('proveedores/IA.html')

@app.route('/IA/consultar', methods=['POST'])
def IA_consultar():
    pregunta = request.json.get('question')
    data = request.get_json()
    wifi = data.get('wifi')
    
    # 1. Obtener la pregunta enviada por el usuario (JSON)
    busco = ""
    resultado = ""
    # 2. Parámetros para la búsqueda en Google (SerpApi)
    params = {
        "q": pregunta,
        "location": "Mexico",
        "hl": "es",
        "gl": "mx",
        "google_domain": "google.com.mx",
        "api_key": key  # Usa tu variable de clave de SerpApi
    }
    """
    Ruta para consultar la IA.
    1. Recibe una pregunta del usuario.
    2. Realiza una búsqueda en Google usando SerpApi.
    3. Extrae preguntas relacionadas y respuestas.
    4. Consulta la base de datos de proveedores.
    5. Llama al modelo de IA de Google Gemini para generar una respuesta personalizada.
    6. Devuelve la respuesta en formato JSON.
    """
    #cuando esta apagado envia true, entonces para no complicarme. cuando esta en false haga algo
    if wifi is False:
        # 3. Realizar la búsqueda en Google usando SerpApi
        try:
            search = Gg(params)
            result = search.get_dict()
        except Exception as e:
            correo_error(e)
            resultado = "Error en la búsqueda."
        else:
            # 4. Extraer preguntas relacionadas del resultado
            Contenido = result.get("related_questions", [])
            # 5. Construir una cadena con las preguntas y respuestas encontradas
            for solicitud in Contenido:
                snippet = solicitud.get('snippet')
                lista = solicitud.get('list')
                respuesta = snippet if snippet is not None else (lista if lista is not None else "Sin respuesta")
                busco += f"Respuesta: {respuesta}\n, link: {solicitud.get('link','')}\n"
            resultado = busco
    else:
        # 3. Si wifi es True, no realiza búsqueda y usa un mensaje predeterminado
        resultado = "El usuario no ha pedido búsqueda en intent."

    # 8. Obtener información de proveedores de la base de datos
    tools = []
    tools.append(Tool(url_context=types.UrlContext))
    tools.append(Tool(google_search=types.GoogleSearch))
    informacion = ""
    empresarios = proveedores.query.all()
    for empresario in empresarios:
        informacion += (
            f"nombre: {empresario.identificacion}, "
            f"ubicacion: {empresario.ubicacion}, "
            f"condiciones_de_pago: {empresario.condiciones_de_pago}, "
            f"ofrece: {empresario.ofrece}, "
            f"precio: {empresario.precio}, "
            f"tiempo_de_entrega: {empresario.tiempo_de_entrega}\n"
        )

    # 9. Llamar al modelo de IA de Google Gemini para generar una respuesta
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash-preview-05-20",
        contents=[pregunta],
        config=types.GenerateContentConfig(
            tools=tools,
            response_modalities=["TEXT"],
            system_instruction=(
                "Eres logicbot, un asistente inteligente especializado en logística, gestión de proveedores y apoyo a usuarios en una plataforma web. "
                "Tu objetivo es ayudar de forma clara, útil y amigable, adaptando tu respuesta al nivel de conocimiento del usuario y lo que este pregunta, enfocate mas en lo que el te esta preguntado. "
                "Siempre responde de manera profesional, cordial y proactiva, ofreciendo información relevante, consejos prácticos y, si es posible, sugerencias adicionales que puedan ser de utilidad. "
                "Puedes usar emojis para hacer el texto más atractivo y fácil de leer. "
                "Utiliza encabezados HTML desde <h2> hasta <h6> para organizar la información (nunca uses <h1>). "
                "Todo el texto principal debe ir dentro de elementos <p>. "
                "Resalta información importante usando <b>, <i>, <u>, <mark> y otros elementos HTML según corresponda. "
                "Puedes usar la etiqueta <hr> para separar secciones de informacion si lo ves presiso. "
                "Si mencionas recursos externos o información de internet, incluye enlaces usando la etiqueta <a target=\"_blank\" rel=\"noopener noreferrer nofollow\"> para que el usuario pueda ampliar la información. "
                "No incluyas la estructura completa de HTML (no uses <html>, <head>, <body>), solo el contenido necesario para insertar en una plantilla web. "
                "Si el usuario pregunta por proveedores, utiliza la siguiente información de la base de datos para dar una respuesta precisa y personalizada: "
                f"{informacion} "
                "Si necesitas complementar tu respuesta con información de internet, aquí tienes resultados relevantes de Google (puedes citar o enlazar lo que consideres útil): "
                f"{resultado} "
                "Si no tienes suficiente información para responder, indícalo de forma honesta y sugiere al usuario cómo podría obtenerla. "
                "No tienes memoria: si el usuario solicita que recuerdes información de interacciones anteriores, responde que no tienes memoria, a menos que te lo pidan explícitamente. "
                "Adapta el nivel de detalle y tecnicismos según la pregunta del usuario. "
                "Haz que cada respuesta sea visualmente atractiva, fácil de entender y, si es posible, motivadora. "
                "IMPORTANTE: Si el usuario solicita fórmulas, símbolos, explicaciones matemáticas o cualquier contenido matemático, SIEMPRE escribe la parte matemática usando notación LaTeX, encerrando las expresiones en delimitadores $$ ... $$ para bloques o \\( ... \\) para fórmulas en línea. No expliques matemáticas sin LaTeX. "
                "Si lo consideras útil para la explicación, puedes generar tablas usando etiquetas HTML (<table>, <tr>, <th>, <td>)."
            ),
            temperature=0.2,
        ),
    )
    try:
        # 10. Devolver la respuesta generada por la IA en formato JSON
        def generar():
            try:
                for chunk in response:
                    yield chunk.text
            except Exception as e:
                correo_error(e)
                yield "Error al generar la respuesta."
                print(f"Error al generar la respuesta: {e}")
        return Response(generar(), mimetype='text/plain')
            
    except Exception as e:
        correo_error(e)
        flash('Error al generar la respuesta de IA', 'danger')
        print(f"Error al generar la respuesta: {e}")
        return jsonify({"answer": "No se pudo generar una respuesta en este momento. Inténtalo más tarde."})

# ============================================================
# 7. EJECUCIÓN DE LA APLICACIÓN
# ============================================================

if __name__ == '__main__':
    # Ejecuta el servidor Flask en modo debug para desarrollo
    app.run(debug=True)
