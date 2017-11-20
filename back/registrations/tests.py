from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from registrations.models import Registration, RegistrationMeta, Event
from registrations.utils import code_is_correct


class RegistrationTestCase(TestCase):
    def test_can_create_registration(self):
        Registration.objects.create(code=1, first_name="First", last_name="Last")

    def test_can_create_registration_meta(self):
        registration = Registration.objects.create(code=1, first_name="First", last_name="Last")
        RegistrationMeta.objects.create(property="bus", value="Clermont", registration=registration)


class ValidationTestCase(TestCase):
    def test_can_create_validation_event(self):
        registration = Registration.objects.create(code=1, first_name="First", last_name="Last")
        Event.objects.create(registration=registration, type='scan')


class ViewTestCase(TestCase):
    def setUp(self):
        self.registration = Registration.objects.create(code=1, first_name="First", last_name="Last")
        RegistrationMeta.objects.create(property="bus", value="Lille", registration=self.registration)
        Event.objects.create(registration=self.registration, type='scan')

    def test_get_info(self):
        response = self.client.get(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}))
        json = response.json()

        self.assertEqual(json['events'][0]['type'], 'scan')
        del json['events']
        self.assertEqual(json, {
            'code': 1,
            'first_name': 'First',
            'last_name': 'Last',
            'meta': {
                'bus': 'Lille'
            }
        })

    def test_can_post_info(self):
        response = self.client.post(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}), data={
            'type': 'entrance'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.registration.events.all()[1].type, 'entrance')

    def test_cannot_post_nawak(self):
        response = self.client.post(reverse('view_code', kwargs={'code': '1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='}), data={
            'type': 'prout'
        })

        self.assertEqual(response.status_code, 400)


class SignatureTestCase(TestCase):
    def test_signature(self):
        self.assertIs(code_is_correct('1.prou'), False)
        self.assertIs(code_is_correct('1.Hhv2SqmQwO8UBEwp50X8ZWPbIvk='), True)
