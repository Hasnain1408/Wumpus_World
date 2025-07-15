"""
Fixed Logical Inference Engine for Wumpus World
FIXED: Prevents agent from moving to cells that are not completely safe
"""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import itertools


@dataclass
class Knowledge:
    """Knowledge base entry"""
    position: Tuple[int, int]
    facts: Dict[str, bool]
    confidence: float = 1.0
    
    def __str__(self):
        return f"Knowledge({self.position}): {self.facts}"


class LogicalInference:
    """Logical inference engine with proper constraint satisfaction"""
    debug = True

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
        
        # Track cells that are safe from specific dangers
        self.safe_from_pits: Set[Tuple[int, int]] = set()
        self.safe_from_wumpus: Set[Tuple[int, int]] = set()
        
        # Constraint tracking
        self.breeze_constraints: Set[Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]] = set()
        self.stench_constraints: Set[Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]] = set()
        
        # Initialize with starting position as safe
        start_pos = (0, board.size - 1)
        self.safe_cells.add(start_pos)
        self.safe_from_pits.add(start_pos)
        self.safe_from_wumpus.add(start_pos)
        self.add_knowledge(start_pos, {'safe': True, 'visited': True})
        
        # Debug mode
        self.debug = True
    
    def add_knowledge(self, position: Tuple[int, int], facts: Dict[str, bool], confidence: float = 1.0):
        """Add knowledge about a position"""
        if position not in self.knowledge_base:
            self.knowledge_base[position] = Knowledge(position, {}, confidence)
        
        # Update facts
        self.knowledge_base[position].facts.update(facts)
        self.knowledge_base[position].confidence = min(self.knowledge_base[position].confidence, confidence)
        
        if self.debug:
            #print(f"logical_inference.add_knowledge() ->  ")
            #print(f"Added knowledge: {position} -> {facts}")
            pass
    def update_knowledge(self, move):
        """Update knowledge base after a move"""
        if not move or not hasattr(move, 'result') or not move.result:
            return
        
        current_pos = (self.board.agent.x, self.board.agent.y)
        percepts = getattr(move, 'percepts', {})
        
        # Ensure we have the current percepts
        if not percepts:
            percepts = self.board.get_percepts()
        
        if self.debug:
            #print(f"logical_inference.update_knowledge() -> ")
            #print(f"Updating knowledge for position {current_pos} with percepts: {percepts}")
            #print(f"Agent direction: {self.board.agent.direction}")
            pass
        # Add current position to visited and safe
        self.safe_cells.add(current_pos)
        self.safe_from_pits.add(current_pos)
        self.safe_from_wumpus.add(current_pos)
        
        # Add percept information
        facts = {
            'visited': True,
            'safe': True,
            'breeze': percepts.get('breeze', False),
            'stench': percepts.get('stench', False),
            'glitter': percepts.get('glitter', False)
        }
        
        self.add_knowledge(current_pos, facts)
        
        # Update frontier BEFORE applying logical rules
        self.update_frontier()
        
        # Apply logical rules
        self.apply_logical_rules(current_pos, percepts)
        
        # Perform constraint satisfaction
        self.solve_constraints()
    
    def update_frontier(self):
        """Update frontier cells (unvisited adjacent cells)"""
        self.frontier.clear()
        
        # Get all adjacent cells to visited cells
        for visited_pos in self.board.visited_cells:
            x, y = visited_pos
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                adj_x, adj_y = x + dx, y + dy
                adj_pos = (adj_x, adj_y)
                
                if (self.board.is_valid_position(adj_x, adj_y) and 
                    adj_pos not in self.board.visited_cells and
                    adj_pos not in self.dangerous_cells):
                    self.frontier.add(adj_pos)
                    if self.debug:
                        #print(f"logical_inference.update_frontier() -> {adj_pos} - added to frontier")
                        pass
        if self.debug:
            pass
            #print(f"-------------------------------------Current frontier-----------------------: {self.frontier}")

    def apply_logical_rules(self, position: Tuple[int, int], percepts: Dict[str, bool]):
        """Apply logical inference rules"""
        x, y = position
        adjacent_cells = self.board.get_adjacent_positions(x, y)
        
        if self.debug:
            pass
            #print(f"-----------------------   logical_inference.apply_logical_rules() ->    ---------------------------")
            #print(f"Applying logical rules at {position}")
            #print(f"Adjacent cells: {adjacent_cells}")
        
        # Rule 1: If no breeze, adjacent cells are safe from pits
        if not percepts.get('breeze', False):
            #print(f"   Rule 1 -> ")
            pass
            for adj_pos in adjacent_cells:
                if adj_pos not in self.board.visited_cells:
                    self.safe_from_pits.add(adj_pos)
                    self.add_knowledge(adj_pos, {'safe_from_pit': True})
                    self.possible_pits.discard(adj_pos)
                    if self.debug:
                        pass
                        #print(f"No breeze detected - marking {adj_pos} as safe from pits")
        
        # Rule 2: If no stench, adjacent cells are safe from wumpus
        if not percepts.get('stench', False):
            #print(f"   Rule 2 -> ")
            for adj_pos in adjacent_cells:
                if adj_pos not in self.board.visited_cells:
                    self.safe_from_wumpus.add(adj_pos)
                    self.add_knowledge(adj_pos, {'safe_from_wumpus': True})
                    self.possible_wumpus.discard(adj_pos)
                    if self.debug:
                        pass
                        #print(f"No stench detected - marking {adj_pos} as safe from wumpus")
        
        # Rule 3: If breeze, add constraint that at least one adjacent cell has a pit
        if percepts.get('breeze', False):
            #print(f"   Rule 3 -> ")
            unvisited_adjacent = [pos for pos in adjacent_cells if pos not in self.board.visited_cells]
            unvisited_adjacent = [pos for pos in unvisited_adjacent if pos not in self.safe_from_pits]
            
            if unvisited_adjacent:
                constraint = (position, tuple(sorted(unvisited_adjacent)))
                if constraint not in self.breeze_constraints:
                    if self.debug:
                        pass
                        #print(f"Breeze detected - adding NEW pit constraint for {unvisited_adjacent}")
                    
                    # Add to possible pits
                    for adj_pos in unvisited_adjacent:
                        self.possible_pits.add(adj_pos)
                        self.add_knowledge(adj_pos, {'possible_pit': True}, 0.5)
                    
                    # Add constraint
                    self.breeze_constraints.add(constraint)
                else:
                    if self.debug:
                        #print(f"Breeze constraint already exists for {position}")
                        pass
        
        # Rule 4: If stench, add constraint that at least one adjacent cell has wumpus
        if percepts.get('stench', False) and self.board.wumpus_alive:
            #print(f"   Rule 4 -> ")
            unvisited_adjacent = [pos for pos in adjacent_cells if pos not in self.board.visited_cells]
            unvisited_adjacent = [pos for pos in unvisited_adjacent if pos not in self.safe_from_wumpus]
            
            if unvisited_adjacent:
                constraint = (position, tuple(sorted(unvisited_adjacent)))
                if constraint not in self.stench_constraints:
                    if self.debug:
                        #print(f"Stench detected - adding NEW wumpus constraint for {unvisited_adjacent}")
                        pass
                    
                    # Add to possible wumpus
                    for adj_pos in unvisited_adjacent:
                        self.possible_wumpus.add(adj_pos)
                        self.add_knowledge(adj_pos, {'possible_wumpus': True}, 0.5)
                    
                    # Add constraint
                    self.stench_constraints.add(constraint)
                else:
                    if self.debug:
                        #print(f"Stench constraint already exists for {position}")
                        pass
    
    def solve_constraints(self):
        """Solve constraints using constraint satisfaction"""
        if self.debug:
            #print("logical_inference.solve_constraints() -> ")
            pass
        
        # Solve pit constraints
        self.solve_pit_constraints()
        
        # Solve wumpus constraints
        self.solve_wumpus_constraints()
        
        # Update safe cells
        self.update_safe_cells()
    
    def solve_pit_constraints(self):
        """Solve pit location constraints using constraint satisfaction"""
        #print(f"logical_inference.solve_pit_constraints() -> ")
        if not self.breeze_constraints:
            return
        
        if self.debug:
            pass
            #print(f"Solving {len(self.breeze_constraints)} pit constraints")
        
        # Get all possible pit locations
        all_possible_pits = set()
        for _, adjacent_cells in self.breeze_constraints:
            all_possible_pits.update(adjacent_cells)

        #print(f"---------Breeze Constraints--------- : {self.breeze_constraints}")
        #print(f"------Possible pit locations before filtering ---- : {all_possible_pits}")
        
        # Remove cells that are already known to be safe from pits
        all_possible_pits = {pos for pos in all_possible_pits if pos not in self.safe_from_pits}
        #print(f"------Possible pit locations after filtering ---- : {all_possible_pits}")
        
        if not all_possible_pits:
            return
        
        # Try all possible combinations of pit placements
        valid_assignments = []
        
        # For efficiency, limit the search space
        max_pits = min(len(all_possible_pits), 3)  # Reasonable limit
        
        for num_pits in range(1, max_pits + 1):
            for pit_combination in itertools.combinations(all_possible_pits, num_pits):
                if self.is_valid_pit_assignment(set(pit_combination)):
                    valid_assignments.append(set(pit_combination))
        
        if self.debug:
            #print(f"Found {len(valid_assignments)} valid pit assignments")
            pass
        
        # Find cells that must be pits (in all valid assignments)
        if valid_assignments:
            definite_pits = set.intersection(*valid_assignments)
            for pit_pos in definite_pits:
                self.pit_cells.add(pit_pos)
                self.dangerous_cells.add(pit_pos)
                self.add_knowledge(pit_pos, {'pit': True, 'dangerous': True})
                if self.debug:
                    pass
                    #print(f"Definite pit found at {pit_pos}")
            
            # Find cells that cannot be pits (not in any valid assignment)
            all_in_assignments = set.union(*valid_assignments) if valid_assignments else set()
            safe_from_pits = all_possible_pits - all_in_assignments
            for safe_pos in safe_from_pits:
                self.safe_from_pits.add(safe_pos)
                self.add_knowledge(safe_pos, {'safe_from_pit': True})
                self.possible_pits.discard(safe_pos)
                if self.debug:
                    pass
                    #print(f"Cell {safe_pos} is safe from pits")
    
    def solve_wumpus_constraints(self):
        """Solve wumpus location constraints"""
        #print("logical_inference.solve_wumpus_constraints() -> ")
        if not self.stench_constraints or not self.board.wumpus_alive:
            return
        
        if self.debug:
            #print(f"Solving {len(self.stench_constraints)} wumpus constraints")
            pass
        
        # Get all possible wumpus locations
        all_possible_wumpus = set()
        for _, adjacent_cells in self.stench_constraints:
            all_possible_wumpus.update(adjacent_cells)
        
        # Remove cells that are already known to be safe from wumpus
        all_possible_wumpus = {pos for pos in all_possible_wumpus if pos not in self.safe_from_wumpus}
        
        if not all_possible_wumpus:
            return
        
        # Since there's only one wumpus, try each possible location
        valid_wumpus_positions = []
        
        for wumpus_pos in all_possible_wumpus:
            if self.is_valid_wumpus_assignment(wumpus_pos):
                valid_wumpus_positions.append(wumpus_pos)
        
        if self.debug:
            print(f"Valid wumpus positions: {valid_wumpus_positions}")
        
        # If only one valid position, that's where the wumpus is
        if len(valid_wumpus_positions) == 1:
            wumpus_pos = valid_wumpus_positions[0]
            self.wumpus_cells.add(wumpus_pos)
            self.dangerous_cells.add(wumpus_pos)
            self.add_knowledge(wumpus_pos, {'wumpus': True, 'dangerous': True})
            if self.debug:
                print(f"Definite wumpus found at {wumpus_pos}")
            
            # Mark other possible positions as safe from wumpus
            for pos in all_possible_wumpus:
                if pos != wumpus_pos:
                    self.safe_from_wumpus.add(pos)
                    self.add_knowledge(pos, {'safe_from_wumpus': True})
                    self.possible_wumpus.discard(pos)
    
    def is_valid_pit_assignment(self, pit_positions: Set[Tuple[int, int]]) -> bool:
        """Check if a pit assignment satisfies all breeze constraints"""
        for breeze_pos, adjacent_cells in self.breeze_constraints:
            # At least one adjacent cell must have a pit
            if not any(pos in pit_positions for pos in adjacent_cells):
                return False
        
        return True
    
    def is_valid_wumpus_assignment(self, wumpus_pos: Tuple[int, int]) -> bool:
        """Check if a wumpus assignment satisfies all stench constraints"""
        for stench_pos, adjacent_cells in self.stench_constraints:
            # The wumpus must be in one of the adjacent cells
            if wumpus_pos not in adjacent_cells:
                return False
        
        return True
    
    def update_safe_cells(self):
        """Update safe cells based on current knowledge"""
        #print("logical_inference.update_safe_cells() -> ")
        #print(f"Safe from pits: {self.safe_from_pits}")
        #print(f"Safe from wumpus: {self.safe_from_wumpus}")
        
        # A cell is only safe if it's safe from BOTH pits AND wumpus
        for pos in self.frontier:
            if (pos not in self.dangerous_cells and 
                pos in self.safe_from_pits and 
                pos in self.safe_from_wumpus):
                if pos not in self.safe_cells:
                    self.safe_cells.add(pos)
                    self.add_knowledge(pos, {'safe': True})
                    if self.debug:
                        pass
                        #print(f"Cell {pos} is TRULY SAFE (safe from both pits and wumpus)")
            else:
                # Remove from safe cells if it's not completely safe
                if pos in self.safe_cells:
                    self.safe_cells.remove(pos)
                    if self.debug:
                        pit_safe = pos in self.safe_from_pits
                        wumpus_safe = pos in self.safe_from_wumpus
                        #print(f"Cell {pos} REMOVED from safe cells - pit_safe: {pit_safe}, wumpus_safe: {wumpus_safe}")
                else:
                    if self.debug:
                        pit_safe = pos in self.safe_from_pits
                        wumpus_safe = pos in self.safe_from_wumpus
                        #print(f"Cell {pos} is NOT completely safe - pit_safe: {pit_safe}, wumpus_safe: {wumpus_safe}")
        
        #print(f"----------------------------------------------------------------------   Current safe cells: ---{self.safe_cells}")
    
    def is_cell_completely_safe(self, position: Tuple[int, int]) -> bool:
        """
        FIXED: Check if a cell is completely safe (safe from both pits and wumpus)
        This is the key fix to prevent moving to unsafe cells
        """
        # If already visited, it's safe
        if position in self.board.visited_cells:
            return True
            
        # If it's in dangerous cells, it's not safe
        if position in self.dangerous_cells:
            return False
            
        # If it's a possible pit or wumpus location, it's not safe
        if position in self.possible_pits or position in self.possible_wumpus:
            return False
            
        # Must be safe from both pits and wumpus
        return (position in self.safe_from_pits and 
                position in self.safe_from_wumpus)
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_safest_move(self) -> Optional[str]:
        """Get safest move with optimized gold retrieval"""
        agent_pos = (self.board.agent.x, self.board.agent.y)
        
        # 1. Priority actions (gold/climb)
        if self.board.get_percepts().get('glitter', False):
            return 'grab'
        
        # Special case: if holding gold, focus exclusively on going home
        if self.board.agent.has_gold:
            home_pos = (0, self.board.size - 1)
            if agent_pos == home_pos:
                return 'climb'
            
            # Find safest path home using strict A*
            path = self.a_star_search(agent_pos, home_pos)
            if path:
                return self.get_move_from_path(agent_pos, path)
            
            # If no safe path exists, try riskier path home
            risky_path = self.risky_a_star_search(agent_pos, home_pos)
            if risky_path:
                # Shoot any blocking Wumpus first
                next_pos = risky_path[1]
                if (self.is_facing(next_pos) and
                    self.calculate_wumpus_probability(next_pos) > 0.5 and
                    self.board.agent.arrows > 0):
                    return 'shoot'
                return self.get_move_from_path(agent_pos, risky_path)
            
            return None  # Can't find any path home

        # 2. Normal exploration logic (when not holding gold)
        unvisited = [
            pos for pos, knowledge in self.knowledge_base.items()
            if not knowledge.facts.get('visited', False)
        ]
        
        safe_unvisited = [pos for pos in unvisited if self.is_cell_completely_safe(pos)]
        risky_unvisited = [pos for pos in unvisited if not self.is_cell_completely_safe(pos)]

        # 3. Try A* to safe targets first
        if safe_unvisited:
            safe_unvisited.sort(key=lambda pos: (
                self.manhattan_distance(agent_pos, pos),
                -len([p for p in self.board.get_adjacent_positions(*pos) 
                    if p not in self.board.visited_cells])
            ))
            for target in safe_unvisited:
                path = self.a_star_search(agent_pos, target)
                if path:
                    return self.get_move_from_path(agent_pos, path)

        # 4. Backtrack if needed
        if not safe_unvisited and not self.all_unvisited_are_risky():
            backtrack_target = self.find_backtrack_target()
            if backtrack_target:
                path = self.a_star_search(agent_pos, backtrack_target)
                if path:
                    return self.get_move_from_path(agent_pos, path)

        # 5. Only consider risky moves if ALL unvisited are risky
        if risky_unvisited and self.all_unvisited_are_risky():
            risky_unvisited.sort(key=lambda pos: (
                self.calculate_risk(pos),
                self.manhattan_distance(agent_pos, pos)
            ))
            for target in risky_unvisited:
                path = self.risky_a_star_search(agent_pos, target)
                if path:
                    next_pos = path[1]
                    if (self.is_facing(next_pos) and
                        self.calculate_wumpus_probability(next_pos) > 0.5 and
                        self.board.agent.arrows > 0):
                        return 'shoot'
                    return self.get_move_from_path(agent_pos, path)

        return None

    def a_star_search(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Safe A* that only uses known-safe cells"""
        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        
        while open_set:
            current = min(open_set, key=lambda pos: f_score[pos])
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            open_set.remove(current)
            
            for neighbor in self.board.get_adjacent_positions(*current):
                if not self.is_cell_completely_safe(neighbor):
                    continue
                    
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.manhattan_distance(neighbor, goal)
                    if neighbor not in open_set:
                        open_set.add(neighbor)
        
        return []

    def risky_a_star_search(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Risk-aware A* with danger penalties"""
        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        
        while open_set:
            current = min(open_set, key=lambda pos: f_score[pos])
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            open_set.remove(current)
            
            for neighbor in self.board.get_adjacent_positions(*current):
                if neighbor in self.dangerous_cells:
                    continue
                    
                # Higher cost for riskier cells
                risk = self.calculate_risk(neighbor)
                cost = 1 + (10 * risk)
                
                tentative_g = g_score[current] + cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.manhattan_distance(neighbor, goal)
                    if neighbor not in open_set:
                        open_set.add(neighbor)
        
        return []

    def reconstruct_path(self, came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct path from A* search results"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def all_unvisited_are_risky(self) -> bool:
        """Check if ALL unvisited cells are risky"""
        return all(
            not self.is_cell_completely_safe(pos)
            for pos, knowledge in self.knowledge_base.items()
            if not knowledge.facts.get('visited', False)
        )

    def find_backtrack_target(self) -> Optional[Tuple[int, int]]:
        """Find best position to backtrack to"""
        candidates = []
        for visited_pos in self.board.visited_cells:
            # Prefer cells adjacent to unexplored areas
            if any(adj not in self.board.visited_cells 
                for adj in self.board.get_adjacent_positions(*visited_pos)):
                candidates.append(visited_pos)
        
        if candidates:
            current_pos = (self.board.agent.x, self.board.agent.y)
            candidates.sort(key=lambda pos: self.manhattan_distance(current_pos, pos))
            return candidates[0]
        return None

    def get_move_from_path(self, current_pos: Tuple[int, int], path: List[Tuple[int, int]]) -> str:
        """Convert path into movement command"""
        if len(path) < 2:
            return None
            
        next_pos = path[1]
        direction = self.get_direction_to_position(current_pos, next_pos)
        if direction == self.board.agent.direction:
            return 'forward'
        return self.get_turn_to_direction(self.board.agent.direction, direction)

    def is_facing(self, pos: Tuple[int, int]) -> bool:
        """Check if agent is facing the position (using existing direction logic)"""
        dx = pos[0] - self.board.agent.x
        dy = pos[1] - self.board.agent.y
        return ((dx > 0 and self.board.agent.direction == 'right') or
                (dx < 0 and self.board.agent.direction == 'left') or
                (dy > 0 and self.board.agent.direction == 'down') or
                (dy < 0 and self.board.agent.direction == 'up'))
    
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
            return 'right'  # Default if same position
    
    def get_turn_to_direction(self, current_direction: str, target_direction: str) -> str:
        """Get the turn command to face target direction"""
        directions = ['right', 'down', 'left', 'up']
        
        try:
            current_index = directions.index(current_direction)
            target_index = directions.index(target_direction)
        except ValueError:
            if self.debug:
                print(f"Invalid direction: current={current_direction}, target={target_direction}")
            return 'turn_right'
        
        # Calculate the shortest turn
        diff = (target_index - current_index) % 4
        
        if diff == 0:
            if self.debug:
                #print("Already facing the right direction")
                pass
            return 'forward'
        elif diff == 1:
            return 'turn_right'
        elif diff == 2:
            return 'turn_right'  # Turn around - use right turns consistently
        elif diff == 3:
            return 'turn_left'
        else:
            return 'turn_right'  # Default
    
    def calculate_risk(self, position: Tuple[int, int]) -> float:
        """Calculate risk score for a position (0 = safe, 1 = definitely dangerous)"""
        if position in self.safe_cells and position not in self.board.visited_cells:
            return 0.0
        if position in self.safe_cells:
            return 0.1
        if position in self.dangerous_cells:
            return 1.0
        
        # Calculate probability based on constraints
        pit_probability = self.calculate_pit_probability(position)
        wumpus_probability = self.calculate_wumpus_probability(position)
        
        # Risk is the probability of any danger
        # Using 1 - (1-p_pit) * (1-p_wumpus) for independent events
        return 1.0 - (1.0 - pit_probability) * (1.0 - wumpus_probability)
    
    def calculate_pit_probability(self, position: Tuple[int, int]) -> float:
        """Calculate probability that a position contains a pit"""
        # 1. Check definitive knowledge first
        if position in self.pit_cells:
            return 1.0
        if position in self.safe_from_pits:
            return 0.0
        
        # 2. Check for adjacent cells without breeze (NEW CRITICAL CHECK)
        for adj_pos in self.board.get_adjacent_positions(*position):
            adj_cell = self.board.get_cell(*adj_pos)
            if adj_cell.visited and not adj_cell.breeze:
                self.safe_from_pits.add(position)  # Mark as definitely safe
                return 0.0
        
        # 3. Original constraint-based probability calculation
        relevant_constraints = sum(1 for _, cells in self.breeze_constraints 
                                if position in cells)
        total_constraints = len(self.breeze_constraints)
        
        if total_constraints == 0:
            return 0.1  # Base probability for unexplored cells
        
        return min(0.8, relevant_constraints / total_constraints * 0.5)
    
    def calculate_wumpus_probability(self, position: Tuple[int, int]) -> float:
        """Calculate probability that a position contains the wumpus with negative evidence checks"""
        # 1. Check definitive knowledge first
        if not self.board.wumpus_alive:
            return 0.0
        if position in self.wumpus_cells:
            return 1.0
        if position in self.safe_from_wumpus:
            return 0.0
        
        # 2. Check for adjacent cells without stench (NEW CRITICAL CHECK)
        for adj_pos in self.board.get_adjacent_positions(*position):
            adj_cell = self.board.get_cell(*adj_pos)
            if adj_cell.visited and not adj_cell.stench:
                self.safe_from_wumpus.add(position)  # Mark as definitely safe
                return 0.0
        
        # 3. Check if all adjacent stenches are explained by other possible wumpus locations
        if position in self.possible_wumpus:
            can_explain_all = True
            for stench_pos, _ in self.stench_constraints:
                if position in self.board.get_adjacent_positions(*stench_pos):
                    other_explanations = [p for p in self.possible_wumpus 
                                        if p != position and 
                                        p in self.board.get_adjacent_positions(*stench_pos)]
                    if not other_explanations:
                        can_explain_all = False
                        break
            
            if not can_explain_all:
                return 0.0  # This cell can't explain all required stenches
        
        # 4. Original constraint-based probability calculation
        relevant_constraints = sum(1 for _, cells in self.stench_constraints 
                                if position in cells)
        total_possible = len(self.possible_wumpus)
        
        if relevant_constraints == 0:
            return 0.1  # Base probability
        
        return min(0.8, relevant_constraints / (total_possible + 1) * 0.7)
    
    def print_knowledge_state(self):
        """Print current knowledge state for debugging"""
        print("\n=== KNOWLEDGE STATE ===")
        print(f"Safe cells: {self.safe_cells}")
        print(f"Safe from pits: {self.safe_from_pits}")
        print(f"Safe from wumpus: {self.safe_from_wumpus}")
        print(f"Dangerous cells: {self.dangerous_cells}")
        print(f"Possible pits: {self.possible_pits}")
        print(f"Possible wumpus: {self.possible_wumpus}")
        print(f"Definite pits: {self.pit_cells}")
        print(f"Definite wumpus: {self.wumpus_cells}")
        print(f"Breeze constraints: {len(self.breeze_constraints)}")
        print(f"Stench constraints: {len(self.stench_constraints)}")
        print("========================\n")
        self.print_knowledge_base()
        print("========================\n")

        

    def print_knowledge_base(self):
        """Prints the raw knowledge_base dictionary with detailed cell knowledge"""
        print("\n=== KNOWLEDGE BASE DUMP ===")
        print(f"{'Position':<8} | {'Facts':<85} | {'Confidence'}")
        print("-" * 70)
        
        for position, knowledge in self.knowledge_base.items():
            x, y = position
            facts_str = ", ".join([f"{k}:{v}" for k, v in knowledge.facts.items()])
            print(f"({x},{y})    | {facts_str:<45} | {knowledge.confidence:.2f}")
        
        print("=" * 70 + "\n")


    
    # Keep all other methods from the original class for compatibility
    def get_safe_cells(self) -> List[Tuple[int, int]]:
        return list(self.safe_cells)
    
    def get_dangerous_cells(self) -> List[Tuple[int, int]]:
        return list(self.dangerous_cells)
    
    def get_frontier_cells(self) -> List[Tuple[int, int]]:
        return list(self.frontier)
    
    def is_safe(self, position: Tuple[int, int]) -> bool:
        return position in self.safe_cells
    
    def is_dangerous(self, position: Tuple[int, int]) -> bool:
        return position in self.dangerous_cells
    
    def suggest_next_move(self) -> Optional[str]:
        return self.get_safest_move()
    
    def get_best_move(self) -> Optional[str]:
        return self.get_safest_move()