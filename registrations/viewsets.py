from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from registrations.models import Registration, TicketEvent
from registrations.serializers import RegistrationSerializer, EventSerializer


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ("event", "uuid")


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    queryset = TicketEvent.objects.all()
    serializer_class = EventSerializer
