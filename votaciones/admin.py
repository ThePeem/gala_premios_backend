from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Premio, Nominado, Voto, Sugerencia # Importamos nuestros modelos

# Creamos una clase de administración personalizada para Usuario
class CustomUserAdmin(UserAdmin):
    # Aquí puedes personalizar qué campos se muestran en la lista de usuarios en el admin
    list_display = UserAdmin.list_display + ('verificado',) # Añade 'verificado' a la lista de columnas

    # Aquí puedes personalizar los campos que se editan al ver o añadir un usuario
    # Puedes añadir 'verificado' a uno de los fieldsets existentes o crear uno nuevo.
    fieldsets = UserAdmin.fieldsets + (
        ('Verificación', {'fields': ('verificado',)}),
    )
    # También puedes añadirlo al add_fieldsets si los tienes personalizados para la creación

# Desregistra el User por defecto si ya lo habías registrado antes y registra tu CustomUserAdmin
admin.site.register(Usuario, CustomUserAdmin)

# Registramos cada modelo para que aparezca en el panel de administración
admin.site.register(Usuario)
admin.site.register(Premio)
admin.site.register(Nominado)
admin.site.register(Voto)
admin.site.register(Sugerencia)