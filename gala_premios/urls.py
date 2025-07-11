"""
URL configuration for gala_premios project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# gala_premios/gala_premios/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

# Vistas públicas y de usuario
from votaciones.views import RegistroUsuarioView, ListaPremiosView, VotarView, ListaParticipantesView, MiPerfilView, MisNominacionesView, EnviarSugerenciaView, ResultadosView, ResultadosPublicosView, UsuarioListCreateView, UsuarioDetailView

# ¡NUEVA IMPORTACIÓN para las vistas administrativas!
from votaciones import views_admin # Importamos el módulo completo

# ¡NUEVAS IMPORTACIONES para servir archivos estáticos y media en desarrollo!
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de autenticación de DRF
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/register/', RegistroUsuarioView.as_view(), name='register'),

    # URLs de usuario general
    path('api/premios/', ListaPremiosView.as_view(), name='lista_premios'),
    path('api/votar/', VotarView.as_view(), name='votar'),
    path('api/participantes/', ListaParticipantesView.as_view(), name='lista_participantes'),
    path('api/mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
    path('api/mis-nominaciones/', MisNominacionesView.as_view(), name='mis_nominaciones'),
    path('api/sugerencias/', EnviarSugerenciaView.as_view(), name='enviar_sugerencia'),
    path('api/resultados/', ResultadosView.as_view(), name='resultados'), # GET es cálculo, POST es publicar (para admins)
    path('api/resultados-publicos/', ResultadosPublicosView.as_view(), name='resultados_publicos'),

    # ¡NUEVAS URLs para la administración vía API!
    path('api/admin/premios/', views_admin.PremioListCreateAPIView.as_view(), name='admin_lista_crear_premios'),
    path('api/admin/premios/<uuid:id>/', views_admin.PremioRetrieveUpdateDestroyAPIView.as_view(), name='admin_detalle_premios'),
    path('api/admin/nominados/', views_admin.NominadoListCreateAPIView.as_view(), name='admin_lista_crear_nominados'),
    path('api/admin/nominados/<uuid:id>/', views_admin.NominadoRetrieveUpdateDestroyAPIView.as_view(), name='admin_detalle_nominados'),

    # ** MODIFICAR: NUEVAS URLs para la administración de usuarios por API **
    path('api/admin/users/', UsuarioListCreateView.as_view(), name='admin-user-list-create'),
    path('api/admin/users/<int:pk>/', UsuarioDetailView.as_view(), name='admin-user-detail'),
]

# ¡SOLO EN MODO DEBUG! Sirve archivos media y estáticos durante el desarrollo.
# En producción, un servidor web como Nginx o la configuración de Render/Whitenoise
# manejarán estos archivos.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Esto ya lo manejará Whitenoise en prod