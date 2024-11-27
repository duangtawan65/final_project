from .models import Questionnaire, Question, Choice, Result
from django.contrib import admin
from .models import Profile,DoctorProfile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'gender', 'age', 'location')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Check if role is being updated to doctor
        if 'doctor' in obj.user.groups.values_list('name', flat=True):
            # Create a DoctorProfile if it doesn't exist
            doctor_profile, created = DoctorProfile.objects.get_or_create(
                user=obj.user,
                defaults={
                    'specialty': 'Add specialty here',
                    'bio': 'Add bio here',
                    'contact': obj.user.profile.location,  # Assuming location as initial contact
                }
            )

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'specialty', 'work_location', 'session_rate')

    def get_user(self, obj):
        return obj.profile.user.username  # Correctly access the username via profile

    get_user.short_description = 'User'

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Result)