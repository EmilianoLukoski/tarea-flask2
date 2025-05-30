from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import os, logging
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
import logging, os, ssl, socket
import certifi
import asyncio
from aiomqtt import Client, MqttError
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/tareaflask2'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configuración de entorno
MQTT_BROKER = os.getenv("MQTT_BROKER")  # Nombre de servicio Docker o IP
MQTT_PORT = int(os.getenv("MQTT_PORT"))  # Puerto TLS
MQTT_USER = os.getenv("MQTT_USR")  # Cambiado de MQTT_USER a MQTT_USR
MQTT_PASS = os.getenv("MQTT_PASS")

# Configuración MQTT
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

async def publish_mqtt(topic: str, payload: str):
    try:
        # Verificación DNS
        try:
            ip = socket.gethostbyname(MQTT_BROKER)
            logging.info(f"Resolución DNS: {MQTT_BROKER} → {ip}")
        except socket.gaierror:
            logging.error(f"Error DNS: {MQTT_BROKER} no se resuelve")
            return False

        # Conexión y publicación en un solo bloque async
        async with Client(
            MQTT_BROKER,
            port=MQTT_PORT,
            username=MQTT_USER,
            password=MQTT_PASS,
            tls_context=ssl_context
        ) as client:
            logging.info(f"Conectado a {MQTT_BROKER}:{MQTT_PORT} con TLS certificado")
            logging.info(f"Publicando en {topic}: {payload}")
            await client.publish(topic, payload, qos=1)
            logging.info("Publicación exitosa")
            return True
    except MqttError as e:
        logging.error(f"Error MQTT: {e}")
        logging.error(f"Configuración MQTT - Broker: {MQTT_BROKER}, Puerto: {MQTT_PORT}, Usuario: {MQTT_USER}")
        return False
    except Exception as e:
        logging.error(f"Error inesperado en MQTT: {str(e)}")
        return False

@app.before_request
def before_request():
    if request.script_root != app.config['APPLICATION_ROOT']:
        request.environ['SCRIPT_NAME'] = app.config['APPLICATION_ROOT']

# Configuración general
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config["PERMANENT_SESSION_LIFETIME"] = 300

