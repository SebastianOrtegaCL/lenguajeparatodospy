from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect  # Para el token de protección
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
#libreria para crear random en StringAleatorio
from random import sample
import openpyxl
from werkzeug.utils import secure_filename
import cv2
import datetime, time
import os
import numpy as np
from threading import Thread
import mediapipe as mp
import pandas as pd
import pickle

from base64 import b64encode

# Modelos
from models.ModelUser import ModelUser

# Entidades
from models.entities.User import User

global capture,rec_frame, grey, switch, neg, face, rec, out 
capture=0
grey=0
neg=0
face=0
switch=1
rec=0

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_drawing_styles = mp.solutions.drawing_styles

app = Flask(__name__)

app.secret_key = 'B!1w8NAt1T^%kvhUI*S^'
csrf = CSRFProtect(app)

db = MySQL(app)
login_manager_app = LoginManager(app)

app.config['DEBUG'] = True
app.config['MYSQL_HOST'] = 'lenguajeparatodoos.mariadb.database.azure.com'
app.config['MYSQL_USER'] = 'administrador@lenguajeparatodoos'
app.config['MYSQL_PASSWORD'] = 'Lenguaje123'
app.config['MYSQL_DB'] = 'lenguajeparatodos'
app.config['MYSQL_PORT'] = 3306

# app.config['DEBUG'] = True
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'clave'
# app.config['MYSQL_DB'] = 'lenguajeparatodos'
# app.config['MYSQL_PORT'] = 3306

    

def image_processed(hand_img):
    #BGR to RGB
    img_rgb = cv2.cvtColor(hand_img, cv2.COLOR_BGR2RGB)

    img_flip = cv2.flip(img_rgb, 1)


    hands = mp_hands.Hands(static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.7)   

    output = hands.process(img_flip)

    hands.close()

    try:
        data = output.multi_hand_landmarks[0]
        data = str(data)

        data = data.strip().split('\n')

        garbage = ['landmark {', ' visibility: 0.0', ' presence: 0.0', '}']

        without_garbage = []

        for i in data:
            if i not in garbage:
                without_garbage.append(i)
        clean = []

        for i in without_garbage:
            i = i.strip()
            clean.append(i[2:])

        for i in range(0, len(clean)):
            clean[i] = float(clean[i])
        return (clean)
    except:
        return(np.zeros([1,63], dtype=int)[0])

def gen_frames():  # generate frame by frame from camera
    camera = cv2.VideoCapture(0)
    with open('model.pkl', 'rb') as f:
        svm = pickle.load(f)
    global out, capture,rec_frame
    while True:
        success, frame = camera.read() 
        data = image_processed(frame)
        data = np.array(data)
        y_pred = svm.predict(data.reshape(-1, 63))
        print(y_pred)
        font = cv2.FONT_HERSHEY_SIMPLEX

        org = (50, 100)

        fontScale = 3

        color = (255, 0, 0)

        thickness = 5

        frame = cv2.putText(frame, str(y_pred[0]),
        org, font, fontScale, color, thickness, cv2.LINE_AA)

        if success:
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
        else:
            pass


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=1, max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=1, max=30)])

class LoginRegisterForm(FlaskForm):
    rut = StringField('rut', validators=[InputRequired()])
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    comuna = StringField('comuna', validators=[InputRequired()])
    nombre = StringField('nombre', validators=[InputRequired()])
    apellido = StringField('apellidos', validators=[InputRequired()])
    tipoUsuario = StringField('tipoUsuario', validators=[InputRequired()])
    telefono = StringField('telefono', validators=[InputRequired()])
    direccion = StringField('direccion', validators=[InputRequired()])
    correo = StringField('correo', validators=[InputRequired()])
    tiposexo = StringField('tiposexo', validators=[InputRequired()])
###
class UserForm(FlaskForm):
    nombre = StringField('Nombre', validators=[InputRequired(), Length(min=3, max=25)])
    apellidos = StringField('Apellido', validators=[InputRequired(), Length(min=3, max=25)])
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=25)])
    password = PasswordField('Contraseña', validators=[InputRequired(),])
    correo = EmailField('Correo', validators=[InputRequired()])
    imagen = FileField('Sube tu foto de perfil', validators=[InputRequired()])

@app.route('/tareas', methods=['POST', 'GET'])
def tareas():
    if request.method == 'POST':
        contenido = request.form['content']
        creado_por = current_user.id
        print(contenido, creado_por)
        try:
            cur = db.connection.cursor()
            cur.execute("INSERT INTO tabla_tareas (contenido, creado_por) VALUES (%s, %s)", [contenido, creado_por])
            db.connection.commit()
            return redirect('/tareas')
        except:
            return 'No se ha podido agregar la tarea'
    else:
        cur = db.connection.cursor()
        cur.execute('SELECT * FROM tabla_tareas WHERE creado_por = {}'.format(current_user.id))
        # SELECT * FROM tabla_tareas WHERE creado_por = 19;
                # WHERE id = {}'.format(id)
        tasks = cur.fetchall()
        return render_template('tarea.html', tasks=tasks)

