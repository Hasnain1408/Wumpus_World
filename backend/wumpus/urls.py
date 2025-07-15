from django.urls import path
from . import views

app_name = 'wumpus'

urlpatterns = [
    # Main board view
    path('', views.wumpus_board, name='board'),
    path('board/', views.wumpus_board, name='board'),
    
    # API endpoints
    path('api/make-move/', views.make_move, name='make_move'),
    path('api/manual-command/', views.manual_command, name='manual_command'),
    path('api/auto-play/', views.auto_play_game, name='auto_play'),
    path('api/ai-hint/', views.get_ai_hint, name='ai_hint'),
    path('api/reset-game/', views.reset_game, name='reset_game'),
    path('api/game-state/', views.get_game_state, name='game_state'),
    path('api/load-environment/', views.load_environment, name='load_environment'),
    path('api/load-default-environment/', views.load_default_environment, name='load_default_environment'),
    path('api/benchmark/', views.run_benchmark, name='benchmark'),
    path('api/compare-strategies/', views.compare_strategies, name='compare_strategies'),
    path('api/performance-stats/', views.get_performance_stats, name='performance_stats'),
    path('api/safe-dangerous-cells/', views.get_safe_dangerous_cells, name='safe_dangerous_cells'),
    path('api/save-game/', views.save_game_state, name='save_game'),
    path('api/statistics/', views.get_game_statistics, name='statistics'),
    path('api/random-environment/', views.get_random_environment, name='random_environment'),
]