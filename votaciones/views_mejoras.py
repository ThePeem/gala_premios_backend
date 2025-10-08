from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db import transaction, models
from django.core.exceptions import ValidationError

from .models import Premio, Voto, Usuario
from .serializers import PremioSerializer, VotoSerializer

class VerificarVotoView(APIView):
    """
    Verifica si el usuario ya ha votado en la ronda actual de un premio
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, premio_id):
        try:
            premio = Premio.objects.get(id=premio_id)
        except Premio.DoesNotExist:
            return Response(
                {"error": "Premio no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        ya_voto = Voto.objects.filter(
            usuario=request.user,
            premio=premio,
            ronda=premio.ronda_actual
        ).exists()

        return Response({
            "ya_voto": ya_voto,
            "ronda_actual": premio.ronda_actual,
            "estado_premio": premio.get_estado_display(),
            "limite_votos": 5 if premio.ronda_actual == 1 else 3
        })

class MisVotosView(APIView):
    """
    Muestra los votos emitidos por el usuario autenticado
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        votos = Voto.objects.filter(usuario=request.user).select_related('premio', 'nominado')
        
        resultados = {}
        for voto in votos:
            if voto.premio.id not in resultados:
                resultados[voto.premio.id] = {
                    'ronda_1': [],
                    'ronda_2': []
                }
            
            voto_data = {
                'id': str(voto.id),
                'nominado': voto.nominado.nombre,
                'fecha': voto.fecha_voto.isoformat(),
                'orden': voto.orden_ronda2
            }
            
            if voto.ronda == 1:
                resultados[voto.premio.id]['ronda_1'].append(voto_data)
            else:
                resultados[voto.premio.id]['ronda_2'].append(voto_data)
                
        return Response(list(resultados.values()))

class CambiarEstadoPremioView(APIView):
    """
    Permite a los administradores cambiar el estado de un premio
    """

    def post(self, request, premio_id):
        try:
            premio = Premio.objects.get(id=premio_id)
        except Premio.DoesNotExist:
            return Response(
                {"error": "Premio no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        nuevo_estado = request.data.get('nuevo_estado')
        
        # Validar transición de estado
        transiciones_validas = {
            'preparacion': ['votacion_1'],
            'votacion_1': ['votacion_2', 'finalizado'],
            'votacion_2': ['finalizado'],
            'finalizado': []
        }
        
        if nuevo_estado not in dict(Premio.ESTADO_CHOICES):
            return Response(
                {"error": "Estado inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if nuevo_estado not in transiciones_validas[premio.estado]:
            return Response(
                {"error": f"No se puede cambiar de {premio.estado} a {nuevo_estado}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar estado y fechas
        with transaction.atomic():
            ahora = timezone.now()
            if nuevo_estado == 'votacion_1':
                premio.fecha_inicio_ronda1 = ahora
                premio.ronda_actual = 1
            elif nuevo_estado == 'votacion_2':
                premio.fecha_fin_ronda1 = ahora
                premio.fecha_inicio_ronda2 = ahora
                premio.ronda_actual = 2
            elif nuevo_estado == 'finalizado':
                premio.fecha_fin_ronda2 = ahora
                premio.fecha_resultados_publicados = ahora
            
            premio.estado = nuevo_estado
            premio.save()
            
        return Response({
            "mensaje": f"Estado del premio actualizado a {nuevo_estado}",
            "premio": PremioSerializer(premio).data
        })

class EstadisticasAdminView(APIView):
    """
    Proporciona estadísticas para el panel de administración
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_usuarios = Usuario.objects.count()
        total_premios = Premio.objects.count()
        
        # Premios por estado
        premios_por_estado = Premio.objects.values('estado').annotate(
            total=models.Count('id')
        )
        
        # Votos por ronda
        votos_por_ronda = Voto.objects.values('ronda').annotate(
            total=models.Count('id')
        )
        
        # Últimos votos
        ultimos_votos = (Voto.objects
                          .select_related('usuario', 'premio', 'nominado')
                          .order_by('-fecha_voto')[:10])
        
        # Usuarios más activos (más votos emitidos)
        usuarios_activos = Usuario.objects.annotate(
            total_votos=models.Count('votos_emitidos')
        ).order_by('-total_votos')[:5]
        
        return Response({
            'total_usuarios': total_usuarios,
            'total_premios': total_premios,
            'premios_por_estado': {p['estado']: p['total'] for p in premios_por_estado},
            'votos_por_ronda': {f"ronda_{v['ronda']}": v['total'] for v in votos_por_ronda},
            'ultimos_votos': [
                {
                    'usuario': v.usuario.username,
                    'premio': v.premio.nombre,
                    'nominado': v.nominado.nombre,
                    'ronda': v.ronda,
                    'fecha': v.fecha_voto.isoformat()
                } for v in ultimos_votos
            ],
            'usuarios_activos': [
                {
                    'usuario': u.username,
                    'total_votos': u.total_votos
                } for u in usuarios_activos
            ]
        })
