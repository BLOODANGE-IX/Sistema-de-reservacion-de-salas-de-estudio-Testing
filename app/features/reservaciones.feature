Feature: Registrar una reservación
  Como usuario autenticado
  Quiero seleccionar una sala disponible y registrar una reservación
  Para asegurar el uso exclusivo de la sala

  Scenario: CA-01 Registrar una reservación válida
    Dado que existe una sala activa con capacidad suficiente
    Y el usuario ha iniciado sesión
    Y no existe otra reservación vigente que se traslape con el horario solicitado
    Cuando captura una fecha válida, una hora de inicio y una hora de fin válidas
    Y captura un número de asistentes permitido y un propósito válido
    Y envía el formulario
    Entonces el sistema registra la reservación con estado "VIGENTE"
    Y muestra un mensaje de confirmación
    Y la reservación aparece en la lista de reservaciones del usuario