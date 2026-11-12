from django.db import models
from django.conf import settings

class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - Capacidad: {self.capacidad}"

class Reservacion(models.Model):
    ESTADOS = [
        ('VIGENTE', 'Vigente'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.PositiveIntegerField()
    proposito = models.CharField(max_length=200)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='VIGENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reservación de {self.usuario.username} en {self.sala.nombre} ({self.fecha})"
