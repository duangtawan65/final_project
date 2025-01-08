from django.db import models
from django.contrib.auth.models import User
from healmind.models import Appointment
# Create your models here.




class ChatRoom(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='chat_room')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_chats')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('ended', 'Ended')],
        default='active'
    )

    def __str__(self):
        return f"Chat: {self.member.username} - {self.doctor.username}"

    def has_participants(self):
        """เช็คว่ามีทั้ง member และ doctor ในห้องไหม"""
        return self.member is not None and self.doctor is not None

    def end_chat(self):
        """จบการแชทและเปลี่ยนสถานะ"""
        self.status = 'ended'
        self.save()


