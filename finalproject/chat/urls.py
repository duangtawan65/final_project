from django.urls import path, include
from . import views

from django.contrib.auth.views import LoginView, LogoutView
app_name = 'chat'

urlpatterns = [
    path('create/', views.create_room, name='create_room'),
    path('rooms/', views.room_list, name='room_list'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),  # เพิ่มห้องแสดงรายละเอียด
    path('chat/<int:room_id>/', views.chatPage, name='chat_page'),
    path('exit_room/<int:room_id>/', views.exit_room, name='exit_room'),


]