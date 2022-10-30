from wsgiref.validate import validator
from xml.dom import ValidationErr
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect  # Para el token de protección
from flask_login import LoginManager, login_user, logout_user, login_required

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *

import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
import mediapipe as mp
import pandas as pd
import pickle

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

app.secret_key = 'B!1w8NAt1T^%kvhUI*S^'
csrf = CSRFProtect(app)

db = MySQL(app)
login_manager_app = LoginManager(app)

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


@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def pindex():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form=LoginForm()
    if request.method == 'POST':
         user = User(0, 1, form.username.data,
                     form.password.data, 4, 5, 6, 7, 8, 9, 10, 11)
         logged_user = ModelUser.login(db, user)
         if logged_user != None:
             if logged_user.password:
                 login_user(logged_user)
                 return redirect(url_for('home'))
             else:
                 flash("Clave Incorrecta...")
                 return render_template('auth/login.html', form=form)
         else:
             print("Usuario no encontrado")
             flash("Usuario no encontrado...")
             return render_template('auth/login.html', form=form)
    else:
         return render_template('auth/login.html', form=form)   


@app.route('/home')
@login_required  # Login necesario, si no, tira error.
def home():
    return render_template('auth/home.html')

@app.route('/aprende')
def aprende():
    return render_template('aprende.html')

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
    cur.execute('SELECT U.id, U.rut, U.username, U.password, C.nombre FROM usuario U JOIN comunas C ON U.comuna = C.codCom;')
    data = cur.fetchall()
    print(type(data))
    return render_template('edit.html', usuarios = data)

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
        cur.execute("CALL AgregarUsuarioI(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (rut, username, password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoSexo))
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


if __name__ == '__main__':
    app.run(debug=True)