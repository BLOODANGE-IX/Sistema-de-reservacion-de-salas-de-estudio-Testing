from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReservacionForm
from .services import crear_reservacion, cancelar_reservacion
from .models import Reservacion

@login_required
def lista_reservaciones(request):
    reservaciones = Reservacion.objects.filter(usuario=request.user).order_by('-fecha', '-hora_inicio')
    return render(request, 'reservaciones/lista.html', {'reservaciones': reservaciones})

@login_required
def crear_reservacion_view(request):
    if request.method == 'POST':
        form = ReservacionForm(request.POST)
        if form.is_valid():
            try:
                # Usamos el servicio para respetar las reglas de negocio
                crear_reservacion(
                    usuario=request.user,
                    sala=form.cleaned_data['sala'],
                    fecha=form.cleaned_data['fecha'],
                    hora_inicio=form.cleaned_data['hora_inicio'],
                    hora_fin=form.cleaned_data['hora_fin'],
                    asistentes=form.cleaned_data['asistentes'],
                    proposito=form.cleaned_data['proposito']
                )
                messages.success(request, "Reservación registrada exitosamente.")
                return redirect('lista_reservaciones')
            except ValueError as e:
                # Capturamos los errores del servicio (ej. traslapes) y los mostramos
                messages.error(request, str(e))
    else:
        form = ReservacionForm()

    return render(request, 'reservaciones/formulario.html', {'form': form})

@login_required
def cancelar_reservacion_view(request, pk):
    if request.method == 'POST': # Solo aceptamos POST por seguridad (RT-12)
        try:
            reserva = Reservacion.objects.get(pk=pk)
            cancelar_reservacion(reserva, request.user)
            messages.success(request, "Reservación cancelada exitosamente.")
        except Reservacion.DoesNotExist:
            messages.error(request, "La reservación no existe.")
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('lista_reservaciones')