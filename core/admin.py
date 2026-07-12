from django.contrib import admin

from .models import MockInterview, Note, QuizResult, Resume, StudentProfile, UserActivity


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "university", "department", "semester")
    search_fields = ("full_name", "user__email", "university", "department")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "updated_at")
    search_fields = ("title", "student__email")


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("topic", "student", "score", "total_questions", "taken_at")
    search_fields = ("topic", "student__email")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "progress", "updated_at")
    search_fields = ("title", "student__email")


@admin.register(MockInterview)
class MockInterviewAdmin(admin.ModelAdmin):
    list_display = ("role", "student", "score", "completed_at")
    search_fields = ("role", "student__email")


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "ip_address", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__email", "user__username", "description")
