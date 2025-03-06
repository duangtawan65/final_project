import json
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LogoutView
from django.views.decorators.http import require_http_methods

from .forms import *
from django.contrib.auth.decorators import login_required,user_passes_test
from .models import *
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sessions.models import Session
from django.utils.timezone import  now,  localtime
from django.shortcuts import render , redirect , HttpResponse,get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from chat.models import ChatRoom
import stripe
from django.urls import reverse
from decimal import Decimal
from django.conf import settings
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
import random



# Home view
def home_view(request):
    # Redirect admins to the admin dashboard
    if request.user.is_staff:
        return redirect('admin_dashboard')

    # If the user is logged in, add user group info
    if request.user.is_authenticated:
        is_member = request.user.groups.filter(name='member').exists()
        is_doctor = request.user.groups.filter(name='doctor').exists()
        return render(request, 'home.html', {'is_member': is_member, 'is_doctor': is_doctor})


    return render(request, 'home.html', {'is_member': False, 'is_doctor': False})


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


@login_required
def doctor_profile_view(request, id):
    doctor = get_object_or_404(DoctorProfile, user_id=id)
    form = DoctorProfileForm(instance=doctor)
    is_doctor = request.user.groups.filter(name='doctor').exists()
    is_authenticated = request.user.is_authenticated

    context = {
        'doctor': doctor,
        'form': form,
        'is_doctor': is_doctor,
        'is_authenticated': is_authenticated,
        'today': datetime.now().date(),
        'max_date': datetime.now().date() + timedelta(days=30),
        'average_rating': doctor.get_average_rating(),
        'hours': ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
                  "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"],
        'review_count': doctor.get_review_count(),
    }

    if request.user == doctor.user:
        context['questionnaires'] = Questionnaire.objects.filter(
            created_by=request.user
        ).order_by('-created_at')

    if request.method == 'POST':
        if request.user != doctor.user:
            return JsonResponse({'status': 'error', 'message': 'ไม่มีสิทธิ์แก้ไขโปรไฟล์นี้'})

        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    return render(request, 'doctor_profile.html', context)


def doctor_list(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'doctorlist.html', {'doctors': doctors})



# หน้าแรกสำหรับเลือกแบบทดสอบ
def select_quiz_view(request):
    if request.user.groups.filter(name='member').exists():
        # หา appointments ของ member ก่อน
        member_appointments = Appointment.objects.filter(member__user=request.user)

        # แล้วค่อยหา doctors จาก appointments
        doctor_ids = member_appointments.values_list('doctor_id', flat=True)

        # จากนั้นหาแบบทดสอบ
        questionnaires = Questionnaire.objects.filter(
            Q(is_system=True) |  # แบบทดสอบของระบบ
            Q(created_by_id__in=doctor_ids)  # แบบทดสอบของ doctors ที่มี appointment
        ).distinct()

        # Debug prints
        print("DEBUG - Member:", request.user)
        print("DEBUG - Doctor IDs:", list(doctor_ids))
        print("DEBUG - Questionnaires count:", questionnaires.count())
        print("DEBUG - Query:", questionnaires.query)
    else:
        questionnaires = Questionnaire.objects.all()

    return render(request, 'select_questions.html', {'questionnaires': questionnaires})



# หน้าสำหรับแสดงคำถามของแบบทดสอบที่เลือก
@login_required(login_url='login')
def take_quiz_view(request, questionnaire_id):
    # ดึงแบบทดสอบ
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # เช็คว่าเป็น member หรือไม่
    if not request.user.groups.filter(name='member').exists():
        return redirect('home')

    # เช็คสิทธิ์การเข้าถึง - ต้องเป็นแบบทดสอบของระบบ หรือมีการนัดหมายกับ doctor ที่สร้างแบบทดสอบ
    if not (questionnaire.is_system or
            Appointment.objects.filter(
                member__user=request.user,
                doctor__user=questionnaire.created_by
            ).exists()):
        return redirect('select_questions')

    # ดึงคำถามทั้งหมดของแบบทดสอบ
    questions = questionnaire.questions.all()

    # กรณีส่งคำตอบ
    if request.method == 'POST':
        score = 0
        # คำนวณคะแนนจากคำตอบที่เลือก
        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                choice = Choice.objects.get(id=selected_choice_id)
                score += choice.response_value

        # ไปหน้าแสดงผลลัพธ์
        return redirect('questions_result', questionnaire_id=questionnaire.id, score=score)

    # กรณีเข้ามาดูแบบทดสอบ
    return render(request, 'take_questions.html', {
        'questionnaire': questionnaire,
        'questions': questions
    })



