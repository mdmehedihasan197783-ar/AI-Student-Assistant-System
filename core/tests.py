from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AIChat, MockInterview, Note, QuizResult, Resume, StudentProfile, UserActivity


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
                "form_type": "profile",
                "full_name": "Existing Student",
                "email": "student@example.com",
                "university": "AI University",
                "department": "CSE",
                "semester": "6th",
                "career_goal": "AI Engineer",
                "skills": "Python, Django, PostgreSQL",
                "learning_goals": "Build a complete student assistant system",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("core:profile"))
        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.semester, "6th")
        self.assertEqual(profile.skills, "Python, Django, PostgreSQL")
        self.assertEqual(profile.learning_goals, "Build a complete student assistant system")
        self.assertTrue(UserActivity.objects.filter(user=user, action=UserActivity.Action.PROFILE_UPDATED).exists())

    def test_feature_pages_save_student_data(self):
        user = User.objects.create_user(username="student@example.com", email="student@example.com", password="test-pass-123")
        StudentProfile.objects.create(
            user=user,
            full_name="Feature Student",
            university="AI University",
            department="CSE",
            semester="7th",
        )
        self.client.login(username="student@example.com", password="test-pass-123")

        self.client.post(reverse("core:ai_tutor"), {"question": "What is database normalization?"})
        self.client.post(reverse("core:notes"), {"title": "Normalization", "content": "Database normalization notes"})
        self.client.post(reverse("core:quizzes"), {"topic": "DBMS", "score": 8, "total_questions": 10})
        self.client.post(
            reverse("core:resume_builder"),
            {
                "title": "Software Resume",
                "education": "BSc in CSE",
                "skills": "Python, Django",
                "projects": "AI Student Assistant",
                "experience": "Academic projects",
                "progress": 80,
            },
        )
        self.client.post(reverse("core:mock_interview"), {"role": "Software Engineer", "answer": "I solved a project using Django and PostgreSQL."})

        self.assertTrue(AIChat.objects.filter(student=user).exists())
        self.assertTrue(Note.objects.filter(student=user, title="Normalization").exists())
        self.assertTrue(QuizResult.objects.filter(student=user, topic="DBMS").exists())
        self.assertTrue(Resume.objects.filter(student=user, title="Software Resume").exists())
        self.assertTrue(MockInterview.objects.filter(student=user, role="Software Engineer").exists())
