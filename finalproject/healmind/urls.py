# In your `urls.py`
from django.urls import path,include
from django.contrib.auth import views as auth_views
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [

    path("",home_view, name="home"),
    # authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='register'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),


    path('profile/', profile_view, name='profile'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctor_profile/<int:id>/', doctor_profile_view, name='doctor_profile'),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),

    path('schedule/', views.schedule_view, name='schedule'),
    path('create-appointment/', views.create_appointment, name='create_appointment'),


    path('request-doctor/', views.request_doctor_approval, name='request_doctor'),
    path('admin/doctor-requests/', views.doctor_approval_list, name='doctor_requests_list'),
    path('admin/doctor-requests/<int:request_id>/approve/', views.handle_doctor_approval, name='handle_doctor_approval'),
    path('admin/doctor-requests/<int:request_id>/', views.doctor_request_detail, name='doctor_request_detail'),



    path('questionnaire/', select_quiz_view, name='select_questions'),
    path('questionnaire/<int:questionnaire_id>/', take_quiz_view, name='take_questions'),
    path('questionnaire/<int:questionnaire_id>/result/<int:score>/', quiz_result_view, name='questions_result'),
    path('test-history/', views.quiz_history_view, name='test_history'),




]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)