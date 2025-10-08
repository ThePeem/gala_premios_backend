# gala_premios/votaciones/views_admin.py

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser

from votaciones.models import Premio, Nominado, Usuario, Sugerencia # Importaciones absolutas
from votaciones.serializers import PremioSerializer, NominadoSerializer, SugerenciaSerializer # Importaciones absolutas

# Vistas CRUD para Premios (Solo para Administradores)

class PremioListCreateAPIView(ListCreateAPIView):
    """
    Permite a los administradores listar todos los premios y crear nuevos premios.
    """
    queryset = Premio.objects.all()
    serializer_class = PremioSerializer
    permission_classes = [IsAdminUser] # Solo administradores

class PremioRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Permite a los administradores recuperar, actualizar o eliminar un premio específico.
    """
    queryset = Premio.objects.all()
    serializer_class = PremioSerializer
    permission_classes = [IsAdminUser] # Solo administradores
    lookup_field = 'id' # Usa el campo 'id' (UUID) para buscar el objeto

# Vistas para Sugerencias (Solo para Administradores)

class SugerenciaListAPIView(ListAPIView):
    """
    Lista todas las sugerencias enviadas por usuarios, ordenadas por más recientes.
    """
    queryset = Sugerencia.objects.all().order_by('-fecha_sugerencia')
    serializer_class = SugerenciaSerializer
    permission_classes = [IsAdminUser]

class SugerenciaRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Permite a los administradores ver una sugerencia concreta, marcarla como revisada
    y añadir notas, o eliminarla si procede.
    """
    queryset = Sugerencia.objects.all()
    serializer_class = SugerenciaSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

# Vistas CRUD para Nominados (Solo para Administradores)

class NominadoListCreateAPIView(ListCreateAPIView):
    """
    Permite a los administradores listar todos los nominados y crear nuevos nominados.
    """
    queryset = Nominado.objects.all()
    serializer_class = NominadoSerializer
    permission_classes = [IsAdminUser] # Solo administradores

class NominadoRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Permite a los administradores recuperar, actualizar o eliminar un nominado específico.
    """
    queryset = Nominado.objects.all()
    serializer_class = NominadoSerializer
    permission_classes = [IsAdminUser] # Solo administradores
    lookup_field = 'id' # Usa el campo 'id' (UUID) para buscar el objeto


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Premio, Voto, Usuario, ConfiguracionSistema

@api_view(['GET'])
@permission_classes([IsAdminUser])
def estadisticas(request):
    """
    Vista para obtener estadísticas generales del sistema.
    """
    # Obtener o crear la configuración del sistema
    config, created = ConfiguracionSistema.objects.get_or_create()
    
    # Estadísticas de usuarios
    total_usuarios = Usuario.objects.count()
    total_votantes = Voto.objects.values('usuario').distinct().count()
    porcentaje_participacion = (total_votantes / total_usuarios * 100) if total_usuarios > 0 else 0
    
    # Estadísticas de premios
    premios_totales = Premio.objects.count()
    premios_abiertos = Premio.objects.filter(estado='abierto').count()
    premios_cerrados = Premio.objects.filter(estado='cerrado').count()
    
    # Obtener la fase actual y la próxima fase
    fase_actual = config.fase_actual
    proxima_fase = config.get_proxima_fase()
    
    # Determinar si se puede avanzar de fase
    puede_avanzar_fase = fase_actual != 'finalizado'
    
    # Determinar si se pueden publicar resultados
    puede_publicar_resultados = fase_actual == 'finalizado'
    
    return Response({
        'total_usuarios': total_usuarios,
        'total_votantes': total_votantes,
        'porcentaje_participacion': round(porcentaje_participacion, 2),
        'premios_totales': premios_totales,
        'premios_abiertos': premios_abiertos,
        'premios_cerrados': premios_cerrados,
        'fase_actual': fase_actual,
        'proxima_fase': proxima_fase,
        'puede_avanzar_fase': puede_avanzar_fase,
        'puede_publicar_resultados': puede_publicar_resultados,
        'fecha_consulta': timezone.now().isoformat()
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def avanzar_fase(request):
    """
    Vista para avanzar a la siguiente fase del sistema.
    """
    try:
        config = ConfiguracionSistema.objects.first()
        if not config:
            return Response(
                {'error': 'Configuración del sistema no encontrada'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # Obtener la próxima fase
        proxima_fase = config.get_proxima_fase()
        
        if not proxima_fase:
            return Response(
                {'error': 'No hay más fases disponibles'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar la fase actual
        config.fase_actual = proxima_fase
        config.save()
        
        # Lógica adicional según la fase a la que se avanza
        if proxima_fase == 'votacion_1':
            # Lógica para la primera ronda de votación
            pass
        elif proxima_fase == 'votacion_2':
            # Lógica para la segunda ronda de votación
            # Por ejemplo, determinar los finalistas de la ronda 1
            pass
        elif proxima_fase == 'finalizado':
            # Lógica para finalizar las votaciones
            # Por ejemplo, calcular ganadores finales
            pass
        
        return Response({
            'mensaje': f'Se ha avanzado a la fase: {config.get_fase_actual_display()}',
            'fase_actual': config.fase_actual,
            'fase_actual_display': config.get_fase_actual_display(),
            'proxima_fase': config.get_proxima_fase()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error al avanzar de fase: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )