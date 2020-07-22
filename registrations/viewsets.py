from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from registrations.models import Registration, TicketEvent
from registrations.serializers import RegistrationSerializer, EventSerializer


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ("event", "uuid")


class EventViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = TicketEvent.objects.all()
    serializer_class = EventSerializer