# Logging
logging.basicConfig(format='%(asctime)s - CRUD - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializar la base de datos
mysql = MySQL(app)

# Verificar conexión a la base de datos
try:
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        logging.info(f"Conexión a la base de datos establecida correctamente en {app.config['MYSQL_HOST']}")
except Exception as e:
    logging.error(f"Error al conectar con la base de datos: {str(e)}")
    raise

# Rutas

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Modificar la ruta principal para consultar y pasar la lista de nodos
@app.route('/')
@require_login
def index():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, id_dispositivo FROM nodos")
        nodos = cur.fetchall()
        
        # Obtener la preferencia de tema del usuario
        cur.execute("SELECT tema FROM usuarios WHERE usuario = %s", (session.get("user_id"),))
        tema_result = cur.fetchone()
        tema_preferido = tema_result[0] if tema_result else 0
        
        # Obtener el dispositivo seleccionado de la sesión
        dispositivo_seleccionado = session.get("id_dispositivo")
        
        cur.close()
        return render_template('bienvenida.html', 
                             username=session.get("user_id"), 
                             nodos=nodos,
                             tema_preferido=tema_preferido,
                             dispositivo_seleccionado=dispositivo_seleccionado)
    except Exception as e:
        logging.error(f"Error al obtener nodos: {str(e)}")
        flash("Error al cargar la lista de nodos")
        return redirect(url_for('index'))

@app.route('/seleccionar_dispositivo', methods=['POST'])
@require_login
def seleccionar_dispositivo():
    try:
        id_dispositivo = request.form.get('id_dispositivo')
        if id_dispositivo:
            session['id_dispositivo'] = id_dispositivo
            flash(f"Dispositivo seleccionado correctamente", "success")
        else:
            flash("No se seleccionó ningún dispositivo", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error al seleccionar dispositivo: {str(e)}")
        flash("Error al seleccionar el dispositivo", "danger")
        return redirect(url_for('index'))

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        try:
            usuario = request.form.get("usuario")
            password = request.form.get("password")
            
            if not usuario:
                flash("El campo usuario es obligatorio", "danger")
                return redirect(url_for('registrar'))
            elif not password:
                flash("El campo contraseña es obligatorio", "danger")
                return redirect(url_for('registrar'))
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
            if cur.fetchone():
                flash("El usuario ya existe", "danger")
                return redirect(url_for('registrar'))
            
            passhash = generate_password_hash(password, method='scrypt', salt_length=16)
            cur.execute("INSERT INTO usuarios (usuario, hash) VALUES (%s, %s)", (usuario, passhash[17:]))
            mysql.connection.commit()
            cur.close()
            
            flash("¡Usuario creado con éxito! Por favor inicie sesión", "success")
            logging.info("Se agregó un usuario")
            return redirect(url_for('login'))
            
        except Exception as e:
            logging.error(f"Error en el registro: {str(e)}")
            flash('Error al registrar el usuario. Por favor, intente nuevamente.', "danger")
            return redirect(url_for('registrar'))
            
    return render_template('registrar.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            usuario = request.form.get("usuario")
            password = request.form.get("password")
            
            logging.info(f"Intento de login para usuario: {usuario}")
            
            if not usuario:
                flash("El campo usuario es obligatorio", "danger")
                return redirect(url_for('login'))
            elif not password:
                flash("El campo contraseña es obligatorio", "danger")
                return redirect(url_for('login'))

            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
            rows = cur.fetchone()
            
            if rows and check_password_hash('scrypt:32768:8:1$' + rows[2], password):
                session.permanent = True
                session["user_id"] = usuario
                session["tema"] = rows[3]  # Guardar la preferencia de tema en la sesión
                logging.info(f"Usuario autenticado exitosamente: {usuario}")
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrecto', "danger")
                logging.warning(f"Intento de login fallido para usuario: {usuario}")
                return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error en el login: {str(e)}")
            flash('Error al iniciar sesión. Por favor, intente nuevamente.', "danger")
            return redirect(url_for('login'))
        finally:
            if 'cur' in locals():
                cur.close()
            
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# Configuración para manejar CORS y respuestas JSON
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Nuevas rutas para el control de nodos
@app.route('/flash', methods=['POST'])
@require_login
def flash_command():
    try:
        id_dispositivo = session.get("id_dispositivo")
        if not id_dispositivo:
            flash("No hay dispositivo seleccionado", "danger")
            return redirect(url_for('index'))
            
        topic = f"{id_dispositivo}/destello"
        payload = "1"
        
        # Ejecutar la publicación MQTT de forma asíncrona
        success = asyncio.run(publish_mqtt(topic, payload))
        
        if success:
            flash("Comando de destello enviado correctamente", "success")
        else:
            flash("Error al enviar el comando de destello. Verifique la conexión MQTT.", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error al procesar comando de destello: {str(e)}")
        flash('Error al enviar el comando de destello', "danger")
        return redirect(url_for('index'))

@app.route('/setpoint', methods=['GET', 'POST'])
@require_login
def setpoint_command():
    try:
        id_dispositivo = session.get("id_dispositivo")
        if not id_dispositivo:
            flash("No hay dispositivo seleccionado", "danger")
            return redirect(url_for('index'))
            
        topic = f"{id_dispositivo}/setpoint"
        
        if request.method == 'GET':
            setpoint = request.args.get('setpoint')
            if not setpoint or setpoint.strip() == '':
                logging.info("Intento de actualizar setpoint sin valor")
                flash("No se proporcionó un valor de setpoint", "danger")
                return redirect(url_for('index'))
            
            # Ejecutar la publicación MQTT de forma asíncrona
            success = asyncio.run(publish_mqtt(topic, setpoint))
            
            if success:
                flash(f"Setpoint actualizado correctamente a {setpoint}", "success")
            else:
                flash("Error al actualizar el setpoint. Verifique la conexión MQTT.", "danger")
            return redirect(url_for('index'))
            
        # Para POST mantenemos el comportamiento actual
        logging.info("Recibida petición POST a /setpoint")
        flash("Setpoint actualizado correctamente", "success")
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error al procesar setpoint: {str(e)}")
        flash('Error al actualizar el setpoint', "danger")
        return redirect(url_for('index'))

@app.route('/values', methods=['GET'])
@require_login
def get_values():
    return jsonify({
        "flash": 1,
        "setpoint": 0.0
    }), 200

@app.route('/agregar_nodo', methods=['GET', 'POST'])
@require_login
def agregar_nodo():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            id_dispositivo = request.form.get('id_dispositivo')
            
            if not nombre or not id_dispositivo:
                flash("Todos los campos son obligatorios", "danger")
                return redirect(url_for('agregar_nodo'))
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO nodos (nombre, id_dispositivo) VALUES (%s, %s)", (nombre, id_dispositivo))
            mysql.connection.commit()
            cur.close()
            
            flash("¡Nodo agregado correctamente!", "success")
            return redirect(url_for('index'))
            
        except Exception as e:
            logging.error(f"Error al agregar nodo: {str(e)}")
            flash('Error al agregar el nodo. Por favor, intente nuevamente.', "danger")
            return redirect(url_for('agregar_nodo'))
    
    # Obtener la preferencia de tema del usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT tema FROM usuarios WHERE usuario = %s", (session.get("user_id"),))
    tema_result = cur.fetchone()
    tema_preferido = tema_result[0] if tema_result else 0
    cur.close()
    
    return render_template('agregar_nodo.html', tema_preferido=tema_preferido)

@app.route('/actualizar_tema', methods=['POST'])
@require_login
def actualizar_tema():
    try:
        tema = request.form.get('tema')
        if tema is not None:
            tema_valor = 1 if tema == 'dark' else 0
            cur = mysql.connection.cursor()
            cur.execute("UPDATE usuarios SET tema = %s WHERE usuario = %s", 
                       (tema_valor, session.get("user_id")))
            mysql.connection.commit()
            cur.close()
            return jsonify({"success": True}), 200
        return jsonify({"error": "No se proporcionó tema"}), 400
    except Exception as e:
        logging.error(f"Error al actualizar tema: {str(e)}")
        return jsonify({"error": "Error al actualizar tema"}), 500