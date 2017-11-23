from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404

from .models import Registration, Event, RegistrationMeta
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
            return queryset.filter(events__type=Event.TYPE_SCAN)
        if self.value() == 'validated':
            return queryset.filter(events__type=Event.TYPE_ENTRANCE)
        if self.value() == 'cancelled':
            return queryset.filter(events__type=Event.TYPE_CANCEL)


class MetaInline(admin.TabularInline):
    model = RegistrationMeta
    fields = ('property', 'value')


class EventInline(admin.TabularInline):
    model = Event
    readonly_fields = ['type', 'time']
    extra = 0


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('numero', 'qrcode_display', 'ticket_link')
    list_filter = ('type', 'gender', 'ticket_status', EventFilter)
    list_display = ('numero', 'full_name', 'gender', 'type', 'ticket_status')
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
            return '<img src="%s"/>' % reverse('admin:registrations_registration_qrcode', args=[instance.numero])
        else:
            return '-'
    qrcode_display.short_description = 'QRCode'
    qrcode_display.allow_tags = True

    def ticket_link(self, instance):
        if instance._state.adding:
            return '-'

        return '<a href="%s">Voir le ticket</a>' % reverse('admin:registrations_registration_ticket', args=[instance.numero])
    ticket_link.short_description = 'Ticket'
    ticket_link.allow_tags = True

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


admin.site.register(Registration, RegistrationAdmin)
