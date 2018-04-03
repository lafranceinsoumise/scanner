from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.views import View

from .models import ScannerAction
from .actions.scans import scan_code, mark_registration, InvalidCodeException


class CodeView(View):
    def get_person(self):
        person = self.request.GET.get('person')

        if person is None or len(person) > 255:
            raise PermissionDenied()

        return person

    def get(self, request, code):
        person = self.get_person()

        try:
            registration = scan_code(code, person)
        except InvalidCodeException:
            raise Http404

        return JsonResponse({
            'numero': registration.numero,
            'full_name': registration.full_name,
            'gender': registration.gender,
            'type': registration.category.name,
            'meta': dict([(meta.property, meta.value) for meta in registration.metas.all()]),
            'events': [{'time': event.time, 'type': event.type, 'person': event.person} for event in registration.events.all()]
        })

    def post(self, request, code):
        person = self.get_person()
        type = self.request.POST.get('type')

        if type not in [ScannerAction.TYPE_ENTRANCE, ScannerAction.TYPE_CANCEL]:
            return HttpResponseBadRequest()

        try:
            mark_registration(code, type, person)
        except InvalidCodeException:
            return Http404

        return HttpResponse('OK')
