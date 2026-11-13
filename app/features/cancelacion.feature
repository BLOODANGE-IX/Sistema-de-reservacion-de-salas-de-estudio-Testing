Característica: Cancelar una reservación
  Como usuario autenticado propietario de una reservación
  Quiero cancelar una reservación que ya no utilizaré
  Para liberar la sala y permitir que otro usuario pueda reservarla

  Escenario: Cancelar una reservación vigente con anticipación suficiente
    Dado que el usuario ha iniciado sesión
    Y es propietario de una reservación vigente cuyo inicio ocurrirá dentro de más de 60 minutos
    Cuando confirma la cancelación
    Entonces el sistema cambia el estado de la reservación a "CANCELADA"
    Y registra la fecha y hora de cancelación
    Y muestra un mensaje de confirmación
    Y la sala vuelve a estar disponible para ese horario

  Escenario: Impedir que un usuario cancele una reservación ajena
    Dado que el usuario ha iniciado sesión
    Y existe una reservación vigente perteneciente a otro usuario
    Y el usuario autenticado intenta cancelarla
    Entonces el sistema rechaza la operación
    Y mantiene la reservación en estado "VIGENTE"
    Y responde sin revelar información sensible de la reservación

  Escenario: Impedir cancelación fuera del periodo permitido
    Dado que el usuario ha iniciado sesión
    Y que el usuario es propietario de una reservación vigente
    Y faltan 60 minutos o menos para su inicio
    Cuando intenta cancelarla
    Entonces el sistema rechaza la operación
    Y mantiene la reservación en estado "VIGENTE"
    Y muestra un mensaje indicando que el periodo de cancelación ha concluido

  Escenario: Impedir cancelar nuevamente una reservación cancelada
    Dado que el usuario es propietario de una reservación cancelada
    Cuando intenta cancelarla nuevamente
    Entonces el sistema rechaza la operación
    Y conserva el estado "CANCELADA"
    Y muestra un mensaje indicando que la reservación ya fue cancelada

  Escenario: Mantener la trazabilidad de la cancelación
    Dado que el usuario cancela correctamente una reservación
    Cuando consulta su historial
    Entonces observa la reservación con estado "CANCELADA"
    Y puede identificar la fecha y hora en la que se realizó la cancelación