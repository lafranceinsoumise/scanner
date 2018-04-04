from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.html import format_html

from .models import Registration, ScannerAction, RegistrationMeta, TicketEvent, TicketCategory
from .actions import codes, tickets


class EventFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Ticket'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'ticket'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('scanned', 'Scanné'),
            ('validated', 'Validé'),
            ('cancelled', 'Annulé'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'scanned':
            return queryset.filter(events__type=ScannerAction.TYPE_SCAN).distinct()
        if self.value() == 'validated':
            return queryset.filter(events__type=ScannerAction.TYPE_ENTRANCE).distinct()
        if self.value() == 'cancelled':
            return queryset.filter(events__type=ScannerAction.TYPE_CANCEL).distinct()


class MetaInline(admin.TabularInline):
    model = RegistrationMeta
    fields = ('property', 'value')


class EventInline(admin.TabularInline):
    model = ScannerAction
    readonly_fields = ['type', 'time', 'person']
    extra = 0


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('numero', 'qrcode_display', 'ticket_link')
    list_filter = ('category__name', 'gender', 'ticket_status', EventFilter)
    list_display = ('numero', 'full_name', 'gender', 'ticket_status')
    search_fields = ('full_name', 'numero')

    inlines = (
        MetaInline,
        EventInline
    )

    def get_urls(self):
        urls = super().get_urls()
        return [
            url(r'^(.+)/qrcode/$', self.admin_site.admin_view(self.qrcode_view), name='registrations_registration_qrcode'),
            url(r'^(.+)/ticket/$', self.admin_site.admin_view(self.ticket_view), name='registrations_registration_ticket')
        ] + urls

    def full_name(self, instance):
        return instance.first_name + ' ' + instance.last_name

    def qrcode_display(self, instance):
        if instance.numero:
            return format_html('<img src="{}"/>', reverse('admin:registrations_registration_qrcode', args=[instance.numero]))
        else:
            return '-'
    qrcode_display.short_description = 'QRCode'

    def ticket_link(self, instance):
        if instance._state.adding:
            return '-'

        return format_html('<a href="{}">Voir le ticket</a>', reverse('admin:registrations_registration_ticket', args=[instance.numero]))
    ticket_link.short_description = 'Ticket'

    def qrcode_view(self, request, object_id):
        img = codes.gen_qrcode(object_id)
        response = HttpResponse(content_type='image/png')
        img.save(response, "PNG")

        return response

    def ticket_view(self, request, object_id):
        registration = get_object_or_404(Registration, numero=object_id)
        ticket = tickets.gen_ticket(registration)
        response = HttpResponse(ticket, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="ticket_{}.pdf"'.format(registration.pk)

        return response


class TicketEventAdmin(admin.ModelAdmin):
    model = TicketEvent
    list_display = ('name',)


class TicketCategoryAdmin(admin.ModelAdmin):
    model = TicketCategory
    list_display = ('name', 'event', 'color', 'background_color')

admin.site.register(Registration, RegistrationAdmin)
admin.site.register(TicketCategory, TicketCategoryAdmin)
admin.site.register(TicketEvent, TicketEventAdmin)
