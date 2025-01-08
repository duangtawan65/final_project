# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required


@login_required
def chatPage(request, room_id, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login")

    # ค้นหาห้องแชทตาม room_id
    room = get_object_or_404(ChatRoom, id=room_id)

    # ตรวจสอบว่าในห้องมีผู้ใช้แล้ว 2 คนหรือยัง
    if room.is_full():
        return redirect('chat:room_list')  # ถ้าห้องเต็มแล้วให้ไปที่หน้าแสดงห้อง

    # หากห้องยังไม่เต็มให้เพิ่มผู้ใช้เข้าในห้อง
    if room.user1 is None:
        room.user1 = request.user
    elif room.user2 is None:
        room.user2 = request.user
    room.save()

    context = {
        'room': room,
    }

    return render(request, "chatpage.html", context)


@login_required
def room_list(request):
    rooms = ChatRoom.objects.all()  # ดึงห้องทั้งหมด
    return render(request, 'room_list.html', {'rooms': rooms})



@login_required
def create_room(request):
    if request.method == "POST":
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            chat_room = form.save(commit=False)
            chat_room.owner = request.user  # เจ้าของห้องคือผู้ใช้ที่สร้างห้อง
            chat_room.save()
            return redirect('chat:room_list')  # ไปที่หน้าแสดงห้อง
    else:
        form = ChatRoomForm()

    return render(request, 'create_room.html', {'form': form})






@login_required
def exit_room(request, room_id):
    # ค้นหาห้องแชทตาม room_id
    room = get_object_or_404(ChatRoom, id=room_id)

    # ตรวจสอบว่าผู้ใช้เป็นผู้เข้าร่วมในห้องหรือไม่
    if room.user1 == request.user:
        room.user1 = None  # ลบผู้ใช้คนแรกออกจากห้อง
    elif room.user2 == request.user:
        room.user2 = None  # ลบผู้ใช้คนที่สองออกจากห้อง

    # หากห้องไม่มีผู้ใช้อีกแล้วให้ลบห้อง
    if room.user1 is None and room.user2 is None:
        room.delete()  # ลบห้อง

    else:
        room.save()  # หากยังมีผู้ใช้อยู่ในห้อง ให้บันทึกข้อมูล

    return redirect('chat:room_list')  # กลับไปที่หน้าแสดงห้องทั้งหมด