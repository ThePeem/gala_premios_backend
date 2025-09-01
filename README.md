# Gala Premios Piorn - Backend

Backend Django para el sistema de votación de la Gala Premios Piorn.

## 🚀 Despliegue Rápido

### 1. Clonar y configurar
```bash
git clone <tu-repositorio-backend>
cd gala_premios
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
cp env.example .env
# Editar .env con tus valores
```

### 3. Ejecutar migraciones
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Crear superusuario
```bash
python manage.py createsuperuser
```

### 5. Ejecutar servidor
```bash
python manage.py runserver
```

## 🌐 Despliegue en Render

### Variables de entorno necesarias:
- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: false
- `ALLOWED_HOSTS`: galapremiospiorn.onrender.com
- `CORS_ALLOWED_ORIGINS`: https://galapremiospiorn.vercel.app

### Comando de inicio:
```bash
gunicorn gala_premios.wsgi:application
```

## 📚 API Endpoints

### Autenticación
- `POST /api-token-auth/` - Login
- `POST /api/auth/register/` - Registro

### Usuario
- `GET /api/mi-perfil/` - Perfil del usuario
- `GET /api/mis-nominaciones/` - Nominaciones del usuario

### Votación
- `GET /api/premios/` - Lista de premios
- `POST /api/votar/` - Emitir voto
- `GET /api/participantes/` - Lista de participantes

### Resultados
- `GET /api/resultados/` - Resultados (cálculo)
- `POST /api/resultados/` - Publicar resultados (admin)
- `GET /api/resultados-publicos/` - Resultados públicos

### Administración
- `GET/POST /api/admin/premios/` - CRUD premios
- `GET/POST /api/admin/nominados/` - CRUD nominados
- `GET/POST /api/admin/users/` - CRUD usuarios

## 🔧 Desarrollo

### Script de despliegue automático:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Estructura del proyecto:
```
gala_premios/
├── gala_premios/     # Configuración principal
├── votaciones/       # App principal
├── manage.py         # Script de Django
├── requirements.txt  # Dependencias
└── Procfile         # Configuración para Render
```

## 📝 Notas

- El backend está configurado para funcionar con el frontend en Vercel
- CORS está configurado para permitir comunicación entre dominios
- Los archivos estáticos se sirven con Whitenoise
- La base de datos en producción es PostgreSQL (Render)
