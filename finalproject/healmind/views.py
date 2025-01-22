from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LogoutView
from .forms import *
from django.contrib.auth.decorators import login_required,user_passes_test
from .models import *
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sessions.models import Session
from django.utils.timezone import  now, timedelta, localtime
from django.shortcuts import render , redirect , HttpResponse,get_object_or_404
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from chat.models import ChatRoom




# Home view
def home_view(request):
    # Redirect admins to the admin dashboard
    if request.user.is_staff:
        return redirect('admin_dashboard')

    # If the user is logged in, just render the home page
    if request.user.is_authenticated:

        is_member = request.user.groups.filter(name='member').exists()

        is_doctor = request.user.groups.filter(name='doctor').exists()



        return render(request, 'home.html', {'is_member': is_member, 'is_doctor': is_doctor})

    # If not authenticated, redirect to the login page
    return redirect('login')  # Redirect to login page if the user is not logged in
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


def doctor_profile_view(request, id):
    # ดึงข้อมูลโปรไฟล์ของแพทย์จากฐานข้อมูลโดยใช้ id ของ DoctorProfile
    doctor = get_object_or_404(DoctorProfile, user_id=id)

    # สร้างฟอร์มสำหรับการแก้ไข
    form = DoctorProfileForm(instance=doctor)

    is_doctor = request.user.groups.filter(name='doctor').exists()
    is_authenticated = request.user.is_authenticated

    if request.method == 'POST':
        # ตรวจสอบว่าเป็นเจ้าของโปรไฟล์
        if request.user != doctor.user:
            return JsonResponse({'status': 'error', 'message': 'ไม่มีสิทธิ์แก้ไขโปรไฟล์นี้'})

        # สร้างฟอร์มใหม่พร้อมข้อมูลจาก POST และไฟล์ที่ถูกอัปโหลด
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)

        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    return render(request, 'doctor_profile.html', {
        'doctor': doctor,
        'form': form,
        'is_doctor': is_doctor,
        'is_authenticated': is_authenticated,
        'today': datetime.now().date(),
        'max_date': datetime.now().date() + timedelta(days=30),
        'average_rating': doctor.get_average_rating(),
        'review_count': doctor.get_review_count()
    })


def doctor_list(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'doctorlist.html', {'doctors': doctors})



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

    result = Result.objects.filter(
        questionnaire=questionnaire,
        score_low__lte=score,
        score_high__gte=score
    ).first()

    if result:
        recommendation = result.result_description
        stress_level = result.stress_level
    else:
        recommendation = "No recommendation available for this score."
        stress_level = "Unknown"

    # บันทึกประวัติการทำแบบทดสอบ
    QuizHistory.objects.create(
        user=request.user,
        questionnaire=questionnaire,
        score=score,
        stress_level=stress_level,
        result_description=recommendation
    )

    return render(request, 'questions_result.html', {
        'questionnaire': questionnaire,
        'score': score,
        'recommendation': recommendation,
        'stress_level': stress_level,
    })




