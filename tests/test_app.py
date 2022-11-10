import os
import tempfile
from pybase64 import b64encode

import pytest
from flask import Flask, url_for
from app import app

from unittest import mock

from models.entities import User


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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








