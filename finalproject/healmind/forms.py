from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django import forms
import json
import os




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


class DoctorVerificationForm(forms.ModelForm):
    province = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900'
        })
    )
    amphure = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900'
        })
    )
    tambon = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
            'placeholder': 'ชื่อ'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
            'placeholder': 'นามสกุล'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
            'placeholder': 'อีเมล'
        })
    )
    title = forms.ChoiceField(
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
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg text-gray-900'
        })
    )

    class Meta:
        model = DoctorApprovalRequest
        fields = [
            'title', 'first_name', 'last_name', 'email',
            'work_location', 'address', 'province','amphure',
            'tambon', 'postal_code', 'phone', 'document', 'note'
        ]
        widgets = {
            'work_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
                'placeholder': 'สถานที่ทำงานปัจจุบัน'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
                'placeholder': 'บ้านเลขที่/หมู่บ้าน'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
                'placeholder': 'รหัสไปรษณีย์'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg text-gray-900',
                'placeholder': 'เบอร์โทรติดต่อ'
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg text-gray-900',
                'rows': 4,
                'placeholder': 'หมายเหตุเพิ่มเติม (ถ้ามี)'
            }),
            'document': forms.FileInput(attrs={
                'class': 'w-full',
                'accept': 'application/pdf'  # รับเฉพาะไฟล์ PDF
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Populate fields if user exists
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

            # Check for doctor profile
            if hasattr(user, 'doctorprofile'):
                self.fields['phone'].initial = user.doctorprofile.contact
                self.fields['work_location'].initial = user.doctorprofile.work_location


class QuestionnaireForm(forms.Form):
    questionnaire_name = forms.CharField(
        label='ชื่อแบบทดสอบ',
        max_length=255,
        required=True,
        error_messages={
            'required': 'กรุณาระบุชื่อแบบทดสอบ',
            'max_length': 'ชื่อแบบทดสอบต้องไม่เกิน 255 ตัวอักษร'
        }
    )
    description = forms.CharField(
        label='คำอธิบาย',
        widget=forms.Textarea,
        required=True,
        error_messages={
            'required': 'กรุณาระบุคำอธิบาย'
        }
    )

class QuestionForm(forms.Form):
    question_content = forms.CharField(
        label='คำถาม',
        widget=forms.Textarea,
        required=True,
        error_messages={
            'required': 'กรุณาระบุคำถาม'
        }
    )

class ChoiceForm(forms.Form):
    response_text = forms.CharField(
        label='ตัวเลือก',
        required=True,
        error_messages={
            'required': 'กรุณาระบุตัวเลือก'
        }
    )
    response_value = forms.IntegerField(
        label='คะแนน',
        required=True,
        error_messages={
            'required': 'กรุณาระบุคะแนน',
            'invalid': 'คะแนนต้องเป็นตัวเลขเท่านั้น'
        }
    )

    def clean_response_value(self):
        value = self.cleaned_data['response_value']
        if value < 0:
            raise forms.ValidationError('คะแนนต้องไม่ต่ำกว่า 0')
        return value

class ResultForm(forms.Form):
    score_low = forms.IntegerField(
        label='คะแนนต่ำสุด',
        required=True,
        error_messages={
            'required': 'กรุณาระบุคะแนนต่ำสุด',
            'invalid': 'คะแนนต้องเป็นตัวเลขเท่านั้น'
        }
    )
    score_high = forms.IntegerField(
        label='คะแนนสูงสุด',
        required=True,
        error_messages={
            'required': 'กรุณาระบุคะแนนสูงสุด',
            'invalid': 'คะแนนต้องเป็นตัวเลขเท่านั้น'
        }
    )
    stress_level = forms.CharField(
        label='ระดับความเครียด',
        max_length=255,
        required=True,
        error_messages={
            'required': 'กรุณาระบุระดับความเครียด',
            'max_length': 'ระดับความเครียดต้องไม่เกิน 255 ตัวอักษร'
        }
    )
    result_description = forms.CharField(
        label='คำอธิบายผล',
        widget=forms.Textarea,
        required=True,
        error_messages={
            'required': 'กรุณาระบุคำอธิบายผล'
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        score_low = cleaned_data.get('score_low')
        score_high = cleaned_data.get('score_high')

        if score_low is not None and score_high is not None:
            if score_low >= score_high:
                raise forms.ValidationError({
                    'score_low': 'คะแนนต่ำสุดต้องน้อยกว่าคะแนนสูงสุด',
                    'score_high': 'คะแนนสูงสุดต้องมากกว่าคะแนนต่ำสุด'
                })
            if score_low < 0:
                raise forms.ValidationError({
                    'score_low': 'คะแนนต้องไม่ต่ำกว่า 0'
                })
        return cleaned_data
