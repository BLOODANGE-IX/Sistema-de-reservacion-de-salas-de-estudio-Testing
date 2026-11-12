from django import forms
from django.utils import timezone
from datetime import time, datetime, timedelta
from .models import Reservacion

class ReservacionForm(forms.ModelForm):
    class Meta:
        model = Reservacion
        fields = ['sala', 'fecha', 'hora_inicio', 'hora_fin', 'asistentes', 'proposito']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

    """UT-02: Propósito entre 10 y 200 caracteres (sin contar espacios extra)."""
    def clean_proposito(self):
        proposito = self.cleaned_data.get('proposito', '').strip()
        if len(proposito) < 10 or len(proposito) > 200:
            raise forms.ValidationError("El propósito debe tener entre 10 y 200 caracteres.")
        return proposito

    """UT-05: La fecha no puede ser anterior a hoy."""
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < timezone.now().date():
            raise forms.ValidationError("La fecha no puede ser anterior al día actual.")
        return fecha

    """UT-03: Asistentes debe ser al menos 1."""
    def clean_asistentes(self):
        asistentes = self.cleaned_data.get('asistentes')
        if asistentes is not None and asistentes < 1:
            raise forms.ValidationError("Debe haber al menos 1 asistente.")
        return asistentes


    def clean(self):
        cleaned_data = super().clean()
        sala = cleaned_data.get('sala')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        asistentes = cleaned_data.get('asistentes')

        # RN-01 y UT-04: Sala activa y capacidad
        if sala:
            if not sala.activa:
                self.add_error('sala', "La sala no se encuentra disponible para reservación.")
            elif asistentes and asistentes > sala.capacidad:
                self.add_error('asistentes', "El número de asistentes supera la capacidad de la sala.")

        # UT-06: Hora fin > hora inicio
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                self.add_error('hora_fin', "La hora de fin debe ser posterior a la hora de inicio.")
            else:
                # RN-05: Duración (mín 30 min, máx 2 horas)
                inicio_dt = datetime.combine(timezone.now().date(), hora_inicio)
                fin_dt = datetime.combine(timezone.now().date(), hora_fin)
                duracion = fin_dt - inicio_dt
                
                if duracion < timedelta(minutes=30):
                    self.add_error('hora_fin', "La reservación debe durar como mínimo 30 minutos.")
                elif duracion > timedelta(hours=2):
                    self.add_error('hora_fin', "La reservación debe durar como máximo 2 horas.")

        # RN-04: Horario institucional (08:00 a 20:00)
        if hora_inicio:
            if hora_inicio < time(8, 0) or hora_inicio > time(19, 0):
                self.add_error('hora_inicio', "La hora de inicio debe estar entre las 08:00 y 19:00.")
        if hora_fin:
            if hora_fin > time(20, 0):
                self.add_error('hora_fin', "La hora de fin no puede exceder las 20:00.")

        return cleaned_data