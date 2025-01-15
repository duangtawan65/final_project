from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django import forms
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
        # Create User instance first
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            # Create the Profile instance
            profile = Profile.objects.create(
                user=user,
                gender=self.cleaned_data['gender'],
                age=self.cleaned_data['age'],
                location=self.cleaned_data['location']
                 # Set default role
            )

        return user



# forms.py

class ProfileForm(forms.ModelForm):
    # เพิ่มฟิลด์จาก User model
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black',
            'placeholder': 'Enter your last name'
        })
    )
    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black'
        })
    )
    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black',
            'placeholder': 'Enter your age'
        })
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-black',
            'placeholder': 'Enter your location'
        })
    )
    profile_picture = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*'
        }), required=False
    )

    class Meta:
        model = Profile
        fields = ['gender', 'age', 'location', 'profile_picture']
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.instance.user:
            # อัปเดตข้อมูลใน User model
            user = self.instance.user
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.save()  # บันทึกข้อมูลใน User model

        if commit:
            profile.save()  # บันทึกข้อมูลใน Profile model

        return profile

class DoctorProfileForm(forms.ModelForm):

    # เพิ่ม fields สำหรับ User model
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
        'id': 'id_first_name'
    }))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
        'id': 'id_last_name'
    }))

    class Meta:
        model = DoctorProfile
        fields = ['title',  'specialty', 'bio','work_location', 'session_rate', 'service_mode', 'contact','profile_image']
        widgets = {
                'title': forms.Select(
                    choices=[
                        ('', 'เลือกคำนำหน้า'),
                        ('นพ.', 'นายแพทย์'),
                        ('พญ.', 'แพทย์หญิง'),
                        ('ผศ.นพ.', 'ผู้ช่วยศาสตราจารย์นายแพทย์'),
                        ('ผศ.พญ.', 'ผู้ช่วยศาสตราจารย์แพทย์หญิง'),
                        ('รศ.นพ.', 'รองศาสตราจารย์นายแพทย์'),
                        ('รศ.พญ.', 'รองศาสตราจารย์แพทย์หญิง'),
                        ('ศ.นพ.', 'ศาสตราจารย์นายแพทย์'),
                        ('ศ.พญ.', 'ศาสตราจารย์แพทย์หญิง'),
                    ],
                    attrs={
                        'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                    }
                ),
            'specialty': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'id': 'id_specialty'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'rows': 4,
                'id': 'id_bio'
            }),
            'work_location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'id': 'id_work_location'
            }),
            'session_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'id': 'id_session_rate'
            }),
            'service_mode': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'id': 'id_service_mode'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'id': 'id_contact'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'id_profile_image'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            # ใส่ค่าเริ่มต้นจาก User model
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            # บันทึกข้อมูลใน User model
            user = instance.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.save()
            instance.save()
        return instance