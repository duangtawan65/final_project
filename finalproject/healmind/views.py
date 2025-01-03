from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LogoutView
from .forms import CustomUserCreationForm
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required,user_passes_test
from .models import *
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sessions.models import Session
from django.utils.timezone import  now, timedelta, localtime
from django.shortcuts import render , redirect , HttpResponse,get_object_or_404


# Home view
def home_view(request):
    # Redirect admins to the admin dashboard
    if request.user.is_staff:
        return redirect('admin_dashboard')  # Replace with your actual admin dashboard URL name

    # For regular users, try to render the home page even if they don't have a profile
    profile = getattr(request.user, 'profile', None)  # Use getattr to avoid exceptions

    return render(request, 'home.html', {'profile': profile})

# Register view
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})





class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)




@login_required
def profile_view(request):
    # ดึงข้อมูล Profile หรือสร้างใหม่ถ้าไม่มี
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # กลับไปที่หน้าโปรไฟล์
    else:
        form = ProfileForm(instance=profile)  # โหลดข้อมูลปัจจุบันของผู้ใช้

    return render(request, 'profile.html', {
        'form': form,
        'profile': profile
    })


@login_required
def doctor_profile_view(request):
    profile = request.user.profile
    doctor_profile = profile.doctor_profile  # ดึงข้อมูล DoctorProfile
    return render(request, 'doctor_profile.html', {'profile': profile, 'doctor_profile': doctor_profile})




# หน้าแรกสำหรับเลือกแบบทดสอบ
def select_quiz_view(request):
    questionnaires = Questionnaire.objects.all()
    print(questionnaires)  # Add this to check if data is being fetched
    return render(request, 'select_questions.html', {'questionnaires': questionnaires})

# หน้าสำหรับแสดงคำถามของแบบทดสอบที่เลือก
@login_required(login_url='login')  # Specify the URL to redirect to if not logged in
def take_quiz_view(request, questionnaire_id):
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    questions = questionnaire.questions.all()  # Get all the questions in the quiz
    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                choice = Choice.objects.get(id=selected_choice_id)
                score += choice.response_value  # Use response_value instead of score
        return redirect('questions_result', questionnaire_id=questionnaire.id, score=score)
    return render(request, 'take_questions.html', {'questionnaire': questionnaire, 'questions': questions})

# หน้าสำหรับแสดงผลลัพธ์หลังทำแบบทดสอบ
def quiz_result_view(request, questionnaire_id, score):
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)

    # Fetch the appropriate result based on the score range
    result = Result.objects.filter(
        questionnaire=questionnaire,
        score_low__lte=score,
        score_high__gte=score
    ).first()

    # If a result is found, use its fields for the recommendation, otherwise set a default message
    if result:
        recommendation = result.result_description
        stress_level = result.stress_level
    else:
        recommendation = "No recommendation available for this score."
        stress_level = "Unknown"

    return render(request, 'questions_result.html', {
        'questionnaire': questionnaire,
        'score': score,
        'recommendation': recommendation,
        'stress_level': stress_level,  # You can also pass the stress level if needed in the template
    })


@login_required
def doctor_dashboard(request):
    if request.user.profile.role != 'doctor':
        return redirect('home')  # Redirect if the user is not a doctor
    return render(request, 'doctor_dashboard.html')

def is_admin(user):
    return user.is_staff and user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    users = User.objects.all()

    # Assign roles and calculate online status and formatted login
    for user in users:
        if user.is_staff and user.is_superuser:
            user.role = 'admin'
        elif user.groups.filter(name='doctor').exists():
            user.role = 'doctor'
        elif user.groups.filter(name='member').exists():
            user.role = 'member'
        else:
            user.role = 'member'


        user.is_online = is_user_online(user)


        user.formatted_last_login = (
            localtime(user.last_login).strftime('%d/%m/%Y %H:%M:%S')
        )

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        user = User.objects.get(id=user_id)

        if action == "change_role":
            new_role = request.POST.get("role")
            user.groups.clear()
            if new_role in ['member', 'doctor']:
                group, created = Group.objects.get_or_create(name=new_role)
                user.groups.add(group)
            if new_role == "admin":
                user.is_staff = True
                user.is_superuser = True
                user.save()
        elif action == "delete_user":
            user.delete()

        return redirect("admin_dashboard")

    return render(request, "admin_dashboard.html", {"users": users})

def is_user_online(user):
    if user.last_login:
        return user.last_login >= now() - timedelta(minutes=5)
    return False


