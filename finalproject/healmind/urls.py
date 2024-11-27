# In your `urls.py`
from django.urls import path,include
from django.contrib.auth import views as auth_views
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('', home_view, name='home'),
    # authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='register'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),


    path('profile/', profile_view, name='profile'),
    path('doctor_profile/', doctor_profile_view, name='doctor_profile'),  # สำหรับ Doctor
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),



    path('questionnaire/', select_quiz_view, name='select_questions'),
    path('questionnaire/<int:questionnaire_id>/', take_quiz_view, name='take_questions'),
    path('questionnaire/<int:questionnaire_id>/result/<int:score>/', quiz_result_view, name='questions_result'),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)