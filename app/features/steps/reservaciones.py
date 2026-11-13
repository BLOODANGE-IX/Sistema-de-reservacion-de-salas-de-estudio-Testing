from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, timedelta
import time

@given('que existe una sala activa con capacidad suficiente')
def step_impl(context):
    # La sala ya se creó en environment.py
    pass

@given('el usuario ha iniciado sesión')
def step_impl(context):
    context.driver.get(f"{context.base_url}/accounts/login/")
    
    # Esperar a que cargue el formulario de login
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    
    context.driver.find_element(By.NAME, "username").send_keys("bdd_user")
    context.driver.find_element(By.NAME, "password").send_keys("password123")
    context.driver.find_element(By.XPATH, "//button[@type='submit']").click()

@given('no existe otra reservación vigente que se traslape con el horario solicitado')
def step_impl(context):
    pass # Asumimos que está limpio

@when('captura una fecha válida, una hora de inicio y una hora de fin válidas')
def step_impl(context):
    context.driver.get(f"{context.base_url}/nueva/")
    manana = date.today() + timedelta(days=1)
    
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "fecha"))
    )
    
    context.driver.find_element(By.NAME, "fecha").send_keys(manana.strftime("%Y-%m-%d"))
    context.driver.find_element(By.NAME, "hora_inicio").send_keys("10:00")
    context.driver.find_element(By.NAME, "hora_fin").send_keys("11:00")

@when('captura un número de asistentes permitido y un propósito válido')
def step_impl(context):
    # Seleccionar la sala usando el ID
    Select(context.driver.find_element(By.NAME, "sala")).select_by_value(str(context.sala_a.id))
    
    context.driver.find_element(By.NAME, "asistentes").send_keys("3")
    context.driver.find_element(By.NAME, "proposito").send_keys("Estudiar para el examen de BDD")

@when('envía el formulario')
def step_impl(context):
    context.driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2) # Esperar que el servidor procese el POST

@then('el sistema registra la reservación con estado "VIGENTE"')
def step_impl(context):
    from reservaciones.models import Reservacion
    reserva = Reservacion.objects.first()
    assert reserva is not None
    assert reserva.estado == 'VIGENTE'

@then('muestra un mensaje de confirmación')
def step_impl(context):
    assert "Reservación registrada exitosamente" in context.driver.page_source

@then('la reservación aparece en la lista de reservaciones del usuario')
def step_impl(context):
    assert "Sala A" in context.driver.page_source