@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def eliminar_tarea(id):
    try:
        cur = db.connection.cursor()
        cur.execute("CALL EliminarTarea(%s)", (id,))
        db.connection.commit()
        return redirect('/tareas')
    except:
        return 'No se ha podido eliminar la tarea'
    

@app.route('/perfil', methods=['GET'])
@login_required
def perfil():
    return render_template('perfil.html')

#Método para crear nombre aleatorio de la imagen
def stringAleatorio():
    #Generando string aleatorio
    string_aleatorio = "0123456789abcdefghijklmnopqrstuvwxyz_"
    longitud         = 20
    secuencia        = string_aleatorio.upper()
    resultado_aleatorio  = sample(secuencia, longitud)
    string_aleatorio     = "".join(resultado_aleatorio)
    return string_aleatorio

#Actualizar Perfil unitario
@app.route('/perfil/update/<id>', methods=['GET', 'POST'])
@login_required
def updatePerfil(id):
    cur = db.connection.cursor()
    form = UserForm()
    cur.execute('SELECT * FROM usuario WHERE id = {}'.format(id))
    form_update = cur.fetchall()
    if request.method == 'POST' and form.validate_on_submit:
        nombre = form.nombre.data
        apellidos = form.apellidos.data
        username = form.username.data
        password = form.password.data
        correo = form.correo.data
        comuna = request.form['comuna']
        file = form.imagen.data
        basepath = os.path.dirname (__file__) #La ruta donde se encuentra el archivo actual
        filename = secure_filename(file.filename) #Nombre original del archivo
        #capturando extensión del archivo ejemplo: (.png, .jpg, .pdf ...etc)
        extension = os.path.splitext(filename)[1]
        nuevoNombreFile  = stringAleatorio() + extension

        #Guardar Archivo en la carpeta img_perfiles que se encuentra en static
        upload_path = os.path.join (basepath, 'static/img_perfiles', nuevoNombreFile) 
        file.save(upload_path)
        print('Registro: ' + nombre, apellidos, username, password, correo, comuna, nuevoNombreFile)
        try:
            cur.execute("""
                UPDATE usuario
                SET nombre = %s,
                    apellidos = %s,
                    username = %s,
                    password = %s,
                    correo = %s,
                    comuna = %s,
                    imagen = %s
                WHERE id = %s
            """, (nombre, apellidos, username, password, correo, comuna, nuevoNombreFile, id))
            db.connection.commit()
            flash("Info actualizada correctamente")
            return redirect(url_for('perfil'))
        except:
            flash("Error, datos no han podido ser modificados")
            return render_template("perfil.html", form=form,  )
    else:
        return render_template('update.html', form=form, form_update=form_update[0], )

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def pindex():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        user = User(0, 1, form.username.data,
                    form.password.data, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if logged_user.password:
                session['tipoUsuario'] = logged_user.tipoUsuario
                login_user(logged_user)

                if session['tipoUsuario'] == 1:
                    return redirect(url_for('menuAdministrador'))
                elif session['tipoUsuario'] == 2:
                    return redirect(url_for('menuDocente'))
                elif session['tipoUsuario'] == 3:
                    return redirect(url_for('menuEstudiante'))
            else:
                flash("Clave Incorrecta...")
                return render_template('auth/login.html', form=form)
        else:
            #print("Usuario no encontrado")
            flash("Usuario no encontrado...")
            return render_template('auth/login.html', form=form)
    else:
        return render_template('auth/login.html', form=form)   

@app.route('/aprende')
@login_required
def aprende():
    if 'tipoUsuario' in session:
        tipoUsuario = session['tipoUsuario']
    if tipoUsuario == 1:
        return "<h1> No tiene acceso a este modulo</h1>"
    elif tipoUsuario == 2:
        return render_template('aprende.html')
    elif tipoUsuario == 3:
        return render_template('aprende.html')
        # return render_template('error401', 400)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests', methods=['POST','GET'])
def tasks():
    global switch, camera
    if request.method == 'POST':
        if request.form.get('stop') == 'Stop/Start':
            if(switch==1):
                switch=0
                camera.release()
                cv2.destroyAllWindows()
                #flash("Cámara Apagada...")
            else:
                camera = cv2.VideoCapture(0)
                switch=1
    elif request.method == 'GET':
        return redirect(url_for('aprende'))
    return redirect(url_for('aprende'))

@app.route('/edit/')
@login_required
def Edit():
    cur = db.connection.cursor()
    cur.execute(
        'SELECT U.id, U.rut, U.nombre, U.apellidos, C.nombre, t.tipoUsuario FROM usuario U INNER JOIN comunas C ON U.comuna = C.codCom INNER JOIN tipousuario t ON U.tipousuario = t.codtipoUsuario;')
    data = cur.fetchall()
    print(type(data))
    return render_template('edit.html', usuarios=data)

@app.route('/agregarUsuario', methods=['GET', 'POST'])
@login_required
def agregarUsuario():

    cur = db.connection.cursor()
    cur.execute("SELECT * FROM tipousuario")
    tipoUsuario = cur.fetchall()

    cur = db.connection.cursor()
    cur.execute("SELECT * FROM comunas")
    comunas = cur.fetchall()

    cur = db.connection.cursor()
    cur.execute("SELECT * FROM tiposexo")
    tipoSexo = cur.fetchall()

    if request.method == 'POST':
        rut = request.form['rut']
        username = request.form['username']
        password = request.form['password']
        comuna = request.form['comuna']
        nombre = request.form['nombre']
        apellidos = request.form['apellido']
        tipoUsuario = request.form['tipoUsuario']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        correo = request.form['correo']
        tipoDeSexo = request.form['tipoSexo']
        imagen = "imagen.png"
        print('Registro' + rut, username,
                password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoDeSexo, imagen)
        try:
            cur = db.connection.cursor()
            cur.execute("CALL AgregarUsuarioI(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (rut, username,
                password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoDeSexo, imagen))
            db.connection.commit()
            flash('Usuario agregado')
            return redirect('/agregarUsuario')
        except:
            return 'No se ha podido agregar el usuario'
    else: 
        return render_template('agregarUsuario.html', tipoUsuario= tipoUsuario, comunas = comunas, tipoSexo = tipoSexo)