# หน้าสำหรับแสดงผลลัพธ์หลังทำแบบทดสอบ
def quiz_result_view(request, questionnaire_id, score):
    # ดึงแบบทดสอบ
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # ค้นหาผลลัพธ์จากคะแนน
    result = Result.objects.filter(
        questionnaire=questionnaire,
        score_low__lte=score,
        score_high__gte=score
    ).first()

    # กำหนดผลลัพธ์และระดับความเครียด
    if result:
        recommendation = result.result_description
        stress_level = result.stress_level
    else:
        recommendation = "No recommendation available for this score."
        stress_level = "Unknown"

    # ตรวจสอบสิทธิ์
    if not request.user.groups.filter(name='member').exists():
        return redirect('home')

    # เช็คสิทธิ์การเข้าถึง - เหมือนใน take_quiz_view
    if not (questionnaire.is_system or
            Appointment.objects.filter(
                member__user=request.user,
                doctor__user=questionnaire.created_by
            ).exists()):
        return redirect('select_questions')

    # บันทึกประวัติการทำแบบทดสอบ
    QuizHistory.objects.create(
        user=request.user,
        questionnaire=questionnaire,
        score=score,
        stress_level=stress_level,
        result_description=recommendation
    )

    # แสดงผลลัพธ์
    return render(request, 'questions_result.html', {
        'questionnaire': questionnaire,
        'score': score,
        'recommendation': recommendation,
        'stress_level': stress_level,
    })




@login_required
def quiz_history_view(request):
    if request.user.groups.filter(name='member').exists():
        # ถ้าเป็น member ดูได้แค่ประวัติตัวเอง
        histories = QuizHistory.objects.filter(user=request.user)
    elif request.user.groups.filter(name='doctor').exists():
        # ถ้าเป็น doctor ดูได้เฉพาะประวัติของ member ที่เคย appointment
        histories = QuizHistory.objects.filter(
            user__profile__member_appointments__doctor__user=request.user
        )
    else:
        return redirect('home')

    histories = histories.select_related('questionnaire', 'user').order_by('-created_at')
    return render(request, 'test_history.html', {'histories': histories})




