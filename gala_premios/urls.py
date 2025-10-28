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
from votaciones.views import RegistroUsuarioView, ListaPremiosView, VotarView, ListaParticipantesView, MiPerfilView, MisNominacionesView, EnviarSugerenciaView, ResultadosView, ResultadosPublicosView, UsuarioListCreateView, UsuarioDetailView, GoogleAuthView, MisEstadisticasView, ListaTodosPremiosView
from votaciones.views_mejoras import VerificarVotoView, MisVotosView, CambiarEstadoPremioView, EstadisticasAdminView

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
    path('api/auth/google/', GoogleAuthView.as_view(), name='google_auth'),

    # URLs de usuario general
    path('api/premios/', ListaPremiosView.as_view(), name='lista_premios'),
    path('api/premios-todos/', ListaTodosPremiosView.as_view(), name='lista_todos_premios'),
    path('api/votar/', VotarView.as_view(), name='votar'),
    path('api/mis-nominaciones/', MisNominacionesView.as_view(), name='mis_nominaciones'),
    path('api/participantes/', ListaParticipantesView.as_view(), name='lista_participantes'),
    path('api/mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
    path('api/mis-estadisticas/', MisEstadisticasView.as_view(), name='mis_estadisticas'),
    path('api/sugerencias/', EnviarSugerenciaView.as_view(), name='enviar_sugerencia'),
    path('api/resultados/', ResultadosView.as_view(), name='resultados'), # GET es cálculo, POST es publicar (para admins)
    path('api/resultados-publicos/', ResultadosPublicosView.as_view(), name='resultados_publicos'),

    # URLs de administración (solo para superusuarios)
    path('api/admin/usuarios/', UsuarioListCreateView.as_view(), name='admin_usuarios_list'),
    path('api/admin/usuarios/<uuid:pk>/', UsuarioDetailView.as_view(), name='admin_usuarios_detail'),
    
    # URLs para el panel de administración
    path('api/admin/estadisticas/', views_admin.estadisticas, name='admin_estadisticas'),
    path('api/admin/premios-top/', views_admin.premios_top, name='admin_premios_top'),
    path('api/admin/avanzar-fase/', views_admin.avanzar_fase, name='avanzar_fase'),
    path('api/admin/reset-gala/', views_admin.reset_gala, name='reset_gala'),
    # CRUD Admin Premios
    path('api/admin/premios/', views_admin.PremioListCreateAPIView.as_view(), name='admin_premios_list_create'),
    path('api/admin/premios/<uuid:id>/', views_admin.PremioRetrieveUpdateDestroyAPIView.as_view(), name='admin_premios_rud'),
    # CRUD Admin Nominados
    path('api/admin/nominados/', views_admin.NominadoListCreateAPIView.as_view(), name='admin_nominados_list_create'),
    path('api/admin/nominados/<uuid:id>/', views_admin.NominadoRetrieveUpdateDestroyAPIView.as_view(), name='admin_nominados_rud'),
    # CRUD Admin Sugerencias
    path('api/admin/sugerencias/', views_admin.SugerenciaListAPIView.as_view(), name='admin_sugerencias_list'),
    path('api/admin/sugerencias/<uuid:id>/', views_admin.SugerenciaRetrieveUpdateDestroyAPIView.as_view(), name='admin_sugerencias_rud'),
    
    # Nuevas URLs para las mejoras
    path('api/verificar-voto/<uuid:premio_id>/', VerificarVotoView.as_view(), name='verificar_voto'),
    path('api/mis-votos/', MisVotosView.as_view(), name='mis_votos'),
    path('api/admin/cambiar-estado-premio/<uuid:premio_id>/', CambiarEstadoPremioView.as_view(), name='cambiar_estado_premio'),
    path('api/admin/estadisticas-detalladas/', EstadisticasAdminView.as_view(), name='estadisticas_detalladas'),
]

# ¡SOLO EN MODO DEBUG! Sirve archivos media y estáticos durante el desarrollo.
# En producción, un servidor web como Nginx o la configuración de Render/Whitenoise
# manejarán estos archivos.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Esto ya lo manejará Whitenoise en prod