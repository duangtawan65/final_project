# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from healmind.models import Appointment
from django.http import JsonResponse



@login_required
def chatPage(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user != appointment.member.user and request.user != appointment.doctor.user:
        return redirect('home')

    chat_room, created = ChatRoom.objects.get_or_create(
        appointment=appointment,
        defaults={
            'member': appointment.member.user,
            'doctor': appointment.doctor.user
        }
    )

    # เช็คว่าสามารถเริ่มแชทได้หรือไม่
    if not chat_room.can_start_chat():
        return redirect('schedule')

    # บันทึกเวลาเริ่มแชทถ้าเพิ่งสร้างห้องใหม่
    if created:
        chat_room.start_chat()

    context = {
        'room': chat_room,
        'appointment': appointment
    }
    return render(request, "chatpage.html", context)

@login_required
def end_chat(request, appointment_id):
    chat_room = get_object_or_404(ChatRoom, appointment_id=appointment_id)

    if request.user != chat_room.member and request.user != chat_room.doctor:
        return redirect('home')

    try:
        chat_room.end_chat()
        return redirect('schedule')
    except Exception as e:
        print(f"Error ending chat: {e}")
        return redirect('schedule')


@login_required
def chat_history(request):
    # เช็ค role ของ user
    is_doctor = request.user.groups.filter(name='doctor').exists()

    if is_doctor:
        histories = ChatRoomHistory.objects.filter(
            appointment__doctor__user=request.user
        )
    else:
        histories = ChatRoomHistory.objects.filter(
            appointment__member__user=request.user
        )

    context = {
        'histories': histories,
        'is_doctor': is_doctor
    }

    return render(request, 'chat_history.html', context)


@login_required
def submit_review(request):
    if request.method == 'POST':
        history_id = request.POST.get('history_id')
        rating = request.POST.get('rating')
        history = get_object_or_404(ChatRoomHistory, id=history_id)

        if request.user == history.member:
            history.rating = rating
            history.save()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)