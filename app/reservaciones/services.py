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