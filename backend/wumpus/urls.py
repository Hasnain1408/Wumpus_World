from django.urls import path
from . import views

app_name = 'wumpus'

urlpatterns = [
    # Main board view
    path('', views.wumpus_board, name='board'),
    path('board/', views.wumpus_board, name='board'),
    
    # API endpoints
    path('api/load-environment/', views.load_environment, name='load_environment'),
    path('api/save-game/', views.save_game_state, name='save_game'),
    path('api/statistics/', views.get_game_statistics, name='statistics'),
    path('api/random-environment/', views.get_random_environment, name='random_environment'),
]