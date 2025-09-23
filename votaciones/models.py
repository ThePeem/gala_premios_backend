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
        ('abierto', 'Abierto para votación'),
        ('cerrado', 'Votación cerrada'),
        ('resultados', 'Resultados publicados'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Premio")
    # Tipo de premio: directo (usuarios) o indirecto (frases/obras/etc)
    TIPO_CHOICES = [
        ('directo', 'Directo (Usuarios)'),
        ('indirecto', 'Indirecto (Frases/Objetos)'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='directo', verbose_name="Tipo de Premio")
    # Identificador estable para URLs amigables y assets estáticos
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name="Slug")
    # URL absoluta de imagen (Cloudinary/S3/etc). Alternativa a usar assets estáticos
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de Imagen")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_entrega = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    ronda_actual = models.PositiveIntegerField(default=1, verbose_name="Ronda Actual de Votación")
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='abierto', verbose_name="Estado")

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
    ronda = models.PositiveIntegerField(default=1, verbose_name="Ronda de Votación")
    # ¡NUEVO CAMPO! Para el orden en la Ronda 2. Es opcional (null=True, blank=True)
    orden_ronda2 = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Orden en Ronda 2 (1=Oro, 2=Plata, 3=Bronce)"
    )

    def __str__(self):
        if self.ronda == 2 and self.orden_ronda2:
            return f"Voto {self.orden_ronda2} de {self.usuario.username} por {self.nominado.nombre} en {self.premio.nombre} (Ronda {self.ronda})"
        return f"Voto de {self.usuario.username} por {self.nominado.nombre} en {self.premio.nombre} (Ronda {self.ronda})"

    class Meta:
        verbose_name_plural = "Votos"
        # ¡IMPORTANTE! unique_together sigue siendo ('usuario', 'premio', 'ronda')
        # Esto permite múltiples votos por premio en Ronda 1 (máximo 5),
        # y asegura que no se duplique un voto exacto para la misma ronda y premio.
        # Las reglas de los 5/3 votos y el orden se validarán en la vista.
        unique_together = ('usuario', 'premio', 'ronda', 'nominado') # Añadimos 'nominado' para permitir múltiples votos por premio/ronda, pero no por el mismo nominado.
        ordering = ['-fecha_voto']

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
        return f"Sugerencia de {self.usuario.username} ({self.get_tipo_display()})"

    class Meta:
        verbose_name_plural = "Sugerencias"
        ordering = ['-fecha_sugerencia'] # Ordenar por las más recientes primero