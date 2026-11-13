import os
import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. PRIMERO configuramos Django y lo iniciamos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. DESPUÉS (y solo después) importamos los modelos
from django.contrib.auth.models import User
from reservaciones.models import Sala, Reservacion


def before_all(context):
    print("========== BEFORE_ALL EJECUTADO ==========") # Para confirmar que entra
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-features=HttpsUpgrades")
    
    context.driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    context.base_url = "http://reservaciones-app:8000" 

def before_scenario(context, scenario):
    # Limpiamos la base de datos
    Reservacion.objects.all().delete()
    Sala.objects.all().delete()
    User.objects.all().delete()

    # Creamos los datos de prueba
    context.user = User.objects.create_user(username='bdd_user', password='password123')
    context.sala_a = Sala.objects.create(nombre="Sala A", ubicacion="Biblioteca, planta baja", capacidad=4, activa=True)
    context.sala_inactiva = Sala.objects.create(nombre="Sala Mantenimiento", ubicacion="Piso 2", capacidad=6, activa=False)

def after_all(context):
    context.driver.quit()