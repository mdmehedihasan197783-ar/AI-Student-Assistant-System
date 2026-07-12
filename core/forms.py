from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import StudentProfile


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
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
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
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
