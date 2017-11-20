from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views import View

from registrations.models import Registration, Event


class CodeView(View):
    def get(self, request, code=None):
        registration = get_object_or_404(Registration, code=code.split('.')[0])

        return JsonResponse({
            'code': registration.code,
            'first_name': registration.first_name,
            'last_name': registration.last_name,
            'meta': dict([(meta.property, meta.value) for meta in registration.metas.all()]),
            'events': [{'time': event.time, 'type': event.type} for event in registration.events.all()]
        })

    def post(self, request, code=None):
        if (request.POST.get('type', None) not in [choice[0] for choice in Event.TYPE_CHOICES]):
            return HttpResponseBadRequest()

        registration = get_object_or_404(Registration, code=code.split('.')[0])
        Event.objects.create(registration=registration, type=request.POST['type'])

        return HttpResponse('OK')
