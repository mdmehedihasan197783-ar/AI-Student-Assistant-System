from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AIChatForm,
    AccountSettingsForm,
    DeleteAccountForm,
    MockInterviewForm,
    NoteForm,
    QuizResultForm,
    ResumeForm,
    StudentLoginForm,
    StudentProfileForm,
    StudentRegistrationForm,
)
from .models import AIChat, MockInterview, Note, QuizResult, Resume, StudentProfile, UserActivity


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_activity(request, user, action, description=""):
    UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request),
    )


def get_student_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            "full_name": user.get_full_name() or user.email or user.username,
            "university": "",
            "department": "",
            "semester": "",
        },
    )
    return profile


def build_ai_answer(question):
    return (
        "AI Tutor response: I saved your question and prepared a study-focused answer draft. "
        f"Key idea: {question.strip()[:180]} "
        "Break the topic into definition, example, practice problem, and short revision notes."
    )


def landing(request):
    return render(request, "core/landing.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        record_activity(request, user, UserActivity.Action.REGISTERED, "Student account was created.")
        login(request, user)
        messages.success(request, "Registration successful. Welcome to your dashboard.")
        return redirect("core:dashboard")

    return render(request, "core/register.html", {"form": form})


def student_login(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = StudentLoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        record_activity(request, form.user, UserActivity.Action.LOGGED_IN, "Student logged in.")
        return redirect("core:dashboard")

    return render(request, "core/login.html", {"form": form})


def student_logout(request):
    if request.user.is_authenticated:
        record_activity(request, request.user, UserActivity.Action.LOGGED_OUT, "Student logged out.")
    logout(request)
    return redirect("core:landing")


@login_required
def dashboard(request):
    profile = get_student_profile(request.user)
    recent_notes = Note.objects.filter(student=request.user)[:4]
    recent_quizzes = QuizResult.objects.filter(student=request.user)[:4]
    latest_resume = Resume.objects.filter(student=request.user).first()
    latest_interview = MockInterview.objects.filter(student=request.user).first()
    recent_activities = UserActivity.objects.filter(user=request.user)[:5]
    all_quizzes = QuizResult.objects.filter(student=request.user)
    quiz_percentages = [
        round((quiz.score / quiz.total_questions) * 100)
        for quiz in all_quizzes
        if quiz.total_questions
    ]

    stats = {
        "notes": Note.objects.filter(student=request.user).count(),
        "quizzes": all_quizzes.count(),
        "resume_progress": latest_resume.progress if latest_resume else 0,
        "interviews": MockInterview.objects.filter(student=request.user).count(),
        "interview_score": latest_interview.score if latest_interview else 0,
        "activities": AIChat.objects.filter(student=request.user).count(),
        "average_quiz_score": round(sum(quiz_percentages) / len(quiz_percentages)) if quiz_percentages else 0,
        "highest_quiz_score": max(quiz_percentages) if quiz_percentages else 0,
    }

    chart_quizzes = list(reversed(list(all_quizzes[:6])))
    chart_points = []
    chart_labels = []
    if chart_quizzes:
        x_min, x_max = 44, 340
        y_min, y_max = 16, 152
        x_step = (x_max - x_min) / (len(chart_quizzes) - 1) if len(chart_quizzes) > 1 else 0
        for index, quiz in enumerate(chart_quizzes):
            percentage = round((quiz.score / quiz.total_questions) * 100) if quiz.total_questions else 0
            percentage = min(100, max(0, percentage))
            x = round(x_min + (x_step * index))
            y = round(y_max - ((percentage / 100) * (y_max - y_min)))
            chart_points.append({"x": x, "y": y, "score": percentage})
            chart_labels.append({"x": x, "label": quiz.taken_at.strftime("%b %d")})

    chart_polyline = " ".join(f"{point['x']},{point['y']}" for point in chart_points)
    chart_area_path = ""
    if chart_points:
        first_point = chart_points[0]
        last_point = chart_points[-1]
        chart_area_path = (
            f"M{first_point['x']} {first_point['y']} "
            + " ".join(f"L{point['x']} {point['y']}" for point in chart_points[1:])
            + f" V152 H{first_point['x']} Z"
        )

    return render(
        request,
        "core/dashboard.html",
        {
            "profile": profile,
            "recent_notes": recent_notes,
            "recent_quizzes": recent_quizzes,
            "latest_resume": latest_resume,
            "latest_interview": latest_interview,
            "recent_activities": recent_activities,
            "stats": stats,
            "display_stats": stats,
            "quiz_chart": {
                "points": chart_points,
                "labels": chart_labels,
                "polyline": chart_polyline,
                "area_path": chart_area_path,
            },
        },
    )


@login_required
def ai_tutor(request):
    profile = get_student_profile(request.user)
    form = AIChatForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        chat = form.save(commit=False)
        chat.student = request.user
        chat.answer = build_ai_answer(chat.question)
        chat.save()
        record_activity(request, request.user, UserActivity.Action.AI_CHAT, "AI tutor question was saved.")
        messages.success(request, "Question saved and answer generated.")
        return redirect("core:ai_tutor")

    chats = AIChat.objects.filter(student=request.user)[:8]
    return render(request, "core/ai_tutor.html", {"profile": profile, "form": form, "chats": chats, "active_page": "ai_tutor"})


@login_required
def notes(request):
    profile = get_student_profile(request.user)
    query = request.GET.get("q", "").strip()
    note_list = Note.objects.filter(student=request.user)
    if query:
        note_list = note_list.filter(Q(title__icontains=query) | Q(content__icontains=query))

    form = NoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.student = request.user
        note.save()
        record_activity(request, request.user, UserActivity.Action.NOTE_SAVED, "Study note was saved.")
        messages.success(request, "Note saved successfully.")
        return redirect("core:notes")

    return render(request, "core/notes.html", {"profile": profile, "form": form, "notes": note_list, "query": query, "active_page": "notes"})


@login_required
def note_edit(request, pk):
    profile = get_student_profile(request.user)
    note = get_object_or_404(Note, pk=pk, student=request.user)
    form = NoteForm(request.POST or None, instance=note)
    if request.method == "POST" and form.is_valid():
        form.save()
        record_activity(request, request.user, UserActivity.Action.NOTE_SAVED, "Study note was updated.")
        messages.success(request, "Note updated successfully.")
        return redirect("core:notes")
    return render(request, "core/note_edit.html", {"profile": profile, "form": form, "note": note, "active_page": "notes"})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, student=request.user)
    if request.method == "POST":
        note.delete()
        messages.success(request, "Note deleted successfully.")
    return redirect("core:notes")


@login_required
def quizzes(request):
    profile = get_student_profile(request.user)
    form = QuizResultForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.student = request.user
        quiz.save()
        record_activity(request, request.user, UserActivity.Action.QUIZ_SAVED, "Quiz result was saved.")
        messages.success(request, "Quiz result saved successfully.")
        return redirect("core:quizzes")

    quiz_results = QuizResult.objects.filter(student=request.user)
    return render(request, "core/quizzes.html", {"profile": profile, "form": form, "quiz_results": quiz_results, "active_page": "quizzes"})


@login_required
def resume_builder(request):
    profile = get_student_profile(request.user)
    resume = Resume.objects.filter(student=request.user).first()
    form = ResumeForm(request.POST or None, instance=resume)
    if request.method == "POST" and form.is_valid():
        saved_resume = form.save(commit=False)
        saved_resume.student = request.user
        saved_resume.save()
        record_activity(request, request.user, UserActivity.Action.RESUME_UPDATED, "Resume information was updated.")
        messages.success(request, "Resume saved successfully.")
        return redirect("core:resume_builder")

    return render(request, "core/resume_builder.html", {"profile": profile, "form": form, "resume": resume, "active_page": "resume"})


@login_required
def mock_interview(request):
    profile = get_student_profile(request.user)
    form = MockInterviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        interview = form.save(commit=False)
        interview.student = request.user
        answer = form.cleaned_data["answer"]
        interview.score = min(100, max(40, len(answer.split()) * 3))
        interview.feedback = "Saved practice answer. Improve by using STAR structure, adding measurable results, and keeping the answer concise."
        interview.save()
        record_activity(request, request.user, UserActivity.Action.INTERVIEW_COMPLETED, "Mock interview practice was completed.")
        messages.success(request, "Mock interview practice saved.")
        return redirect("core:mock_interview")

    interviews = MockInterview.objects.filter(student=request.user)[:5]
    return render(request, "core/mock_interview.html", {"profile": profile, "form": form, "interviews": interviews, "active_page": "interview"})


@login_required
def settings_page(request):
    profile = get_student_profile(request.user)
    form = AccountSettingsForm(request.POST or None, instance=profile, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        record_activity(request, request.user, UserActivity.Action.PROFILE_UPDATED, "Account settings were updated.")
        messages.success(request, "Settings updated successfully.")
        return redirect("core:settings")

    return render(request, "core/settings.html", {"profile": profile, "form": form, "active_page": "settings"})


@login_required
def profile(request):
    student_profile = get_student_profile(request.user)
    form_type = request.POST.get("form_type") if request.method == "POST" else None
    profile_data = request.POST if form_type == "profile" else None
    profile_files = request.FILES if form_type == "profile" else None
    profile_form = StudentProfileForm(
        profile_data,
        profile_files,
        instance=student_profile,
        user=request.user,
    )
    password_form = PasswordChangeForm(request.user, request.POST if form_type == "password" else None)
    delete_form = DeleteAccountForm(request.POST if form_type == "delete" else None, user=request.user)
    password_placeholders = {
        "old_password": "Current password",
        "new_password1": "New password",
        "new_password2": "Retype new password",
    }
    for name, field in password_form.fields.items():
        field.widget.attrs.setdefault("class", "form-control")
        field.widget.attrs.setdefault("placeholder", password_placeholders.get(name, ""))

    if request.method == "POST" and form_type == "profile" and profile_form.is_valid():
        profile_form.save()
        record_activity(request, request.user, UserActivity.Action.PROFILE_UPDATED, "Student profile information was updated.")
        messages.success(request, "Profile updated successfully.")
        return redirect("core:profile")

    if request.method == "POST" and form_type == "password" and password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        record_activity(request, request.user, UserActivity.Action.PROFILE_UPDATED, "Student password was changed.")
        messages.success(request, "Password changed successfully.")
        return redirect("core:profile")

    if request.method == "POST" and form_type == "delete" and delete_form.is_valid():
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("core:landing")

    return render(
        request,
        "core/profile.html",
        {
            "form": profile_form,
            "password_form": password_form,
            "delete_form": delete_form,
            "profile": student_profile,
            "active_page": "profile",
            "active_profile_tab": form_type or "details",
        },
    )
