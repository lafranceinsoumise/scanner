from rest_framework import viewsets, mixins

from registrations.models import Registration
from registrations.serializers import RegistrationSerializer


class RegistrationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
