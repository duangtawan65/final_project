from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=True)
    age = forms.IntegerField(required=True)
    location = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            # Create the Profile instance
            profile = User.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],

                gender=self.cleaned_data['gender'],
                age=self.cleaned_data['age'],
                location=self.cleaned_data['location']
            )
            profile.save()

        return user




# forms.py

class ProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    # ฟิลด์อีเมล
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'
    }))

    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={
        'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'
    }))

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'gender', 'age', 'location', 'profile_picture',
                  'email']  # Include email in the fields
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'last_name': forms.TextInput(
                attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'age': forms.NumberInput(
                attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'location': forms.TextInput(
                attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
        }

    def __init__(self, *args, **kwargs):
        # ดึงข้อมูลจาก User instance
        user = kwargs.get('instance').user if 'instance' in kwargs else None
        super(ProfileForm, self).__init__(*args, **kwargs)

        # ถ้า User instance มีการเชื่อมโยงไว้
        if user:
            self.fields['email'].initial = user.email  # กำหนดค่าเริ่มต้นให้ฟิลด์ email
            self.fields['first_name'].initial = user.first_name  # กำหนดค่าเริ่มต้นให้ฟิลด์ first_name
            self.fields['last_name'].initial = user.last_name  # กำหนดค่าเริ่มต้นให้ฟิลด์ last_name

    def save(self, commit=True):
        # ดึง User instance จาก Profile instance
        user = self.instance.user  # ใช้ User instance ที่มีการเชื่อมโยงกับ Profile

        # อัปเดตข้อมูลใน User
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()  # บันทึกข้อมูล User

            # บันทึก Profile
            profile = super().save(commit=False)
            profile.user = user  # เชื่อมโยง Profile กับ User instance
            profile.save()

        return user

