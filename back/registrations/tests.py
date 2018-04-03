from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from registrations.models import Registration, RegistrationMeta, Event, TicketEvent, TicketCategory

from .actions import codes

class RegistrationTestCase(TestCase):
    def setUp(self):
        self.event = TicketEvent.objects.create(name="Événement", send_tickets_until=timezone.now())
        self.category = TicketCategory.objects.create(name="Catégorie", color="white", background_color="blue", event=self.event)

    def test_can_create_registration(self):
        Registration.objects.create(numero=1, full_name="Full Name", gender='F', event=self.event, category=self.category)

    def test_can_create_registration_meta(self):
        registration = Registration.objects.create(numero=1, full_name="Full Name", gender='F', event=self.event, category=self.category)
        RegistrationMeta.objects.create(property="bus", value="Clermont", registration=registration)


class ValidationTestCase(TestCase):
    def setUp(self):
        self.event = TicketEvent.objects.create(name="Événement", send_tickets_until=timezone.now())
        self.category = TicketCategory.objects.create(name="Catégorie", color="white", background_color="blue",
                                                      event=self.event)

    def test_can_create_validation_event(self):
        registration = Registration.objects.create(numero=1, full_name="Full Name", event=self.event, category=self.category)
        Event.objects.create(registration=registration, type='scan')


class ViewTestCase(TestCase):
    def setUp(self):
        self.event = TicketEvent.objects.create(name="Événement", send_tickets_until=timezone.now())
        self.category = TicketCategory.objects.create(name="Catégorie", color="white", background_color="blue",
                                                      event=self.event)
        self.registration = Registration.objects.create(numero=1, full_name="Full Name", event=self.event, category=self.category)
        RegistrationMeta.objects.create(property="bus", value="Lille", registration=self.registration)
        Event.objects.create(registration=self.registration, type='scan')

    def test_author_is_required(self):
        response = self.client.get(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}))

        self.assertEqual(response.status_code, 403)

    def test_get_info(self):
        response = self.client.get(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}) + '?person=Guillaume%20Royer')
        json = response.json()

        self.assertEqual(json['events'][0]['type'], 'scan')
        self.assertEqual(json['events'][1]['person'], 'Guillaume Royer')
        del json['events']
        self.assertEqual(json, {
            'numero': 1,
            'gender': '',
            'full_name': 'Full Name',
            'type': 'Catégorie',
            'meta': {
                'bus': 'Lille'
            }
        })

        self.assertEqual(self.registration.events.count(), 2)

    def test_can_post_info(self):
        response = self.client.post(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}) + '?person=Guillaume%20Royer', data={
            'type': 'entrance'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.registration.events.all()[1].type, 'entrance')
        self.assertEqual(self.registration.events.all()[1].person, 'Guillaume Royer')

    def test_cannot_post_nawak(self):
        response = self.client.post(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}) + '?person=Guillaume%20Royer', data={
            'type': 'prout'
        })

        self.assertEqual(response.status_code, 400)


class SignatureTestCase(TestCase):
    def test_raise_on_wrong_codes(self):
        wrong_codes = [
            "jzdaz_dhuidza",  # no point
            "oizefjie.ize.daz",  # several points
            "jio.jifezf",  # identifier is not an integer
            "1343.jiodzé&",  # signature is not base64
            "1234.abcde",  # signature has incorrect base64 padding
            "1234.Y2VjaQ==",  # incorrect signature
        ]

        for code in wrong_codes:
            with self.assertRaises(codes.InvalidCodeException):
                codes.get_id_from_code(code)

    @override_settings(SIGNATURE_KEY=b'prout')
    def test_get_id(self):
        self.assertEqual(codes.get_id_from_code('1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='), 1)
