#from werkzeug.security import check_password_hash
from flask_login import UserMixin  # Atributo para las sesiones
#from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin):

    def __init__(self, id, rut, username, password, comuna, nombre, apellidos, tipoUsuario, telefono, direccion, correo, tipoSexo):
        self.id = id
        self.rut = rut
        self.username = username
        self.password = password
        self.comuna = comuna
        self.nombre = nombre
        self.apellidos = apellidos
        self.tipoUsuario = tipoUsuario
        self.telefono = telefono
        self.direccion = direccion
        self.correo = correo
        self.tipoSexo = tipoSexo

       
    @classmethod
    def check_password(self, password, password2):
        if(password == password2):
            return True



#print(generate_password_hash("123"))

