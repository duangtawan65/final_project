# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from healmind.models import Appointment
from django.http import JsonResponse
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch



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


MODEL_NAME = "meta-llama/Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def chat_view(request):
    response_text = ""

    # เมื่อผู้ใช้เข้าหน้าใหม่ ให้เคลียร์ประวัติการแชท
    request.session.pop("chat_history", None)

    if request.method == "POST":
        form = ChatForm(request.POST)

        if form.is_valid():
            user_message = form.cleaned_data["message"]

            # เริ่มแชทใหม่ ถ้าไม่มี chat_history
            if "chat_history" not in request.session:
                request.session["chat_history"] = []

            # บันทึกข้อความของผู้ใช้
            request.session["chat_history"].append({"role": "user", "content": user_message})

            # เตรียมอินพุตสำหรับโมเดล
            inputs = tokenizer(user_message, return_tensors="pt")

            # ใช้ GPU ถ้ามี ไม่งั้นใช้ CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(device)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # ให้โมเดลตอบกลับ
            with torch.no_grad():
                output = model.generate(**inputs, max_length=100)
                response_text = tokenizer.decode(output[0], skip_special_tokens=True)

            # บันทึกข้อความของ AI
            request.session["chat_history"].append({"role": "assistant", "content": response_text})

            # อัปเดต session
            request.session.modified = True

    else:
        form = ChatForm()

    return render(request, "chat.html", {"form": form, "response_text": response_text})