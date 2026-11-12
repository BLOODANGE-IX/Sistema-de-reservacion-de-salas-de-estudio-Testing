from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django import forms
from .forms import ReservacionForm
from datetime import date, time
from .models import Sala, Reservacion

class ReservacionModelTest(TestCase):
    def setUp(self):
        # Creamos datos de prueba básicos
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Test', capacidad=4, ubicacion='Piso 1', activa=True)
        self.hoy = timezone.now().date()

    """UT-01: Crear reservación válida -> Se registra con estado VIGENTE"""
    def test_crear_reservacion_valida(self):
        reservacion = Reservacion.objects.create(
            usuario=self.user,
            sala=self.sala,
            fecha=self.hoy,
            hora_inicio='10:00',
            hora_fin='11:00',
            asistentes=3,
            proposito='Estudiar para el examen de TDD'
        )
        
        self.assertEqual(reservacion.estado, 'VIGENTE')
        self.assertEqual(reservacion.usuario.username, 'testuser')
        self.assertEqual(Reservacion.objects.count(), 1)

class ReservacionFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Form', capacidad=4, ubicacion='Piso 2', activa=True)
        self.manana = date.today() + timedelta(days=1)

    """UT-02: Propósito debe tener entre 10 y 200 caracteres."""
    def test_rechazar_proposito_menor_a_10_caracteres(self):
        form = ReservacionForm(data={
            'sala': self.sala.id,
            'fecha': self.manana,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': 2,
            'proposito': 'Nada'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('proposito', form.errors)

    """UT-03: Asistentes debe ser > 0 y entero."""
    def test_rechazar_asistentes_invalidos(self):
        form = ReservacionForm(data={
            'sala': self.sala.id,
            'fecha': self.manana,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': 0,
            'proposito': 'Estudiar para el examen de TDD'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('asistentes', form.errors)

    """UT-05: Fecha no puede ser anterior a hoy."""
    def test_rechazar_fecha_pasada(self):
        ayer = date.today() - timedelta(days=1)
        form = ReservacionForm(data={
            'sala': self.sala.id,
            'fecha': ayer,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': 2,
            'proposito': 'Estudiar para el examen de TDD'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fecha', form.errors)

    """UT-06: Hora fin debe ser posterior a hora inicio."""
    def test_rechazar_hora_fin_menor_a_inicio(self):
        form = ReservacionForm(data={
            'sala': self.sala.id,
            'fecha': self.manana,
            'hora_inicio': '11:00',
            'hora_fin': '10:00',
            'asistentes': 2,
            'proposito': 'Estudiar para el examen de TDD'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('hora_fin', form.errors)