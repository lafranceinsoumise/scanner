from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse

from .models import Registration
from .actions import codes

class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('numero', 'qrcode_display',)
    list_filter = ('type', 'gender')
    list_display = ('full_name', 'gender', 'type')

    def get_urls(self):
        urls = super().get_urls()
        return [
            url(r'^(.+)/qrcode/$', self.admin_site.admin_view(self.qrcode_view), name='registrations_registration_qrcode')
        ] + urls

    def qrcode_view(self, request, object_id):
        img = codes.gen_qrcode(object_id)
        response = HttpResponse(content_type='image/png')
        img.save(response, "PNG")

        return response

    def full_name(self, instance):
        return instance.first_name + ' ' + instance.last_name

    def qrcode_display(self, instance):
        if instance.code:
            return '<img src="%s"/>' % reverse('admin:registrations_registration_qrcode', args=[instance.code])
        else:
            return '-'

    qrcode_display.short_description = 'QRCode'
    qrcode_display.allow_tags = True


admin.site.register(Registration, RegistrationAdmin)