@login_required
def quiz_history_view(request):
    # ใช้ select_related เพื่อลดจำนวนการ query
    histories = QuizHistory.objects.filter(user=request.user) \
        .select_related('questionnaire', 'user') \
        .order_by('-created_at')  # เรียงจากใหม่ไปเก่า

    return render(request, 'test_history.html', {
        'histories': histories
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


def schedule_view(request):
    if hasattr(request.user, 'doctorprofile'):
        appointments = Appointment.objects.filter(doctor=request.user.doctorprofile)
    else:
        appointments = Appointment.objects.filter(member=request.user.profile)

    appointments = appointments.order_by('appointment_date', 'time')
    now = timezone.now()

    for appointment in appointments:
        try:
            # พยายามดึง chat room หรือสร้างใหม่ถ้ายังไม่มี
            chat_room, created = ChatRoom.objects.get_or_create(
                appointment=appointment,
                defaults={
                    'member': appointment.member.user,
                    'doctor': appointment.doctor.user,
                    'status': 'active'
                }
            )

            appointment_datetime = timezone.make_aware(
                datetime.combine(appointment.appointment_date, appointment.time)
            )
            end_time = appointment_datetime + timedelta(hours=1)

            appointment.is_in_session = appointment_datetime <= now <= end_time
            appointment.chat_status = chat_room.status
            appointment.chat_active = (
                    chat_room.status == 'active' and
                    appointment.is_in_session
            )

        except Exception as e:
            print(f"Error processing appointment: {e}")
            appointment.chat_status = None
            appointment.is_in_session = False
            appointment.chat_active = False

    context = {
        'appointments': appointments,
        'current_time': now,
    }
    return render(request, 'schedule.html', context)



# view สำหรับสร้างการนัดหมายใหม่
def create_appointment(request):
    if request.method == 'GET':
        date = request.GET.get('date')
        time = request.GET.get('time')
        doctor_id = request.GET.get('doctor_id')

        # เพิ่ม print เพื่อ debug
        print(f"Received data: date={date}, time={time}, doctor_id={doctor_id}")

        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time, '%H:%M').time()

            print(f"Parsed date: {appointment_date}")
            print(f"Parsed time: {appointment_time}")

            # เช็คข้อมูลก่อนสร้าง appointment
            print(f"User profile: {request.user.profile}")
            print(f"Doctor id: {doctor_id}")

            appointment = Appointment.objects.create(
                doctor_id=doctor_id,
                member=request.user.profile,
                appointment_date=appointment_date,
                time=appointment_time,
                service_mode='Online'
            )

            print(f"Successfully created appointment: {appointment}")
            return redirect('schedule')

        except Exception as e:
            print(f"Detailed error: {str(e)}")
            return redirect('home')

    return redirect('home')


@login_required
def request_doctor_approval(request):
    # เช็คว่าเป็น member และยังไม่เป็น doctor
    if request.user.groups.filter(name='doctor').exists():
        messages.error(request, 'คุณเป็นแพทย์อยู่แล้ว')
        return redirect('home')

    if not request.user.groups.filter(name='member').exists():
        messages.error(request, 'คุณไม่มีสิทธิ์ในการขอเป็นแพทย์')
        return redirect('home')

    # เช็คว่ามีคำขอที่รออยู่หรือไม่
    existing_request = DoctorApprovalRequest.objects.filter(
        user=request.user,
        status='pending'
    ).exists()

    if existing_request:
        messages.info(request, 'คุณมีคำขอที่รออนุมัติอยู่แล้ว')
        return redirect('home')

    if request.method == 'POST':
        form = DoctorVerificationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            doctor_request = form.save(commit=False)
            doctor_request.user = request.user
            doctor_request.save()
            messages.success(request, 'ส่งคำขอเรียบร้อยแล้ว')
            return redirect('home')
    else:
        form = DoctorVerificationForm(user=request.user)

    return render(request, 'request_doctor_approval.html', {'form': form})


# สำหรับ Superuser ดูรายการคำขอ
@user_passes_test(lambda u: u.is_superuser)
def doctor_approval_list(request):
    requests = DoctorApprovalRequest.objects.all()
    return render(request, 'doctor_approval_list.html', {
        'pending_requests': requests.filter(status='pending'),
        'approved_requests': requests.filter(status='approved'),
        'rejected_requests': requests.filter(status='rejected')
    })


# สำหรับ Superuser ดูรายละเอียดคำขอ
@user_passes_test(lambda u: u.is_superuser)
def doctor_request_detail(request, request_id):
    approval_request = get_object_or_404(DoctorApprovalRequest, id=request_id)
    return render(request, 'doctor_request_detail.html', {
        'request': approval_request
    })


# สำหรับ Superuser อนุมัติ/ปฏิเสธ
@user_passes_test(lambda u: u.is_superuser)
def handle_doctor_approval(request, request_id):
    approval_request = get_object_or_404(DoctorApprovalRequest, id=request_id)

    # ถ้าไม่ใช่สถานะ pending ให้ redirect กลับ
    if approval_request.status != 'pending':
        messages.error(request, 'คำขอนี้ถูกดำเนินการไปแล้ว')
        return redirect('doctor_requests_list')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            try:
                with transaction.atomic():
                    # เช็คว่ามี groups ที่ต้องการหรือไม่
                    try:
                        doctor_group = Group.objects.get(name='doctor')
                        member_group = Group.objects.get(name='member')
                    except Group.DoesNotExist:
                        messages.error(request, 'เกิดข้อผิดพลาดในการจัดการกลุ่มผู้ใช้')
                        return redirect('doctor_requests_list')

                    user = approval_request.user
                    # เปลี่ยนกลุ่ม
                    user.groups.remove(member_group)
                    user.groups.add(doctor_group)

                    # สร้าง DoctorProfile
                    DoctorProfile.objects.create(
                        user=user,
                        title=approval_request.title,
                        specialty='',  # เพิ่มตามต้องการ
                        work_location=approval_request.work_location,
                        contact=approval_request.phone
                    )

                    approval_request.status = 'approved'
                    approval_request.save()

                    messages.success(request, f'อนุมัติคำขอของ {user.get_full_name()} เรียบร้อยแล้ว')

            except Exception as e:
                messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
                return redirect('doctor_requests_list')

        elif action == 'reject':
            approval_request.status = 'rejected'
            approval_request.save()
            messages.info(request, f'ปฏิเสธคำขอของ {approval_request.user.get_full_name()} เรียบร้อยแล้ว')

    return redirect('doctor_requests_list')
