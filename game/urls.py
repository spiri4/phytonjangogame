from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_view, name='play'),
    path('action/', views.action_view, name='action'),
    path('rules/', views.rules_view, name='rules'),
    path('about/', views.about_view, name='about'),
    path('author/', views.author_view, name='author'),
]
