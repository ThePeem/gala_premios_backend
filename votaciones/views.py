# gala_premios/votaciones/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView

from django.db.models import Sum, Case, When, F 
from django.utils import timezone # Para la fecha de publicación de resultados
from django.conf import settings

from .serializers import (
    RegistroUsuarioSerializer, UsuarioSerializer, AdminUsuarioSerializer,
    PremioSerializer, VotoSerializer, NominadoSerializer, SugerenciaSerializer,
    ResultadosPremioSerializer, MisNominacionSerializer
)
from .models import Usuario, Premio, Nominado, Voto, Sugerencia

# Google token verification
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from django.utils.crypto import get_random_string

# Vista para el registro de nuevos usuarios
class RegistroUsuarioView(APIView):
    permission_classes = [AllowAny] # Permite que cualquiera (no autenticado) acceda a esta vista

    def post(self, request):
        # Instanciamos el serializer con los datos de la solicitud
        serializer = RegistroUsuarioSerializer(data=request.data)
        # Validamos los datos. Si no son válidos, se lanzará una excepción (HTTP 400)
        serializer.is_valid(raise_exception=True)
        # Guardamos el nuevo usuario (esto llama al método create() del serializer)
        user = serializer.save()

        # Opcional: Serializar el usuario creado con UsuarioSerializer para la respuesta
        # Esto asegura que la respuesta solo contenga los campos públicos definidos en UsuarioSerializer
        response_serializer = UsuarioSerializer(user)

        # Devolvemos una respuesta con los datos del usuario creado y un estado 201 CREATED
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/
    Body: { "id_token": "<google_id_token>" }
    Verifica el id_token de Google, crea/encuentra al usuario por email y devuelve token DRF.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({"detail": "Falta id_token"}, status=status.HTTP_400_BAD_REQUEST)

        google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        if not google_client_id:
            return Response({"detail": "GOOGLE_CLIENT_ID no configurado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Verify the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                google_client_id
            )

            # Additional checks
            if idinfo.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                return Response({"detail": "Emisor inválido"}, status=status.HTTP_400_BAD_REQUEST)

            email_verified = idinfo.get('email_verified', False)
            if not email_verified:
                return Response({"detail": "Email de Google no verificado"}, status=status.HTTP_400_BAD_REQUEST)

            email = idinfo.get('email')
            given_name = idinfo.get('given_name') or ''
            family_name = idinfo.get('family_name') or ''
            picture = idinfo.get('picture')

            if not email:
                return Response({"detail": "Token sin email"}, status=status.HTTP_400_BAD_REQUEST)

            # Find or create user
            user = Usuario.objects.filter(email=email).first()
            if not user:
                # Generate a username from email
                base_username = email.split('@')[0]
                username_candidate = base_username
                suffix = 1
                while Usuario.objects.filter(username=username_candidate).exists():
                    username_candidate = f"{base_username}{suffix}"
                    suffix += 1

                user = Usuario.objects.create_user(
                    username=username_candidate,
                    email=email,
                    first_name=given_name,
                    last_name=family_name,
                    password = get_random_string(12)  # longitud 12, puedes cambiarla
                )

            # Issue DRF token
            from rest_framework.authtoken.models import Token
            token, _ = Token.objects.get_or_create(user=user)

            user_data = UsuarioSerializer(user).data
            return Response({"token": token.key, "user": user_data}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": "id_token inválido", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Vista para listar todos los premios con sus nominados
class ListaPremiosView(APIView):
    # Por defecto, DRF ya usa IsAuthenticated debido a tu settings.py,
    # pero es buena práctica especificarlo explícitamente para claridad.
    permission_classes = [AllowAny]

    def get(self, request):
        # Filtramos solo los premios que están activos y abiertos para votación
        # (se puede ajustar según la lógica de negocio, por ejemplo, mostrar inactivos a admins)
        premios = Premio.objects.filter(activo=True, estado='abierto').order_by('nombre')
        # Pasamos el contexto de la request al serializer para que 'ya_votado_por_usuario' funcione
        serializer = PremioSerializer(premios, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# Vista para emitir un voto
class VotarView(APIView):
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden votar

    def post(self, request):
        
        user = request.user
        if not user.verificado:
            return Response(
                {"detail": "Tu cuenta no ha sido verificada por un administrador y no puedes votar.", "code": "user_not_verified"},
                status=status.HTTP_403_FORBIDDEN # 403 Forbidden
            )
        
        serializer = VotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        premio = serializer.validated_data['premio']
        nominado = serializer.validated_data['nominado']
        ronda = serializer.validated_data.get('ronda', 1) # Si no se especifica, asume ronda 1
        orden_ronda2 = serializer.validated_data.get('orden_ronda2', None) # Obtiene el orden, puede ser None

        # 1. Validar que el usuario no se vote a sí mismo
        # Comprueba si el nominado actual está vinculado al usuario que vota
        if nominado.usuarios_vinculados.filter(id=request.user.id).exists():
            return Response(
                {"detail": "No puedes votarte a ti mismo en ninguna ronda.", "code": "self_vote_forbidden"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Verificar que el premio está activo y abierto para votación en la ronda correcta
        if not premio.activo or premio.estado != 'abierto' or premio.ronda_actual != ronda:
            return Response(
                {"detail": f"Este premio no está abierto para votación en la Ronda {ronda}.", "code": "premio_not_open"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Verificar que el nominado pertenece al premio
        if not nominado.premio == premio:
            return Response(
                {"detail": "El nominado seleccionado no pertenece a este premio.", "code": "nominado_mismatch"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Lógica de votación por rondas
        existing_votes = Voto.objects.filter(usuario=request.user, premio=premio, ronda=ronda)

        if ronda == 1:
            # En la Ronda 1, el usuario puede votar hasta 5 nominados diferentes por premio
            if existing_votes.count() >= 5:
                return Response(
                    {"detail": "Ya has emitido el máximo de 5 votos para este premio en la Ronda 1.", "code": "max_votes_r1_reached"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Asegurarse de que no vota dos veces por el mismo nominado en la misma ronda
            if existing_votes.filter(nominado=nominado).exists():
                return Response(
                    {"detail": "Ya has votado por este nominado en esta ronda.", "code": "already_voted_nominado_r1"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Asegurarse de que 'orden_ronda2' no se envía en Ronda 1
            if orden_ronda2 is not None:
                return Response(
                    {"detail": "El campo 'orden_ronda2' no es válido en la Ronda 1.", "code": "invalid_order_r1"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif ronda == 2:
            # En la Ronda 2, el usuario vota su top 3 (Oro, Plata, Bronce)
            if orden_ronda2 is None:
                return Response(
                    {"detail": "Para la Ronda 2, debes especificar un 'orden_ronda2' (1, 2 o 3).", "code": "missing_order_r2"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if orden_ronda2 not in [1, 2, 3]:
                return Response(
                    {"detail": "El 'orden_ronda2' debe ser 1 (Oro), 2 (Plata) o 3 (Bronce).", "code": "invalid_order_value"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Comprobar que no ha votado 3 veces ya en la ronda 2 para este premio
            if existing_votes.count() >= 3:
                 return Response(
                    {"detail": "Ya has emitido el máximo de 3 votos para este premio en la Ronda 2.", "code": "max_votes_r2_reached"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Comprobar que la posición (orden_ronda2) no ha sido usada ya para este premio en Ronda 2
            if existing_votes.filter(orden_ronda2=orden_ronda2).exists():
                return Response(
                    {"detail": f"Ya has usado la posición {orden_ronda2} para este premio en la Ronda 2.", "code": "position_already_used"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Comprobar que no ha votado por el mismo nominado dos veces en Ronda 2 (aunque la posición sea diferente)
            if existing_votes.filter(nominado=nominado).exists():
                return Response(
                    {"detail": "Ya has votado por este nominado en esta Ronda 2.", "code": "already_voted_nominado_r2"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Opcional: Validación de que el nominado es un finalista (esto requiere más lógica)
            # Por ahora, asumimos que el frontend solo presentará finalistas válidos.
            # futura_logica_finalistas = premio.nominados.filter(es_finalista_ronda2=True)
            # if nominado not in futura_logica_finalistas: ...

        else:
            return Response(
                {"detail": "Ronda de votación no válida.", "code": "invalid_round"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si todas las validaciones pasan, guardar el voto
        # El serializer no tiene el usuario, lo asignamos aquí
        serializer.save(usuario=request.user)

        return Response(
            {"message": "Voto registrado con éxito.", "voto_id": serializer.data['id']},
            status=status.HTTP_201_CREATED
        )

# Vista para listar todos los usuarios (participantes)
class ListaParticipantesView(APIView):
    permission_classes = [AllowAny] # Vista pública

    def get(self, request):
        # Opcional: Podrías filtrar por usuarios que tienen rol 'votante'
        # o que tienen 'descripcion' o 'foto_perfil' para que no salgan superusuarios "vacíos"
        # usuarios = Usuario.objects.filter(rol='votante', activo=True).order_by('username')
        usuarios = Usuario.objects.filter(verificado=True).order_by('username') # Solo participantes verificados
        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Vista para ver y editar el perfil del usuario autenticado
class MiPerfilView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated] # Solo el usuario logueado puede acceder
    serializer_class = UsuarioSerializer # Usamos UsuarioSerializer para mostrar y actualizar

    # Este método asegura que solo se acceda al perfil del usuario autenticado
    def get_object(self):
        return self.request.user # Devuelve el objeto Usuario del usuario autenticado


# Vista para listar las nominaciones del usuario autenticado
class MisNominacionesView(APIView):
    permission_classes = [IsAuthenticated] # Solo el usuario logueado puede ver sus nominaciones

    def get(self, request):
        # Filtra los nominados donde el usuario autenticado está vinculado
        nominaciones = Nominado.objects.filter(usuarios_vinculados=request.user).order_by('nombre')
        serializer = MisNominacionSerializer(nominaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MisEstadisticasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Nominaciones del usuario
        nominaciones_qs = Nominado.objects.filter(usuarios_vinculados=user)
        total_nominaciones = nominaciones_qs.count()

        # Votos recibidos: todos los votos a nominados vinculados a este usuario
        total_votos_recibidos = Voto.objects.filter(nominado__in=nominaciones_qs).count()

        # Medallas: contar en Premios si alguno de sus ganadores apunta a un nominado vinculado al usuario
        oros = Premio.objects.filter(ganador_oro__in=nominaciones_qs).count()
        platas = Premio.objects.filter(ganador_plata__in=nominaciones_qs).count()
        bronces = Premio.objects.filter(ganador_bronce__in=nominaciones_qs).count()

        # Flags de fase
        mostrar_ronda2 = Premio.objects.filter(ronda_actual=2, estado='abierto').exists()
        mostrar_medallas = Premio.objects.filter(estado='resultados').exists()

        data = {
            "total_nominaciones": total_nominaciones,
            "total_votos_recibidos": total_votos_recibidos,
            "oros": oros,
            "platas": platas,
            "bronces": bronces,
            "fase": {
                "mostrar_medallas": mostrar_medallas,
                "mostrar_ronda2": mostrar_ronda2,
            },
        }
        return Response(data, status=status.HTTP_200_OK)

# Vista para que los usuarios envíen sugerencias
class EnviarSugerenciaView(CreateAPIView):
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden enviar sugerencias
    serializer_class = SugerenciaSerializer

    # Asigna automáticamente el usuario autenticado a la sugerencia
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

# Vista para calcular y mostrar los resultados finales de la Ronda 2 (GET)
# Y para que el admin publique y guarde los resultados (POST)
class ResultadosView(APIView):
    # GET: Solo admins inicialmente. POST: Solo admins.
    permission_classes = [IsAdminUser]

    def get(self, request):
        # ... (Tu lógica existente para el método GET de ResultadosView, no la modifiques aquí)
        PUNTOS_ORO = 3
        PUNTOS_PLATA = 2
        PUNTOS_BRONCE = 1

        premios = Premio.objects.all().order_by('nombre')
        resultados_finales = []

        for premio in premios:
            nominados_con_puntos = Voto.objects.filter(
                premio=premio,
                ronda=2,
                orden_ronda2__in=[1, 2, 3]
            ).values('nominado__id', 'nominado__nombre', 'nominado__descripcion', 'nominado__imagen').annotate(
                puntos_totales=Sum(
                    Case(
                        When(orden_ronda2=1, then=PUNTOS_ORO),
                        When(orden_ronda2=2, then=PUNTOS_PLATA),
                        When(orden_ronda2=3, then=PUNTOS_BRONCE),
                        default=0
                    )
                )
            ).order_by('-puntos_totales', 'nominado__nombre')

            ganador_oro = None
            ganador_plata = None
            ganador_bronce = None

            nominados_lista = list(nominados_con_puntos)

            if len(nominados_lista) > 0:
                ganador_oro = Nominado.objects.get(id=nominados_lista[0]['nominado__id'])
            if len(nominados_lista) > 1:
                ganador_plata = Nominado.objects.get(id=nominados_lista[1]['nominado__id'])
            if len(nominados_lista) > 2:
                ganador_bronce = Nominado.objects.get(id=nominados_lista[2]['nominado__id'])

            resultados_finales.append({
                'premio_id': str(premio.id),
                'premio_nombre': premio.nombre,
                'ganadores': {
                    'oro': NominadoSerializer(ganador_oro).data if ganador_oro else None,
                    'plata': NominadoSerializer(ganador_plata).data if ganador_plata else None,
                    'bronce': NominadoSerializer(ganador_bronce).data if ganador_bronce else None,
                },
                'nominados_por_puntos': list(nominados_con_puntos)
            })

        return Response(resultados_finales, status=status.HTTP_200_OK)


    # ¡NUEVO MÉTODO POST! Para que el administrador publique los resultados.
    def post(self, request):
        premio_id = request.data.get('premio_id')

        if not premio_id:
            return Response(
                {"detail": "Se requiere el ID del premio para publicar los resultados.", "code": "missing_premio_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            premio = Premio.objects.get(id=premio_id)
        except Premio.DoesNotExist:
            return Response(
                {"detail": "Premio no encontrado.", "code": "premio_not_found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validación: No permitir si los resultados ya han sido publicados
        if premio.estado == 'resultados':
            return Response(
                {"detail": f"Los resultados para '{premio.nombre}' ya han sido publicados.", "code": "results_already_published"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reutilizar la lógica de cálculo de puntos de la Ronda 2 (similar al GET)
        PUNTOS_ORO = 3
        PUNTOS_PLATA = 2
        PUNTOS_BRONCE = 1

        nominados_con_puntos = Voto.objects.filter(
            premio=premio,
            ronda=2,
            orden_ronda2__in=[1, 2, 3]
        ).values('nominado__id', 'nominado__nombre').annotate( # Solo necesitamos ID y nombre para identificar
            puntos_totales=Sum(
                Case(
                    When(orden_ronda2=1, then=PUNTOS_ORO),
                    When(orden_ronda2=2, then=PUNTOS_PLATA),
                    When(orden_ronda2=3, then=PUNTOS_BRONCE),
                    default=0
                )
            )
        ).order_by('-puntos_totales', 'nominado__nombre')

        ganador_oro = None
        ganador_plata = None
        ganador_bronce = None

        nominados_lista = list(nominados_con_puntos)

        if len(nominados_lista) > 0:
            ganador_oro = Nominado.objects.get(id=nominados_lista[0]['nominado__id'])
        if len(nominados_lista) > 1:
            ganador_plata = Nominado.objects.get(id=nominados_lista[1]['nominado__id'])
        if len(nominados_lista) > 2:
            ganador_bronce = Nominado.objects.get(id=nominados_lista[2]['nominado__id'])

        # Guardar los ganadores en el modelo Premio
        premio.ganador_oro = ganador_oro
        premio.ganador_plata = ganador_plata
        premio.ganador_bronce = ganador_bronce
        premio.fecha_resultados_publicados = timezone.now() # Establece la fecha de publicación
        premio.estado = 'resultados' # Cambia el estado del premio
        premio.save()

        # Serializar el premio para devolver la información actualizada
        serializer = ResultadosPremioSerializer(premio) # Usamos el serializer de resultados
        
        return Response(
            {"message": f"Resultados para '{premio.nombre}' calculados y publicados con éxito.", "premio_resultados": serializer.data},
            status=status.HTTP_200_OK
        )
# Vista para mostrar públicamente los resultados de premios ya publicados
class ResultadosPublicosView(APIView):
    permission_classes = [AllowAny] # Cualquiera puede ver los resultados publicados

    def get(self, request):
        # Filtra los premios que tienen sus resultados publicados
        premios_publicados = Premio.objects.filter(
            estado='resultados',
            fecha_resultados_publicados__isnull=False
        ).order_by('nombre')

        serializer = ResultadosPremioSerializer(premios_publicados, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Vistas para la administración de usuarios por parte de administradores
class UsuarioListCreateView(ListCreateAPIView): 
    queryset = Usuario.objects.all().order_by('username') 
    serializer_class = AdminUsuarioSerializer
    permission_classes = [IsAdminUser] 

    # Opcional: para la creación, puedes sobrescribir perform_create si necesitas lógica adicional,
    # pero el UsuarioSerializer debería manejarlo bien con los campos especificados.
    # Si permites la creación de usuarios desde aquí, asegúrate de que maneje contraseñas.
    # El RegistroUsuarioSerializer es para el registro público, este es para admins.


class UsuarioDetailView(RetrieveUpdateDestroyAPIView): 
    queryset = Usuario.objects.all()
    serializer_class = AdminUsuarioSerializer
    permission_classes = [IsAdminUser] 
    lookup_field = 'pk' 