#Agregar Usuario simple (Excel)
@app.route('/agregarUsuarioFacil', methods=['GET', 'POST'])
@login_required
def agregarUsuarioFacil():
    print('Registro: ')

    if request.method == 'POST':
        tipoDeUsuario = request.form['tipoUsuario']
        # Script para archivo
        file = request.files['archivo']
        # La ruta donde se encuentra el archivo actual
        basepath = os.path.dirname(__file__)
        # Nombre original del archivo
        filename = secure_filename(file.filename)

        # capturando extensión del archivo ejemplo: (.png, .jpg, .pdf ...etc)
        extension = os.path.splitext(filename)[1]
        print(extension)
        nuevoNombreFile = stringAleatorio() + extension
        print(nuevoNombreFile)

        upload_path = os.path.join(
            basepath, 'static/archivos', nuevoNombreFile)
        file.save(upload_path)

        df = pd.read_excel(upload_path)

        for row, datos in df.iterrows():
            rut = str(datos['Rut'])
            nombre = str(datos['Nombre'])
            apellidos = str(datos['Apellido'])
            username = str(datos['Username'])
            password = str(datos['Password'])
            comuna = int(datos['Comuna'])
            tipoUsuario = tipoDeUsuario
            telefono = str(datos['Telefono'])
            direccion = str(datos['Direccion'])
            correo = str(datos['Correo'])
            tipoSexo = int(datos['Sexo'])
            imagen = str(datos['Imagen'])
            cur = db.connection.cursor()
            cur.execute("CALL AgregarUsuarioI(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (rut, username,
                                                                                   password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoSexo, imagen))
            db.connection.commit()
            print("Usuario agregado")
    #os.remove("static/archivos/nuevoNombreFile")
    flash("Usuario Agregado")
    return redirect(url_for('agregarUsuario'),)

@app.route('/delete/<id>')
@login_required
def delete_user(id):
    # flash(id)
    cur = db.connection.cursor()
    cur.execute("SELECT tipoUsuario FROM usuario where id=(%s)", (id,))
    data = cur.fetchall()
    tipoUsuario = data[0]

    if (tipoUsuario == (1,)):
        print("Administrador")
        flash("Se Eliminó un administrador")
        cur.execute("CALL EliminarUsuarioA_U(%s)", (id,))
        db.connection.commit()
    elif (tipoUsuario == (2,)):
        flash("Se Eliminó un profesor")
        cur.execute("CALL EliminarUsuarioP_U(%s)", (id,))
        db.connection.commit()
    else:
        flash("Otro Usuario")
        cur.execute("SELECT tipoUsuario FROM usuario WHERE id=(%s)", (id,))
        db.connection.commit()
    return redirect(url_for('Edit'))

