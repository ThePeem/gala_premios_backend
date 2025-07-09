from django.contrib import admin
from .models import Usuario, Premio, Nominado, Voto, Sugerencia # Importamos nuestros modelos

# Registramos cada modelo para que aparezca en el panel de administración
admin.site.register(Usuario)
admin.site.register(Premio)
admin.site.register(Nominado)
admin.site.register(Voto)
admin.site.register(Sugerencia)