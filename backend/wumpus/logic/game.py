"""
Wumpus World Game Logic
Main game controller and state management
"""

import json
import random
from typing import Dict, List, Tuple, Optional
from .board import WumpusBoard
from .move import Move, MoveResult
from .logical_inference import LogicalInference


class WumpusGame:
    """Main game controller for Wumpus World"""
    
    def __init__(self, board_size: int = 10):
        self.board = WumpusBoard(board_size)
        self.move_history: List[Move] = []
        self.score = 0
        self.max_moves = 1000
        self.inference_engine = LogicalInference(self.board)
        self.game_id = self.generate_game_id()
        
        # Scoring system
        self.scoring = {
            'move': -1,
            'arrow': -10,
            'death': -1000,
            'gold': 1000,
            'win': 1000
        }
    
    def generate_game_id(self) -> str:
        """Generate unique game ID"""
        return f"game_{random.randint(1000, 9999)}"
    
    def make_move(self, action: str, direction: str = None) -> MoveResult:
        """Make a move with support for direct movement actions"""
        if self.board.game_over:
            return MoveResult(False, "Game is over", self.get_game_state())
        
        if len(self.move_history) >= self.max_moves:
            self.board.game_over = True
            return MoveResult(False, "Maximum moves reached", self.get_game_state())
        
        # Handle direct movement actions
        if action.startswith('move_'):
            direction = action.split('_')[1]
            return self.move_agent(direction)
        
        # Create move object
        move = Move(action, direction, self.board.agent.x, self.board.agent.y)
        
        # Execute move
        success = False
        message = ""
        
        if action == 'forward':
            success = self.move_forward()
            message = "Moved forward" if success else "Cannot move forward"
            
        elif action == 'turn_left':
            success = self.turn_left()
            message = "Turned left"
            
        elif action == 'turn_right':
            success = self.turn_right()
            message = "Turned right"
            
        elif action == 'shoot':
            success = self.shoot_arrow()
            message = "Shot arrow" if success else "No arrows left"
            
        elif action == 'grab':
            success = self.grab_gold()
            message = "Grabbed gold" if success else "No gold here"
            
        elif action == 'climb':
            success = self.climb_out()
            message = "Climbed out" if success else "Can only climb out from starting position"
        
        else:
            return MoveResult(False, "Invalid action", self.get_game_state())
        
        # Update score
        self.update_score(action, success)
        
        # Store move
        move.result = success
        move.percepts = self.board.get_percepts()
        self.move_history.append(move)
        
        # Update inference engine
        self.inference_engine.update_knowledge(move)
        
        # Check game status
        if self.board.is_game_won():
            self.board.game_won = True
            self.board.game_over = True
            self.score += self.scoring['win']
            message += " - Game won!"
        
        return MoveResult(success, message, self.get_game_state())
    
    def move_forward(self) -> bool:
        """Move agent forward in current direction"""
        return self.board.move_agent(self.board.agent.direction)
    
    def turn_left(self) -> bool:
        """Turn agent left (counter-clockwise)"""
        # Fixed direction order: up, right, down, left (clockwise)
        directions = ['up', 'right', 'down', 'left']
        current_index = directions.index(self.board.agent.direction)
        new_direction = directions[(current_index - 1) % 4]  # Counter-clockwise
        self.board.turn_agent(new_direction)
        return True
    
    def turn_right(self) -> bool:
        """Turn agent right (clockwise)"""
        # Fixed direction order: up, right, down, left (clockwise)
        directions = ['up', 'right', 'down', 'left']
        current_index = directions.index(self.board.agent.direction)
        new_direction = directions[(current_index + 1) % 4]  # Clockwise
        self.board.turn_agent(new_direction)
        return True
    
    def shoot_arrow(self) -> bool:
        """Shoot arrow in current direction"""
        return self.board.shoot_arrow(self.board.agent.direction)
    
    def grab_gold(self) -> bool:
        """Grab gold if present"""
        cell = self.board.get_cell(self.board.agent.x, self.board.agent.y)
        if cell and cell.gold and not self.board.agent.has_gold:
            self.board.agent.has_gold = True
            cell.gold = False
            cell.glitter = False
            return True
        return False
    
    def climb_out(self) -> bool:
        """Climb out of the cave"""
        # Can only climb out from starting position
        if self.board.agent.x == 0 and self.board.agent.y == self.board.size - 1:
            if self.board.agent.has_gold:
                self.board.game_won = True
            self.board.game_over = True
            return True
        return False
    
    def update_score(self, action: str, success: bool):
        """Update game score based on action"""
        if action == 'forward' and success:
            self.score += self.scoring['move']
        elif action == 'shoot' and success:
            self.score += self.scoring['arrow']
        elif action == 'grab' and success:
            self.score += self.scoring['gold']
        
        # Check for death
        if not self.board.agent.alive:
            self.score += self.scoring['death']
    
    def get_game_state(self) -> Dict:
        """Get current game state"""
        board_state = self.board.get_board_state()
        
        return {
            'game_id': self.game_id,
            'board': board_state['board'],
            'agent': board_state['agent'],
            'wumpus_alive': board_state['wumpus_alive'],
            'game_over': board_state['game_over'],
            'game_won': board_state['game_won'],
            'score': self.score,
            'moves_made': len(self.move_history),
            'max_moves': self.max_moves,
            'percepts': self.board.get_percepts() if not self.board.game_over else {},
            'safe_cells': list(self.board.safe_cells),
            'visited_cells': list(self.board.visited_cells)
        }
    
    def get_possible_actions(self) -> List[str]:
        """Get list of possible actions"""
        if self.board.game_over:
            return []
        
        actions = ['forward', 'turn_left', 'turn_right']
        
        # Can shoot if has arrows
        if self.board.agent.arrows > 0:
            actions.append('shoot')
        
        # Can grab if gold is present
        cell = self.board.get_cell(self.board.agent.x, self.board.agent.y)
        if cell and cell.gold:
            actions.append('grab')
        
        # Can climb out from starting position
        if self.board.agent.x == 0 and self.board.agent.y == self.board.size - 1:
            actions.append('climb')
        
        return actions
    
    def get_move_history(self) -> List[Dict]:
        """Get formatted move history"""
        return [move.to_dict() for move in self.move_history]
    
    def reset_game(self):
        """Reset game to initial state"""
        self.board = WumpusBoard(self.board.size)
        self.move_history = []
        self.score = 0
        self.inference_engine = LogicalInference(self.board)
        self.game_id = self.generate_game_id()
    
    def load_environment(self, environment: Dict) -> bool:
        """Load custom environment"""
        success = self.board.load_environment(environment)
        if success:
            # Reset inference engine with new environment
            self.inference_engine = LogicalInference(self.board)
        return success
    
    def get_ai_suggestion(self) -> Optional[str]:
        """Get AI suggestion for the next move"""
        if self.board.game_over:
            return None
        
        try:
            suggestion = self.inference_engine.get_best_move()
            return suggestion
        except Exception as e:
            print(f"Error getting AI suggestion: {e}")
            return None

    def move_agent(self, direction: str) -> MoveResult:
        """Move agent in specified direction"""
        old_x, old_y = self.board.agent.x, self.board.agent.y
        
        # Calculate new position
        new_x, new_y = old_x, old_y
        if direction == 'up':
            new_y = max(0, old_y - 1)
        elif direction == 'down':
            new_y = min(self.board.size - 1, old_y + 1)
        elif direction == 'left':
            new_x = max(0, old_x - 1)
        elif direction == 'right':
            new_x = min(self.board.size - 1, old_x + 1)
        
        # Check if movement is valid
        if new_x == old_x and new_y == old_y:
            return MoveResult(False, "Cannot move outside the board", self.get_game_state())
        
        # Move agent
        self.board.agent.x = new_x
        self.board.agent.y = new_y
        
        # Mark cell as visited
        self.board.board[new_y][new_x].visited = True
        
        # Update score
        self.score += self.scoring['move']
        
        # Check for hazards
        cell = self.board.board[new_y][new_x]
        message = f"Moved {direction}"
        
        if cell.pit:
            self.board.game_over = True
            self.score += self.scoring['death']
            message += " - Fell into pit! Game over!"
        elif cell.wumpus:
            self.board.game_over = True
            self.score += self.scoring['death']
            message += " - Eaten by Wumpus! Game over!"
        else:
            # Add perceptions
            perceptions = []
            if cell.breeze:
                perceptions.append('breeze')
            if cell.stench:
                perceptions.append('stench')
            if cell.glitter:
                perceptions.append('glitter')
            
            if perceptions:
                message += f" - You perceive: {', '.join(perceptions)}"
        
        # Create and store move
        move = Move(f'move_{direction}', direction, old_x, old_y)
        move.result = True
        move.percepts = self.board.get_percepts()
        self.move_history.append(move)
        
        # Update inference engine
        self.inference_engine.update_knowledge(move)
        
        return MoveResult(True, message, self.get_game_state())

    def get_safe_cells(self) -> List[Tuple[int, int]]:
        """Get list of cells that are known to be safe"""
        return self.inference_engine.get_safe_cells()
    
    def get_dangerous_cells(self) -> List[Tuple[int, int]]:
        """Get list of cells that are known to be dangerous"""
        return self.inference_engine.get_dangerous_cells()
    
    def get_direction_to_cell(self, target_x: int, target_y: int) -> Optional[str]:
        """Get the direction needed to move to a target cell from current position"""
        current_x, current_y = self.board.agent.x, self.board.agent.y
        
        # Calculate direction needed
        if target_x > current_x:
            return 'right'
        elif target_x < current_x:
            return 'left'
        elif target_y > current_y:
            return 'down'
        elif target_y < current_y:
            return 'up'
        else:
            return None  # Same position
    
    def get_turn_actions_to_face_direction(self, target_direction: str) -> List[str]:
        """Get the sequence of turn actions needed to face a target direction"""
        if target_direction is None:
            return []
        
        current_direction = self.board.agent.direction
        if current_direction == target_direction:
            return []
        
        # Direction order: up, right, down, left (clockwise)
        directions = ['up', 'right', 'down', 'left']
        current_index = directions.index(current_direction)
        target_index = directions.index(target_direction)
        
        # Calculate shortest rotation
        diff = (target_index - current_index) % 4
        
        if diff == 1:  # Turn right once
            return ['turn_right']
        elif diff == 2:  # Turn around (2 turns, prefer right)
            return ['turn_right', 'turn_right']
        elif diff == 3:  # Turn left once
            return ['turn_left']
        else:
            return []
    
    def get_enhanced_ai_suggestion(self) -> Optional[str]:
        """Enhanced AI suggestion that handles movement and turning properly"""
        if self.board.game_over:
            return None
        
        try:
            # Get safe cells from inference engine
            safe_cells = self.inference_engine.get_safe_cells()
            
            # Find the best safe cell to move to
            current_x, current_y = self.board.agent.x, self.board.agent.y
            
            # Look for adjacent safe cells
            adjacent_cells = [
                (current_x, current_y - 1, 'up'),
                (current_x + 1, current_y, 'right'),
                (current_x, current_y + 1, 'down'),
                (current_x - 1, current_y, 'left')
            ]
            
            # Filter valid adjacent cells
            valid_adjacent = []
            for x, y, direction in adjacent_cells:
                if (0 <= x < self.board.size and 
                    0 <= y < self.board.size and 
                    (x, y) in [cell[0] for cell in safe_cells]):
                    valid_adjacent.append((x, y, direction))
            
            if valid_adjacent:
                # Choose the first safe adjacent cell
                target_x, target_y, needed_direction = valid_adjacent[0]
                
                # Check if we're already facing the right direction
                current_direction = self.board.agent.direction
                if current_direction == needed_direction:
                    return 'forward'
                else:
                    # Get turn actions needed
                    turn_actions = self.get_turn_actions_to_face_direction(needed_direction)
                    if turn_actions:
                        return turn_actions[0]  # Return the first turn action
            
            # If no safe adjacent cells, try other actions
            possible_actions = self.get_possible_actions()
            
            # Check if we can grab gold
            if 'grab' in possible_actions:
                return 'grab'
            
            # Check if we should climb out (if we have gold)
            if 'climb' in possible_actions and self.board.agent.has_gold:
                return 'climb'
            
            # Default to exploring
            if 'forward' in possible_actions:
                return 'forward'
            elif 'turn_right' in possible_actions:
                return 'turn_right'
            
            return None
            
        except Exception as e:
            print(f"Error getting enhanced AI suggestion: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """Get game statistics"""
        return {
            'moves_made': len(self.move_history),
            'score': self.score,
            'arrows_used': 1 - self.board.agent.arrows,
            'cells_visited': len(self.board.visited_cells),
            'gold_collected': self.board.agent.has_gold,
            'wumpus_killed': not self.board.wumpus_alive,
            'game_won': self.board.game_won,
            'agent_alive': self.board.agent.alive
        }
    
    def save_game(self, filename: str = None) -> str:
        """Save game state to file"""
        if filename is None:
            filename = f"{self.game_id}.json"
        
        game_data = {
            'game_id': self.game_id,
            'board_size': self.board.size,
            'game_state': self.get_game_state(),
            'move_history': self.get_move_history(),
            'statistics': self.get_statistics()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(game_data, f, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving game: {e}")
            return None
    
    def load_game(self, filename: str) -> bool:
        """Load game state from file"""
        try:
            with open(filename, 'r') as f:
                game_data = json.load(f)
            
            # Reconstruct game state
            self.game_id = game_data['game_id']
            # Additional reconstruction logic would go here
            
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False