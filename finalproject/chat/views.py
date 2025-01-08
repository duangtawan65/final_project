# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from healmind.models import Appointment



@login_required
def chatPage(request, appointment_id):
    # ดึงข้อมูล appointment
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # ตรวจสอบว่าผู้ใช้เป็น member หรือ doctor ของ appointment นี้
    if request.user != appointment.member.user and request.user != appointment.doctor.user:
        return redirect('home')

    # ดึงหรือสร้างห้องแชท
    chat_room, created = ChatRoom.objects.get_or_create(
        appointment=appointment,
        defaults={
            'member': appointment.member.user,
            'doctor': appointment.doctor.user
        }
    )

    context = {
        'room': chat_room,
        'appointment': appointment
    }

    return render(request, "chatpage.html", context)


@login_required
def end_chat(request, appointment_id):
    chat_room = get_object_or_404(ChatRoom, appointment_id=appointment_id)

    # ตรวจสอบว่าผู้ใช้มีสิทธิ์จบการแชทหรือไม่
    if request.user != chat_room.member and request.user != chat_room.doctor:
        return redirect('home')

    chat_room.end_chat()
    return redirect('schedule')  # หรือหน้าอื่นที่ต้องการ