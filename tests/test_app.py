import os
import tempfile
from pybase64 import b64encode
from requests.auth import _basic_auth_str
import pytest
from flask import Flask, url_for
from app import app
import unittest
from unittest import mock
from flask_login import LoginManager
from flask_mysqldb import MySQL
from models.entities.User import User


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

#Unit test

def test_new_user(client):
    user = User(1, '293293-4', 'end', '123', '2', 'Sebastian', 'Ortega', '1', '569-3283283', 'Walker Martinez 3200', 'test@inacapmail.cl', '1', 'image.png')
    assert user.id == 1
    assert user.rut == '293293-4'
    assert user.username == 'end'
    assert user.password == '123'
    assert user.comuna == '2'
    assert user.nombre == 'Sebastian'
    assert user.apellidos == 'Ortega'
    assert user.tipoUsuario == '1'
    assert user.telefono == '569-3283283'
    assert user.direccion == 'Walker Martinez 3200'
    assert user.correo == 'test@inacapmail.cl'
    assert user.tipoSexo == '1'
    assert user.imagen == 'image.png'


##Functional test

def test_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_admin(client):
    response = client.get('/menuAdministrador')
    assert response.status_code == 401

def test_login_docente(client):
    response = client.get('/menuDocente')
    assert response.status_code == 401

def test_login_estudiante(client):
    response = client.get('/menuEstudiante')
    assert response.status_code == 401










