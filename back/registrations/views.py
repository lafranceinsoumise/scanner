from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from registrations.models import Registration


def view_code(self, code=None):
    registration = get_object_or_404(Registration, code=code.split('.')[0])

    return JsonResponse({
        'code': registration.code,
        'first_name': registration.first_name,
        'last_name': registration.last_name,
        'meta': dict([(meta.property, meta.value) for meta in registration.metas.all()])
    })
