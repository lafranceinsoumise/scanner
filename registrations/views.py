from django.core.exceptions import PermissionDenied
from django.db.models import Q, F, Max
from django.http import FileResponse, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.views import View
from django.views.generic import CreateView
import subprocess

from .models import Registration, ScannerAction, ScanPoint, ScanSeq, TicketEvent
from .actions.scans import scan_code, mark_registration, InvalidCodeException


class CodeView(View):
    def get_person(self):
        person = self.request.GET.get("person")

        if person is None or len(person) > 255:
            raise PermissionDenied()

        return person

    def get_event(self):
        try:
            TicketEvent.objects.get(id=self.request.GET.get("event"))
        except (TicketEvent.DoesNotExist, ValueError, TypeError):
            return None
        

    def get_point(self):
        try:
            return ScanPoint.objects.get(id=self.request.GET.get("point"))
        except (ScanPoint.DoesNotExist, ValueError, TypeError):
            points = ScanPoint.objects.get(event__id=self.request.GET.get("event"))
            if points:
                return points.first()
            return None

    def get(self, request, code):
        person = self.get_person()
        point = self.get_point()
        event = self.get_event()

        try:
            registration = scan_code(code, person, point, event)
        except InvalidCodeException:
            raise Http404

        return JsonResponse(
            {
                "numero": registration.numero,
                "ticket_event_id": registration.event.id,
                "canceled": registration.canceled,
                "full_name": registration.full_name,
                "gender": registration.gender,
                "category": {
                    "name": registration.category.name,
                    "color": registration.category.color,
                    "background-color": registration.category.background_color,
                },
                "meta": dict(
                    [(meta.property, meta.value) for meta in registration.metas.all()]
                ),
                "events": [
                    {
                        "id": event.id,
                        "time": event.time,
                        "type": event.type,
                        "person": event.person,
                        "point": event.point.name if event.point is not None else None,
                    }
                    for event in registration.events.annotate(
                        last_seq=Max("point__seqs__created")
                    ).filter(Q(last_seq=None) | Q(last_seq__lt=F("time")))
                ],
            }
        )

    def post(self, request, code):
        person = self.get_person()
        type = self.request.POST.get("type")
        point = self.get_point()

        if type not in [ScannerAction.TYPE_ENTRANCE, ScannerAction.TYPE_CANCEL]:
            return HttpResponseBadRequest()

        if point is None and request.POST:
            return HttpResponseBadRequest()

        try:
            mark_registration(code, type, person, point)
        except InvalidCodeException:
            return Http404

        return HttpResponse("OK")


class CreateSeqView(CreateView):
    model = ScanSeq
    fields = ("point",)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponse("OK")

class DownloadWalletPassView(View):
    def get(self, request, registration_id, token):
        registration = get_object_or_404(
            Registration,
            pk=registration_id,
            wallet_token=token
        )
        
        if not registration.wallet_pass:
            registration.generate_wallet_pass()
        
        if registration.wallet_pass:
            response = FileResponse(
                registration.wallet_pass.open('rb'),
                as_attachment=True,
                filename=f'ticket_{registration.numero}.pkpass'
            )
            
            response['Content-Type'] = 'application/vnd.apple.pkpass'
            response['Content-Disposition'] = f'attachment; filename="ticket_{registration.numero}.pkpass"'
            return response
            
        raise Http404("Fichier Wallet Pass non disponible")