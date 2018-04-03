from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Registration, Event
from .actions import codes


class CodeView(View):
    def get_object(self):
        try:
            object_id = codes.get_id_from_code(self.code)
        except codes.InvalidCodeException:
            raise Http404()

        return get_object_or_404(Registration, numero=object_id)

    def get(self, request, code):
        if request.GET.get('person') is None or len(request.GET.get('person')) > 255:
            raise PermissionDenied()

        self.code = code
        registration = self.get_object()
        Event.objects.create(registration=registration, type='scan', person=request.GET.get('person'))

        return JsonResponse({
            'numero': registration.numero,
            'full_name': registration.full_name,
            'gender': registration.gender,
            'type': registration.category.name,
            'meta': dict([(meta.property, meta.value) for meta in registration.metas.all()]),
            'events': [{'time': event.time, 'type': event.type, 'person': event.person} for event in registration.events.all()]
        })

    def post(self, request, code):
        if request.GET.get('person') is None or len(request.GET.get('person')) > 255:
            raise PermissionDenied()

        self.code = code

        if (request.POST.get('type', None) not in [choice[0] for choice in Event.TYPE_CHOICES]):
            return HttpResponseBadRequest()

        registration = self.get_object()
        Event.objects.create(registration=registration, type=request.POST['type'], person=request.GET.get('person'))

        return HttpResponse('OK')
