from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid

# Modelo de Usuario
class Usuario(AbstractUser):
    # Aquí puedes añadir campos adicionales a tu modelo de usuario
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ... otros campos que hayas añadido (ej. foto_perfil)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    # Nueva URL de foto (Cloudinary/S3/etc.) para no depender de almacenamiento local
    foto_url = models.URLField(blank=True, null=True, verbose_name="URL de Foto de Perfil")
    # Descripción/bio del usuario para mostrar en su perfil
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Perfil")

    # Nuevo campo para la verificación
    verificado = models.BooleanField(default=False,
                                     help_text="Indica si el usuario ha sido verificado por un administrador y puede votar.")

    # Vinculación explícita con un slot de participante visible en la web
    PARTICIPANTE_CHOICES = (
        ('Jose', 'Jose'),
        ('Garcia', 'Garcia'),
        ('Felipe', 'Felipe'),
        ('Catedra', 'Catedra'),
        ('Richi', 'Richi'),
        ('Alex', 'Alex'),
        ('Chema', 'Chema'),
        ('Dani', 'Dani'),
        ('Alejandra', 'Alejandra'),
        ('Sandra', 'Sandra'),
        ('Rocio', 'Rocio'),
        ('Joaquin', 'Joaquin'),
        ('Silvia', 'Silvia'),
        ('Gema', 'Gema'),
        ('Ana', 'Ana'),
        ('Tomas', 'Tomas'),
        # Añade aquí los dos restantes si se suben (hasta 18)
    )
    participante_tag = models.CharField(
        max_length=32,
        choices=PARTICIPANTE_CHOICES,
        null=True,
        blank=True,
        unique=True,
        help_text="Etiqueta del slot de participante asignado (único)."
    )

    # Resolución de colisiones de related_name para grupos y permisos
    # Es vital cuando se usa un Custom User Model
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="votaciones_usuario_set", # <--- ¡CAMBIO CLAVE AQUÍ!
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="votaciones_usuario_permissions", # <--- ¡CAMBIO CLAVE AQUÍ!
        related_query_name="usuario",
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username

# Modelo de Premio
class Premio(models.Model):
    ESTADO_CHOICES = [
        ('preparacion', 'En preparación'),
        ('votacion_1', 'Votación Ronda 1'),
        ('votacion_2', 'Votación Ronda 2'),
        ('finalizado', 'Finalizado')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Premio")
    # Tipo de premio: directo (usuarios) o indirecto (frases/obras/etc)
    TIPO_CHOICES = [
        ('directo', 'Directo (Usuarios)'),
        ('indirecto', 'Indirecto (Frases/Objetos)'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='directo', verbose_name="Tipo de Premio")
    
    # Fechas de las rondas
    fecha_inicio_ronda1 = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Ronda 1")
    fecha_fin_ronda1 = models.DateTimeField(null=True, blank=True, verbose_name="Fin Ronda 1")
    fecha_inicio_ronda2 = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Ronda 2")
    fecha_fin_ronda2 = models.DateTimeField(null=True, blank=True, verbose_name="Fin Ronda 2")
    
    # Ronda actual (1 o 2)
    ronda_actual = models.PositiveSmallIntegerField(default=1, verbose_name="Ronda Actual")
    # Identificador estable para URLs amigables y assets estáticos
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name="Slug")
    # URL absoluta de imagen (Cloudinary/S3/etc). Alternativa a usar assets estáticos
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de Imagen")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_entrega = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='preparacion', verbose_name="Estado")

    # Nuevo: cantidad de usuarios vinculados requeridos por nominado para este premio (1 por defecto; p.ej. Pareja del Año = 2)
    vinculos_requeridos = models.PositiveIntegerField(default=1, verbose_name="Usuarios vinculados requeridos")

    # ¡NUEVOS CAMPOS para los ganadores!
    ganador_oro = models.ForeignKey(
        'Nominado',
        on_delete=models.SET_NULL, # Si el nominado se elimina, este campo se pone a NULL
        related_name='premios_oro',
        blank=True,
        null=True,
        verbose_name="Ganador Oro"
    )
    ganador_plata = models.ForeignKey(
        'Nominado',
        on_delete=models.SET_NULL,
        related_name='premios_plata',
        blank=True,
        null=True,
        verbose_name="Ganador Plata"
    )
    ganador_bronce = models.ForeignKey(
        'Nominado',
        on_delete=models.SET_NULL,
        related_name='premios_bronce',
        blank=True,
        null=True,
        verbose_name="Ganador Bronce"
    )
    # Fecha en la que se publicaron los resultados
    fecha_resultados_publicados = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Publicación de Resultados"
    )

    # Historial de ganadores (lista de objetos con {year, name})
    # Requiere Django 3.1+ para JSONField en todos los backends.
    try:
        from django.db.models import JSONField as BuiltinJSONField  # type: ignore
        JSONField = BuiltinJSONField  # type: ignore
    except Exception:  # pragma: no cover
        from django.contrib.postgres.fields import JSONField  # type: ignore

    ganadores_historicos = JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Lista de los últimos ganadores: [{ 'year': 2024, 'name': 'Nombre' }, ...]"
    )


    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Premio"
        verbose_name_plural = "Premios"
        ordering = ['nombre']