@login_required
@require_http_methods(["GET"])
def get_questionnaire_history_view(request):
    questionnaire_id = request.GET.get('questionnaire_id')
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # ตรวจสอบสิทธิ์ก่อนดึงข้อมูล
    if request.user != questionnaire.created_by and not request.user.groups.filter(name='doctor').exists():
        return JsonResponse({'status': 'error', 'message': 'ไม่มีสิทธิ์ดูประวัติ'})

    # ถ้าเป็น doctor ให้ดูได้เฉพาะประวัติของ member ที่เคย appointment
    if request.user.groups.filter(name='doctor').exists():
        histories = QuizHistory.objects.filter(
            questionnaire=questionnaire,
            user__profile__member_appointments__doctor__user=request.user
        ).select_related('user').order_by('-created_at').distinct()
    else:
        histories = QuizHistory.objects.filter(
            questionnaire=questionnaire
        ).select_related('user').order_by('-created_at')

    try:
        history_data = [{
            'member_name': f"{history.user.first_name} {history.user.last_name}",
            'date': history.created_at.strftime('%Y-%m-%d %H:%M'),
            'score': history.score,
            'result': history.stress_level
        } for history in histories]

        return JsonResponse({
            'status': 'success',
            'history': history_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
@transaction.atomic
def create_questionnaire_view(request):
   if not request.user.groups.filter(name='doctor').exists():
       return redirect('home')

   if request.method == 'POST':
       print("POST Data:", request.POST)  # Debug print
       questionnaire_form = QuestionnaireForm(request.POST)

       if questionnaire_form.is_valid():
           try:
               # สร้างแบบทดสอบ
               questionnaire = Questionnaire.objects.create(
                   questionnaire_name=questionnaire_form.cleaned_data['questionnaire_name'],
                   description=questionnaire_form.cleaned_data['description'],
                   created_by=request.user,
                   is_system=False
               )

               # สร้างคำถามและตัวเลือก
               questions = request.POST.getlist('questions[]')
               for i in range(len(questions)):
                   question = Question.objects.create(
                       questionnaire=questionnaire,
                       question_content=questions[i]
                   )

                   choices = request.POST.getlist(f'choices[{i+1}][]')
                   values = request.POST.getlist(f'values[{i+1}][]')

                   for choice_text, value in zip(choices, values):
                       Choice.objects.create(
                           question=question,
                           response_text=choice_text,
                           response_value=value
                       )

               # สร้างเกณฑ์การประเมิน
               score_lows = request.POST.getlist('score_low[]')
               score_highs = request.POST.getlist('score_high[]')
               stress_levels = request.POST.getlist('stress_level[]')
               descriptions = request.POST.getlist('result_description[]')

               for i in range(len(score_lows)):
                   Result.objects.create(
                       questionnaire=questionnaire,
                       score_low=score_lows[i],
                       score_high=score_highs[i],
                       stress_level=stress_levels[i],
                       result_description=descriptions[i]
                   )



               messages.success(request, 'สร้างแบบทดสอบสำเร็จ')
               return redirect('doctor_profile', id=request.user.id)

           except Exception as e:
               messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
               return redirect('create_questionnaire')

       messages.error(request, 'กรุณากรอกข้อมูลให้ถูกต้อง')

   return render(request, 'create_questionnaire.html')


@login_required
@transaction.atomic
def edit_questionnaire_view(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    if request.user != questionnaire.created_by:
        messages.error(request, 'คุณไม่มีสิทธิ์แก้ไขแบบทดสอบนี้')
        return redirect('doctor_profile', id=request.user.id)

    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debug print
        questionnaire_form = QuestionnaireForm(request.POST)

        if questionnaire_form.is_valid():
            try:
                with transaction.atomic():
                    # อัพเดทข้อมูลแบบทดสอบ
                    questionnaire.questionnaire_name = questionnaire_form.cleaned_data['questionnaire_name']
                    questionnaire.description = questionnaire_form.cleaned_data['description']
                    questionnaire.save()

                    # ลบคำถามและตัวเลือกเก่า
                    questionnaire.questions.all().delete()

                    # สร้างคำถามและตัวเลือกใหม่
                    questions = request.POST.getlist('questions[]')
                    for i in range(len(questions)):
                        question = Question.objects.create(
                            questionnaire=questionnaire,
                            question_content=questions[i]
                        )

                        choices = request.POST.getlist(f'choices[{i + 1}][]')
                        values = request.POST.getlist(f'values[{i + 1}][]')

                        for choice_text, value in zip(choices, values):
                            Choice.objects.create(
                                question=question,
                                response_text=choice_text,
                                response_value=value
                            )

                    # ลบเกณฑ์การประเมินเก่า
                    questionnaire.results.all().delete()

                    # สร้างเกณฑ์การประเมินใหม่
                    score_lows = request.POST.getlist('score_low[]')
                    score_highs = request.POST.getlist('score_high[]')
                    stress_levels = request.POST.getlist('stress_level[]')
                    descriptions = request.POST.getlist('result_description[]')

                    for i in range(len(score_lows)):
                        Result.objects.create(
                            questionnaire=questionnaire,
                            score_low=score_lows[i],
                            score_high=score_highs[i],
                            stress_level=stress_levels[i],
                            result_description=descriptions[i]
                        )

                messages.success(request, 'แก้ไขแบบทดสอบสำเร็จ')
                return redirect('doctor_profile', id=request.user.id)

            except Exception as e:
                messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
                return redirect('edit_questionnaire', questionnaire_id=questionnaire_id)

        messages.error(request, 'กรุณากรอกข้อมูลให้ถูกต้อง')

    initial_data = {
        'questionnaire_name': questionnaire.questionnaire_name,
        'description': questionnaire.description
    }
    questionnaire_form = QuestionnaireForm(initial=initial_data)

    context = {
        'questionnaire': questionnaire,
        'form': questionnaire_form,
        'questions': questionnaire.questions.all().prefetch_related('choices'),
        'results': questionnaire.results.all(),
        'doctor': request.user.doctorprofile
    }
    return render(request, 'edit_questionnaire.html', context)


@login_required
def system_questionnaire_stats(request):
    # ดึงแบบทดสอบของระบบ
    system_questionnaires = Questionnaire.objects.filter(is_system=True)
    stats = []

    for questionnaire in system_questionnaires:
        try:
            # จำนวนผู้ทำแบบทดสอบ
            total_responses = QuizHistory.objects.filter(
                questionnaire=questionnaire,
                is_completed=True
            ).count()

            # คะแนนเฉลี่ย
            avg_score = QuizHistory.objects.filter(
                questionnaire=questionnaire,
                is_completed=True
            ).aggregate(Avg('score'))['score__avg']

            # ระดับความเครียดที่พบบ่อย
            common_stress = QuizHistory.objects.filter(
                questionnaire=questionnaire,
                is_completed=True
            ).values('stress_level').annotate(
                count=Count('id')
            ).order_by('-count').first()

            # แนวโน้มรายเดือน
            six_months_ago = datetime.now() - timedelta(days=180)
            monthly_trends = QuizHistory.objects.filter(
                questionnaire=questionnaire,
                is_completed=True,
                created_at__gte=six_months_ago
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                avg_score=Avg('score'),
                count=Count('id')
            ).order_by('month')

            # จำนวนผู้ที่มีความเครียดสูง
            high_stress_count = QuizHistory.objects.filter(
                questionnaire=questionnaire,
                is_completed=True,
                stress_level='สูง'  # ปรับตามค่าที่คุณใช้ในระบบ
            ).count()

            high_stress_percentage = (high_stress_count / total_responses * 100) if total_responses > 0 else 0

            # เตรียมข้อมูลสำหรับส่งไป template
            stats.append({
                'name': questionnaire.questionnaire_name,
                'total_responses': total_responses,
                'avg_score': round(avg_score, 2) if avg_score else 0,
                'common_stress': common_stress['stress_level'] if common_stress else 'ไม่มีข้อมูล',
                'monthly_trends': list(monthly_trends),
                'high_stress_percentage': round(high_stress_percentage, 2)
            })

        except Exception as e:
            print(f"Error processing questionnaire {questionnaire.id}: {str(e)}")
            continue

    context = {
        'stats': stats,
        'page_title': 'สถิติแบบทดสอบสุขภาพจิต',
        'total_questionnaires': len(stats)
    }

    return render(request, 'questionnaire_stats.html', context)



def is_admin(user):
    return user.is_staff and user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard_view(request):
    # Get filters from request
    group_filter = request.GET.get('group', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    users = User.objects.all().order_by('-date_joined')

    # Apply filters
    if group_filter:
        if group_filter == 'admin':
            users = users.filter(is_staff=True, is_superuser=True)
        else:
            users = users.filter(groups__name=group_filter)

    # Apply search
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Calculate statistics
    total_users = User.objects.count()
    total_doctors = User.objects.filter(groups__name='doctor').count()
    total_members = User.objects.filter(groups__name='member').count()
    total_admins = User.objects.filter(is_staff=True, is_superuser=True).count()

    # Pagination
    paginator = Paginator(users, 10)  # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Process each user in current page
    for user in page_obj:
        # Set role attribute
        if user.is_staff and user.is_superuser:
            user.role = 'admin'
        elif user.groups.filter(name='doctor').exists():
            user.role = 'doctor'
        elif user.groups.filter(name='member').exists():
            user.role = 'member'
        else:
            user.role = 'member'

        # Set online status
        user.is_online = is_user_online(user)

        # Format last login
        if user.last_login:
            user.formatted_last_login = localtime(user.last_login).strftime('%d/%m/%Y %H:%M:%S')
        else:
            user.formatted_last_login = 'ไม่เคยเข้าสู่ระบบ'

    # Handle POST requests
    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        try:
            user = User.objects.get(id=user_id)
            if action == "change_group":  # Changed from change_role
                new_group = request.POST.get("group")  # Changed from role
                # Reset permissions
                user.groups.clear()
                user.is_staff = False
                user.is_superuser = False

                # Apply new group/permissions
                if new_group in ['member', 'doctor']:
                    group, created = Group.objects.get_or_create(name=new_group)
                    user.groups.add(group)
                elif new_group == "admin":
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
            elif action == "delete_user":
                user.delete()
        except User.DoesNotExist:
            messages.error(request, 'ไม่พบผู้ใช้งานที่ระบุ')

        return redirect("admin_dashboard")

    context = {
        'users': page_obj,
        'group_filter': group_filter,
        'search_query': search_query,
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_members': total_members,
        'total_admins': total_admins,
    }

    return render(request, "admin_dashboard.html", context)


@login_required
def admin_statistics_view(request):
    # ข้อมูลพื้นฐาน
    total_profiles = Profile.objects.count()
    total_doctors = DoctorProfile.objects.count()
    total_questionnaires = Questionnaire.objects.count()
    total_appointments = Appointment.objects.count()

    # นับการนัดหมายตามสถานะ
    completed_appointments = Appointment.objects.filter(status='ended').count()
    canceled_appointments = Appointment.objects.filter(payment_status__in=['canceled', 'expired']).count()

    # นับจำนวนการนัดหมายที่ชำระเงินแล้ว
    total_consultations = Appointment.objects.filter(payment_status='paid').count()  # ใช้การนัดหมายที่จ่ายแล้ว

    # คำนวณรายได้รวม
    appointments = Appointment.objects.filter(payment_status='paid')
    total_revenue = sum(
        appointment.doctor.session_rate
        for appointment in appointments
        if appointment.doctor.session_rate
    )

    # คำนวณส่วนแบ่ง
    system_fee_total = total_revenue * Decimal('0.20')
    doctor_fee_total = total_revenue - system_fee_total

    # ข้อมูลกราฟรายเดือน
    appointments_2025 = Appointment.objects.filter(appointment_date__year=2025)
    all_months_data = []
    all_months_revenues = []
    month_labels = []

    THAI_MONTHS = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]

    for month in range(1, 13):
        # ดึงข้อมูลแต่ละเดือน
        monthly_appointments = appointments_2025.filter(
            appointment_date__month=month
        )

        # จำนวนนัดหมาย
        appointment_count = monthly_appointments.count()
        all_months_data.append(appointment_count)

        # รายได้
        monthly_revenue = sum(
            appointment.doctor.session_rate
            for appointment in monthly_appointments.filter(payment_status='paid')
            if appointment.doctor.session_rate
        )
        all_months_revenues.append(float(monthly_revenue))

        # เพิ่มชื่อเดือน
        month_labels.append(THAI_MONTHS[month - 1])

    context = {
        'total_profiles': total_profiles,
        'total_doctors': total_doctors,
        'total_questionnaires': total_questionnaires,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'canceled_appointments': canceled_appointments,
        'total_revenue': total_revenue,
        'system_fee_total': system_fee_total,
        'doctor_fee_total': doctor_fee_total,
        'months': month_labels,
        'appointment_counts': all_months_data,
        'revenues': all_months_revenues,
        'total_consultations': total_consultations  # ส่งข้อมูลจำนวนการนัดหมายที่จ่ายเงินแล้ว
    }

    return render(request, 'admin_statistics.html', context)


def is_user_online(user):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id_list = []

    # เก็บ user_id จากทุก session ที่ยังไม่หมดอายุ
    for session in sessions:
        data = session.get_decoded()
        user_id_list.append(data.get('_auth_user_id', None))

    # เช็คว่า user_id อยู่ใน active sessions หรือไม่
    return str(user.id) in user_id_list


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

    # เพิ่ม Pagination

    paginator = Paginator(appointments, 10)  # แสดง 10 รายการต่อหน้า

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'appointments': page_obj,
        'current_time': now,
        'page_obj': page_obj,
    }
    return render(request, 'schedule.html', context)



# view สำหรับสร้างการนัดหมายใหม่
def create_appointment(request):
    if request.method == 'GET':
        date = request.GET.get('date')
        time = request.GET.get('time')
        doctor_id = request.GET.get('doctor_id')

        try:
            doctor = DoctorProfile.objects.get(id=doctor_id)
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time, '%H:%M').time()

            # ตรวจสอบการจองซ้ำ
            existing_appointment = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                time=appointment_time
            ).exists()

            if existing_appointment:
                messages.error(request, 'เวลานี้มีการนัดหมายแล้ว')
                return redirect('doctor_profile', id=doctor.user.id)

            # สร้าง Appointment
            appointment = Appointment.objects.create(
                doctor=doctor,
                member=request.user.profile,  # สมมติว่ามี user.profile
                appointment_date=appointment_date,
                time=appointment_time,
                service_mode='Online',
                payment_status='pending',
            )

            # อัปเดตตารางเวลาหมอ (DoctorSchedule) เป็นไม่ว่าง
            DoctorSchedule.objects.filter(
                doctor_id=doctor_id,
                date=appointment_date,
                time=appointment_time
            ).update(is_available=False)

            # หลังสร้างเสร็จ => redirect ไปหน้าชำระเงิน
            return redirect('create_payment', appointment_id=appointment.id)

        except Exception as e:
            print("Error:", e)
            messages.error(request, 'เกิดข้อผิดพลาดในการสร้างการนัดหมาย')
            return redirect('home')

    return redirect('home')



