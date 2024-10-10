from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LogoutView
from .forms import CustomUserCreationForm
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from .models import *
# Home view
def home_view(request):
    return render(request, 'home.html')


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
    profile = request.user.profile  # Assuming you have a OneToOne relation between User and Profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)  # Use request.FILES to handle file uploads
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form, 'profile': profile})




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
