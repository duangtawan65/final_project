from django import forms
from .models import ChatRoom
from django.contrib.auth.models import User





class ChatRoomForm(forms.ModelForm):
    class Meta:
        model = ChatRoom
        fields = []  # ไม่มีฟิลด์ให้กรอก เพราะสร้างอัตโนมัติจาก appointment

class ChatForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'ถามอะไรได้เลย...'}))