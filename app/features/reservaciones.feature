Característica: Registrar una reservación
  Como usuario autenticado
  Quiero seleccionar una sala disponible y registrar una reservación
  Para asegurar el uso exclusivo de la sala

  Escenario: Registrar una reservación válida
    Dado que existe una sala activa con capacidad suficiente
    Y el usuario ha iniciado sesión
    Y no existe otra reservación vigente que se traslape con el horario solicitado
    Cuando captura una fecha válida, una hora de inicio y una hora de fin válidas
    Y captura un número de asistentes permitido y un propósito válido
    Y envía el formulario
    Entonces el sistema registra la reservación con estado "VIGENTE"
    Y muestra un mensaje de confirmación
    Y la reservación aparece en la lista de reservaciones del usuario

Escenario: Rechazar una reservación con horario traslapado
    Dado que existe una reservación vigente para una sala entre las 10:00 y las 11:00
    Y el usuario ha iniciado sesión
    Cuando intenta registrar otra reservación para la misma sala entre las 10:30 y las 11:30
    Entonces el sistema no registra la nueva reservación
    Y muestra un mensaje indicando que la sala no está disponible en el horario solicitado

  Escenario: Rechazar una reservación que exceda la capacidad
    Dado que una sala activa tiene capacidad para 4 personas
    Y el usuario ha iniciado sesión
    Cuando intenta registrar una reservación para 5 asistentes
    Entonces el sistema no registra la reservación
    Y muestra un mensaje indicando que el número de asistentes supera la capacidad

  Escenario: Rechazar una fecha inválida
    Dado que el usuario ha iniciado sesión
    Cuando intenta reservar una sala con una fecha anterior al día actual
    Entonces el sistema no registra la reservación
    Y muestra el mensaje de validación correspondiente

  Escenario: Rechazar un horario inválido
    Dado que el usuario ha iniciado sesión
    Cuando intenta reservar una sala donde la hora de fin no es posterior a la hora de inicio
    Entonces el sistema no registra la reservación
    Y muestra el mensaje de validación correspondiente

  Escenario: Rechazar una sala inactiva
    Dado que existe una sala marcada como inactiva
    Y el usuario ha iniciado sesión
    Cuando intenta registrar una reservación para esa sala
    Entonces el sistema no registra la reservación
    Y muestra un mensaje indicando que la sala no se encuentra disponible

  Escenario: Evitar una doble reservación ante solicitudes concurrentes
    Dado que una sala está disponible para un horario específico
    Cuando dos solicitudes intentan registrar simultáneamente una reservación para la misma sala y horario
    Entonces solo una reservación queda registrada como vigente
    Y la segunda solicitud recibe una respuesta controlada indicando que la sala ya no está disponible