"""
Move and MoveResult classes for Wumpus World
"""

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Move:
    """Represents a single move in the game"""
    action: str
    direction: Optional[str] = None
    from_x: int = 0
    from_y: int = 0
    to_x: Optional[int] = None
    to_y: Optional[int] = None
    result: bool = False
    percepts: Dict[str, bool] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.percepts is None:
            self.percepts = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert move to dictionary"""
        return {
            'action': self.action,
            'direction': self.direction,
            'from_position': {'x': self.from_x, 'y': self.from_y},
            'to_position': {'x': self.to_x, 'y': self.to_y} if self.to_x is not None else None,
            'result': self.result,
            'percepts': self.percepts,
            'timestamp': self.timestamp
        }
    
    def __str__(self):
        return f"Move: {self.action} at ({self.from_x}, {self.from_y}) -> Success: {self.result}"


@dataclass
class MoveResult:
    """Result of a move attempt"""
    success: bool
    message: str
    game_state: Dict[str, Any]
    percepts: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.percepts is None:
            self.percepts = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'message': self.message,
            'game_state': self.game_state,
            'percepts': self.percepts
        }


class MoveValidator:
    """Validates moves before execution"""
    
    def __init__(self, board):
        self.board = board
    
    def validate_move(self, action: str, direction: str = None) -> bool:
        """Validate if a move is legal"""
        if self.board.game_over:
            return False
        
        if action == 'forward':
            return self.validate_forward_move()
        elif action in ['turn_left', 'turn_right']:
            return True
        elif action == 'shoot':
            return self.board.agent.arrows > 0
        elif action == 'grab':
            return self.validate_grab()
        elif action == 'climb':
            return self.validate_climb()
        
        return False
    
    def validate_forward_move(self) -> bool:
        """Validate forward movement"""
        agent = self.board.agent
        new_x, new_y = agent.x, agent.y
        
        if agent.direction == 'right':
            new_x += 1
        elif agent.direction == 'left':
            new_x -= 1
        elif agent.direction == 'up':
            new_y -= 1
        elif agent.direction == 'down':
            new_y += 1
        
        return self.board.is_valid_position(new_x, new_y)
    
    def validate_grab(self) -> bool:
        """Validate gold grabbing"""
        cell = self.board.get_cell(self.board.agent.x, self.board.agent.y)
        return cell and cell.gold and not self.board.agent.has_gold
    
    def validate_climb(self) -> bool:
        """Validate climbing out"""
        agent = self.board.agent
        return agent.x == 0 and agent.y == self.board.size - 1


class MoveExecutor:
    """Executes validated moves"""
    
    def __init__(self, board):
        self.board = board
        self.validator = MoveValidator(board)
    
    def execute_move(self, move: Move) -> MoveResult:
        """Execute a move and return result"""
        if not self.validator.validate_move(move.action, move.direction):
            return MoveResult(False, "Invalid move", self.board.get_board_state())
        
        # Store original position
        original_x, original_y = self.board.agent.x, self.board.agent.y
        
        # Execute the move
        success = False
        message = ""
        
        if move.action == 'forward':
            success = self.execute_forward()
            message = "Moved forward" if success else "Cannot move forward"
            
        elif move.action == 'turn_left':
            success = self.execute_turn_left()
            message = "Turned left"
            
        elif move.action == 'turn_right':
            success = self.execute_turn_right()
            message = "Turned right"
            
        elif move.action == 'shoot':
            success = self.execute_shoot()
            message = "Shot arrow" if success else "No arrows left"
            
        elif move.action == 'grab':
            success = self.execute_grab()
            message = "Grabbed gold" if success else "No gold here"
            
        elif move.action == 'climb':
            success = self.execute_climb()
            message = "Climbed out" if success else "Can only climb out from starting position"
        
        # Update move with result
        move.result = success
        move.to_x = self.board.agent.x
        move.to_y = self.board.agent.y
        move.percepts = self.board.get_percepts()
        
        return MoveResult(success, message, self.board.get_board_state(), move.percepts)
    
    def execute_forward(self) -> bool:
        """Execute forward movement"""
        return self.board.move_agent(self.board.agent.direction)
    
    def execute_turn_left(self) -> bool:
        """Execute left turn"""
        directions = ['right', 'up', 'left', 'down']
        current_index = directions.index(self.board.agent.direction)
        new_direction = directions[(current_index - 1) % 4]
        self.board.turn_agent(new_direction)
        return True
    
    def execute_turn_right(self) -> bool:
        """Execute right turn"""
        directions = ['right', 'up', 'left', 'down']
        current_index = directions.index(self.board.agent.direction)
        new_direction = directions[(current_index + 1) % 4]
        self.board.turn_agent(new_direction)
        return True
    
    def execute_shoot(self) -> bool:
        """Execute arrow shooting"""
        return self.board.shoot_arrow(self.board.agent.direction)
    
    def execute_grab(self) -> bool:
        """Execute gold grabbing"""
        cell = self.board.get_cell(self.board.agent.x, self.board.agent.y)
        if cell and cell.gold and not self.board.agent.has_gold:
            self.board.agent.has_gold = True
            cell.gold = False
            cell.glitter = False
            return True
        return False
    
    def execute_climb(self) -> bool:
        """Execute climbing out"""
        # Can only climb out from starting position
        if self.board.agent.x == 0 and self.board.agent.y == self.board.size - 1:
            if self.board.agent.has_gold:
                self.board.game_won = True
            self.board.game_over = True
            return True
        return False


class MoveHistory:
    """Manages move history and analysis"""
    
    def __init__(self):
        self.moves: List[Move] = []
        self.move_count = 0
    
    def add_move(self, move: Move):
        """Add a move to history"""
        self.moves.append(move)
        self.move_count += 1
    
    def get_last_move(self) -> Optional[Move]:
        """Get the last move made"""
        return self.moves[-1] if self.moves else None
    
    def get_moves_by_action(self, action: str) -> List[Move]:
        """Get all moves of a specific action type"""
        return [move for move in self.moves if move.action == action]
    
    def get_move_summary(self) -> Dict[str, int]:
        """Get summary of moves made"""
        summary = {}
        for move in self.moves:
            summary[move.action] = summary.get(move.action, 0) + 1
        return summary
    
    def get_positions_visited(self) -> List[tuple]:
        """Get all unique positions visited"""
        positions = set()
        for move in self.moves:
            positions.add((move.from_x, move.from_y))
            if move.to_x is not None and move.to_y is not None:
                positions.add((move.to_x, move.to_y))
        return list(positions)
    
    def analyze_efficiency(self) -> Dict[str, Any]:
        """Analyze move efficiency"""
        if not self.moves:
            return {'efficiency': 0, 'redundant_moves': 0, 'exploration_rate': 0}
        
        # Count unique positions visited
        unique_positions = len(self.get_positions_visited())
        
        # Calculate exploration rate
        total_cells = 100  # 10x10 board
        exploration_rate = unique_positions / total_cells
        
        # Count redundant moves (returning to same position)
        position_counts = {}
        redundant_moves = 0
        
        for move in self.moves:
            pos = (move.from_x, move.from_y)
            position_counts[pos] = position_counts.get(pos, 0) + 1
            if position_counts[pos] > 1:
                redundant_moves += 1
        
        efficiency = 1 - (redundant_moves / len(self.moves))
        
        return {
            'efficiency': efficiency,
            'redundant_moves': redundant_moves,
            'exploration_rate': exploration_rate,
            'unique_positions': unique_positions,
            'total_moves': len(self.moves)
        }
