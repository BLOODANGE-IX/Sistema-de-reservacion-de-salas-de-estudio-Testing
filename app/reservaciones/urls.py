from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_reservaciones, name='lista_reservaciones'),
    path('nueva/', views.crear_reservacion_view, name='crear_reservacion'),
    path('cancelar/<int:pk>/', views.cancelar_reservacion_view, name='cancelar_reservacion'),
]
