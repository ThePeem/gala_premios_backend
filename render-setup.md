# 🚀 Configuración de Render para el Backend

## 📋 Pasos para Configurar Render

### 1. Crear Cuenta en Render
- Ve a [render.com](https://render.com)
- Crea una cuenta o inicia sesión
- Conecta tu cuenta de GitHub

### 2. Crear Nuevo Web Service
- Haz clic en "New +"
- Selecciona "Web Service"
- Conecta tu repositorio de GitHub del backend

### 3. Configuración del Servicio

**Información Básica:**
- **Name**: `gala-premios-backend`
- **Environment**: `Python 3`
- **Region**: Elige la más cercana a tus usuarios

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn gala_premios.wsgi:application`

### 4. Variables de Entorno

**Configura estas variables en Render:**

```env
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura-aqui
DEBUG=false
ALLOWED_HOSTS=galapremiospiorn.onrender.com
CORS_ALLOWED_ORIGINS=https://galapremiospiorn.vercel.app
```

**Para generar una SECRET_KEY segura:**
```python
import secrets
print(secrets.token_urlsafe(50))
```

### 5. Configuración Avanzada

**Health Check Path:** `/admin/`
**Auto-Deploy:** ✅ Habilitado
**Branch:** `main`

### 6. Base de Datos (Opcional)

Render puede crear automáticamente una base de datos PostgreSQL:
- **Database Type**: PostgreSQL
- **Name**: `gala_premios_db`
- **Database**: `gala_premios`
- **User**: Se genera automáticamente
- **Password**: Se genera automáticamente

**Si usas base de datos externa, añade:**
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

## 🔧 Configuración de Django para PostgreSQL

Si usas PostgreSQL, actualiza `settings.py`:

```python
import dj_database_url

# Configuración de base de datos
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
    )
}
```

Y añade `dj-database-url` a `requirements.txt`:
```
dj-database-url==2.1.0
```

## 📊 Monitoreo

### Logs
- Ve a tu servicio en Render
- Haz clic en "Logs" para ver logs en tiempo real
- Útil para debugging

### Métricas
- Render proporciona métricas básicas
- Uso de CPU, memoria, requests
- Tiempo de respuesta

## 🚨 Solución de Problemas

### Error: "ModuleNotFoundError"
- Verifica que `requirements.txt` esté actualizado
- Asegúrate de que el build command sea correcto

### Error: "SECRET_KEY not set"
- Verifica que la variable de entorno esté configurada
- No debe tener espacios extra

### Error: "CORS blocked"
- Verifica `CORS_ALLOWED_ORIGINS`
- Asegúrate de que la URL del frontend esté incluida

### Error: "Database connection failed"
- Verifica la URL de la base de datos
- Asegúrate de que las credenciales sean correctas

## 🔄 Despliegue Automático

Una vez configurado:
1. Cada push a `main` activará un nuevo deploy
2. Render construirá y desplegará automáticamente
3. Los logs te mostrarán el progreso

## 📞 Soporte

- **Documentación Render**: [docs.render.com](https://docs.render.com)
- **Comunidad**: [community.render.com](https://community.render.com)
- **Soporte**: [support.render.com](https://support.render.com)

---

**¡Tu backend estará funcionando en Render en minutos! 🎉**
