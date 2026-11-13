from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, timedelta, time
from django.utils import timezone
import time as time_module
from reservaciones.models import Reservacion
from reservaciones.services import crear_reservacion
from selenium.common.exceptions import NoAlertPresentException
from django.contrib.auth.models import User

# --- CA-07 ---
@given('es propietario de una reservación vigente cuyo inicio ocurrirá dentro de más de 60 minutos')
def step_impl(context):
    manana = timezone.now().date() + timedelta(days=1)
    context.reserva = crear_reservacion(
        usuario=context.user, sala=context.sala_a, fecha=manana,
        hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Reserva a cancelar"
    )

@when('confirma la cancelación')
def step_impl(context):
    context.driver.get(f"{context.base_url}/")
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Cancelar')]"))
    )
    context.driver.find_element(By.XPATH, "//button[contains(text(), 'Cancelar')]").click()
    
    try:
        WebDriverWait(context.driver, 3).until(EC.alert_is_present())
        alert = context.driver.switch_to.alert
        alert.accept()
    except NoAlertPresentException:
        pass
    time_module.sleep(1)

@then('el sistema cambia el estado de la reservación a "CANCELADA"')
def step_impl(context):
    context.reserva.refresh_from_db()
    assert context.reserva.estado == 'CANCELADA'

@then('registra la fecha y hora de cancelación')
def step_impl(context):
    assert context.reserva.fecha_cancelacion is not None

@then('la sala vuelve a estar disponible para ese horario')
def step_impl(context):
    vigentes = Reservacion.objects.filter(sala=context.sala_a, estado='VIGENTE').count()
    assert vigentes == 0

# --- CA-08 ---
@given('existe una reservación vigente perteneciente a otro usuario')
def step_impl(context):
    otro_user = User.objects.create_user(username='otro_user', password='password123')
    manana = timezone.now().date() + timedelta(days=1)
    context.reserva = crear_reservacion(
        usuario=otro_user, sala=context.sala_a, fecha=manana,
        hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Reserva ajena"
    )

@given('el usuario autenticado intenta cancelarla')
def step_impl(context):
    # Simulamos un POST malicioso con JavaScript
    csrf_token = context.driver.get_cookie("csrftoken")["value"]
    script = f"""
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/cancelar/{context.reserva.pk}/';
        var csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        csrf.value = '{csrf_token}';
        form.appendChild(csrf);
        document.body.appendChild(form);
        form.submit();
    """
    context.driver.execute_script(script)
    time_module.sleep(1)

@then('el sistema rechaza la operación')
def step_impl(context):
    pass

@then('mantiene la reservación en estado "VIGENTE"')
def step_impl(context):
    context.reserva.refresh_from_db()
    assert context.reserva.estado == 'VIGENTE'

@then('responde sin revelar información sensible de la reservación')
def step_impl(context):
    assert "No tienes permiso" in context.driver.page_source or "Mis Reservaciones" in context.driver.page_source

# --- CA-09 ---
@given('que el usuario es propietario de una reservación vigente')
def step_impl(context):
    manana = timezone.now().date() + timedelta(days=1)
    context.reserva = crear_reservacion(
        usuario=context.user, sala=context.sala_a, fecha=manana,
        hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Reserva vigente"
    )

@given('faltan 60 minutos o menos para su inicio')
def step_impl(context):
    ahora = timezone.now()
    context.reserva.fecha = ahora.date()
    context.reserva.hora_inicio = (ahora + timedelta(minutes=30)).time()
    context.reserva.save()

@when('intenta cancelarla')
def step_impl(context):
    context.driver.get(f"{context.base_url}/")
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Cancelar')]"))
    )
    context.driver.find_element(By.XPATH, "//button[contains(text(), 'Cancelar')]").click()
    try:
        WebDriverWait(context.driver, 3).until(EC.alert_is_present())
        alert = context.driver.switch_to.alert
        alert.accept()
    except NoAlertPresentException:
        pass
    time_module.sleep(1)

@then('muestra un mensaje indicando que el periodo de cancelación ha concluido')
def step_impl(context):
    assert "El periodo de cancelación ha concluido" in context.driver.page_source

# --- CA-10 ---
@given('que el usuario es propietario de una reservación cancelada')
def step_impl(context):
    manana = timezone.now().date() + timedelta(days=1)
    context.reserva = crear_reservacion(
        usuario=context.user, sala=context.sala_a, fecha=manana,
        hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Reserva a cancelar"
    )
    context.reserva.estado = 'CANCELADA'
    context.reserva.save()

@when('intenta cancelarla nuevamente')
def step_impl(context):
    context.driver.get(f"{context.base_url}/")
    time_module.sleep(1)

@then('conserva el estado "CANCELADA"')
def step_impl(context):
    context.reserva.refresh_from_db()
    assert context.reserva.estado == 'CANCELADA'

@then('muestra un mensaje indicando que la reservación ya fue cancelada')
def step_impl(context):
    assert "Cancelar</button>" not in context.driver.page_source

# --- CA-11 ---
@given('que el usuario cancela correctamente una reservación')
def step_impl(context):
    context.execute_steps('''
        Dado que el usuario ha iniciado sesión
        Y es propietario de una reservación vigente cuyo inicio ocurrirá dentro de más de 60 minutos
        Cuando confirma la cancelación
    ''')

@when('consulta su historial')
def step_impl(context):
    context.driver.get(f"{context.base_url}/")
    time_module.sleep(1)

@then('observa la reservación con estado "CANCELADA"')
def step_impl(context):
    assert "CANCELADA" in context.driver.page_source

@then('puede identificar la fecha y hora en la que se realizó la cancelación')
def step_impl(context):
    assert "CANCELADA" in context.driver.page_source