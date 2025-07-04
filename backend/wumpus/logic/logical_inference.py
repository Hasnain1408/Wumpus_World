"""
Logical Inference Engine for Wumpus World
Implements logical reasoning for safe navigation
"""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import random


@dataclass
class Knowledge:
    """Knowledge base entry"""
    position: Tuple[int, int]
    facts: Dict[str, bool]
    confidence: float = 1.0
    
    def __str__(self):
        return f"Knowledge({self.position}): {self.facts}"


class LogicalInference:
    """Logical inference engine for Wumpus World"""
    
    def __init__(self, board):
        self.board = board
        self.knowledge_base: Dict[Tuple[int, int], Knowledge] = {}
        self.safe_cells: Set[Tuple[int, int]] = set()
        self.dangerous_cells: Set[Tuple[int, int]] = set()
        self.pit_cells: Set[Tuple[int, int]] = set()
        self.wumpus_cells: Set[Tuple[int, int]] = set()
        self.possible_wumpus: Set[Tuple[int, int]] = set()
        self.possible_pits: Set[Tuple[int, int]] = set()
        self.frontier: Set[Tuple[int, int]] = set()
        
        # Initialize with starting position as safe
        start_pos = (0, board.size - 1)
        self.safe_cells.add(start_pos)
        self.add_knowledge(start_pos, {'safe': True})
    
    def add_knowledge(self, position: Tuple[int, int], facts: Dict[str, bool], confidence: float = 1.0):
        """Add knowledge about a position"""
        if position not in self.knowledge_base:
            self.knowledge_base[position] = Knowledge(position, {}, confidence)
        
        # Update facts
        self.knowledge_base[position].facts.update(facts)
        self.knowledge_base[position].confidence = min(self.knowledge_base[position].confidence, confidence)
    
    def update_knowledge(self, move):
        """Update knowledge base after a move"""
        if not move.result:
            return
        
        current_pos = (self.board.agent.x, self.board.agent.y)
        percepts = move.percepts
        
        # Add current position to visited
        self.safe_cells.add(current_pos)
        
        # Add percept information
        facts = {
            'visited': True,
            'safe': True,
            'breeze': percepts.get('breeze', False),
            'stench': percepts.get('stench', False),
            'glitter': percepts.get('glitter', False)
        }
        
        self.add_knowledge(current_pos, facts)
        
        # Update frontier
        self.update_frontier(current_pos)
        
        # Apply logical rules
        self.apply_logical_rules(current_pos, percepts)
    
    def update_frontier(self, position: Tuple[int, int]):
        """Update frontier cells (unvisited adjacent cells)"""
        x, y = position
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            adj_pos = (adj_x, adj_y)
            
            if (self.board.is_valid_position(adj_x, adj_y) and 
                adj_pos not in self.board.visited_cells and
                adj_pos not in self.dangerous_cells):
                self.frontier.add(adj_pos)
    
    def apply_logical_rules(self, position: Tuple[int, int], percepts: Dict[str, bool]):
        """Apply logical inference rules"""
        x, y = position
        adjacent_cells = self.board.get_adjacent_positions(x, y)
        
        # Rule 1: If no breeze, adjacent cells are safe from pits
        if not percepts.get('breeze', False):
            for adj_pos in adjacent_cells:
                if adj_pos not in self.safe_cells:
                    self.safe_cells.add(adj_pos)
                    self.add_knowledge(adj_pos, {'safe_from_pit': True})
        
        # Rule 2: If no stench, adjacent cells are safe from wumpus
        if not percepts.get('stench', False):
            for adj_pos in adjacent_cells:
                if adj_pos not in self.safe_cells:
                    self.safe_cells.add(adj_pos)
                    self.add_knowledge(adj_pos, {'safe_from_wumpus': True})
        
        # Rule 3: If breeze, at least one adjacent cell has a pit
        if percepts.get('breeze', False):
            unvisited_adjacent = [pos for pos in adjacent_cells if pos not in self.board.visited_cells]
            if unvisited_adjacent:
                for adj_pos in unvisited_adjacent:
                    self.possible_pits.add(adj_pos)
                    self.add_knowledge(adj_pos, {'possible_pit': True}, 0.5)
        
        # Rule 4: If stench, at least one adjacent cell has wumpus
        if percepts.get('stench', False) and self.board.wumpus_alive:
            unvisited_adjacent = [pos for pos in adjacent_cells if pos not in self.board.visited_cells]
            if unvisited_adjacent:
                for adj_pos in unvisited_adjacent:
                    self.possible_wumpus.add(adj_pos)
                    self.add_knowledge(adj_pos, {'possible_wumpus': True}, 0.5)
        
        # Advanced reasoning
        self.apply_advanced_reasoning()
    
    def apply_advanced_reasoning(self):
        """Apply more complex logical reasoning"""
        # Constraint satisfaction for pit locations
        self.resolve_pit_constraints()
        
        # Constraint satisfaction for wumpus location
        self.resolve_wumpus_constraints()
        
        # Mark definitively safe cells
        self.mark_safe_cells()
    
    def resolve_pit_constraints(self):
        """Resolve pit location constraints"""
        # For each cell with breeze, check if we can narrow down pit locations
        for pos, knowledge in self.knowledge_base.items():
            if knowledge.facts.get('breeze', False):
                x, y = pos
                adjacent_cells = self.board.get_adjacent_positions(x, y)
                
                # Find unvisited adjacent cells
                unvisited_adjacent = [adj for adj in adjacent_cells if adj not in self.board.visited_cells]
                safe_adjacent = [adj for adj in adjacent_cells if adj in self.safe_cells]
                
                # If only one unvisited adjacent cell, it must have a pit
                if len(unvisited_adjacent) == 1:
                    pit_pos = unvisited_adjacent[0]
                    self.pit_cells.add(pit_pos)
                    self.dangerous_cells.add(pit_pos)
                    self.add_knowledge(pit_pos, {'pit': True, 'dangerous': True})
    
    def resolve_wumpus_constraints(self):
        """Resolve wumpus location constraints"""
        if not self.board.wumpus_alive:
            return
        
        # For each cell with stench, check if we can narrow down wumpus location
        for pos, knowledge in self.knowledge_base.items():
            if knowledge.facts.get('stench', False):
                x, y = pos
                adjacent_cells = self.board.get_adjacent_positions(x, y)
                
                # Find unvisited adjacent cells
                unvisited_adjacent = [adj for adj in adjacent_cells if adj not in self.board.visited_cells]
                
                # If only one unvisited adjacent cell, it must have wumpus
                if len(unvisited_adjacent) == 1:
                    wumpus_pos = unvisited_adjacent[0]
                    self.wumpus_cells.add(wumpus_pos)
                    self.dangerous_cells.add(wumpus_pos)
                    self.add_knowledge(wumpus_pos, {'wumpus': True, 'dangerous': True})
    
    def mark_safe_cells(self):
        """Mark cells as definitively safe"""
        for pos in self.frontier:
            if pos not in self.dangerous_cells and pos not in self.possible_pits and pos not in self.possible_wumpus:
                self.safe_cells.add(pos)
                self.add_knowledge(pos, {'safe': True})
    
    def get_safe_cells(self) -> List[Tuple[int, int]]:
        """Get list of known safe cells"""
        return list(self.safe_cells)
    
    def get_dangerous_cells(self) -> List[Tuple[int, int]]:
        """Get list of known dangerous cells"""
        return list(self.dangerous_cells)
    
    def get_frontier_cells(self) -> List[Tuple[int, int]]:
        """Get list of frontier cells"""
        return list(self.frontier)
    
    def is_safe(self, position: Tuple[int, int]) -> bool:
        """Check if a position is known to be safe"""
        return position in self.safe_cells
    
    def is_dangerous(self, position: Tuple[int, int]) -> bool:
        """Check if a position is known to be dangerous"""
        return position in self.dangerous_cells
    
    def calculate_risk(self, position: Tuple[int, int]) -> float:
        """Calculate risk score for a position (0 = safe, 1 = definitely dangerous)"""
        if position in self.safe_cells:
            return 0.0
        if position in self.dangerous_cells:
            return 1.0
        if position in self.possible_pits or position in self.possible_wumpus:
            return 0.5
        return 0.2  # Unknown cells have low risk
    
    def suggest_next_move(self) -> Optional[str]:
        """Suggest the best next move based on current knowledge"""
        # First, try to find a safe move
        safe_move = self.find_best_safe_move()
        if safe_move:
            return safe_move
        
        # If no safe move, try the least risky move
        risky_move = self.find_least_risky_move()
        if risky_move:
            return risky_move
        
        # If agent has arrow and can shoot wumpus, do it
        if self.should_shoot():
            return 'shoot'
        
        # Last resort: random exploration
        return self.explore_unknown()
    
    def find_best_safe_move(self) -> Optional[str]:
        """Find the best safe move to make"""
        agent_pos = (self.board.agent.x, self.board.agent.y)
        
        # Get safe adjacent cells
        safe_adjacent = []
        for adj_pos in self.board.get_adjacent_positions(agent_pos[0], agent_pos[1]):
            if adj_pos in self.safe_cells and adj_pos not in self.board.visited_cells:
                safe_adjacent.append(adj_pos)
        
        if not safe_adjacent:
            return None
        
        # Choose the closest safe cell
        best_cell = min(safe_adjacent, key=lambda pos: abs(pos[0] - agent_pos[0]) + abs(pos[1] - agent_pos[1]))
        
        # Get direction to move to that cell
        direction = self.get_direction_to_position(agent_pos, best_cell)
        
        # Check if we need to turn
        if direction != self.board.agent.direction:
            return self.get_turn_to_direction(self.board.agent.direction, direction)
        else:
            return 'forward'
    
    def find_least_risky_move(self) -> Optional[str]:
        """Find the least risky move when no safe moves available"""
        agent_pos = (self.board.agent.x, self.board.agent.y)
        
        # Get all possible moves with their risk scores
        moves_with_risk = []
        for adj_pos in self.board.get_adjacent_positions(agent_pos[0], agent_pos[1]):
            if adj_pos not in self.board.visited_cells:
                risk = self.calculate_risk(adj_pos)
                moves_with_risk.append((adj_pos, risk))
        
        if not moves_with_risk:
            return None
        
        # Choose the move with lowest risk
        best_move = min(moves_with_risk, key=lambda x: x[1])
        best_cell = best_move[0]
        
        # Get direction to move to that cell
        direction = self.get_direction_to_position(agent_pos, best_cell)
        
        # Check if we need to turn
        if direction != self.board.agent.direction:
            return self.get_turn_to_direction(self.board.agent.direction, direction)
        else:
            return 'forward'
    
    def should_shoot(self) -> bool:
        """Check if agent should shoot an arrow"""
        if self.board.agent.arrows <= 0:
            return False
        
        # Check if wumpus is in shooting direction
        agent_pos = (self.board.agent.x, self.board.agent.y)
        direction = self.board.agent.direction
        
        return self.is_wumpus_in_direction(agent_pos, direction)
    
    def explore_unknown(self) -> str:
        """Explore unknown areas when no better option"""
        # Try to move to an unvisited cell
        agent_pos = (self.board.agent.x, self.board.agent.y)
        
        for adj_pos in self.board.get_adjacent_positions(agent_pos[0], agent_pos[1]):
            if adj_pos not in self.board.visited_cells:
                direction = self.get_direction_to_position(agent_pos, adj_pos)
                if direction != self.board.agent.direction:
                    return self.get_turn_to_direction(self.board.agent.direction, direction)
                else:
                    return 'forward'
        
        # If no unvisited adjacent cells, just turn around
        return 'turn_right'
    
    def get_direction_to_position(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """Get direction to move from one position to another"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        if dx > 0:
            return 'right'
        elif dx < 0:
            return 'left'
        elif dy > 0:
            return 'down'
        elif dy < 0:
            return 'up'
        else:
            return 'right'  # Default
    
    def get_turn_to_direction(self, current_direction: str, target_direction: str) -> str:
        """Get the turn command to face target direction"""
        directions = ['right', 'up', 'left', 'down']
        current_index = directions.index(current_direction)
        target_index = directions.index(target_direction)
        
        # Calculate the shortest turn
        diff = (target_index - current_index) % 4
        
        if diff == 1:
            return 'turn_right'
        elif diff == 3:
            return 'turn_left'
        else:
            return 'turn_right'  # Default to right turn
    
    def is_wumpus_in_direction(self, agent_pos: Tuple[int, int], direction: str) -> bool:
        """Check if wumpus is in the given direction from agent"""
        x, y = agent_pos
        
        # Check all cells in the direction
        while True:
            if direction == 'right':
                x += 1
            elif direction == 'left':
                x -= 1
            elif direction == 'up':
                y -= 1
            elif direction == 'down':
                y += 1
            
            if not self.board.is_valid_position(x, y):
                break
            
            if (x, y) in self.wumpus_cells:
                return True
        
        return False
    
    def get_knowledge_summary(self) -> Dict:
        """Get summary of current knowledge"""
        return {
            'safe_cells': len(self.safe_cells),
            'dangerous_cells': len(self.dangerous_cells),
            'frontier_cells': len(self.frontier),
            'possible_pits': len(self.possible_pits),
            'possible_wumpus': len(self.possible_wumpus),
            'wumpus_alive': self.board.wumpus_alive
        }
    
    def reset(self):
        """Reset the inference engine"""
        self.knowledge_base.clear()
        self.safe_cells.clear()
        self.dangerous_cells.clear()
        self.pit_cells.clear()
        self.wumpus_cells.clear()
        self.possible_wumpus.clear()
        self.possible_pits.clear()
        self.frontier.clear()
        
        # Initialize with starting position as safe
        start_pos = (0, self.board.size - 1)
        self.safe_cells.add(start_pos)
        self.add_knowledge(start_pos, {'safe': True})
    
    def get_best_move(self) -> Optional[str]:
        """Get the best move based on current knowledge"""
        return self.suggest_next_move()
    
    def update_from_perceptions(self):
        """Update knowledge based on current perceptions"""
        agent_pos = (self.board.agent.x, self.board.agent.y)
        percepts = self.board.get_percepts()
        
        # Update knowledge with current percepts
        facts = {
            'visited': True,
            'safe': True,
            'breeze': percepts.get('breeze', False),
            'stench': percepts.get('stench', False),
            'glitter': percepts.get('glitter', False)
        }
        
        self.add_knowledge(agent_pos, facts)
        self.apply_logical_rules(agent_pos, percepts)
    
    def get_safest_move(self) -> Optional[str]:
        """Get the safest possible move"""
        return self.find_best_safe_move()
    
    def calculate_risk_score(self, position: Tuple[int, int]) -> float:
        """Calculate detailed risk score for a position"""
        return self.calculate_risk(position)
    
    def should_shoot_wumpus(self) -> Optional[str]:
        """Check if agent should shoot wumpus and return direction"""
        if self.should_shoot():
            return 'shoot'
        return None
    
    def get_move_toward_start(self) -> Optional[str]:
        """Get move toward starting position"""
        agent_pos = (self.board.agent.x, self.board.agent.y)
        start_pos = (0, self.board.size - 1)
        
        if agent_pos == start_pos:
            return 'climb'
        
        # Move toward start position
        direction = self.get_direction_to_cell(agent_pos, start_pos)
        if direction:
            if direction != self.board.agent.direction:
                return self.get_turn_to_direction(self.board.agent.direction, direction)
            else:
                return 'forward'
        
        return None
    
    def get_direction_to_cell(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Optional[str]:
        """Get direction to move toward a target cell"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        # Choose the direction with largest difference
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'down' if dy > 0 else 'up'
    
    def get_adjacent_cells(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get list of adjacent cells"""
        return self.board.get_adjacent_positions(position[0], position[1])
