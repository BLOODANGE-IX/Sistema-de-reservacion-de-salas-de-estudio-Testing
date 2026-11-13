import os
import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.contrib.auth.models import User
from reservaciones.models import Sala, Reservacion

# Configurar Django para que Behave pueda usar la BD
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def before_all(context):
    # Configurar Selenium para que corra en modo Headless (sin ventana)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Conectarse al contenedor de Selenium
    context.driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    # Usamos el nombre del servicio de Docker para la URL
    context.base_url = "http://app:8000" 

def before_scenario(context, scenario):
    # Limpiar la base de datos antes de cada escenario para que sea determinista
    Reservacion.objects.all().delete()
    Sala.objects.all().delete()
    User.objects.all().delete()

    # Crear usuario de prueba
    context.user = User.objects.create_user(username='bdd_user', password='password123')

    # Crear salas de prueba (una activa y una inactiva)
    context.sala_a = Sala.objects.create(nombre="Sala A", ubicacion="Biblioteca, planta baja", capacidad=4, activa=True)
    context.sala_inactiva = Sala.objects.create(nombre="Sala Mantenimiento", ubicacion="Piso 2", capacidad=6, activa=False)

def after_all(context):
    # Cerrar el navegador al final
    context.driver.quit()