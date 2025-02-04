
# Create your views here.
# article/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from healmind.models import DoctorProfile  # Import จาก healmind app
from .models import Article
from .forms import ArticleForm

def is_doctor(user):
    return user.groups.filter(name='django').exists()

def create_article(request):
    # ตรวจสอบว่ามี DoctorProfile หรือไม่
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user)
        # ถ้ามี DoctorProfile ดำเนินการสร้างบทความต่อไป
        if request.method == 'POST':
            form = ArticleForm(request.POST, request.FILES)
            if form.is_valid():
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                return redirect('article:article_list')
        else:
            form = ArticleForm()
        return render(request, 'articles/create_article.html', {
            'form': form,
            'doctor_profile': doctor_profile
        })
    except DoctorProfile.DoesNotExist:
        # ถ้าไม่มี DoctorProfile ให้ redirect ไปหน้าขอเป็นหมอ
        return redirect('request_doctor')
def article_list(request):
    articles = Article.objects.all().order_by('-created_at')
    return render(request, 'articles/article_list.html', {'articles': articles})

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    try:
        doctor_profile = article.get_author_profile()
    except DoctorProfile.DoesNotExist:
        doctor_profile = None
    return render(request, 'articles/article_detail.html', {
        'article': article,
        'doctor_profile': doctor_profile
    })