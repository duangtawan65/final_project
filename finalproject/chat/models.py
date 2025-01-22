from django.db import models
from django.contrib.auth.models import User
from healmind.models import Appointment
from django.utils import timezone
from datetime import datetime, timedelta
# Create your models here.


class ChatRoom(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='chat_room')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_chats')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    chat_start_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('ended', 'Ended')],
        default='active'
    )

    def __str__(self):
        return f"Chat: {self.member.username} - {self.doctor.username}"

    def has_participants(self):

        return bool(self.member and self.doctor)

    def start_chat(self):
        """บันทึกเวลาเริ่มแชทเมื่อมีผู้ใช้ครบ 2 คนและอยู่ในช่วงเวลานัด"""
        if not self.chat_start_time:  # ถ้ายังไม่เคยบันทึกเวลาเริ่ม
            self.chat_start_time = timezone.now()
            self.status = 'active'
            self.save()

    def is_in_session_time(self):
        """เช็คว่าอยู่ในช่วงเวลานัดหรือไม่"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            datetime.combine(
                self.appointment.appointment_date,
                self.appointment.time
            )
        )
        session_end = appointment_datetime + timedelta(hours=1)
        return appointment_datetime <= now <= session_end

    def can_start_chat(self):
        """เช็คว่าสามารถเริ่มแชทได้หรือไม่"""
        return (
                self.status == 'active' and
                self.has_participants() and
                self.is_in_session_time()
        )

    def end_chat(self):
        """จบการแชทและสร้างประวัติ"""
        if self.status == 'active':  # เช็คว่ายังไม่ได้จบแชท
            ChatRoomHistory.objects.create(
                appointment=self.appointment,
                member=self.member,
                doctor=self.doctor,
                chat_start_time=self.chat_start_time or self.created_at,
                chat_end_time=timezone.now(),
                status='completed'
            )
            self.status = 'ended'
            self.save()

class ChatRoomHistory(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='chat_history')
    chat_start_time = models.DateTimeField(null=True, blank=True)
    chat_end_time = models.DateTimeField(null=True, blank=True)
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_chat_histories')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_chat_histories')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show')
        ],
        default='completed'
    )

    class Meta:
        ordering = ['-chat_end_time']

    def __str__(self):
        return f"{self.member.username} - {self.doctor.username} ({self.chat_start_time})"

    @property
    def chat_duration(self):
        if self.chat_start_time and self.chat_end_time:
            duration = self.chat_end_time - self.chat_start_time
            return duration.total_seconds() // 60
        return 0

    @property
    def stars(self):
        if self.rating:
            return '★' * self.rating + '☆' * (5 - self.rating)
        return None
