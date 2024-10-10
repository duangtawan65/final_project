from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    age = models.IntegerField( blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('questionnaire_name', 'description')

# Model for the questionnaire
class Questionnaire(models.Model):
    questionnaire_name = models.CharField(max_length=255)  # This matches your Questionnaire_Name in the sheet
    description = models.TextField()  # Description field from the sheet

    def __str__(self):
        return self.questionnaire_name


# Model for each question in the questionnaire
class Question(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    question_content = models.TextField()  # This matches your Question_content field

    def __str__(self):
        return f'{self.questionnaire.questionnaire_name} - {self.question_content[:50]}'


# Model for the possible choices (answers) for each question
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    response_value = models.IntegerField()  # This matches your Response_Value
    response_text = models.CharField(max_length=255)  # This matches your Response_Text

    def __str__(self):
        return f'{self.question.question_content[:50]} - {self.response_text}'


# Model for storing the results based on score ranges
class Result(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='results')
    score_low = models.IntegerField()  # This matches your Score_Low field
    score_high = models.IntegerField()  # This matches your Score_High field
    stress_level = models.CharField(max_length=255, default="Unknown")  # This matches your Stress_Level field
    result_description = models.TextField()  # This matches your Result_Description

    def __str__(self):
        return f'{self.stress_level} ({self.score_low}-{self.score_high})'
