"""
Wumpus World Board Logic
Handles the game board state and cell management
"""

import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Cell:
    """Represents a single cell in the Wumpus World board"""
    x: int
    y: int
    wumpus: bool = False
    pit: bool = False
    gold: bool = False
    agent: bool = False
    breeze: bool = False
    stench: bool = False
    glitter: bool = False
    visited: bool = False
    safe: bool = False
    
    def __str__(self):
        return f"Cell({self.x}, {self.y})"


@dataclass
class AgentState:
    """Represents the agent's current state"""
    x: int = 0
    y: int = 9  # Bottom-left corner
    direction: str = 'right'  # right, up, left, down
    arrows: int = 1
    has_gold: bool = False
    alive: bool = True
    
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)


class WumpusBoard:
    """Main board class for Wumpus World"""
    
    def __init__(self, size: int = 10):
        self.size = size
        self.board: List[List[Cell]] = []
        self.agent = AgentState()
        self.wumpus_alive = True
        self.game_over = False
        self.game_won = False
        self.visited_cells: Set[Tuple[int, int]] = set()
        self.safe_cells: Set[Tuple[int, int]] = set()
        self.danger_cells: Set[Tuple[int, int]] = set()
        
        self.initialize_board()
        
    def initialize_board(self):
        """Initialize the board with empty cells"""
        self.board = []
        for y in range(self.size):
            row = []
            for x in range(self.size):
                cell = Cell(x, y)
                row.append(cell)
            self.board.append(row)
        
        # Place agent at starting position
        self.board[self.agent.y][self.agent.x].agent = True
        self.board[self.agent.y][self.agent.x].visited = True
        self.visited_cells.add((self.agent.x, self.agent.y))
        self.safe_cells.add((self.agent.x, self.agent.y))
    
    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Get cell at given coordinates"""
        if self.is_valid_position(x, y):
            return self.board[y][x]
        return None
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within board bounds"""
        return 0 <= x < self.size and 0 <= y < self.size
    
    def get_adjacent_positions(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get all valid adjacent positions"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        adjacent = []
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if self.is_valid_position(new_x, new_y):
                adjacent.append((new_x, new_y))
        
        return adjacent
    
    def place_wumpus(self, x: int, y: int) -> bool:
        """Place wumpus at given position"""
        if not self.is_valid_position(x, y):
            return False
        
        # Can't place wumpus at agent starting position
        if x == 0 and y == self.size - 1:
            return False
        
        cell = self.get_cell(x, y)
        if cell and not cell.pit and not cell.gold:
            cell.wumpus = True
            self.generate_stenches()
            return True
        return False
    
    def place_gold(self, x: int, y: int) -> bool:
        """Place gold at given position"""
        if not self.is_valid_position(x, y):
            return False
        
        cell = self.get_cell(x, y)
        if cell and not cell.wumpus and not cell.pit:
            cell.gold = True
            cell.glitter = True
            return True
        return False
    
    def place_pit(self, x: int, y: int) -> bool:
        """Place pit at given position"""
        if not self.is_valid_position(x, y):
            return False
        
        # Can't place pit at agent starting position
        if x == 0 and y == self.size - 1:
            return False
        
        cell = self.get_cell(x, y)
        if cell and not cell.wumpus and not cell.gold:
            cell.pit = True
            self.generate_breezes()
            return True
        return False
    
    def generate_breezes(self):
        """Generate breezes around all pits"""
        # First, clear existing breezes
        for y in range(self.size):
            for x in range(self.size):
                if not self.board[y][x].pit:
                    self.board[y][x].breeze = False
        
        # Generate new breezes
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x].pit:
                    for adj_x, adj_y in self.get_adjacent_positions(x, y):
                        self.board[adj_y][adj_x].breeze = True
    
    def generate_stenches(self):
        """Generate stenches around the wumpus"""
        # First, clear existing stenches
        for y in range(self.size):
            for x in range(self.size):
                self.board[y][x].stench = False
        
        # Generate new stenches if wumpus is alive
        if self.wumpus_alive:
            for y in range(self.size):
                for x in range(self.size):
                    if self.board[y][x].wumpus:
                        for adj_x, adj_y in self.get_adjacent_positions(x, y):
                            self.board[adj_y][adj_x].stench = True
    
    def move_agent(self, direction: str) -> bool:
        """Move agent in given direction"""
        if self.game_over:
            return False
        
        # Clear current position
        self.board[self.agent.y][self.agent.x].agent = False
        
        # Calculate new position
        new_x, new_y = self.agent.x, self.agent.y
        
        if direction == 'right':
            new_x += 1
        elif direction == 'left':
            new_x -= 1
        elif direction == 'up':
            new_y -= 1
        elif direction == 'down':
            new_y += 1
        
        # Check if move is valid
        if not self.is_valid_position(new_x, new_y):
            # Put agent back
            self.board[self.agent.y][self.agent.x].agent = True
            return False
        
        # Update agent position
        self.agent.x = new_x
        self.agent.y = new_y
        
        # Place agent at new position
        cell = self.board[new_y][new_x]
        cell.agent = True
        cell.visited = True
        
        # Add to visited cells
        self.visited_cells.add((new_x, new_y))
        
        # Check for hazards
        if cell.pit:
            self.agent.alive = False
            self.game_over = True
            return True
        
        if cell.wumpus and self.wumpus_alive:
            self.agent.alive = False
            self.game_over = True
            return True
        
        # Check for gold
        if cell.gold and not self.agent.has_gold:
            self.agent.has_gold = True
            cell.gold = False
            cell.glitter = False
        
        return True
    
    def turn_agent(self, direction: str):
        """Turn agent to face given direction"""
        if direction in ['right', 'up', 'left', 'down']:
            self.agent.direction = direction
        else:
            print(f"Invalid direction: {direction}")
    
    def shoot_arrow(self, direction: str) -> bool:
        """Shoot arrow in given direction"""
        if self.agent.arrows <= 0:
            return False
        
        self.agent.arrows -= 1
        
        # Calculate arrow path
        arrow_x, arrow_y = self.agent.x, self.agent.y
        
        while True:
            # Move arrow
            if direction == 'right':
                arrow_x += 1
            elif direction == 'left':
                arrow_x -= 1
            elif direction == 'up':
                arrow_y -= 1
            elif direction == 'down':
                arrow_y += 1
            
            # Check bounds
            if not self.is_valid_position(arrow_x, arrow_y):
                break
            
            # Check for wumpus
            if self.board[arrow_y][arrow_x].wumpus and self.wumpus_alive:
                self.wumpus_alive = False
                self.board[arrow_y][arrow_x].wumpus = False
                self.generate_stenches()  # Remove stenches
                return True
        
        return False
    
    def get_percepts(self) -> Dict[str, bool]:
        """Get current percepts at agent position"""
        cell = self.board[self.agent.y][self.agent.x]
        
        return {
            'breeze': cell.breeze,
            'stench': cell.stench,
            'glitter': cell.glitter,
            'bump': False,  # Will be set by movement logic
            'scream': False  # Will be set by arrow logic
        }
    
    def is_game_won(self) -> bool:
        """Check if game is won (agent has gold and is at starting position)"""
        return (self.agent.has_gold and 
                self.agent.x == 0 and 
                self.agent.y == self.size - 1 and
                self.agent.alive)
    
    def get_board_state(self) -> Dict:
        """Get current board state as dictionary"""
        board_data = []
        for y in range(self.size):
            row = []
            for x in range(self.size):
                cell = self.board[y][x]
                cell_data = {
                    'x': x,
                    'y': y,
                    'wumpus': cell.wumpus,
                    'pit': cell.pit,
                    'gold': cell.gold,
                    'agent': cell.agent,
                    'breeze': cell.breeze,
                    'stench': cell.stench,
                    'glitter': cell.glitter,
                    'visited': cell.visited,
                    'safe': cell.safe
                }
                row.append(cell_data)
            board_data.append(row)
        
        return {
            'board': board_data,
            'agent': {
                'x': self.agent.x,
                'y': self.agent.y,
                'direction': self.agent.direction,
                'arrows': self.agent.arrows,
                'has_gold': self.agent.has_gold,
                'alive': self.agent.alive
            },
            'wumpus_alive': self.wumpus_alive,
            'game_over': self.game_over,
            'game_won': self.is_game_won()
        }
    
    def load_environment(self, environment: Dict) -> bool:
        """Load environment configuration"""
        try:
            # Clear existing environment
            for y in range(self.size):
                for x in range(self.size):
                    cell = self.board[y][x]
                    cell.wumpus = False
                    cell.pit = False
                    cell.gold = False
                    cell.breeze = False
                    cell.stench = False
                    cell.glitter = False
            
            # Place wumpus
            if 'wumpus' in environment:
                wumpus_pos = environment['wumpus']
                self.place_wumpus(wumpus_pos['x'], wumpus_pos['y'])
            
            # Place gold
            if 'gold' in environment:
                gold_pos = environment['gold']
                self.place_gold(gold_pos['x'], gold_pos['y'])
            
            # Place pits
            if 'pits' in environment:
                for pit_pos in environment['pits']:
                    self.place_pit(pit_pos['x'], pit_pos['y'])
            
            return True
            
        except Exception as e:
            print(f"Error loading environment: {e}")
            return False
