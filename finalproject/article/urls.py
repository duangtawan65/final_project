from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'article'

urlpatterns = [

    path('create/', views.create_article, name='create_article'),
    path('', views.article_list, name='article_list'),
    path('<int:pk>/', views.article_detail, name='article_detail'),

]