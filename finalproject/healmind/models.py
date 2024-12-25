from django.db import models
from django.contrib.auth.models import User,AbstractUser
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.conf import settings

# Create your models here.
class Profile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, blank=True)
    age = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"



class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)
    bio = models.TextField(blank=True)
    work_location = models.CharField(max_length=255, blank=True)
    session_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    service_mode = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} Doctor Profile"


class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('questionnaire_name', 'description')

# Model for the questionnaire
class Questionnaire(models.Model):
    questionnaire_name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.questionnaire_name


# Model for each question in the questionnaire
class Question(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    question_content = models.TextField()

    def __str__(self):
        return f'{self.questionnaire.questionnaire_name} - {self.question_content[:50]}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    response_value = models.IntegerField()
    response_text = models.CharField(max_length=255)
    def __str__(self):
        return f'{self.question.question_content[:50]} - {self.response_text}'


# Model for storing the results based on score ranges
class Result(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='results')
    score_low = models.IntegerField()
    score_high = models.IntegerField()
    stress_level = models.CharField(max_length=255, default="Unknown")
    result_description = models.TextField()

    def __str__(self):
        return f'{self.stress_level} ({self.score_low}-{self.score_high})'

