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