def create_payment(request, appointment_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    appointment = get_object_or_404(Appointment, id=appointment_id)
    doctor = appointment.doctor

    if not doctor.stripe_account_id:
        messages.error(request, 'แพทย์ยังไม่ได้เชื่อมต่อบัญชีธนาคาร')
        return redirect('doctor_profile', id=doctor.user.id)

    session_rate = doctor.session_rate or 0
    system_fee = session_rate * Decimal('0.20')  # 20%

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'thb',
                'unit_amount': int(session_rate * 100),
                'product_data': {
                    'name': f'ค่าปรึกษา {doctor.user.username}',
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success', args=[appointment.id])),
        cancel_url=request.build_absolute_uri(reverse('payment_cancel', args=[appointment.id])),
        payment_intent_data={
            'application_fee_amount': int(system_fee * 100),
            'transfer_data': {
                'destination': doctor.stripe_account_id,
            },
        }
    )

    appointment.stripe_payment_id = session.id
    appointment.save()

    return redirect(session.url, code=303)

def payment_success(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.payment_status = 'paid'
    appointment.save()
    messages.success(request, 'ชำระเงินสำเร็จ')
    return redirect('schedule')  # หรือหน้าไหนตามต้องการ

def payment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()

    # ปลดล็อกเวลาหมอ
    DoctorSchedule.objects.filter(
        doctor_id=appointment.doctor.id,
        date=appointment.appointment_date,
        time=appointment.time
    ).update(is_available=True)

    messages.error(request, 'การชำระเงินถูกยกเลิก')
    return redirect('home')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event.type == 'checkout.session.completed':
            session = event.data.object
            appointment = Appointment.objects.get(stripe_payment_id=session.id)
            appointment.payment_status = 'paid'
            appointment.save()

        elif event.type == 'checkout.session.expired':
            session = event.data.object
            appointment = Appointment.objects.get(stripe_payment_id=session.id)
            appointment.payment_status = 'expired'
            appointment.save()

            DoctorSchedule.objects.filter(
                doctor_id=appointment.doctor.id,
                date=appointment.appointment_date,
                time=appointment.time
            ).update(is_available=True)

        return HttpResponse(status=200)

    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except Appointment.DoesNotExist:
        return HttpResponse(status=404)


@login_required
def doctor_payment_settings(request):
    try:
        doctor = request.user.doctorprofile
        context = {
            'doctor': doctor,
            'total_earnings': Decimal('0'),
            'monthly_earnings': Decimal('0'),
            'total_consultations': 0,
            'recent_transfers': []
        }

        # คำนวณรายได้ทั้งหมด
        appointments = Appointment.objects.filter(
            doctor=doctor,
            payment_status='paid'  # เฉพาะการนัดหมายที่จ่ายเงินแล้ว
        )
        total_earnings = sum(doctor.session_rate for appointment in appointments if doctor.session_rate)
        total_earnings = total_earnings * Decimal('0.8')  # หักค่าธรรมเนียม 20%

        # คำนวณรายได้เดือนนี้
        first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_appointments = appointments.filter(
            appointment_date__gte=first_day_of_month
        )
        monthly_earnings = sum(doctor.session_rate for appointment in monthly_appointments if doctor.session_rate)
        monthly_earnings = monthly_earnings * Decimal('0.8')

        # จำนวนการปรึกษาทั้งหมด (เฉพาะที่จ่ายแล้ว)
        total_consultations = appointments.count()

        formatted_transfers = []

        # ใช้ข้อมูลการโอนที่จำลอง
        if not formatted_transfers:
            # สร้างข้อมูลการโอนเงินจำลอง
            for month in range(1, 13):
                month_appointments = appointments.filter(
                    appointment_date__year=2025,
                    appointment_date__month=month,
                    payment_status='paid'  # เฉพาะการนัดหมายที่จ่ายแล้ว
                )

                if month_appointments.exists():
                    # คำนวณรายได้ทั้งหมดของเดือนนั้น
                    total_monthly_revenue = sum(
                        appointment.doctor.session_rate for appointment in month_appointments if
                        appointment.doctor.session_rate
                    )

                    # สุ่มจำนวนการโอน
                    num_transfers = month_appointments.count()

                    # สุ่มวันที่การโอน
                    for i in range(num_transfers):
                        transfer_date = datetime(2025, month, random.randint(25, 28))
                        transfer_amount = total_monthly_revenue / num_transfers
                        formatted_transfers.append({
                            'created': transfer_date,
                            'amount': float(transfer_amount * Decimal('0.8')),  # หักค่าธรรมเนียม 20%
                            'status': 'โอนเงินสำเร็จ'
                        })

            formatted_transfers.sort(key=lambda x: x['created'], reverse=True)

        # ใช้ Paginator
        paginator = Paginator(formatted_transfers, 5)  # 5 รายการต่อหน้า
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'account_status': 'active' if doctor.stripe_account_id else 'pending',
            'total_earnings': total_earnings,
            'monthly_earnings': monthly_earnings,
            'total_consultations': total_consultations,  # จำนวนการนัดหมายที่จ่ายเงินแล้ว
            'recent_transfers': page_obj
        })

        return render(request, 'doctor_payment_settings.html', context)

    except Exception as e:
        print(f"Error in payment settings: {str(e)}")
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect('home')


