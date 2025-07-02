from django.core.exceptions import PermissionDenied
from django.db.models import Q, F, Max
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.views import View
from django.views.generic import CreateView
import subprocess

from .models import ScannerAction, ScanPoint, ScanSeq
from .actions.scans import scan_code, mark_registration, InvalidCodeException


class CodeView(View):
    def get_person(self):
        person = self.request.GET.get("person")

        if person is None or len(person) > 255:
            raise PermissionDenied()

        return person

    def get_point(self):
        try:
            return ScanPoint.objects.get(id=self.request.GET.get("point"))
        except (ScanPoint.DoesNotExist, ValueError, TypeError):
            return None

    def get(self, request, code):
        person = self.get_person()
        point = self.get_point()

        try:
            registration = scan_code(code, person, point)
        except InvalidCodeException:
            raise Http404

        return JsonResponse(
            {
                "numero": registration.numero,
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


def test_inkscape_conversion(request, object_id):
    # Récupère la registration (ajuste selon ton modèle)
    from registrations.models import Registration
    registration = Registration.objects.get(pk=object_id)

    # Génère le SVG avec ta fonction existante
    from registrations.actions.tickets import gen_ticket_svg
    svg = gen_ticket_svg(registration)

    process = subprocess.Popen(
        [
            "inkscape",
            "--pipe",
            "--export-type=pdf",
            "--export-filename=-",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        output, error = process.communicate(input=svg.encode("utf-8"), timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return HttpResponse("Timeout lors de la conversion Inkscape", status=500)

    if process.returncode != 0:
        return HttpResponse(
            f"Erreur Inkscape (code {process.returncode}):<br><pre>{error.decode()}</pre>",
            status=500,
        )

    # Si tout va bien, renvoie le PDF en téléchargement
    response = HttpResponse(output, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ticket-{object_id}.pdf"'
    return response
