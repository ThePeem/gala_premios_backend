# gala_premios/votaciones/views_admin.py

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser

from votaciones.models import Premio, Nominado, Usuario # Importaciones absolutas
from votaciones.serializers import PremioSerializer, NominadoSerializer # Importaciones absolutas

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