@login_required
def stripe_payout_settings(request):
    try:
        doctor = request.user.doctorprofile
        if not doctor.stripe_account_id:
            messages.error(request, 'กรุณาเชื่อมต่อบัญชี Stripe ก่อน')
            return redirect('doctor_payment_settings')

        # สร้าง Account Link แทน Login Link
        account_link = stripe.AccountLink.create(
            account=doctor.stripe_account_id,
            refresh_url=request.build_absolute_uri('/stripe/payout-settings/'),
            return_url=request.build_absolute_uri('/payment-settings/'),
            type='account_onboarding'
        )
        return redirect(account_link.url)

    except Exception as e:
        print("Error:", str(e))
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect('doctor_payment_settings')

@login_required
def disconnect_stripe(request):
    """ยกเลิกการเชื่อมต่อ Stripe Account"""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        doctor = request.user.doctorprofile
        if doctor.stripe_account_id:
            # ยกเลิกการเชื่อมต่อใน Stripe
            stripe.Account.delete(doctor.stripe_account_id)

            # ลบ stripe_account_id ในฐานข้อมูล
            doctor.stripe_account_id = None
            doctor.save()

            messages.success(request, 'ยกเลิกการเชื่อมต่อ Stripe สำเร็จ')

        return redirect('doctor_payment_settings')

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect('doctor_payment_settings')

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def stripe_connect_onboarding(request):
    try:
        doctor = request.user.doctorprofile
        if not doctor.stripe_account_id:
            account = stripe.Account.create(
                type='standard',
                country='TH',
                email=request.user.email
            )
            doctor.stripe_account_id = account.id
            doctor.save()

        account_link = stripe.AccountLink.create(
            account=doctor.stripe_account_id,
            refresh_url=request.build_absolute_uri('/stripe/connect/onboarding/'),
            return_url=request.build_absolute_uri('/payment-settings/'),
            type='account_onboarding'
        )
        return redirect(account_link.url)
    except Exception as e:
        print("Error:", str(e))
        return redirect('doctor_payment_settings')


