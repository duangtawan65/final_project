from django.shortcuts import render

# Create your views here.
def video_call(request):
    return render(request, 'video_call.html')