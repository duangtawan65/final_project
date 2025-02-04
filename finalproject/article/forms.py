from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'cover_image', 'description', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'ใส่ชื่อบทความของคุณ'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 resize-none',
                'rows': 3,
                'placeholder': 'เขียนคำอธิบายสั้นๆ เกี่ยวกับบทความของคุณ'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 min-h-[300px]',
                'rows': 10,
                'placeholder': 'เขียนเนื้อหาบทความของคุณที่นี่'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            })
        }