def check_appointments(request):
    date = request.GET.get('date')
    doctor_id = request.GET.get('doctor_id')

    try:
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()

        # ดึงเวลาที่ถูกจองจากทั้ง 2 ตาราง
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=appointment_date
        ).values_list('time', flat=True)

        unavailable_slots = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            date=appointment_date,
            is_available=False
        ).values_list('time', flat=True)

        # รวมเวลาที่ไม่ว่างทั้งหมด
        unavailable_times = set([t.strftime('%H:%M') for t in booked_appointments] +
                                [t.strftime('%H:%M') for t in unavailable_slots])

        return JsonResponse({
            'status': 'success',
            'booked_times': list(unavailable_times)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def load_schedule(request):
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    try:
        schedules = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            date=date
        ).values_list('time', 'is_available', flat=False)

        return JsonResponse({
            'status': 'success',
            'schedules': [{'time': t[0].strftime('%H:%M'), 'is_available': t[1]} for t in schedules]
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def save_schedule(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        doctor = DoctorProfile.objects.get(id=data.get('doctor_id'))
        date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        times = data.get('times', [])

        try:
            # ดึงตารางเวลาที่มีอยู่เดิม
            existing_schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                date=date,
                is_available=False
            ).values_list('time', flat=True)

            # รวมเวลาที่มีอยู่เดิมกับเวลาใหม่
            all_times = set([t.strftime('%H:%M') for t in existing_schedules])
            all_times.update(times)  # เพิ่มเวลาใหม่เข้าไป

            # สร้างหรืออัพเดทตารางเวลา
            for time in all_times:
                DoctorSchedule.objects.update_or_create(
                    doctor=doctor,
                    date=date,
                    time=datetime.strptime(time, '%H:%M').time(),
                    defaults={'is_available': False}
                )

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

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
        print("Received POST request:", request.POST)
        form = DoctorVerificationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            print("Form is valid. Saving data...")
            doctor_request = form.save(commit=False)
            doctor_request.user = request.user
            doctor_request.save()
            messages.success(request, 'ส่งคำขอเรียบร้อยแล้ว')
            return redirect('home')
        else:
            print("Form is invalid:", form.errors)
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



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIR = os.path.join(BASE_DIR, 'healmind', 'fixtures')

with open(os.path.join(FIXTURE_DIR, 'thai_provinces.json'), encoding='utf-8') as f:
    PROVINCES = json.load(f)

with open(os.path.join(FIXTURE_DIR, 'thai_amphures.json'), encoding='utf-8') as f:
    AMPHURES = json.load(f)

with open(os.path.join(FIXTURE_DIR, 'thai_tambons.json'), encoding='utf-8') as f:
    TAMBONS = json.load(f)


def get_provinces(request):
    try:
        return JsonResponse(PROVINCES, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_amphures(request):
    province_name = request.GET.get('province')
    if not province_name:
        return JsonResponse([], safe=False)

    # หาฟิลด์ province_id จาก province_name
    province = next((p for p in PROVINCES if p['name_th'] == province_name), None)
    if not province:
        return JsonResponse([], safe=False)

    province_id = province['id']  # ดึง province_id

    # กรอง amphures โดยใช้ province_id
    filtered_amphures = [
        amphure for amphure in AMPHURES if amphure['province_id'] == province_id
    ]

    return JsonResponse(filtered_amphures, safe=False)


def get_tambons(request):
    amphure_name = request.GET.get('amphure')
    if not amphure_name:
        return JsonResponse([], safe=False)

    amphure = next((a for a in AMPHURES if a['name_th'] == amphure_name), None)
    if not amphure:
        return JsonResponse([], safe=False)

    amphure_id = amphure['id']

    # กรองตำบลและเพิ่ม zip_code
    filtered_tambons = [
        {
            **tambon,
            'zip_code': tambon.get('zip_code', '')  # เพิ่ม zip_code จาก thai_tambons.json
        }
        for tambon in TAMBONS
        if tambon['amphure_id'] == amphure_id
    ]

    return JsonResponse(filtered_tambons, safe=False)


