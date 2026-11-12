from django.db import migrations

def crear_salas_iniciales(apps, schema_editor):
    Sala = apps.get_model('reservaciones', 'Sala')
    Sala.objects.bulk_create([
        Sala(nombre="Sala A", ubicacion="Biblioteca, planta baja", capacidad=4, activa=True),
        Sala(nombre="Sala B", ubicacion="Biblioteca, planta baja", capacidad=8, activa=True),
        Sala(nombre="Sala C", ubicacion="Biblioteca, planta alta", capacidad=12, activa=True),
        Sala(nombre="Sala de mantenimiento", ubicacion="Biblioteca, planta alta", capacidad=6, activa=False),
    ])

class Migration(migrations.Migration):
    dependencies = [
        ('reservaciones', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(crear_salas_iniciales, migrations.RunPython.noop),
    ]