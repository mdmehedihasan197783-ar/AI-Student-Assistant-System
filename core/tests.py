from django.test import TestCase
from django.urls import reverse


class LandingPageTests(TestCase):
    def test_landing_page_loads(self):
        response = self.client.get(reverse("core:landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your intelligent academic companion")
        self.assertContains(response, "AI Tutor")
        self.assertContains(response, "Student Registration")
        self.assertContains(response, "Contact Us")
