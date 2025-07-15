"""
Auto Play AI for Wumpus World
Implements autonomous AI agent for playing Wumpus World
"""

import random
import time
from typing import Dict, List, Tuple, Optional
from .game import WumpusGame
from .logical_inference import LogicalInference


class AutoPlayAI:
    """Autonomous AI agent for Wumpus World"""
    
    def __init__(self, board_size: int = 10):
        self.game = WumpusGame(board_size)
        self.strategy = 'logical'  # 'logical', 'random', 'cautious', 'aggressive'
        self.max_moves = 1000
        self.thinking_time = 0.1  # Seconds to "think" between moves
        self.performance_stats = {
            'games_played': 0,
            'games_won': 0,
            'total_score': 0,
            'best_score': float('-inf'),
            'worst_score': float('inf'),
            'average_moves': 0,
            'total_moves': 0
        }
    
    def set_strategy(self, strategy: str):
        """Set AI strategy"""
        valid_strategies = ['logical', 'random', 'cautious', 'aggressive']
        if strategy in valid_strategies:
            self.strategy = strategy
        else:
            raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")
    
    def play_game(self, environment: Dict = None, verbose: bool = False) -> Dict:
        """Play a complete game autonomously"""
        # Reset game
        self.game.reset_game()
        
        # Load environment if provided
        if environment:
            self.game.load_environment(environment)
        
        move_log = []
        
        if verbose:
            print("AI Starting game...")
            print(f"Strategy: {self.strategy}")
        
        # Game loop
        while not self.game.board.game_over and len(self.game.move_history) < self.max_moves:
            # Get next move
            action = self.get_next_move()
            
            if action is None:
                if verbose:
                    print("AI unable to determine next move")
                break
            
            # Make the move
            result = self.game.make_move(action)
            
            # Log the move
            move_info = {
                'move_number': len(self.game.move_history),
                'action': action,
                'success': result.success,
                'position': (self.game.board.agent.x, self.game.board.agent.y),
                'score': self.game.score,
                'percepts': result.percepts
            }
            move_log.append(move_info)
            
            if verbose:
                print(f"Move {move_info['move_number']}: {action} -> {result.message}")
                print(f"Position: {move_info['position']}, Score: {move_info['score']}")
            
            # Small delay for visualization
            if self.thinking_time > 0:
                time.sleep(self.thinking_time)
        
        # Update performance statistics
        self.update_performance_stats()
        
        # Return game result
        result = {
            'game_won': self.game.board.game_won,
            'agent_alive': self.game.board.agent.alive,
            'score': self.game.score,
            'moves_made': len(self.game.move_history),
            'gold_collected': self.game.board.agent.has_gold,
            'wumpus_killed': not self.game.board.wumpus_alive,
            'move_log': move_log,
            'final_position': (self.game.board.agent.x, self.game.board.agent.y),
            'strategy_used': self.strategy
        }
        
        if verbose:
            print(f"Game finished! Won: {result['game_won']}, Score: {result['score']}")
        
        return result
    
    def get_next_move(self) -> Optional[str]:
        """Get the next move based on current strategy"""
        if self.strategy == 'logical':
            return self.get_logical_move()
        elif self.strategy == 'random':
            return self.get_random_move()
        elif self.strategy == 'cautious':
            return self.get_cautious_move()
        elif self.strategy == 'aggressive':
            return self.get_aggressive_move()
        else:
            return self.get_logical_move()  # Default to logical
    
    def get_logical_move(self) -> Optional[str]:
        """Get move using logical inference"""
        # Use the inference engine's suggestion
        suggestion = self.game.get_ai_suggestion()
        
        if suggestion:
            return suggestion
        
        # Fallback to exploration
        return self.get_exploration_move()
    
    def get_random_move(self) -> Optional[str]:
        """Get random valid move"""
        possible_actions = self.game.get_possible_actions()
        
        if possible_actions:
            return random.choice(possible_actions)
        
        return None
    
    def get_cautious_move(self) -> Optional[str]:
        """Get move using cautious strategy (avoid risks)"""
        # Check if we can grab gold
        cell = self.game.board.get_cell(self.game.board.agent.x, self.game.board.agent.y)
        if cell and cell.gold:
            return 'grab'
        
        # Check if we can climb out with gold
        if (self.game.board.agent.has_gold and 
            self.game.board.agent.x == 0 and 
            self.game.board.agent.y == self.game.board.size - 1):
            return 'climb'
        
        # Get safe moves only
        safe_moves = self.get_safe_moves()
        if safe_moves:
            return random.choice(safe_moves)
        
        # If no safe moves, be very cautious
        return self.get_most_cautious_move()
    
    def get_aggressive_move(self) -> Optional[str]:
        """Get move using aggressive strategy (take calculated risks)"""
        # Always try to grab gold
        cell = self.game.board.get_cell(self.game.board.agent.x, self.game.board.agent.y)
        if cell and cell.gold:
            return 'grab'
        
        # Try to shoot wumpus if we know where it is
        if self.should_shoot_wumpus():
            return 'shoot'
        
        # Explore aggressively
        return self.get_aggressive_exploration_move()
    
    def get_safe_moves(self) -> List[str]:
        """Get list of moves that are known to be safe"""
        safe_moves = []
        current_pos = (self.game.board.agent.x, self.game.board.agent.y)
        
        # Check each possible direction
        directions = ['right', 'up', 'left', 'down']
        
        for direction in directions:
            next_pos = self.get_next_position(current_pos, direction)
            
            if (next_pos and 
                self.game.board.is_valid_position(next_pos[0], next_pos[1]) and
                self.game.inference_engine.is_safe(next_pos)):
                
                # Check if we need to turn
                if self.game.board.agent.direction != direction:
                    required_turn = self.get_required_turn(self.game.board.agent.direction, direction)
                    if required_turn:
                        safe_moves.append(required_turn)
                else:
                    safe_moves.append('forward')
        
        return safe_moves
    
    def get_exploration_move(self) -> Optional[str]:
        """Get move for exploration"""
        # Try to move to frontier cells
        frontier_cells = self.game.inference_engine.get_frontier_cells()
        
        if frontier_cells:
            # Choose closest frontier cell
            current_pos = (self.game.board.agent.x, self.game.board.agent.y)
            closest_frontier = min(frontier_cells, 
                                 key=lambda pos: self.manhattan_distance(current_pos, pos))
            
            # Try to move towards it
            direction = self.get_direction_towards(current_pos, closest_frontier)
            if direction:
                if self.game.board.agent.direction != direction:
                    return self.get_required_turn(self.game.board.agent.direction, direction)
                else:
                    return 'forward'
        
        # Random exploration
        return self.get_random_move()
    
    def get_aggressive_exploration_move(self) -> Optional[str]:
        """Get aggressive exploration move"""
        # Try risky moves if the potential payoff is high
        current_pos = (self.game.board.agent.x, self.game.board.agent.y)
        
        # Check adjacent cells for risk/reward
        adjacent_positions = self.game.board.get_adjacent_positions(current_pos[0], current_pos[1])
        
        best_move = None
        best_score = float('-inf')
        
        for adj_pos in adjacent_positions:
            risk = self.game.inference_engine.calculate_risk(adj_pos)
            reward = self.calculate_potential_reward(adj_pos)
            
            # Risk-reward score (higher is better)
            score = reward - (risk * 0.5)  # Aggressive: less penalty for risk
            
            if score > best_score:
                best_score = score
                direction = self.get_direction_towards(current_pos, adj_pos)
                
                if direction:
                    if self.game.board.agent.direction != direction:
                        best_move = self.get_required_turn(self.game.board.agent.direction, direction)
                    else:
                        best_move = 'forward'
        
        return best_move or self.get_random_move()
    
    def get_most_cautious_move(self) -> Optional[str]:
        """Get the most cautious move possible"""
        # Try to return to a known safe cell
        safe_cells = self.game.get_safe_cells()
        current_pos = (self.game.board.agent.x, self.game.board.agent.y)
        
        if safe_cells:
            # Find safest adjacent cell
            adjacent_positions = self.game.board.get_adjacent_positions(current_pos[0], current_pos[1])
            
            safest_pos = None
            lowest_risk = float('inf')
            
            for adj_pos in adjacent_positions:
                if adj_pos in safe_cells:
                    risk = self.game.inference_engine.calculate_risk(adj_pos)
                    if risk < lowest_risk:
                        lowest_risk = risk
                        safest_pos = adj_pos
            
            if safest_pos:
                direction = self.get_direction_towards(current_pos, safest_pos)
                if direction:
                    if self.game.board.agent.direction != direction:
                        return self.get_required_turn(self.game.board.agent.direction, direction)
                    else:
                        return 'forward'
        
        # If no safe moves, just turn (doesn't change position)
        return random.choice(['turn_left', 'turn_right'])
    
    def should_shoot_wumpus(self) -> bool:
        """Determine if we should shoot the wumpus"""
        if self.game.board.agent.arrows <= 0 or not self.game.board.wumpus_alive:
            return False
        
        # Check if we have a clear shot at wumpus
        wumpus_cells = self.game.inference_engine.wumpus_cells
        if not wumpus_cells:
            return False
        
        current_pos = (self.game.board.agent.x, self.game.board.agent.y)
        current_direction = self.game.board.agent.direction
        
        # Check if wumpus is in line of fire
        x, y = current_pos
        
        while True:
            if current_direction == 'right':
                x += 1
            elif current_direction == 'left':
                x -= 1
            elif current_direction == 'up':
                y -= 1
            elif current_direction == 'down':
                y += 1
            
            if not self.game.board.is_valid_position(x, y):
                break
            
            if (x, y) in wumpus_cells:
                return True
        
        return False
    
    def get_next_position(self, current_pos: Tuple[int, int], direction: str) -> Optional[Tuple[int, int]]:
        """Get the next position in a given direction"""
        x, y = current_pos
        
        if direction == 'right':
            return (x + 1, y)
        elif direction == 'left':
            return (x - 1, y)
        elif direction == 'up':
            return (x, y - 1)
        elif direction == 'down':
            return (x, y + 1)
        
        return None
    
    def get_direction_towards(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Optional[str]:
        """Get direction to move towards target position"""
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        if to_x > from_x:
            return 'right'
        elif to_x < from_x:
            return 'left'
        elif to_y < from_y:
            return 'up'
        elif to_y > from_y:
            return 'down'
        
        return None
    
    def get_required_turn(self, current_direction: str, target_direction: str) -> Optional[str]:
        """Get the turn required to face target direction"""
        directions = ['right', 'up', 'left', 'down']
        
        try:
            current_index = directions.index(current_direction)
            target_index = directions.index(target_direction)
            
            diff = (target_index - current_index) % 4
            
            if diff == 1:
                return 'turn_right'
            elif diff == 3:
                return 'turn_left'
            elif diff == 2:
                return 'turn_right'  # Either turn is fine, choose right
            
        except ValueError:
            pass
        
        return None
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def calculate_potential_reward(self, position: Tuple[int, int]) -> float:
        """Calculate potential reward for visiting a position"""
        reward = 0.0
        
        # Reward for exploration (visiting new cells)
        if position not in self.game.board.visited_cells:
            reward += 10.0
        
        # Reward for frontier cells (likely to reveal new information)
        if position in self.game.inference_engine.get_frontier_cells():
            reward += 5.0
        
        # Penalty for revisiting cells
        if position in self.game.board.visited_cells:
            reward -= 2.0
        
        return reward
    
    def update_performance_stats(self):
        """Update performance statistics"""
        self.performance_stats['games_played'] += 1
        
        if self.game.board.game_won:
            self.performance_stats['games_won'] += 1
        
        score = self.game.score
        self.performance_stats['total_score'] += score
        
        if score > self.performance_stats['best_score']:
            self.performance_stats['best_score'] = score
        
        if score < self.performance_stats['worst_score']:
            self.performance_stats['worst_score'] = score
        
        moves = len(self.game.move_history)
        self.performance_stats['total_moves'] += moves
        self.performance_stats['average_moves'] = (
            self.performance_stats['total_moves'] / self.performance_stats['games_played']
        )
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        
        if stats['games_played'] > 0:
            stats['win_rate'] = stats['games_won'] / stats['games_played']
            stats['average_score'] = stats['total_score'] / stats['games_played']
        else:
            stats['win_rate'] = 0.0
            stats['average_score'] = 0.0
        
        return stats
    
    def run_benchmark(self, num_games: int = 100, environment: Dict = None) -> Dict:
        """Run benchmark with multiple games"""
        print(f"Running benchmark with {num_games} games...")
        
        results = []
        
        for i in range(num_games):
            if i % 10 == 0:
                print(f"Game {i + 1}/{num_games}")
            
            result = self.play_game(environment, verbose=False)
            results.append(result)
        
        # Calculate aggregate statistics
        total_games = len(results)
        games_won = sum(1 for r in results if r['game_won'])
        total_score = sum(r['score'] for r in results)
        total_moves = sum(r['moves_made'] for r in results)
        
        benchmark_stats = {
            'total_games': total_games,
            'games_won': games_won,
            'win_rate': games_won / total_games if total_games > 0 else 0,
            'total_score': total_score,
            'average_score': total_score / total_games if total_games > 0 else 0,
            'total_moves': total_moves,
            'average_moves': total_moves / total_games if total_games > 0 else 0,
            'best_score': max(r['score'] for r in results) if results else 0,
            'worst_score': min(r['score'] for r in results) if results else 0,
            'strategy_used': self.strategy,
            'results': results
        }
        
        print(f"Benchmark completed!")
        print(f"Win rate: {benchmark_stats['win_rate']:.2%}")
        print(f"Average score: {benchmark_stats['average_score']:.2f}")
        print(f"Average moves: {benchmark_stats['average_moves']:.2f}")
        
        return benchmark_stats
    
    def compare_strategies(self, strategies: List[str], num_games: int = 50) -> Dict:
        """Compare different strategies"""
        print(f"Comparing strategies: {strategies}")
        
        comparison_results = {}
        
        for strategy in strategies:
            print(f"\nTesting strategy: {strategy}")
            self.set_strategy(strategy)
            
            # Reset performance stats
            self.performance_stats = {
                'games_played': 0,
                'games_won': 0,
                'total_score': 0,
                'best_score': float('-inf'),
                'worst_score': float('inf'),
                'average_moves': 0,
                'total_moves': 0
            }
            
            # Run benchmark
            benchmark_result = self.run_benchmark(num_games)
            comparison_results[strategy] = benchmark_result
        
        # Find best strategy
        best_strategy = max(comparison_results.keys(), 
                          key=lambda s: comparison_results[s]['win_rate'])
        
        print(f"\nBest strategy: {best_strategy}")
        print(f"Win rate: {comparison_results[best_strategy]['win_rate']:.2%}")
        
        return {
            'results': comparison_results,
            'best_strategy': best_strategy,
            'best_win_rate': comparison_results[best_strategy]['win_rate']
        }
    
    def set_thinking_time(self, seconds: float):
        """Set thinking time between moves"""
        self.thinking_time = max(0.0, seconds)
    
    def set_max_moves(self, max_moves: int):
        """Set maximum number of moves per game"""
        self.max_moves = max(1, max_moves)
