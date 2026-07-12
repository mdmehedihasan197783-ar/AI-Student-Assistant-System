from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import StudentProfile, UserActivity


class LandingPageTests(TestCase):
    def test_landing_page_loads(self):
        response = self.client.get(reverse("core:landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your intelligent academic companion")
        self.assertContains(response, "AI Tutor")
        self.assertContains(response, reverse("core:register"))
        self.assertContains(response, "Contact Us")


class StudentAuthTests(TestCase):
    def test_registration_creates_user_profile_and_opens_dashboard(self):
        response = self.client.post(
            reverse("core:register"),
            {
                "full_name": "Md. Test Student",
                "email": "student@example.com",
                "university": "North South University",
                "department": "CSE",
                "semester": "8th",
                "skills": "Python, Django",
                "learning_goals": "Improve AI project skills",
                "career_goal": "Software Engineer",
                "password": "test-pass-123",
                "confirm_password": "test-pass-123",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        self.assertTrue(User.objects.filter(username="student@example.com").exists())
        profile = StudentProfile.objects.get(user__username="student@example.com")
        self.assertEqual(profile.department, "CSE")
        self.assertTrue(UserActivity.objects.filter(user=profile.user, action=UserActivity.Action.REGISTERED).exists())
        self.assertContains(response, "Md. Test Student")
        self.assertContains(response, "North South University")

    def test_login_with_email_redirects_to_dashboard(self):
        user = User.objects.create_user(username="student@example.com", email="student@example.com", password="test-pass-123")
        StudentProfile.objects.create(
            user=user,
            full_name="Existing Student",
            university="AI University",
            department="CSE",
            semester="5th",
        )

        response = self.client.post(
            reverse("core:login"),
            {"email": "student@example.com", "password": "test-pass-123"},
            follow=True,
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        self.assertContains(response, "Existing Student")
        self.assertTrue(UserActivity.objects.filter(user=user, action=UserActivity.Action.LOGGED_IN).exists())

    def test_profile_update_saves_skills_and_learning_goals(self):
        user = User.objects.create_user(username="student@example.com", email="student@example.com", password="test-pass-123")
        StudentProfile.objects.create(
            user=user,
            full_name="Existing Student",
            university="AI University",
            department="CSE",
            semester="5th",
        )
        self.client.login(username="student@example.com", password="test-pass-123")

        response = self.client.post(
            reverse("core:profile"),
            {
                "full_name": "Existing Student",
                "university": "AI University",
                "department": "CSE",
                "semester": "6th",
                "career_goal": "AI Engineer",
                "skills": "Python, Django, PostgreSQL",
                "learning_goals": "Build a complete student assistant system",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.semester, "6th")
        self.assertEqual(profile.skills, "Python, Django, PostgreSQL")
        self.assertEqual(profile.learning_goals, "Build a complete student assistant system")
        self.assertTrue(UserActivity.objects.filter(user=user, action=UserActivity.Action.PROFILE_UPDATED).exists())
