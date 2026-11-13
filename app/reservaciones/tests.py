from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django import forms
from .forms import ReservacionForm
from datetime import date, time
from .models import Sala, Reservacion
from concurrent.futures import ThreadPoolExecutor
from django.db import connection
from django.test import TransactionTestCase
from .services import crear_reservacion
from django.urls import reverse
from .services import crear_reservacion, cancelar_reservacion

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

class ReservacionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser3', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Servicios', capacidad=10, ubicacion='Piso 3', activa=True)
        self.manana = timezone.now().date() + timedelta(days=1)

    """RN-03: El servicio debe rechazar fechas anteriores al día actual."""
    def test_RN_03_rechazar_fecha_pasada_en_servicio(self):
        ayer = timezone.now().date() - timedelta(days=1)
        
        with self.assertRaises(ValueError) as context:
            crear_reservacion(
                usuario=self.user,
                sala=self.sala,
                fecha=ayer,
                hora_inicio='10:00',
                hora_fin='11:00',
                asistentes=2,
                proposito='Prueba de fecha pasada'
            )
            
        # Verificamos que el mensaje de error sea el correcto
        self.assertEqual(str(context.exception), "La fecha no puede ser anterior al día actual.")

    """UT-07: Rechazar duración menor a 30 min o mayor a 2 horas."""
    def test_rechazar_duracion_invalida(self):
        with self.assertRaises(ValueError):
            crear_reservacion(
                usuario=self.user, sala=self.sala, fecha=self.manana,
                hora_inicio='10:00', hora_fin='10:15', asistentes=2, proposito='Prueba'
            )
        
        with self.assertRaises(ValueError):
            crear_reservacion(
                usuario=self.user, sala=self.sala, fecha=self.manana,
                hora_inicio='10:00', hora_fin='13:00', asistentes=2, proposito='Prueba'
            )

    """UT-08: Detectar traslape parcial, contenido y total."""
    def test_detectar_traslapes(self):
        crear_reservacion(
            usuario=self.user, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Reserva base'
        )
        
        with self.assertRaises(ValueError):
            crear_reservacion(
                usuario=self.user, sala=self.sala, fecha=self.manana,
                hora_inicio='10:30', hora_fin='11:30', asistentes=2, proposito='Traslape parcial'
            )

        with self.assertRaises(ValueError):
            crear_reservacion(
                usuario=self.user, sala=self.sala, fecha=self.manana,
                hora_inicio='10:15', hora_fin='10:45', asistentes=2, proposito='Contenido'
            )

        with self.assertRaises(ValueError):
            crear_reservacion(
                usuario=self.user, sala=self.sala, fecha=self.manana,
                hora_inicio='09:00', hora_fin='12:00', asistentes=2, proposito='Total'
            )

    """UT-09: Permitir horarios adyacentes (10:00-11:00 y 11:00-12:00)."""
    def test_permitir_horarios_adyacentes(self):
        crear_reservacion(
            usuario=self.user, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Primera'
        )
        # No debe lanzar excepción
        reserva2 = crear_reservacion(
            usuario=self.user, sala=self.sala, fecha=self.manana,
            hora_inicio='11:00', hora_fin='12:00', asistentes=2, proposito='Segunda'
        )
        self.assertEqual(Reservacion.objects.filter(estado='VIGENTE').count(), 2)

    """UT-10: Ignorar reservaciones canceladas al calcular disponibilidad."""
    def test_UT_10_ignorar_canceladas(self):
        r1 = crear_reservacion(
            usuario=self.user, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='A cancelar'
        )
        # Cancelamos la reserva
        r1.estado = 'CANCELADA'
        r1.save()

        # Debe permitir reservar el mismo horario porque la anterior está cancelada
        r2 = crear_reservacion(
            usuario=self.user, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Nueva reserva'
        )
        self.assertEqual(r2.estado, 'VIGENTE')

