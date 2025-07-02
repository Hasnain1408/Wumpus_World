from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

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
def load_environment(request):
    """
    API endpoint to load a custom environment configuration
    Expects JSON data with wumpus, gold, and pits positions
    """
    try:
        data = json.loads(request.body)
        
        # Validate environment data
        environment = validate_environment(data)
        
        if environment['valid']:
            return JsonResponse({
                'success': True,
                'message': 'Environment loaded successfully',
                'environment': environment['data']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': environment['error']
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

def get_random_environment(request):
    """
    Generate a random valid environment configuration
    """
    import random
    
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
    
    # Place wumpus
    environment['wumpus'] = get_random_position()
    
    # Place gold
    while True:
        gold_pos = get_random_position()
        if (gold_pos['x'] != environment['wumpus']['x'] or 
            gold_pos['y'] != environment['wumpus']['y']):
            environment['gold'] = gold_pos
            break
    
    # Place pits (3-6 pits)
    num_pits = random.randint(3, 6)
    pits = []
    occupied_positions = [
        (environment['wumpus']['x'], environment['wumpus']['y']),
        (environment['gold']['x'], environment['gold']['y']),
        (agent_start['x'], agent_start['y'])
    ]
    
    for _ in range(num_pits):
        while True:
            pit_pos = get_random_position()
            pos_tuple = (pit_pos['x'], pit_pos['y'])
            if pos_tuple not in occupied_positions:
                pits.append(pit_pos)
                occupied_positions.append(pos_tuple)
                break
    
    environment['pits'] = pits
    
    return JsonResponse({
        'success': True,
        'environment': environment
    })

# Error handlers
def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'wumpus/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'wumpus/500.html', status=500)