# Modelo de Nominado (¡REDIFINIDO CON ManyToMany a Usuario!)
class Nominado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Relación ForeignKey: Un nominado pertenece a un premio.
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE, related_name='nominados', verbose_name="Premio")

    # Campos para el nominado (texto libre e imagen)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Nominado")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    imagen = models.ImageField(upload_to='nominados/', blank=True, null=True, verbose_name="Imagen del Nominado") # Campo para la imagen

    # ¡NUEVA RELACIÓN! Opcional, con uno o varios usuarios
    # related_name='nominaciones_vinculadas' permitirá acceder a estas desde un objeto Usuario
    usuarios_vinculados = models.ManyToManyField(
        Usuario,
        related_name='nominaciones_vinculadas',
        blank=True, # Hace que la relación sea opcional (puede no haber usuarios vinculados)
        verbose_name="Usuarios Vinculados (Opcional)"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    def __str__(self):
        # Mejora la representación para mostrar usuarios vinculados si existen
        if self.usuarios_vinculados.exists():
            # Obtiene los usernames de los usuarios vinculados
            vinculados = ", ".join([u.username for u in self.usuarios_vinculados.all()])
            return f"{self.nombre} ({self.premio.nombre} - Vinculado/s: {vinculados})"
        return f"{self.nombre} ({self.premio.nombre})"

    class Meta:
        verbose_name_plural = "Nominados"
        # Asegura que no haya dos nominados con el mismo nombre para el mismo premio.
        # Si tienes nombres genéricos como "Mejor Momento", esta restricción podría ser muy estricta.
        # Considera si la unicidad debe ser solo por 'nombre' o 'nombre' y 'premio'.
        # Por ahora, mantengamos 'premio' y 'nombre' como únicos para evitar duplicados exactos.
        unique_together = ('premio', 'nombre')
        ordering = ['nombre']

# Modelo de Voto (¡AJUSTADO PARA RONDAS!)
class Voto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='votos_emitidos', verbose_name="Usuario")
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE, related_name='votos', verbose_name="Premio Votado")
    nominado = models.ForeignKey(Nominado, on_delete=models.CASCADE, related_name='votos_recibidos', verbose_name="Nominado Votado")
    fecha_voto = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Voto")
    ronda = models.PositiveSmallIntegerField(default=1, verbose_name="Ronda de Votación")
    orden_ronda2 = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Orden en Ronda 2 (1=Oro, 2=Plata, 3=Bronce)",
        help_text="Solo aplica para la Ronda 2"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    
    class Meta:
        constraints = [
            # Validar que no se pueda votar dos veces al mismo nominado en la misma ronda
            models.UniqueConstraint(
                fields=['usuario', 'premio', 'ronda', 'nominado'],
                name='unico_voto_por_nominado_ronda'
            ),
            # En la ronda 2, validar que el orden sea entre 1 y 3
            models.CheckConstraint(
                check=(
                    models.Q(ronda=2, orden_ronda2__in=[1, 2, 3]) | 
                    (models.Q(ronda=1) & models.Q(orden_ronda2__isnull=True))
                ),
                name='orden_valido_para_ronda2'
            ),
            # Validar que en la ronda 2 no se pueda votar más de 3 veces por premio
            models.UniqueConstraint(
                fields=['usuario', 'premio', 'ronda', 'orden_ronda2'],
                condition=models.Q(ronda=2),
                name='unico_orden_por_voto_ronda2'
            )
        ]
        indexes = [
            models.Index(fields=['usuario', 'premio', 'ronda']),
            models.Index(fields=['premio', 'ronda', 'fecha_voto']),
            models.Index(fields=['fecha_voto']),
        ]
        verbose_name = 'Voto'
        verbose_name_plural = 'Votos'
        ordering = ['-fecha_voto']
    
    def __str__(self):
        if self.ronda == 2 and self.orden_ronda2:
            return f"Voto {self.orden_ronda2} de {self.usuario.username} por {self.nominado.nombre} en {self.premio.nombre} (Ronda {self.ronda})"
        return f"Voto de {self.usuario.username} por {self.nominado.nombre} en {self.premio.nombre} (Ronda {self.ronda})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar que no se vote por uno mismo
        if hasattr(self, 'usuario') and hasattr(self, 'nominado'):
            if self.usuario in self.nominado.usuarios_vinculados.all():
                raise ValidationError("No puedes votar por un nominado al que estás vinculado")
        
        # Validar que el voto sea en la ronda correcta del premio
        if hasattr(self, 'premio') and hasattr(self, 'ronda'):
            if self.premio.estado != f'votacion_{self.ronda}':
                raise ValidationError(f"La ronda {self.ronda} no está activa para este premio")
            
            # Validar que el premio esté en estado de votación
            if not self.premio.estado.startswith('votacion_'):
                raise ValidationError("Este premio no está en período de votación")
            
            # Validar que el usuario no haya votado más veces de las permitidas en esta ronda
            votos_en_ronda = Voto.objects.filter(
                usuario=self.usuario,
                premio=self.premio,
                ronda=self.ronda
            ).exclude(pk=getattr(self, 'pk', None)).count()
            
            if self.ronda == 1 and votos_en_ronda >= 4:
                raise ValidationError("Ya has alcanzado el límite de 4 votos en la Ronda 1")
            elif self.ronda == 2 and votos_en_ronda >= 3:
                raise ValidationError("Ya has alcanzado el límite de 3 votos en la Ronda 2")
    
    def save(self, *args, **kwargs):
        # Si es un voto nuevo (no actualización) y no hay IP/User-Agent en los kwargs
        if not self.pk and not self.ip_address and hasattr(self, 'request'):
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                self.ip_address = x_forwarded_for.split(',')[0]
            else:
                self.ip_address = self.request.META.get('REMOTE_ADDR')
            self.user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:500]
        
        self.full_clean()
        super().save(*args, **kwargs)

