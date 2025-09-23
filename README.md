# Gala Premios Piorn - Backend

Backend en Django/DRF para el sistema de votación de la Gala Premios Piorn.

## 🌐 Entorno de producción

- API: https://galapremiospiorn.onrender.com
- Admin Django: https://galapremiospiorn.onrender.com/admin/

## 🔧 Variables de entorno (Render)

```
SECRET_KEY=...
DEBUG=false
ALLOWED_HOSTS=galapremiospiorn.onrender.com
CORS_ALLOWED_ORIGINS=https://galapremiospiorn.vercel.app
DATABASE_URL=... # Render (PostgreSQL)
```

## 🚀 Despliegue en Render

- Conecta el repo y configura las variables anteriores.
- Comando de build: opcional (colecta estáticos en el start)
- Comando de inicio:
```
gunicorn gala_premios.wsgi:application
```
- Ejecuta migraciones en cada deploy (Startup Command o Job):
```
python manage.py migrate
```

## 📚 API (principales)

- Auth: `POST /api-token-auth/`, `POST /api/auth/register/`
- Participantes: `GET /api/participantes/`
- Premios (admin): `GET/POST /api/admin/premios/`, `PATCH/DELETE /api/admin/premios/{id}/`
- Nominados (admin): `GET/POST /api/admin/nominados/`, `PATCH/DELETE /api/admin/nominados/{id}/`
- Usuarios (admin): `GET /api/admin/users/`, `PATCH /api/admin/users/{id}/`

## 🧩 Modelado clave

- `Premio` incluye `vinculos_requeridos` (por defecto 1) para soportar premios como “Pareja del Año” (2 vinculados por nominado).
- `Nominado.usuarios_vinculados` es ManyToMany a `Usuario` (permite 1 o más). 

Sugerencia de validación (opcional): en el serializer de `Nominado`, validar que el número de `usuarios_vinculados` coincida con `premio.vinculos_requeridos` para premios directos.

## 🔧 Desarrollo local (opcional)

```
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 📝 Notas

- CORS configurado para el frontend en Vercel.
- Whitenoise para estáticos.
- Base de datos en producción: PostgreSQL (Render).
