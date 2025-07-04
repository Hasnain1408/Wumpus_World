"""
Manual Play Interface for Wumpus World
Handles user input and manual game control
"""

from typing import Dict, List, Optional
from .game import WumpusGame
from .move import Move, MoveResult


class ManualPlayer:
    """Manual player interface for Wumpus World"""
    
    def __init__(self, board_size: int = 10):
        self.game = WumpusGame(board_size)
        self.command_history: List[str] = []
        self.help_text = self.generate_help_text()
    
    def generate_help_text(self) -> str:
        """Generate help text for commands"""
        return """
        Wumpus World Manual Play Commands:
        
        Movement:
        - 'forward' or 'f': Move forward in current direction
        - 'turn_left' or 'l': Turn left
        - 'turn_right' or 'r': Turn right
        
        Actions:
        - 'shoot' or 's': Shoot arrow in current direction
        - 'grab' or 'g': Grab gold if present
        - 'climb' or 'c': Climb out of cave (only at starting position)
        
        Game Control:
        - 'help' or 'h': Show this help text
        - 'status': Show current game status
        - 'board': Show current board state
        - 'reset': Reset the game
        - 'quit' or 'q': Quit the game
        
        Environment:
        - 'load_env': Load custom environment
        - 'random_env': Generate random environment
        - 'show_percepts': Show current percepts
        
        AI Help:
        - 'hint': Get AI suggestion for next move
        - 'safe_cells': Show known safe cells
        - 'dangerous_cells': Show known dangerous cells
        """
    
    def process_command(self, command: str) -> Dict:
        """Process a user command and return result"""
        command = command.strip().lower()
        
        if not command:
            return {'success': False, 'message': 'Please enter a command'}
        
        # Add to command history
        self.command_history.append(command)
        
        # Handle game commands
        if command in ['help', 'h']:
            return {'success': True, 'message': self.help_text}
        
        elif command == 'status':
            return self.get_status()
        
        elif command == 'board':
            return self.get_board_display()
        
        elif command == 'reset':
            return self.reset_game()
        
        elif command in ['quit', 'q']:
            return {'success': True, 'message': 'Game ended', 'action': 'quit'}
        
        elif command == 'show_percepts':
            return self.show_percepts()
        
        elif command == 'hint':
            return self.get_ai_hint()
        
        elif command == 'safe_cells':
            return self.show_safe_cells()
        
        elif command == 'dangerous_cells':
            return self.show_dangerous_cells()
        
        elif command == 'random_env':
            return self.generate_random_environment()
        
        # Handle movement and action commands
        elif command in ['forward', 'f']:
            return self.make_move('forward')
        
        elif command in ['turn_left', 'l']:
            return self.make_move('turn_left')
        
        elif command in ['turn_right', 'r']:
            return self.make_move('turn_right')
        
        elif command in ['shoot', 's']:
            return self.make_move('shoot')
        
        elif command in ['grab', 'g']:
            return self.make_move('grab')
        
        elif command in ['climb', 'c']:
            return self.make_move('climb')
        
        else:
            return {'success': False, 'message': f'Unknown command: {command}. Type "help" for available commands.'}
    
    def make_move(self, action: str) -> Dict:
        """Make a move and return formatted result"""
        try:
            result = self.game.make_move(action)
            
            response = {
                'success': result.success,
                'message': result.message,
                'game_state': result.game_state,
                'percepts': result.percepts
            }
            
            # Add additional context
            if result.success:
                response['position'] = f"({self.game.board.agent.x}, {self.game.board.agent.y})"
                response['direction'] = self.game.board.agent.direction
                response['score'] = self.game.score
                
                # Check for game end conditions
                if self.game.board.game_over:
                    if self.game.board.game_won:
                        response['message'] += " Congratulations! You won!"
                    elif not self.game.board.agent.alive:
                        response['message'] += " Game over! You died."
                    else:
                        response['message'] += " Game over!"
            
            return response
            
        except Exception as e:
            return {'success': False, 'message': f'Error making move: {str(e)}'}
    
    def get_status(self) -> Dict:
        """Get current game status"""
        agent = self.game.board.agent
        
        status_info = {
            'position': f"({agent.x}, {agent.y})",
            'direction': agent.direction,
            'arrows': agent.arrows,
            'has_gold': agent.has_gold,
            'score': self.game.score,
            'moves_made': len(self.game.move_history),
            'game_over': self.game.board.game_over,
            'game_won': self.game.board.game_won,
            'agent_alive': agent.alive,
            'wumpus_alive': self.game.board.wumpus_alive
        }
        
        status_text = f"""
        Game Status:
        Position: {status_info['position']}
        Direction: {status_info['direction']}
        Arrows: {status_info['arrows']}
        Has Gold: {status_info['has_gold']}
        Score: {status_info['score']}
        Moves Made: {status_info['moves_made']}
        Game Over: {status_info['game_over']}
        Game Won: {status_info['game_won']}
        Agent Alive: {status_info['agent_alive']}
        Wumpus Alive: {status_info['wumpus_alive']}
        """
        
        return {'success': True, 'message': status_text, 'data': status_info}
    
    def get_board_display(self) -> Dict:
        """Get formatted board display"""
        board_state = self.game.get_game_state()
        
        # Create text representation of board
        board_text = self.format_board_for_display(board_state['board'])
        
        return {
            'success': True,
            'message': board_text,
            'board_state': board_state
        }
    
    def format_board_for_display(self, board_data: List[List[Dict]]) -> str:
        """Format board data for text display"""
        lines = []
        size = len(board_data)
        
        # Header
        lines.append("  " + " ".join(f"{i:2d}" for i in range(size)))
        lines.append("  " + "---" * size)
        
        # Board rows (reverse order for proper display)
        for y in range(size - 1, -1, -1):
            row = board_data[y]
            line = f"{y:2d}|"
            
            for x in range(size):
                cell = row[x]
                symbol = self.get_cell_symbol(cell)
                line += f"{symbol:2s} "
            
            lines.append(line)
        
        # Legend
        lines.append("\nLegend:")
        lines.append("A = Agent, W = Wumpus, G = Gold, P = Pit")
        lines.append("B = Breeze, S = Stench, * = Glitter")
        lines.append(". = Empty, V = Visited, ? = Unknown")
        
        return "\n".join(lines)
    
    def get_cell_symbol(self, cell: Dict) -> str:
        """Get display symbol for a cell"""
        if cell['agent']:
            return 'A'
        elif cell['wumpus']:
            return 'W'
        elif cell['gold']:
            return 'G'
        elif cell['pit']:
            return 'P'
        elif cell['glitter']:
            return '*'
        elif cell['breeze'] and cell['stench']:
            return '&'
        elif cell['breeze']:
            return 'B'
        elif cell['stench']:
            return 'S'
        elif cell['visited']:
            return 'V'
        elif cell['safe']:
            return '.'
        else:
            return '?'
    
    def show_percepts(self) -> Dict:
        """Show current percepts"""
        percepts = self.game.board.get_percepts()
        
        percept_text = "Current Percepts:\n"
        for percept, value in percepts.items():
            percept_text += f"- {percept.capitalize()}: {value}\n"
        
        return {'success': True, 'message': percept_text, 'percepts': percepts}
    
    def get_ai_hint(self) -> Dict:
        """Get AI suggestion for next move"""
        try:
            suggestion = self.game.get_ai_suggestion()
            
            if suggestion:
                hint_text = f"AI Suggestion: {suggestion}"
                
                # Add reasoning
                reasoning = self.get_ai_reasoning(suggestion)
                if reasoning:
                    hint_text += f"\nReasoning: {reasoning}"
                
                return {'success': True, 'message': hint_text, 'suggestion': suggestion}
            else:
                return {'success': False, 'message': 'No AI suggestion available'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error getting AI hint: {str(e)}'}
    
    def get_ai_reasoning(self, suggestion: str) -> str:
        """Get reasoning for AI suggestion"""
        reasoning_map = {
            'forward': 'Move to explore or reach a safe cell',
            'turn_left': 'Turn to face the desired direction',
            'turn_right': 'Turn to face the desired direction',
            'shoot': 'Shoot arrow at suspected wumpus location',
            'grab': 'Grab the gold that is present',
            'climb': 'Climb out with the gold to win'
        }
        
        return reasoning_map.get(suggestion, 'Explore the unknown')
    
    def show_safe_cells(self) -> Dict:
        """Show known safe cells"""
        safe_cells = self.game.get_safe_cells()
        
        if safe_cells:
            safe_text = "Known Safe Cells:\n"
            for cell in safe_cells:
                safe_text += f"- ({cell[0]}, {cell[1]})\n"
        else:
            safe_text = "No safe cells identified yet."
        
        return {'success': True, 'message': safe_text, 'safe_cells': safe_cells}
    
    def show_dangerous_cells(self) -> Dict:
        """Show known dangerous cells"""
        dangerous_cells = self.game.get_dangerous_cells()
        
        if dangerous_cells:
            danger_text = "Known Dangerous Cells:\n"
            for cell in dangerous_cells:
                danger_text += f"- ({cell[0]}, {cell[1]})\n"
        else:
            danger_text = "No dangerous cells identified yet."
        
        return {'success': True, 'message': danger_text, 'dangerous_cells': dangerous_cells}
    
    def reset_game(self) -> Dict:
        """Reset the game"""
        self.game.reset_game()
        self.command_history.clear()
        
        return {
            'success': True,
            'message': 'Game reset successfully',
            'game_state': self.game.get_game_state()
        }
    
    def generate_random_environment(self) -> Dict:
        """Generate and load a random environment"""
        try:
            import random
            
            # Generate random environment
            environment = {
                'wumpus': {'x': random.randint(1, 8), 'y': random.randint(1, 8)},
                'gold': {'x': random.randint(1, 8), 'y': random.randint(1, 8)},
                'pits': []
            }
            
            # Make sure wumpus and gold don't overlap
            while environment['gold']['x'] == environment['wumpus']['x'] and environment['gold']['y'] == environment['wumpus']['y']:
                environment['gold'] = {'x': random.randint(1, 8), 'y': random.randint(1, 8)}
            
            # Add random pits
            occupied_positions = {
                (environment['wumpus']['x'], environment['wumpus']['y']),
                (environment['gold']['x'], environment['gold']['y']),
                (0, 9)  # Agent starting position
            }
            
            num_pits = random.randint(3, 6)
            for _ in range(num_pits):
                attempts = 0
                while attempts < 20:  # Prevent infinite loop
                    pit_x = random.randint(0, 9)
                    pit_y = random.randint(0, 9)
                    
                    if (pit_x, pit_y) not in occupied_positions:
                        environment['pits'].append({'x': pit_x, 'y': pit_y})
                        occupied_positions.add((pit_x, pit_y))
                        break
                    
                    attempts += 1
            
            # Load the environment
            success = self.game.load_environment(environment)
            
            if success:
                return {
                    'success': True,
                    'message': 'Random environment generated and loaded',
                    'environment': environment,
                    'game_state': self.game.get_game_state()
                }
            else:
                return {'success': False, 'message': 'Failed to load random environment'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error generating random environment: {str(e)}'}
    
    def load_custom_environment(self, environment: Dict) -> Dict:
        """Load a custom environment"""
        try:
            success = self.game.load_environment(environment)
            
            if success:
                return {
                    'success': True,
                    'message': 'Custom environment loaded successfully',
                    'environment': environment,
                    'game_state': self.game.get_game_state()
                }
            else:
                return {'success': False, 'message': 'Failed to load custom environment'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error loading custom environment: {str(e)}'}
    
    def get_game_statistics(self) -> Dict:
        """Get comprehensive game statistics"""
        stats = self.game.get_statistics()
        
        stats_text = f"""
        Game Statistics:
        Moves Made: {stats['moves_made']}
        Score: {stats['score']}
        Arrows Used: {stats['arrows_used']}
        Cells Visited: {stats['cells_visited']}
        Gold Collected: {stats['gold_collected']}
        Wumpus Killed: {stats['wumpus_killed']}
        Game Won: {stats['game_won']}
        Agent Alive: {stats['agent_alive']}
        Commands Used: {len(self.command_history)}
        """
        
        return {'success': True, 'message': stats_text, 'statistics': stats}
    
    def save_game(self, filename: str = None) -> Dict:
        """Save current game state"""
        try:
            saved_file = self.game.save_game(filename)
            
            if saved_file:
                return {
                    'success': True,
                    'message': f'Game saved to {saved_file}',
                    'filename': saved_file
                }
            else:
                return {'success': False, 'message': 'Failed to save game'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error saving game: {str(e)}'}
    
    def get_command_history(self) -> List[str]:
        """Get command history"""
        return self.command_history.copy()
    
    def clear_command_history(self):
        """Clear command history"""
        self.command_history.clear()
