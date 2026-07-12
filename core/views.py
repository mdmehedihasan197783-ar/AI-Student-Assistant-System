from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import StudentLoginForm, StudentProfileForm, StudentRegistrationForm
from .models import MockInterview, Note, QuizResult, Resume, StudentProfile, UserActivity


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
    profile = getattr(request.user, "student_profile", None)
    recent_notes = Note.objects.filter(student=request.user)[:4]
    recent_quizzes = QuizResult.objects.filter(student=request.user)[:4]
    latest_resume = Resume.objects.filter(student=request.user).first()
    latest_interview = MockInterview.objects.filter(student=request.user).first()
    recent_activities = UserActivity.objects.filter(user=request.user)[:5]

    stats = {
        "notes": Note.objects.filter(student=request.user).count(),
        "quizzes": QuizResult.objects.filter(student=request.user).count(),
        "resume_progress": latest_resume.progress if latest_resume else 0,
        "interview_score": latest_interview.score if latest_interview else 0,
    }
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
        },
    )


@login_required
def profile(request):
    student_profile, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.email or request.user.username,
            "university": "",
            "department": "",
            "semester": "",
        },
    )
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=student_profile)

    if request.method == "POST" and form.is_valid():
        updated_profile = form.save()
        names = updated_profile.full_name.split(maxsplit=1)
        request.user.first_name = names[0]
        request.user.last_name = names[1] if len(names) > 1 else ""
        request.user.save(update_fields=["first_name", "last_name"])
        record_activity(request, request.user, UserActivity.Action.PROFILE_UPDATED, "Student profile information was updated.")
        messages.success(request, "Profile updated successfully.")
        return redirect("core:dashboard")

    return render(request, "core/profile.html", {"form": form, "profile": student_profile})
