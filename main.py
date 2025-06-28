# ============================================================
# main.py - Aplicación principal Flask para gestión logística
# ============================================================
# Autor: Luis Angel
# Descripción: Plataforma web para gestión de proveedores, usuarios,
# rutas, inteligencia artificial y utilidades logísticas.
# ============================================================

# ============================================================
# 1. IMPORTACIÓN DE LIBRERÍAS Y SERVICIOS
# ============================================================

# --- Librerías de IA y búsqueda ---
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from serpapi import GoogleSearch as Gg

# --- Librerías de Flask y extensiones ---
from flask import (
    Flask, render_template, url_for, request, flash, redirect,
    send_file, session, jsonify, Response, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

# --- Seguridad y utilidades ---
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
from functools import wraps
import io
import time
import os
from datetime import datetime, timedelta
# --- Servicios personalizados ---
from services.correo import correo_error, qr, limpiar_archivos_expirados
from services.Ruta import *
from services.Ruta import minutos_a_tiempo
# ============================================================
# 2. CONFIGURACIÓN DE LA APLICACIÓN Y EXTENSIONES
# ============================================================

app = Flask(__name__)

# --- Configuración de claves y clientes externos ---
client = genai.Client(api_key="AIzaSyBGxDkqcairULlOIvMycALEvclJn3-e-_o")
Clav = "AIzaSyBi_IAVJo42jH0ziRi72nO5XrU9DM7dFcE"
key = "c4ea6b07cbade43b7a7c7955016ffc9463975b858b0ccb50863bdc57e40bf1c8"  # SerpApi
POIs = "5b3ce3597851110001cf6248c78a74e4d1fd423588a0378499a42c6d"

# --- Configuración de base de datos ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Configuración de seguridad y correo ---
app.secret_key = 'a94a8fe5cc5c2b0e5d8cb6e00392e5ed5557788983e1f915d2cdf697ec811b17'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisangelacu10@gmail.com'
app.config['MAIL_PASSWORD'] = 'udjv nbdw qkxd hddf'
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
# 4. DECORADORES Y UTILIDADES DE AUTENTICACIÓN
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

# ============================================================
# 5. RUTAS PRINCIPALES Y DE NAVEGACIÓN
# ============================================================

@app.route("/limpiar")
def ruta_limpieza():
    eliminados = limpiar_archivos_expirados()
    return jsonify({
        "status": "ok",
        "archivos_eliminados": eliminados,
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
# --- Registro de usuario con TOTP ---
@app.route('/usuario/<key>', methods=['GET', 'POST'])
def usuario(key):
    SECRET_TOTP = "MILH6SJUVAPI6UFEDZ633CTNPRVJULV5"
    totp = pyotp.TOTP(SECRET_TOTP)
    if totp.verify(str(key), valid_window=1):
        try:
            if request.method == 'POST':
                user = Usuarios(
                    Usuario = request.form.get('User'),
                    correo = request.form.get('Email'),
                    contraseña = generate_password_hash(request.form.get('Pas'))
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

# --- Página de inicio y formulario de contacto ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/inicio', methods=['GET', 'POST'])
def index():
    """
    Página de inicio. Permite enviar un correo desde un formulario.
    Si el método es POST, procesa el formulario y envía un correo.
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        mensaje = request.form.get('Mensage')
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

# --- Navegación a otras secciones ---
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
# ============================================================
# 5. OPTIMIZACIÓN DE RUTAS
# ============================================================
@app.route('/optimizacion_de_rutas')
def optimizacion_de_rutas():
    return render_template('Optimizacion-de-rutas/Optimizacion-de-rutas.html')
# ============================================================
# 2 rutas sin retorno
# ============================================================
@app.route('/optimizacion_de_rutas/Solo-2-rutas', methods=['GET', 'POST'])
def solo_2_rutas():
    if request.method == 'POST':
        try:
            inicio = obtener_coordenadas(request.form.get('Hubicacion1'))
            destino = obtener_coordenadas(request.form.get('Hubicacion2'))
            vehiculo = request.form.get('vehiculo')  # Valor por defecto si no se selecciona

            distancia, duracion, direccion_mapa, asenso, descenso = ruta_logistica_simple(
                inicio, destino, vehiculo, POIs, nombre_mapa=f"ruta_mapa{inicio}-{destino}.html"
            )
            distancia = round(distancia, 2)
            duracion = minutos_a_tiempo(duracion)
            if asenso == 0:
                asenso = "No hay ascenso"
            if descenso == 0:
                descenso = "No hay descenso"

            return redirect(url_for(
                'solo_2_rutas_mapa_info',
                distancia=distancia,
                duracion=duracion,
                direccion_mapa=direccion_mapa,
                asenso=asenso,
                descenso=descenso
            ))
        except Exception as e:
            print(f"Error al calcular la ruta: {e}")
            flash('Ocurrió un error al calcular la ruta. Por favor, revisa los datos ingresados o intenta más tarde.', 'danger')
            correo_error(e)
            return redirect(url_for('solo_2_rutas'))

    return render_template('Optimizacion-de-rutas/Solo-2-rutas.html')

@app.route('/optimizacion_de_rutas/Solo-2-rutas-mapa/<distancia>/<duracion>/<direccion_mapa>/<asenso>/<descenso>', methods=['GET', 'POST'])
def solo_2_rutas_mapa_info(distancia, duracion, direccion_mapa, asenso, descenso):

    return render_template('Optimizacion-de-rutas/Info-2ruta.html', distancia=distancia, duracion=duracion, direccion_mapa=direccion_mapa, asenso=asenso, descenso=descenso)

@app.route('/mapas/<filename>')
def mostrar_mapa(filename):
    carpeta = os.path.join(os.getcwd(), "templates", "Optimizacion-de-rutas", "temp")
    return send_from_directory(carpeta, filename)
# ============================================================
# Mas de 2 rutas sin retorno
# ============================================================
@app.route('/optimizacion_de_rutas/Mas-de-2-rutas-sin-retorno_cantidad', methods=['GET', 'POST'])
def mas_de_2_rutas_sin_retorno_cantidad():
    if request.method == 'POST':
        
        cantidad = request.form.get('cantidad')
        
        return redirect(url_for('mas_de_2_rutas_sin_retorno', cantidad=cantidad))
    
    return render_template('Optimizacion-de-rutas/Mas-de-2-rutas-sin-retorno-cantidad.html')

@app.route('/optimizacion_de_rutas/Mas-de-2-rutas-sin-retorno/<cantidad>', methods=['GET', 'POST'])
def mas_de_2_rutas_sin_retorno(cantidad):
    if request.method == 'POST':
        rutas = []
        for i in range(int(cantidad)):
            ruta = obtener_coordenadas(request.form.get(f'ruta{i+1}'))
            rutas.append(ruta)
            time.sleep(2)
        return render_template('Optimizacion-de-rutas/Mas-de-2-rutas-sin-retorno.html', rutas=rutas)
    return render_template('Optimizacion-de-rutas/Mas-de-2-rutas-sin-retorno.html', cantidad=int(cantidad))

@app.route('/gestion_de_vehiculos')
def gestion_de_vehiculos():
    """Página de gestión de vehículos."""
    return render_template('Gestion-de-vehiculos.html')

# ============================================================
# 6. AUTENTICACIÓN Y GESTIÓN DE USUARIOS
# ============================================================

@app.route('/comprobar_usuario', methods=['GET', 'POST'])
def comprobar_usuario():
    """
    Ruta para inicio de sesión de usuarios.
    Verifica usuario, correo y contraseña. Si es correcto, inicia sesión.
    """
    if request.method == 'POST':
        User = request.form.get('usuario')
        corre = request.form.get('correo')
        contra = request.form.get('password')
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

# ============================================================
# 7. CRUD DE PROVEEDORES
# ============================================================

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
        proveedor = request.form.get('proveedor')
        Contacto = request.form.get('Contacto')
        Ubicacion = request.form.get('Ubicacion')
        Condicion = request.form.get('Condicion')
        ofrece = request.form.get('ofrece')
        Precio = request.form.get('Precio')
        tiempo = request.form.get('tiempo')
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
        proveedor.identificacion = request.form.get('proveedor')
        proveedor.contacto = request.form.get('Contacto')
        proveedor.ubicacion = request.form.get('Ubicacion')
        proveedor.condiciones_de_pago = request.form.get('Condicion')
        proveedor.ofrece = request.form.get('ofrece')
        proveedor.precio = request.form.get('Precio')
        proveedor.tiempo_de_entrega = request.form.get('tiempo')
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
# 8. INTELIGENCIA ARTIFICIAL (IA)
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
    """
    Ruta para consultar la IA.
    1. Recibe una pregunta del usuario.
    2. Realiza una búsqueda en Google usando SerpApi.
    3. Extrae preguntas relacionadas y respuestas.
    4. Consulta la base de datos de proveedores.
    5. Llama al modelo de IA de Google Gemini para generar una respuesta personalizada.
    6. Devuelve la respuesta en formato JSON.
    """
    pregunta = request.json.get('question')
    data = request.get_json()
    wifi = data.get('wifi')
    busco = ""
    resultado = ""
    params = {
        "q": pregunta,
        "location": "Mexico",
        "hl": "es",
        "gl": "mx",
        "google_domain": "google.com.mx",
        "api_key": key
    }
    if wifi is False:
        try:
            search = Gg(params)
            result = search.get_dict()
        except Exception as e:
            correo_error(e)
            resultado = "Error en la búsqueda."
        else:
            Contenido = result.get("related_questions", [])
            for solicitud in Contenido:
                snippet = solicitud.get('snippet')
                lista = solicitud.get('list')
                respuesta = snippet if snippet is not None else (lista if lista is not None else "Sin respuesta")
                busco += f"Respuesta: {respuesta}\n, link: {solicitud.get('link','')}\n"
            resultado = busco
    else:
        resultado = "El usuario no ha pedido búsqueda en intent."

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
# 9. EJECUCIÓN DE LA APLICACIÓN
# ============================================================

if __name__ == '__main__':
    # Ejecuta el servidor Flask en modo debug para desarrollo
    app.run(debug=True)