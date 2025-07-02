from django.shortcuts import render
from .logic.board import GameBoard
from .logic.game_state import GameState
from .logic.movement import MovementHandler
from .logic.perception import PerceptionSystem
from rest_framework.views import APIView
from rest_framework.response  import Response

class GameView(APIView):
    def post(self, request):
        board = GameBoard()
        game_state = GameState(board)
        request.session['game_state'] = game_state
        
        return Response({
            'board': board.get_visible_cells(game_state.player_pos),
            #'percepts': PerceptionSystem().get_percepts(),
            #'status': game_state.check_game_status()
        })
