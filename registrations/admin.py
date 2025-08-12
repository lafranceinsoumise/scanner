from django.core.mail import get_connection
from django.urls import path, re_path
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.html import format_html

from .actions.emails import envoyer_billet
from .actions.scans import mark_registration, state_change_counter
from .models import (
    Registration,
    ScannerAction,
    RegistrationMeta,
    TicketEvent,
    TicketCategory,
    ScanPoint,
    TicketAttachment,
)
from .actions import codes, tickets


class EventFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Ticket"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "ticket"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ("scanned", "Scanné"),
            ("validated", "Validé"),
            ("cancelled", "Annulé"),
            ("unseen", "Non scanné"),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "scanned":
            return queryset.filter(events__type=ScannerAction.TYPE_SCAN).distinct()
        if self.value() == "validated":
            return queryset.filter(events__type=ScannerAction.TYPE_ENTRANCE).distinct()
        if self.value() == "cancelled":
            return queryset.filter(events__type=ScannerAction.TYPE_CANCEL).distinct()
        if self.value() == "unseen":
            return queryset.filter(events__isnull=True).distinct()


class MetaInline(admin.TabularInline):
    model = RegistrationMeta
    fields = ("property", "value")


class EventInline(admin.TabularInline):
    model = ScannerAction
    readonly_fields = ["type", "time", "person", "point"]
    extra = 0


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = (
        "canceled",
        "qrcode_display",
        "ticket_link",
        "metas_list",
        "wallet_pass_admin",
    )
    list_filter = (
        "category__name",
        "canceled",
        "gender",
        "ticket_status",
        EventFilter,
        "event",
    )
    list_display = (
        "numero",
        "full_name",
        "gender",
        "canceled",
        "ticket_status",
        "metas_list",
    )
    search_fields = ("full_name", "numero", "_contact_emails", "metas__value")

    inlines = (MetaInline, EventInline)

    actions = ["send_tickets_action"]
    
    def wallet_pass_admin(self, obj):
        if obj.wallet_pass:
            url = reverse('admin:registrations_registration_download_pass', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank">Télécharger</a>',
                url
            )
        else:
            generate_url = reverse('admin:registrations_registration_generate_pass', args=[obj.id])
            return format_html(
                '<span style="color:gray">Non généré</span>&nbsp;'
                '<a class="button" href="{}" style="background:#447e9b;color:white;padding:3px 8px;border-radius:3px">Générer</a>',
                generate_url
            )
    wallet_pass_admin.short_description = "Pass Apple Wallet"
    
    def regenerate_wallet_pass(self, obj):
        url = reverse('admin:registrations_registration_regenerate_pass', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" style="background:#ff0;color:#000;padding:3px 8px;border-radius:3px">Regénérer</a>',
            url
        )
    regenerate_wallet_pass.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r"^(?P<object_id>.+)/qrcode/$",
                self.admin_site.admin_view(self.qrcode_view),
                name="registrations_registration_qrcode",
            ),
            re_path(
                r"^(?P<object_id>.+)/valider/$",
                self.admin_site.admin_view(self.valider_view),
                name="registrations_registration_valider",
            ),
            re_path(
                r"^(?P<object_id>.+)/ticket/$",
                self.admin_site.admin_view(self.ticket_view),
                name="registrations_registration_ticket",
            ),
            re_path(
                r"^(?P<object_id>.+)/envoyer-billet/$",
                self.admin_site.admin_view(self.send_ticket_view),
                name="registrations_registration_send_ticket",
            ),
            path('<path:object_id>/generate-pass/',
                 self.admin_site.admin_view(self.generate_pass_view),
                 name='registrations_registration_generate_pass'),
            path('<path:object_id>/download-pass/',
                 self.admin_site.admin_view(self.download_pass_view),
                 name='registrations_registration_download_pass'),
            path('<path:object_id>/regenerate-pass/',
                 self.admin_site.admin_view(self.regenerate_pass_view),
                 name='registrations_registration_regenerate_pass'),
        ]
        return custom_urls + urls

    def full_name(self, instance):
        return instance.first_name + " " + instance.last_name

    def qrcode_display(self, instance):
        if instance.pk is not None:
            if instance.canceled:
                "Billet annulé"
            return format_html(
                '<img src="{}"/><br><a href="{}" class="btn">Valider le ticket</a>',
                reverse("admin:registrations_registration_qrcode", args=[instance.pk]),
                reverse("admin:registrations_registration_valider", args=[instance.pk]),
            )
        else:
            return "-"

    qrcode_display.short_description = "QRCode"

    def metas_list(self, instance):
        return " / ".join(
            [f"{meta.property}: {meta.value}" for meta in instance.metas.all()]
        )

    def ticket_link(self, instance):
        if instance._state.adding:
            return "-"

        return format_html(
            '<a href="{}">Voir le ticket</a><br>'
            '<a class="button" href="{}">Envoyer le billet</a>',
            reverse("admin:registrations_registration_ticket", args=[instance.pk]),
            reverse("admin:registrations_registration_send_ticket", args=[instance.pk]),
        )

    ticket_link.short_description = "Ticket"
    
    def generate_pass_view(self, request, object_id):
        from django.shortcuts import redirect
        obj = self.get_object(request, object_id)
        obj.generate_wallet_pass()
        obj.save()
        self.message_user(request, "Pass Apple Wallet généré avec succès")
        return redirect('admin:registrations_registration_change', object_id)
    
    def download_pass_view(self, request, object_id):
        from django.shortcuts import redirect
        obj = self.get_object(request, object_id)
        if not obj.wallet_pass:
            self.message_user(request, "Le pass n'existe pas encore", level='ERROR')
            return redirect('admin:registrations_registration_change', object_id)
        return redirect(obj.apple_wallet_url)
    
    def regenerate_pass_view(self, request, object_id):
        from django.shortcuts import redirect
        obj = self.get_object(request, object_id)
        if obj.wallet_pass:
            obj.wallet_pass.delete()
        obj.generate_wallet_pass()
        obj.save()
        self.message_user(request, "Pass Apple Wallet regénéré avec succès")
        return redirect('admin:registrations_registration_change', object_id)

    def qrcode_view(self, request, object_id):
        img = codes.gen_qrcode(object_id)
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")

        return response

    def ticket_view(self, request, object_id):
        registration = get_object_or_404(Registration, pk=object_id)
        ticket = tickets.gen_ticket(registration)
        response = HttpResponse(ticket, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="ticket_{}.pdf"'.format(
            registration.pk
        )

        return response

    def valider_view(self, request, object_id):
        registration = get_object_or_404(Registration, pk=object_id)
        ScannerAction.objects.create(
            registration=registration, type=ScannerAction.TYPE_ENTRANCE, person=f"{request.user} - admin", point=registration.event.scan_points.first()
        )
        state_change_counter.labels(ScannerAction.TYPE_ENTRANCE).inc()
        return HttpResponseRedirect(reverse("admin:registrations_registration_change", args=(object_id,)))

    def send_ticket_view(self, request, object_id):
        registration = get_object_or_404(Registration, pk=object_id)
        connection = get_connection()

        registration.ticket_status = "N"
        registration.save()

        try:
            envoyer_billet(registration, connection=connection)
            self.message_user(request, "Billet envoyé avec succès.", messages.SUCCESS)
        except Exception as e:
            self.message_user(
                request,
                f"Erreur lors de l'envoi du billet : {str(e)}",
                level=messages.ERROR,
            )

        connection.close()

        return HttpResponseRedirect(
            reverse("admin:registrations_registration_change", args=[object_id])
        )

    def send_tickets_action(self, request, queryset):
        connection = get_connection()
        success = 0
        errors = 0

        for registration in queryset:
            try:
                registration.ticket_status = "N"
                registration.save()
                envoyer_billet(registration, connection=connection)
                success += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Erreur pour {registration.full_name} : {e}",
                    level=messages.ERROR,
                )
                errors += 1

        connection.close()

        if success:
            self.message_user(
                request,
                f"{success} billet(s) envoyé(s) avec succès.",
                level=messages.SUCCESS,
            )

        if errors:
            self.message_user(
                request,
                f"{errors} erreur(s) lors de l'envoi de billets.",
                level=messages.WARNING,
            )

    send_tickets_action.short_description = "Envoyer les billets sélectionnés"

class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment


class ScanPointInline(admin.TabularInline):
    model = ScanPoint


class TicketEventAdmin(admin.ModelAdmin):
    model = TicketEvent
    list_display = ("name",)
    inlines = [TicketAttachmentInline, ScanPointInline]


class ScanPointAdmin(admin.ModelAdmin):
    model = ScanPoint
    list_display = ("event", "name")


class TicketCategoryAdmin(admin.ModelAdmin):
    model = TicketCategory
    list_display = ("name", "event", "color", "background_color")


admin.site.register(Registration, RegistrationAdmin)
admin.site.register(TicketCategory, TicketCategoryAdmin)
admin.site.register(TicketEvent, TicketEventAdmin)
