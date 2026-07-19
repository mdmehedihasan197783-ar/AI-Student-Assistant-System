from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.student_login, name="login"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("ai-tutor/", views.ai_tutor, name="ai_tutor"),
    path("notes/", views.notes, name="notes"),
    path("notes/<int:pk>/edit/", views.note_edit, name="note_edit"),
    path("notes/<int:pk>/delete/", views.note_delete, name="note_delete"),
    path("quizzes/", views.quizzes, name="quizzes"),
    path("resume-builder/", views.resume_builder, name="resume_builder"),
    path("mock-interview/", views.mock_interview, name="mock_interview"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings_page, name="settings"),
    path("logout/", views.student_logout, name="logout"),
]