@app.route('/menuAdministrador')
@login_required
def menuAdministrador():
    return render_template('menuAdministrador.html')

@app.route('/menuDocente')
@login_required
def menuDocente():
    return render_template('menuDocente.html')

@app.route('/menuEstudiante')
@login_required
def menuEstudiante():
    return render_template('menuEstudiante.html')

@app.route('/logout')
def logout():
    logout_user()
    # return redirect(url_for('login'))
    return render_template('index.html')
    
@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/registro', methods = ['GET', 'POST'])
def registro():
    form=LoginRegisterForm()
    # if request.method == 'POST':
    if request.method == 'POST' and form.validate_on_submit():
        rut = form.rut.data
        username = form.username.data
        password = form.password.data
        comuna = form.comuna.data
        nombre = form.nombre.data
        apellidos = form.apellido.data
        tipoUsuario = form.tipoUsuario.data
        telefono = form.telefono.data
        direccion = form.direccion.data
        correo = form.correo.data
        tipoSexo = form.tiposexo.data

        print('Registro: ' + rut, username, password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoSexo)
        
        cur = db.connection.cursor()
        cur.execute("CALL AgregarUsuarioI(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (rut, username, password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoSexo, "imagen.png"))
        db.connection.commit()
        print("Usuario agregado")
        flash("Usuario Agregado")
        return redirect(url_for('registro'),)
       
    return render_template('registro.html', form=form)

@app.route('/edit/<id>', methods=['POST', 'GET'])
@login_required
def edit_select(id):
    cur = db.connection.cursor()
    cur.execute('SELECT * FROM usuario WHERE id = {}'.format(id))
    data = cur.fetchall()
    return render_template('edit-contact.html', usuarios = data[0])

@app.route('/update/<id>', methods=['POST'])
@login_required
def update(id):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        comuna = request.form['comuna']
        cur = db.connection.cursor()
        cur.execute("""
            UPDATE usuario
            SET username = %s,
                password = %s,
                comuna = %s
            WHERE id = %s
        """, (username, password, comuna, id))
        db.connection.commit()
        return redirect(url_for('Edit'))

#Ruta Diccionario
@app.route('/diccionario')
@login_required
def diccionario():
    cur = db.connection.cursor()
    cur.execute(
        'SELECT * FROM diccionario;')
    data = cur.fetchall()
    print(type(data))
    return render_template('diccionario.html', usuarios=data)

#Ruta Agregar Diccionario
@app.route('/agregarDiccionario', methods=['POST'])
#@login.required
def agregarDiccionario():
    if request.method == 'POST':
        gesto = request.form['gesto']
        definicion = request.form['definicion']
        fuente = request.form['fuente']
        frase = request.form['frase']
        file = request.files['imagen']
        # # La ruta donde se encuentra el archivo actual
        basepath = os.path.dirname(__file__)
        #Nombre original del archivo
        filename = secure_filename(file.filename)
        # capturando extensión del archivo ejemplo: (.png, .jpg, .pdf ...etc)
        extension = os.path.splitext(filename)[1]
        nuevoNombreFile = stringAleatorio() + extension

        # Guardar Archivo en la carpeta img_perfiles que se encuentra en static
        upload_path = os.path.join(basepath, 'static/img_diccionario', nuevoNombreFile)
        file.save(upload_path)
        usuario = request.form['submit']
        print(gesto,definicion,fuente, frase,nuevoNombreFile, usuario)
        cur = db.connection.cursor()
        cur.execute("CALL AgregarGestoI(%s,%s,%s,%s,%s,%s)", (gesto,nuevoNombreFile,definicion,frase,fuente,usuario))
        db.connection.commit()
        #flash
        return redirect(url_for('diccionario'))
    else:
        #flash
        return redirect(url_for('diccionario'))

#Visualizar Contenido
@app.route('/diccionario/<id>', methods=['POST', 'GET'])
@login_required
def show_content(id):
    cur = db.connection.cursor()
    cur.execute('SELECT d.idDiccionario,d.palabra,d.imagen,d.descripcion,d.frase,t.fuente,d.creadoPor FROM diccionario d JOIN tipoFuente t ON d.tipoFuente = t.idFuente WHERE idDiccionario= %s',(id,))
    data = cur.fetchall()
    return render_template('show_content.html', palabras=data[0])

#Errores
#Error 404, página no existente
@app.errorhandler(404)
def page_not_found(err):
    return render_template("page_not_found.html"), 404

#Error 401, Unauthorized
@app.errorhandler(401)
def unauthorized(err):
    return render_template("unauthorized.html"), 401

if __name__ == '__main__':
    app.run(debug=True)