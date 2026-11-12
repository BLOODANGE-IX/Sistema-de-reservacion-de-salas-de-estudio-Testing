from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Sala, Reservacion

class ReservacionModelTest(TestCase):
    def setUp(self):
        # Creamos datos de prueba básicos
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Test', capacidad=4, ubicacion='Piso 1', activa=True)
        self.hoy = timezone.now().date()

    def test_crear_reservacion_valida(self):
        """UT-01: Crear reservación válida -> Se registra con estado VIGENTE"""
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