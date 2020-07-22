from rest_framework import routers

from registrations import viewsets


router = routers.DefaultRouter()
router.register(r"registrations", viewsets.RegistrationViewSet)
router.register(r"events", viewsets.EventViewSet)
