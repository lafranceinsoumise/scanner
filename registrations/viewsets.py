from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins

from registrations.models import Registration
from registrations.serializers import RegistrationSerializer


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ("event", "uuid")
