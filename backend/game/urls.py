from django.urls import path
from . import views

urlpatterns = [
    path('game/', views.GameView.as_view(), name='game-api'),
    #path('game/move/', views.MoveView.as_view(), name='move-api'),
    #path('game/shoot/', views.ShootView.as_view(), name='shoot-api'),
]