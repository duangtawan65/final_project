from django.db import models
import random
from django.contrib.auth.models import User
# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)




class ChatRoom(models.Model):
    name = models.CharField(max_length=255)  # ชื่อห้อง
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_rooms')  # เจ้าของห้อง
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatroom_user1', null=True, blank=True)  # ผู้ใช้คนที่ 1
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatroom_user2', null=True, blank=True)  # ผู้ใช้คนที่ 2
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')  # สถานะห้อง

    def __str__(self):
        return f"{self.name}"

    def is_full(self):
        # ตรวจสอบว่าห้องเต็มหรือไม่
        return self.user1 is not None and self.user2 is not None
    def has_participants(self):
        """ เช็คว่ามีผู้ใช้ในห้องหรือไม่ """
        return self.user1 is not None or self.user2 is not None

    def remove_user(self, user):
        """ ฟังก์ชันที่จะลบผู้ใช้ออกจากห้อง """
        if self.user1 == user:
            self.user1 = None
        elif self.user2 == user:
            self.user2 = None
        self.save()

    def delete_if_empty(self):
        """ หากห้องไม่มีผู้ใช้ จะลบห้องนี้ """
        if not self.has_participants():
            self.delete()



