# gala_premios/gala_premios/settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-tu-clave-secreta-aqui' # <-- ¡Esto es solo para desarrollo!

# Importante: Para producción, la SECRET_KEY debe venir de una variable de entorno
# Por ejemplo, en Render, la configurarías en el dashboard.

# ¡IMPORTANTE! Asegúrate de que no haya un valor por defecto inseguro aquí.
# Si la variable de entorno no está definida, esto generará un error claro,
# que es lo que queremos en producción.
SECRET_KEY = os.environ.get('SECRET_KEY')

AUTH_USER_MODEL = 'votaciones.Usuario' # <--- Asegúrate de que esta línea esté presente

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True # <-- ¡Esto es solo para desarrollo!

# En producción, DEBUG debe ser False. Viene de variable de entorno.
DEBUG = os.environ.get('DEBUG', 'True') == 'True' # Convierte el string 'True'/'False' a booleano


# ALLOWED_HOSTS = [] # <-- ¡Esto es solo para desarrollo!

# En producción, ALLOWED_HOSTS debe incluir los dominios de tu backend y frontend.
# Para Render, tu dominio de Render (ej. 'tu-backend.onrender.com') y tu dominio de Vercel (ej. 'tugala.vercel.app').
# En desarrollo, 'localhost' y '127.0.0.1'.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
# Asegúrate de que no haya espacios extra si los pones en la variable de entorno


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # 'django.contrib.staticfiles', # Lo movemos o suprimimos si usamos whitenoise.runserver_nostatic
    
    # Whitenoise en desarrollo (debe ir antes de staticfiles si lo usas)
    'whitenoise.runserver_nostatic', # <--- Asegúrate de que está aquí y solo si DEBUG es True

    'django.contrib.staticfiles', # Asegurarse de que esté aquí si no está arriba con whitenoise.runserver_nostatic
                                  # Dejarlo así es lo más seguro, ya que whitenoise.runserver_nostatic
                                  # solo actúa en DEBUG=True y sobreescribe el comportamiento.

    'rest_framework',
    'rest_framework.authtoken',
    'votaciones', # Tu app
    'corsheaders', # ¡Añadido para CORS!
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', # <-- ¡MOVER ESTE ARRIBA DEL TODO!
    'whitenoise.middleware.WhiteNoiseMiddleware', # <-- Este puede ir aquí o más abajo, pero CORS es primero
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ... el resto de tus middlewares
]

ROOT_URLCONF = 'gala_premios.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gala_premios.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es-es' # Cambiado a español

TIME_ZONE = 'Europe/Madrid' # Cambiado a la zona horaria de Madrid

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # Directorio donde se recolectarán los archivos estáticos en producción

# Configuración de Whitenoise para archivos estáticos comprimidos y con caché
STORAGES = {
    "default": { # Esto es para los archivos de media por defecto
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": { # Esto es para los archivos estáticos recolectados
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files (user-uploaded content)
MEDIA_URL = '/media/' # URL para acceder a los archivos de media
MEDIA_ROOT = BASE_DIR / 'media' # Directorio donde se guardarán los archivos de media


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# CORS Headers Configuration
# https://github.com/adamchainz/django-cors-headers

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # Frontend de desarrollo
    "https://tugala.vercel.app", # Frontend de producción (cambiar por tu dominio real)
]

# Si necesitas permitir más orígenes dinámicamente o por patrón, puedes usar CORS_ALLOWED_ORIGIN_REGEXES
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^https://\w+\.vercel\.app$", # Ejemplo para permitir cualquier subdominio de vercel.app
# ]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_CREDENTIALS = True # Permite cookies, encabezados de autorización, etc.