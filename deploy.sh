#!/bin/bash

echo "🚀 Iniciando despliegue del backend..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Asegúrate de estar en el directorio del proyecto Django."
    exit 1
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"

echo "✅ Despliegue completado!"
echo "🌐 El backend está listo para funcionar"
echo "🔑 Accede a /admin/ con las credenciales del superusuario"
