# votaciones/serializers.py (MODIFICADO)

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Premio, Nominado, Voto, Sugerencia

# --- Serializers para el Modelo Usuario ---

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información pública de un usuario.
    Ideal para la lista de participantes o para vincular nominados.
    """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'foto_perfil', 'verificado', 'first_name', 'last_name', 'email'] # Añadidos first_name, last_name, email para mostrar
        read_only_fields = ['id', 'username', 'verificado'] # 'first_name', 'last_name', 'email' podrían ser editables en un perfil, pero no en este serializer público.

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.
    Incluye validación de contraseñas y campos de perfil.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        # ¡CAMBIOS CLAVE AQUÍ!
        # 1. 'descripcion' ELIMINADO.
        # 2. 'first_name' y 'last_name' AÑADIDOS (son parte de AbstractUser y los necesitas para el registro).
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'foto_perfil']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True}, # Hacer nombre requerido si así lo deseas
            'last_name': {'required': True},  # Hacer apellido requerido si así lo deseas
            'foto_perfil': {'required': False} # foto_perfil es opcional en el modelo, así que aquí también
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        if Usuario.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Ya existe un usuario con este correo electrónico."})

        # Opcional: Validar que first_name y last_name no estén vacíos si los marcaste como required=True
        # if not attrs.get('first_name'):
        #     raise serializers.ValidationError({"first_name": "El nombre es obligatorio."})
        # if not attrs.get('last_name'):
        #     raise serializers.ValidationError({"last_name": "El apellido es obligatorio."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')

        user = Usuario.objects.create_user(**validated_data)
        return user


# --- Serializers para el Modelo Nominado (DEFINIDO ANTES DE PremioSerializer) ---

class NominadoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Nominado, incluyendo información de los usuarios vinculados
    y permitiendo su asignación por ID.
    """
    # Para lectura: usamos UsuarioSerializer para mostrar detalles completos del usuario.
    # Para escritura: necesitamos un campo que acepte los UUIDs de los usuarios.
    # DRF automáticamente usará los campos correctos para lectura/escritura si los defines así.
    usuarios_vinculados = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        many=True,
        write_only=True # Este campo solo se usa para escribir (enviar IDs)
    )
    # Creamos un campo de solo lectura para mostrar los detalles completos del usuario en GET
    usuarios_vinculados_detalles = UsuarioSerializer(source='usuarios_vinculados', many=True, read_only=True)

    # El campo premio debe ser editable para asignar el premio a un nominado.
    # Usamos PrimaryKeyRelatedField para aceptar el UUID del premio.
    premio = serializers.PrimaryKeyRelatedField(queryset=Premio.objects.all())


    class Meta:
        model = Nominado
        fields = [
            'id', 'premio', 'nombre', 'descripcion', 'imagen',
            'usuarios_vinculados', 'usuarios_vinculados_detalles', # Incluimos ambos campos
            'activo'
        ]
        read_only_fields = ['id', 'activo'] # 'premio' ya no es read_only, 'usuarios_vinculados' es write_only


# --- Serializers para el Modelo Premio (DEFINIDO DESPUÉS DE NominadoSerializer) ---

class PremioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Premio.
    Incluye los nominados anidados y un campo para verificar si el usuario ya votó.
    """
    nominados = NominadoSerializer(many=True, read_only=True) # Ahora NominadoSerializer ya está definido

    ya_votado_por_usuario = serializers.SerializerMethodField()

    class Meta:
        model = Premio
        fields = '__all__'

    def get_ya_votado_por_usuario(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Voto.objects.filter(
                usuario=request.user,
                premio=obj,
                ronda=obj.ronda_actual
            ).exists()
        return False
    
    def get_nominados_con_votos(self, obj):
        nominados = obj.nominados.all().order_by('nombre')
        return NominadoSerializer(nominados, many=True).data

# --- Serializer para el Modelo Voto ---

class VotoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Voto.
    Permite registrar un voto y muestra detalles del votante, premio y nominado.
    """
    # Campos de solo lectura para mostrar información relacionada
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    premio_nombre = serializers.CharField(source='premio.nombre', read_only=True)
    nominado_nombre = serializers.CharField(source='nominado.nombre', read_only=True)

    class Meta:
        model = Voto
        # Campos que se envían desde el frontend para crear el voto
        fields = ['id', 'premio', 'nominado', 'ronda', 'usuario_username', 'premio_nombre', 'nominado_nombre', 'fecha_voto']
        # 'usuario' no se incluye en fields de entrada porque lo asignará la vista automáticamente (request.user)
        read_only_fields = ['id', 'usuario_username', 'premio_nombre', 'nominado_nombre', 'fecha_voto']

    def validate(self, data):
        # La lógica de "máximo 3 votos en Ronda 1" o "solo 1 voto en Ronda 2"
        # se manejará principalmente en la vista o en una capa de servicio.
        # Aquí solo validamos que los IDs existen y pertenecen al premio correcto.

        premio = data.get('premio')
        nominado = data.get('nominado')
        ronda = data.get('ronda') # Asegurarnos que la ronda venga en la data

        if not premio or not nominado:
            raise serializers.ValidationError("Debe especificar un premio y un nominado.")

        # Verificar que el nominado pertenece al premio
        if not nominado.premio == premio:
            raise serializers.ValidationError("El nominado seleccionado no pertenece a este premio.")

        # Verificar si el premio está activo y en la ronda correcta (opcional, también se puede en la vista)
        if not premio.activo or premio.estado != 'abierto' or premio.ronda_actual != ronda:
             raise serializers.ValidationError("Este premio no está abierto para votación en la ronda especificada.")

        return data

# --- Serializer para el Modelo Sugerencia ---

class SugerenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Sugerencia.
    Permite enviar una sugerencia y muestra el nombre de usuario del remitente.
    """
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Sugerencia
        # 'usuario' no se incluye en fields de entrada porque lo asignará la vista
        fields = ['id', 'tipo', 'contenido', 'usuario_username', 'fecha_sugerencia', 'revisada', 'notas_admin']
        read_only_fields = ['id', 'usuario_username', 'fecha_sugerencia', 'revisada', 'notas_admin']

# Re-utilizamos NominadoSerializer para los ganadores, ya que tiene los campos necesarios.
# Si en el futuro necesitas menos campos para los ganadores, podrías crear un NominadoGanadorSerializer.

class ResultadosPremioSerializer(serializers.ModelSerializer):
    # Anidamos el NominadoSerializer para mostrar los detalles de los ganadores
    ganador_oro = NominadoSerializer(read_only=True)
    ganador_plata = NominadoSerializer(read_only=True)
    ganador_bronce = NominadoSerializer(read_only=True)

    class Meta:
        model = Premio
        fields = [
            'id', 'nombre', 'descripcion', 'fecha_entrega',
            'ganador_oro', 'ganador_plata', 'ganador_bronce',
            'fecha_resultados_publicados'
        ]
        read_only_fields = fields # Este serializer es solo para lectura