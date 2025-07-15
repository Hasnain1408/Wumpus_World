from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import random
import time
from .logic.game import WumpusGame
from .logic.manual_play import ManualPlayer
from .logic.auto_play import AutoPlayAI

# Global game instances (in production, use session-based storage)
game_instances = {}
manual_players = {}
auto_players = {}

def wumpus_board(request):
    """
    Render the main Wumpus World board page
    """
    context = {
        'title': 'Wumpus World - 10x10 Board',
        'board_size': 10,
    }
    return render(request, 'wumpus/board.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def make_move(request):
    """
    API endpoint to make a move in the game
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        action = data.get('action')
        
        if not action:
            return JsonResponse({
                'success': False,
                'message': 'Action is required'
            }, status=400)
        
        # Get or create game instance
        if session_id not in game_instances:
            game_instances[session_id] = WumpusGame()
            # Automatically load default environment for new games
            game_instances[session_id].load_default_environment()
        
        game = game_instances[session_id]
        
        # Make the move
        result = game.make_move(action)
        
        return JsonResponse({
            'success': result.success,
            'message': result.message,
            'game_state': result.game_state,
            'percepts': result.percepts
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error making move: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def manual_command(request):
    """
    API endpoint for manual play commands
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        command = data.get('command')
        
        if not command:
            return JsonResponse({
                'success': False,
                'message': 'Command is required'
            }, status=400)
        
        # Get or create manual player instance
        if session_id not in manual_players:
            manual_players[session_id] = ManualPlayer()
        
        player = manual_players[session_id]
        
        # Process the command
        result = player.process_command(command)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing command: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def auto_play_game(request):
    """
    API endpoint to start auto-play game
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        strategy = data.get('strategy', 'random')
        environment = data.get('environment')
        
        # Get or create auto player instance
        if session_id not in auto_players:
            auto_players[session_id] = AutoPlayAI()
        
        ai_player = auto_players[session_id]
        
        # Set strategy
        ai_player.set_strategy(strategy)
        
        # Play the game
        result = ai_player.play_game(environment, verbose=False)
        
        return JsonResponse({
            'success': True,
            'message': 'Auto-play game completed',
            'result': result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error in auto-play: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_ai_hint(request):
    """
    API endpoint to get AI hint for next move
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        # Get game instance
        if session_id not in game_instances:
            game_instances[session_id] = WumpusGame()
            # Automatically load default environment for new games
            game_instances[session_id].load_default_environment()
        
        game = game_instances[session_id]
        
        # Debug: Print game state
        print(f"Game over: {game.board.game_over}")
        print(f"Agent position: ({game.board.agent.x}, {game.board.agent.y})")
        print(f"Agent alive: {game.board.agent.alive}")
        
        # Get AI suggestion
        suggestion = game.get_ai_suggestion()
        
        # Debug: Print suggestion
        print(f"AI suggestion: {suggestion}")
        
        if suggestion:
            return JsonResponse({
                'success': True,
                'suggestion': suggestion,
                'message': f'AI suggests: {suggestion}'
            })
        else:
            # Try some fallback moves
            possible_actions = game.get_possible_actions()
            print(f"Possible actions: {possible_actions}")
            
            if possible_actions:
                # Simple fallback: prefer forward movement
                if 'forward' in possible_actions:
                    suggestion = 'forward'
                elif 'turn_right' in possible_actions:
                    suggestion = 'turn_right'
                else:
                    suggestion = possible_actions[0]
                
                return JsonResponse({
                    'success': True,
                    'suggestion': suggestion,
                    'message': f'AI suggests (fallback): {suggestion}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No AI suggestion available - no possible actions'
                })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error in get_ai_hint: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error getting AI hint: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_game(request):
    """
    API endpoint to reset the game
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        # Reset game instance
        if session_id in game_instances:
            game_instances[session_id].reset_game()
            # Load default environment after reset
            game_instances[session_id].load_default_environment()
        else:
            game_instances[session_id] = WumpusGame()
            # Automatically load default environment for new games
            game_instances[session_id].load_default_environment()
        
        # Reset manual player if exists
        if session_id in manual_players:
            manual_players[session_id].reset_game()
        
        return JsonResponse({
            'success': True,
            'message': 'Game reset successfully',
            'game_state': game_instances[session_id].get_game_state()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error resetting game: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_game_state(request):
    """
    API endpoint to get current game state
    """
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            session_id = data.get('session_id', 'default')
        else:
            session_id = request.GET.get('session_id', 'default')
        
        # Get game instance
        if session_id not in game_instances:
            game_instances[session_id] = WumpusGame()
            # Automatically load default environment for new games
            game_instances[session_id].load_default_environment()
        
        game = game_instances[session_id]
        
        return JsonResponse({
            'success': True,
            'game_state': game.get_game_state()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting game state: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def load_environment(request):
    """
    API endpoint to load a custom environment configuration
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        environment = data.get('environment')
        
        if not environment:
            return JsonResponse({
                'success': False,
                'message': 'Environment data is required'
            }, status=400)
        
        # Get or create game instance
        if session_id not in game_instances:
            game_instances[session_id] = WumpusGame()
            # Note: Don't auto-load default here since we're loading custom environment
        
        game = game_instances[session_id]
        
        # Load the environment
        success = game.load_environment(environment)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Environment loaded successfully',
                'game_state': game.get_game_state()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to load environment'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading environment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def load_default_environment(request):
    """
    API endpoint to load the default environment from wumpus.txt
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        # Get or create game instance
        if session_id not in game_instances:
            game_instances[session_id] = WumpusGame()
        
        game = game_instances[session_id]
        
        # Load from wumpus.txt
        success = game.load_default_environment()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Environment loaded from wumpus.txt',
                'game_state': game.get_game_state()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to load wumpus.txt'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def run_benchmark(request):
    """
    API endpoint to run AI benchmark
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        num_games = data.get('num_games', 10)
        strategy = data.get('strategy', 'logical')
        environment = data.get('environment')
        
        # Get or create auto player instance
        if session_id not in auto_players:
            auto_players[session_id] = AutoPlayAI()
        
        ai_player = auto_players[session_id]
        ai_player.set_strategy(strategy)
        
        # Run benchmark
        benchmark_result = ai_player.run_benchmark(num_games, environment)
        
        return JsonResponse({
            'success': True,
            'message': 'Benchmark completed',
            'benchmark_result': benchmark_result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error running benchmark: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def compare_strategies(request):
    """
    API endpoint to compare AI strategies
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        strategies = data.get('strategies', ['logical', 'random', 'cautious'])
        num_games = data.get('num_games', 20)
        
        # Get or create auto player instance
        if session_id not in auto_players:
            auto_players[session_id] = AutoPlayAI()
        
        ai_player = auto_players[session_id]
        
        # Compare strategies
        comparison_result = ai_player.compare_strategies(strategies, num_games)
        
        return JsonResponse({
            'success': True,
            'message': 'Strategy comparison completed',
            'comparison_result': comparison_result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error comparing strategies: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_performance_stats(request):
    """
    API endpoint to get AI performance statistics
    """
    try:
        session_id = request.GET.get('session_id', 'default')
        
        # Get auto player instance
        if session_id not in auto_players:
            return JsonResponse({
                'success': False,
                'message': 'No AI player found'
            }, status=404)
        
        ai_player = auto_players[session_id]
        stats = ai_player.get_performance_stats()
        
        return JsonResponse({
            'success': True,
            'performance_stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting performance stats: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_safe_dangerous_cells(request):
    """
    API endpoint to get safe and dangerous cells
    """
    try:
        session_id = request.GET.get('session_id', 'default')
        
        # Get game instance
        if session_id not in game_instances:
            return JsonResponse({
                'success': False,
                'message': 'No active game found'
            }, status=404)
        
        game = game_instances[session_id]
        
        safe_cells = game.get_safe_cells()
        dangerous_cells = game.get_dangerous_cells()
        
        return JsonResponse({
            'success': True,
            'safe_cells': safe_cells,
            'dangerous_cells': dangerous_cells
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting cell information: {str(e)}'
        }, status=500)

def validate_environment(data):
    """
    Validate the environment configuration data
    """
    try:
        board_size = 10
        agent_start = {'x': 0, 'y': 9}  # Bottom-left corner
        
        # Check wumpus position
        if 'wumpus' in data:
            wumpus = data['wumpus']
            if not (0 <= wumpus.get('x', -1) < board_size and 0 <= wumpus.get('y', -1) < board_size):
                return {'valid': False, 'error': 'Invalid wumpus position'}
            if wumpus['x'] == agent_start['x'] and wumpus['y'] == agent_start['y']:
                return {'valid': False, 'error': 'Wumpus cannot be at agent starting position'}
        
        # Check gold position
        if 'gold' in data:
            gold = data['gold']
            if not (0 <= gold.get('x', -1) < board_size and 0 <= gold.get('y', -1) < board_size):
                return {'valid': False, 'error': 'Invalid gold position'}
        
        # Check pits positions
        if 'pits' in data:
            pits = data['pits']
            if not isinstance(pits, list):
                return {'valid': False, 'error': 'Pits must be a list'}
            
            for i, pit in enumerate(pits):
                if not (0 <= pit.get('x', -1) < board_size and 0 <= pit.get('y', -1) < board_size):
                    return {'valid': False, 'error': f'Invalid pit position at index {i}'}
                if pit['x'] == agent_start['x'] and pit['y'] == agent_start['y']:
                    return {'valid': False, 'error': 'Pit cannot be at agent starting position'}
        
        # Check for overlapping positions
        positions = []
        
        if 'wumpus' in data:
            positions.append(f"wumpus_{data['wumpus']['x']}_{data['wumpus']['y']}")
        
        if 'gold' in data:
            positions.append(f"gold_{data['gold']['x']}_{data['gold']['y']}")
        
        if 'pits' in data:
            for pit in data['pits']:
                pit_pos = f"pit_{pit['x']}_{pit['y']}"
                if pit_pos in positions:
                    return {'valid': False, 'error': 'Multiple objects cannot occupy the same position'}
                positions.append(pit_pos)
        
        return {'valid': True, 'data': data}
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}

@csrf_exempt
@require_http_methods(["POST"])
def save_game_state(request):
    """
    API endpoint to save the current game state
    """
    try:
        data = json.loads(request.body)
        
        # Here you could save to database or file
        # For now, we'll just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Game state saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving game state: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_game_statistics(request):
    """
    API endpoint to get game statistics
    """
    # This could fetch from database in a real implementation
    stats = {
        'games_played': 0,
        'games_won': 0,
        'best_score': 0,
        'average_score': 0,
        'wumpus_killed': 0,
        'gold_collected': 0
    }
    
    return JsonResponse({
        'success': True,
        'statistics': stats
    })

@require_http_methods(["GET"])
def get_random_environment(request):
    """
    Generate a random valid environment configuration
    """
    
    board_size = 10
    agent_start = {'x': 0, 'y': 9}
    
    # Generate random positions avoiding agent start
    def get_random_position():
        while True:
            x = random.randint(0, board_size - 1)
            y = random.randint(0, board_size - 1)
            if x != agent_start['x'] or y != agent_start['y']:
                return {'x': x, 'y': y}
    
    # Generate random environment
    environment = {}
    
    # Place wumpus (not too close to agent)
    while True:
        wumpus_pos = get_random_position()
        # Ensure wumpus is not adjacent to agent start
        if abs(wumpus_pos['x'] - agent_start['x']) > 1 or abs(wumpus_pos['y'] - agent_start['y']) > 1:
            environment['wumpus'] = wumpus_pos
            break
    
    # Place gold (random location)
    while True:
        gold_pos = get_random_position()
        if (gold_pos['x'] != environment['wumpus']['x'] or 
            gold_pos['y'] != environment['wumpus']['y']):
            environment['gold'] = gold_pos
            break
    
    # Place pits (4-7 pits for good challenge)
    num_pits = random.randint(4, 7)
    pits = []
    occupied_positions = [
        (environment['wumpus']['x'], environment['wumpus']['y']),
        (environment['gold']['x'], environment['gold']['y']),
        (agent_start['x'], agent_start['y'])
    ]
    
    # Ensure at least one safe adjacent cell to agent start
    safe_adjacent = [
        (agent_start['x'] + 1, agent_start['y']),
        (agent_start['x'], agent_start['y'] - 1)
    ]
    
    for _ in range(num_pits):
        attempts = 0
        while attempts < 50:  # Prevent infinite loop
            pit_pos = get_random_position()
            pos_tuple = (pit_pos['x'], pit_pos['y'])
            
            # Don't place pit in occupied positions or safe adjacent cells
            if (pos_tuple not in occupied_positions and 
                pos_tuple not in safe_adjacent):
                pits.append(pit_pos)
                occupied_positions.append(pos_tuple)
                break
            attempts += 1
    
    environment['pits'] = pits
    
    return JsonResponse({
        'success': True,
        'environment': environment,
        'message': f'Generated environment with {len(pits)} pits'
    })

# Error handlers
def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'wumpus/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'wumpus/500.html', status=500)