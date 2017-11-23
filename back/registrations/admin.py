from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404

from .models import Registration, Event, RegistrationMeta
from .actions import codes, tickets


class MetaInline(admin.TabularInline):
    model = RegistrationMeta
    fields = ('property', 'value')


class EventInline(admin.TabularInline):
    model = Event
    readonly_fields = ['type', 'time']
    extra = 0


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('numero', 'qrcode_display', 'ticket_link')
    list_filter = ('type', 'gender')
    list_display = ('full_name', 'gender', 'type')
    search_fields = ('full_name',)

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
