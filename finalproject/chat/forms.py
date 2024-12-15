from django import forms
from .models import ChatRoom
from django.contrib.auth.models import User





class ChatRoomForm(forms.ModelForm):
    class Meta:
        model = ChatRoom
        fields = ['name']

    def save(self, commit=True):
        chat_room = super().save(commit=False)
        if commit:
            chat_room.owner = self.instance.owner  # กำหนดเจ้าของห้องเป็นผู้ใช้ที่สร้าง
            chat_room.save()
        return chat_room