class ReservacionConcurrencyTest(TransactionTestCase):
    """IT-01: Prueba de integración para condiciones de carrera."""
    def setUp(self):
        self.user = User.objects.create_user(username='testuser4', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Concurrencia', capacidad=10, ubicacion='Piso 4', activa=True)
        self.manana = timezone.now().date() + timedelta(days=1)

    """IT-01: Enviar dos solicitudes concurrentes incompatibles -> solo una persiste."""
    def test_doble_reservacion_concurrente(self):
        def intentar_reservar():
            try:
                crear_reservacion(
                    usuario=self.user, sala=self.sala, fecha=self.manana,
                    hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Concurrente'
                )
            except ValueError:
                pass # Simula que la segunda solicitud recibe un error controlado
            finally:
                connection.close() # Importante cerrar conexión en hilos

        # Ejecutamos dos hilos al mismo tiempo
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(intentar_reservar)
            executor.submit(intentar_reservar)

        # Al final, solo debe existir UNA reservación vigente en la BD
        reservas_vigentes = Reservacion.objects.filter(
            sala=self.sala, fecha=self.manana, estado='VIGENTE'
        )
        self.assertEqual(reservas_vigentes.count(), 1)

class ReservacionViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser5', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Vistas', capacidad=10, ubicacion='Piso 5', activa=True)
        self.manana = timezone.now().date() + timedelta(days=1)
        self.url_crear = reverse('crear_reservacion') # Lo definiremos en urls.py

    """UT-11: Impedir acceso anónimo al formulario."""
    def test_impedir_acceso_anonimo(self):
        response = self.client.get(self.url_crear)
        # Debe redirigir al login (código 302)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    """UT-12: Crear reservación mediante POST válido."""
    def test_crear_reservacion_post_valido(self):
        self.client.login(username='testuser5', password='password123')
        
        response = self.client.post(self.url_crear, {
            'sala': self.sala.id,
            'fecha': self.manana,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'asistentes': 2,
            'proposito': 'Estudiar para el examen de TDD'
        })
        
        # Debe redirigir a la lista de reservaciones (código 302)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('lista_reservaciones'))
        
        # Verificar que se creó en la BD
        self.assertEqual(Reservacion.objects.count(), 1)
        reserva = Reservacion.objects.first()
        self.assertEqual(reserva.usuario, self.user)
        self.assertEqual(reserva.estado, 'VIGENTE')

class CancelacionServiceTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.sala = Sala.objects.create(nombre='Sala Cancelaciones', capacidad=10, ubicacion='Piso 6', activa=True)
        
        # Creamos una fecha futura lejana para que pase la validación de fecha
        self.manana = timezone.now().date() + timedelta(days=1)

    def _crear_reserva_base(self):
        return crear_reservacion(
            usuario=self.user1, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Reserva para cancelar'
        )

    """UT-13: Cancelar reservación propia, vigente y con anticipación válida."""
    def test_cancelacion_valida(self):
        reserva = self._crear_reserva_base()
        
        cancelar_reservacion(reserva, self.user1)
        
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'CANCELADA')
        self.assertIsNotNone(reserva.fecha_cancelacion)

    """UT-14: Rechazar cancelación de reservación ajena (RN-09)."""
    def test_rechazar_cancelacion_ajena(self):
        reserva = self._crear_reserva_base()
        
        with self.assertRaises(ValueError):
            cancelar_reservacion(reserva, self.user2) # user2 intenta cancelar la de user1
            
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'VIGENTE')

    """UT-15: Rechazar cancelación con 60 minutos exactos de anticipación."""
    def test_rechazar_exactamente_60_minutos(self):
        reserva = self._crear_reserva_base()
        
        ahora = timezone.now()
        # Sumamos exactamente 60 minutos
        hora_exacta = (ahora + timedelta(minutes=60)).time()
        
        reserva.fecha = ahora.date()
        reserva.hora_inicio = hora_exacta
        reserva.save()

        with self.assertRaises(ValueError):
            cancelar_reservacion(reserva, self.user1)
            
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'VIGENTE')

    """UT-16: Rechazar cancelación con menos de 60 minutos de anticipación."""
    def test_rechazar_menos_de_60_minutos(self):
        reserva = self._crear_reserva_base()
        
        ahora = timezone.now()
        # Sumamos 30 minutos (menos de 60)
        hora_menor = (ahora + timedelta(minutes=30)).time()
        
        reserva.fecha = ahora.date()
        reserva.hora_inicio = hora_menor
        reserva.save()

        with self.assertRaises(ValueError):
            cancelar_reservacion(reserva, self.user1)
            
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'VIGENTE')

    """UT-17: Rechazar segunda cancelación y no modificar la fecha inicial (RN-10)."""
    def test_rechazar_doble_cancelacion(self):
        reserva = self._crear_reserva_base()
        cancelar_reservacion(reserva, self.user1)
        
        reserva.refresh_from_db()
        fecha_primera_cancelacion = reserva.fecha_cancelacion

        # Intentamos cancelar de nuevo
        with self.assertRaises(ValueError):
            cancelar_reservacion(reserva, self.user1)

        reserva.refresh_from_db()
        self.assertEqual(reserva.fecha_cancelacion, fecha_primera_cancelacion)

    """UT-20: Reservar un horario, cancelarlo y volver a reservarlo (RN-12, RN-14)."""
    def test_integracion_reservar_cancelar_reservar(self):
        # 1. Reservamos
        reserva1 = self._crear_reserva_base()
        
        # 2. Cancelamos
        cancelar_reservacion(reserva1, self.user1)
        
        # 3. Intentamos reservar el mismo horario otra vez
        reserva2 = crear_reservacion(
            usuario=self.user2, sala=self.sala, fecha=self.manana,
            hora_inicio='10:00', hora_fin='11:00', asistentes=2, proposito='Reserva despues de cancelacion'
        )
        
        self.assertEqual(reserva2.estado, 'VIGENTE')
        self.assertEqual(Reservacion.objects.filter(estado='VIGENTE').count(), 1)