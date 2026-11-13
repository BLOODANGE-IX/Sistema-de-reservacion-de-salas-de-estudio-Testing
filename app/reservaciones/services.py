from django.db import transaction
from datetime import datetime, timedelta, time
from .models import Reservacion, Sala
from django.utils import timezone

def _convertir_a_time(valor):
    if isinstance(valor, str):
        return datetime.strptime(valor, '%H:%M').time()
    return valor

@transaction.atomic
def crear_reservacion(usuario, sala, fecha, hora_inicio, hora_fin, asistentes, proposito):
    """
    Usa transacciones y bloqueo pesimista para evitar condiciones de carrera (RN-08).
    """
    hora_inicio = _convertir_a_time(hora_inicio)
    hora_fin = _convertir_a_time(hora_fin)

    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)
    
    # UT-07 Duración min 30 mins, max 2 horas
    duracion = fin_dt - inicio_dt
    if duracion < timedelta(minutes=30):
        raise ValueError("La reservación debe durar como mínimo 30 minutos.")
    if duracion > timedelta(hours=2):
        raise ValueError("La reservación debe durar como máximo 2 horas.")

    # RN-01 y UT-04: Sala activa y capacidad
    if not sala.activa:
        raise ValueError("La sala no se encuentra disponible para reservación.")
    if asistentes > sala.capacidad:
        raise ValueError("El número de asistentes supera la capacidad de la sala.")

    # RN-03: Validar que no sea fecha pasada
    if fecha < timezone.now().date():
        raise ValueError("La fecha no puede ser anterior al día actual.")

    # Convertir a objetos datetime para calcular duraciones y traslapes
    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)

    # Bloqueo pesimista sobre la sala para evitar concurrencia
    Sala.objects.select_for_update().get(pk=sala.pk)

    # Buscar traslapes solo en reservaciones VIGENTES
    reservaciones_vigentes = Reservacion.objects.filter(
        sala=sala,
        fecha=fecha,
        estado='VIGENTE'
    )

    for reserva in reservaciones_vigentes:
        existente_inicio = datetime.combine(fecha, reserva.hora_inicio)
        existente_fin = datetime.combine(fecha, reserva.hora_fin)
        
        # Fórmula de traslape: inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente
        if inicio_dt < existente_fin and fin_dt > existente_inicio:
            raise ValueError("La sala no está disponible en el horario solicitado.")

    # Si pasa todas las validaciones, creamos la reservación
    reservacion = Reservacion.objects.create(
        usuario=usuario,
        sala=sala,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        asistentes=asistentes,
        proposito=proposito,
        estado='VIGENTE'
    )
    
    return reservacion

@transaction.atomic
def cancelar_reservacion(reservacion, usuario):
    """
    Cancela una reservación vigente aplicando las reglas de negocio HU-02.
    """
    # RN-09: Solo el propietario puede cancelar
    if reservacion.usuario != usuario:
        raise ValueError("No tienes permiso para cancelar esta reservación.")

    # RN-10: Solo se pueden cancelar reservaciones VIGENTES
    if reservacion.estado != 'VIGENTE':
        raise ValueError("La reservación ya fue cancelada.")

    # RN-11: Deben faltar más de 60 minutos para el inicio
    ahora = timezone.now()
    # Aseguramos que la fecha y hora de la reservación tengan zona horaria
    inicio_dt = timezone.make_aware(datetime.combine(reservacion.fecha, reservacion.hora_inicio))
    
    tiempo_restante = inicio_dt - ahora
    
    if tiempo_restante <= timedelta(minutes=60):
        raise ValueError("El periodo de cancelación ha concluido. Faltan 60 minutos o menos.")

    # RN-12, RN-13: Cambiamos estado y registramos fecha de cancelación
    reservacion.estado = 'CANCELADA'
    reservacion.fecha_cancelacion = ahora
    reservacion.save()

    return reservacion