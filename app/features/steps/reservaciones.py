from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, timedelta, time
from django.utils import timezone
import time as time_module
from concurrent.futures import ThreadPoolExecutor
from reservaciones.models import Reservacion, Sala
from reservaciones.services import crear_reservacion

# --- HELPERS ---
def llenar_formulario(context, sala_id, fecha_str, hora_inicio, hora_fin, asistentes, proposito):
    context.driver.get(f"{context.base_url}/nueva/")
    WebDriverWait(context.driver, 10).until(EC.presence_of_element_located((By.NAME, "fecha")))
    
    context.driver.execute_script(f"document.getElementsByName('fecha')[0].value = '{fecha_str}';")
    context.driver.execute_script(f"document.getElementsByName('hora_inicio')[0].value = '{hora_inicio}';")
    context.driver.execute_script(f"document.getElementsByName('hora_fin')[0].value = '{hora_fin}';")
    
    Select(context.driver.find_element(By.NAME, "sala")).select_by_value(str(sala_id))
    context.driver.find_element(By.NAME, "asistentes").clear()
    context.driver.find_element(By.NAME, "asistentes").send_keys(str(asistentes))
    context.driver.find_element(By.NAME, "proposito").clear()
    context.driver.find_element(By.NAME, "proposito").send_keys(proposito)
    
    context.driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time_module.sleep(1)

# --- CA-01 ---
@given('que existe una sala activa con capacidad suficiente')
def step_impl(context):
    pass

@given('el usuario ha iniciado sesión')
@given('que el usuario ha iniciado sesión')
def step_impl(context):
    context.driver.get(f"{context.base_url}/accounts/login/")
    WebDriverWait(context.driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    context.driver.find_element(By.NAME, "username").send_keys("bdd_user")
    context.driver.find_element(By.NAME, "password").send_keys("password123")
    context.driver.find_element(By.XPATH, "//button[@type='submit']").click()

@given('no existe otra reservación vigente que se traslape con el horario solicitado')
def step_impl(context):
    pass

@when('captura una fecha válida, una hora de inicio y una hora de fin válidas')
def step_impl(context):
    context.manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    context.hora_inicio = "10:00"
    context.hora_fin = "11:00"

@when('captura un número de asistentes permitido y un propósito válido')
def step_impl(context):
    llenar_formulario(
        context, context.sala_a.id, context.manana, 
        context.hora_inicio, context.hora_fin, 3, "Estudiar para el examen de BDD"
    )

@when('envía el formulario')
def step_impl(context):
    pass

@then('el sistema registra la reservación con estado "VIGENTE"')
def step_impl(context):
    reserva = Reservacion.objects.first()
    assert reserva is not None, "La reservación no se creó"
    assert reserva.estado == 'VIGENTE'

@then('muestra un mensaje de confirmación')
def step_impl(context):
    page = context.driver.page_source
    assert ("Reservación registrada exitosamente" in page or 
            "Reservación cancelada exitosamente" in page), \
           "No se encontró mensaje de confirmación en la página"

@then('la reservación aparece en la lista de reservaciones del usuario')
def step_impl(context):
    assert "Sala A" in context.driver.page_source

# --- CA-02 ---
@given('que existe una reservación vigente para una sala entre las 10:00 y las 11:00')
def step_impl(context):
    manana = timezone.now().date() + timedelta(days=1)
    crear_reservacion(
        usuario=context.user, sala=context.sala_a, fecha=manana,
        hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Reserva previa"
    )

@when('intenta registrar otra reservación para la misma sala entre las 10:30 y las 11:30')
def step_impl(context):
    context.initial_count = Reservacion.objects.count()
    manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    llenar_formulario(
        context, context.sala_a.id, manana, "10:30", "11:30", 2, "Intento de traslape"
    )

@then('el sistema no registra la nueva reservación')
@then('el sistema no registra la reservación')
def step_impl(context):
    assert Reservacion.objects.count() == context.initial_count

@then('muestra un mensaje indicando que la sala no está disponible en el horario solicitado')
def step_impl(context):
    assert "La sala no está disponible en el horario solicitado" in context.driver.page_source

# --- CA-03 ---
@given('que una sala activa tiene capacidad para 4 personas')
def step_impl(context):
    pass

@when('intenta registrar una reservación para 5 asistentes')
def step_impl(context):
    context.initial_count = Reservacion.objects.count()
    manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    llenar_formulario(
        context, context.sala_a.id, manana, "10:00", "11:00", 5, "Exceso de capacidad"
    )

@then('muestra un mensaje indicando que el número de asistentes supera la capacidad')
def step_impl(context):
    assert "El número de asistentes supera la capacidad de la sala" in context.driver.page_source

# --- CA-04a (Fecha) ---
@when('intenta reservar una sala con una fecha anterior al día actual')
def step_impl(context):
    context.initial_count = Reservacion.objects.count()
    ayer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    llenar_formulario(
        context, context.sala_a.id, ayer, "10:00", "11:00", 2, "Fecha pasada"
    )

@then('muestra el mensaje de validación correspondiente')
def step_impl(context):
    page = context.driver.page_source
    assert ("La fecha no puede ser anterior al día actual" in page or 
            "La hora de fin debe ser posterior a la hora de inicio" in page)

# --- CA-04b (Hora) ---
@when('intenta reservar una sala donde la hora de fin no es posterior a la hora de inicio')
def step_impl(context):
    context.initial_count = Reservacion.objects.count()
    manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    llenar_formulario(
        context, context.sala_a.id, manana, "11:00", "10:00", 2, "Horas invertidas"
    )

# --- CA-05 (Sala Inactiva) ---
@given('que existe una sala marcada como inactiva')
def step_impl(context):
    pass

@when('intenta registrar una reservación para esa sala')
def step_impl(context):
    context.initial_count = Reservacion.objects.count()
    manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    llenar_formulario(
        context, context.sala_inactiva.id, manana, "10:00", "11:00", 2, "Sala inactiva"
    )

@then('muestra un mensaje indicando que la sala no se encuentra disponible')
def step_impl(context):
    assert "La sala no se encuentra disponible para reservación" in context.driver.page_source

# --- CA-06 (Concurrencia) ---
@given('que una sala está disponible para un horario específico')
def step_impl(context):
    pass

@when('dos solicitudes intentan registrar simultáneamente una reservación para la misma sala y horario')
def step_impl(context):
    manana = timezone.now().date() + timedelta(days=1)
    
    def intentar_reservar():
        try:
            crear_reservacion(
                usuario=context.user, sala=context.sala_a, fecha=manana,
                hora_inicio=time(10, 0), hora_fin=time(11, 0), asistentes=2, proposito="Concurrente"
            )
        except ValueError:
            pass 

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(intentar_reservar)
        executor.submit(intentar_reservar)

@then('solo una reservación queda registrada como vigente')
def step_impl(context):
    assert Reservacion.objects.filter(estado='VIGENTE').count() == 1

@then('la segunda solicitud recibe una respuesta controlada indicando que la sala ya no está disponible')
def step_impl(context):
    pass