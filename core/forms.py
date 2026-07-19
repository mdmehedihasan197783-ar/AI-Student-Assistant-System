from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import AIChat, MockInterview, Note, QuizResult, Resume, StudentProfile


class StudentRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    university = forms.CharField(max_length=160)
    department = forms.CharField(max_length=120)
    semester = forms.CharField(max_length=40)
    skills = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    learning_goals = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    career_goal = forms.CharField(max_length=160, required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

    def save(self):
        full_name = self.cleaned_data["full_name"].strip()
        email = self.cleaned_data["email"]
        first_name, _, last_name = full_name.partition(" ")
        user = User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password"],
            first_name=first_name,
            last_name=last_name,
        )
        StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            university=self.cleaned_data["university"],
            department=self.cleaned_data["department"],
            semester=self.cleaned_data["semester"],
            skills=self.cleaned_data.get("skills", ""),
            learning_goals=self.cleaned_data.get("learning_goals", ""),
            career_goal=self.cleaned_data.get("career_goal", ""),
        )
        return user


class StudentLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").lower()
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid email or password.")
        return cleaned_data


class StudentProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "email",
            "university",
            "department",
            "semester",
            "career_goal",
            "skills",
            "learning_goals",
            "photo",
        ]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 3}),
            "learning_goals": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["email"].initial = self.user.email
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        existing = User.objects.filter(email=email)
        if self.user:
            existing = existing.exclude(pk=self.user.pk)
        if existing.exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.email = self.cleaned_data["email"].lower()
            self.user.username = self.user.email
            names = profile.full_name.split(maxsplit=1)
            self.user.first_name = names[0] if names else ""
            self.user.last_name = names[1] if len(names) > 1 else ""
            if commit:
                self.user.save(update_fields=["email", "username", "first_name", "last_name"])
        return profile


class DeleteAccountForm(forms.Form):
    confirm_delete = forms.BooleanField(
        required=True,
        label="I agree to delete my profile and account",
    )
    current_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["confirm_delete"].widget.attrs.setdefault("class", "form-check-input")
        self.fields["current_password"].widget.attrs.setdefault("class", "form-control")
        self.fields["current_password"].widget.attrs.setdefault("placeholder", "Enter current password")

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Current password is not correct.")
        return password


class AIChatForm(forms.ModelForm):
    class Meta:
        model = AIChat
        fields = ["question"]
        widgets = {
            "question": forms.Textarea(attrs={"rows": 4, "placeholder": "Ask your academic question..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8, "placeholder": "Write your study note..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class QuizResultForm(forms.ModelForm):
    class Meta:
        model = QuizResult
        fields = ["topic", "score", "total_questions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get("score")
        total_questions = cleaned_data.get("total_questions")
        if score is not None and total_questions is not None and score > total_questions:
            self.add_error("score", "Score cannot be greater than total questions.")
        return cleaned_data


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["title", "education", "skills", "projects", "experience", "progress"]
        widgets = {
            "education": forms.Textarea(attrs={"rows": 4}),
            "skills": forms.Textarea(attrs={"rows": 4}),
            "projects": forms.Textarea(attrs={"rows": 4}),
            "experience": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_progress(self):
        progress = self.cleaned_data["progress"]
        if progress > 100:
            raise forms.ValidationError("Progress cannot be greater than 100.")
        return progress


class MockInterviewForm(forms.ModelForm):
    answer = forms.CharField(widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Write your practice answer..."}))

    class Meta:
        model = MockInterview
        fields = ["role", "answer"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class AccountSettingsForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = StudentProfile
        fields = ["full_name", "university", "department", "semester", "career_goal", "skills", "learning_goals"]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 3}),
            "learning_goals": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields["email"].initial = user.email
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        existing = User.objects.filter(email=email).exclude(pk=self.user.pk if self.user else None)
        if existing.exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.email = self.cleaned_data["email"].lower()
            self.user.username = self.user.email
            names = profile.full_name.split(maxsplit=1)
            self.user.first_name = names[0]
            self.user.last_name = names[1] if len(names) > 1 else ""
            if commit:
                self.user.save(update_fields=["email", "username", "first_name", "last_name"])
        return profile
