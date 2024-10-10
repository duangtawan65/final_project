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
            profile = Profile.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                gender=self.cleaned_data['gender'],
                age=self.cleaned_data['age'],
                location=self.cleaned_data['location']
            )
            profile.save()

        return user



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'gender', 'age', 'location', 'profile_picture']


# forms.py
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={
        'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'
    }))

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'gender', 'age', 'location', 'profile_picture']  # Include profile_picture
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'age': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-black text-white border border-gray-500 rounded-lg'}),
        }
