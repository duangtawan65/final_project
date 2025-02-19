from django.db import models
from django.contrib.auth.models import User,AbstractUser
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.conf import settings
from django.apps import apps
from django.utils import timezone
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, blank=True)
    age = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)


    def __str__(self):
        return f"{self.user.username} "



class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=10,  blank=True)
    specialty = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    work_location = models.CharField(max_length=255, blank=True)
    session_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    service_mode = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    stripe_account_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Doctor Profile"

    def get_average_rating(self):
        ChatRoomHistory = apps.get_model('chat', 'ChatRoomHistory')
        histories = ChatRoomHistory.objects.filter(
            doctor=self.user,
            rating__isnull=False
        )
        if histories.exists():
            total_rating = sum(h.rating for h in histories)
            return round(total_rating / histories.count(), 1)
        return 0

    def get_review_count(self):
        ChatRoomHistory = apps.get_model('chat', 'ChatRoomHistory')
        return ChatRoomHistory.objects.filter(
            doctor=self.user,
            rating__isnull=False
        ).count()




class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('questionnaire_name', 'description')

# Model for the questionnaire
class Questionnaire(models.Model):
    questionnaire_name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_system = models.BooleanField(default=False)  # สำหรับแบบทดสอบของระบบ
    created_at = models.DateTimeField(auto_now_add=True)

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

class QuizHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    score = models.IntegerField()
    result = models.ForeignKey(Result, on_delete=models.SET_NULL, null=True)  # เพิ่มแค่ส่วนนี้
    stress_level = models.CharField(max_length=255)
    result_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # คงไว้ตามเดิม
    is_completed = models.BooleanField(default=False)  # เพิ่มถ้าจำเป็น

    class Meta:
        ordering = ['-created_at']




class Appointment(models.Model):
    doctor = models.ForeignKey('DoctorProfile', on_delete=models.CASCADE)
    member = models.ForeignKey('Profile', on_delete=models.CASCADE)
    appointment_date = models.DateField()
    time = models.TimeField()
    service_mode = models.CharField(max_length=50, default='Online')
    status = models.CharField(max_length=20, default='Pending')

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'รอชำระเงิน'),
            ('paid', 'ชำระเงินแล้ว'),
            ('canceled', 'ยกเลิก'),
            ('expired', 'หมดเวลาชำระเงิน'),
        ],
        default='pending'
    )
    stripe_payment_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.doctor.user.username} - {self.appointment_date} {self.time}"



class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['doctor', 'date', 'time']




class DoctorApprovalRequest(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=10, blank=True)
    work_location = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    tambon = models.CharField(max_length=100, blank=True)
    amphure = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # สถานะและเอกสาร
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'รอการอนุมัติ'),
            ('approved', 'อนุมัติแล้ว'),
            ('rejected', 'ปฏิเสธ')
        ],
        default='pending'
    )
    document = models.FileField(upload_to='doctor_documents/', blank=True, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Doctor Request - {self.user.get_full_name()}"

    class Meta:
        ordering = ['-created_at']