# Modelo de Sugerencia
class Sugerencia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Las sugerencias las pueden enviar solo usuarios logueados, de ahí la ForeignKey
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sugerencias_enviadas', verbose_name="Usuario")

    TIPO_SUGERENCIA_CHOICES = (
        ('premio', 'Nuevo Premio'),
        ('nominado', 'Nuevo Nominado'),
        ('otro', 'Otro Tipo'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_SUGERENCIA_CHOICES, verbose_name="Tipo de Sugerencia")
    contenido = models.TextField(verbose_name="Contenido de la Sugerencia")
    fecha_sugerencia = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Sugerencia")
    revisada = models.BooleanField(default=False, verbose_name="Revisada por Administrador")
    notas_admin = models.TextField(blank=True, null=True, verbose_name="Notas del Administrador")

    def __str__(self):
        return f"Sugerencia de {self.usuario.username} - {self.get_tipo_display()}"


class ConfiguracionSistema(models.Model):
    """
    Modelo para almacenar la configuración global del sistema de votación.
    """
    fase_actual = models.CharField(
        max_length=20,
        choices=[
            ('preparacion', 'Preparación'),
            ('votacion_1', 'Votación Ronda 1'),
            ('votacion_2', 'Votación Ronda 2'),
            ('finalizado', 'Finalizado')
        ],
        default='preparacion',
        verbose_name="Fase Actual del Sistema"
    )
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def get_proxima_fase(self):
        fases = ['preparacion', 'votacion_1', 'votacion_2', 'finalizado']
        try:
            indice_actual = fases.index(self.fase_actual)
            if indice_actual < len(fases) - 1:
                return fases[indice_actual + 1]
        except ValueError:
            pass
        return None
    
    def __str__(self):
        return f"Configuración - Fase: {self.get_fase_actual_display()}"
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"