from django.db import models
from django.contrib.auth.models import User
import json

class WumpusEnvironment(models.Model):
    """
    Model to store different Wumpus World environment configurations
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    board_size = models.IntegerField(default=10)
    wumpus_x = models.IntegerField()
    wumpus_y = models.IntegerField()
    gold_x = models.IntegerField()
    gold_y = models.IntegerField()
    pits_data = models.JSONField()  # Store pits as JSON array
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
            ('expert', 'Expert'),
        ],
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Wumpus Environment'
        verbose_name_plural = 'Wumpus Environments'

    def __str__(self):
        return f"{self.name} ({self.difficulty})"

    def get_environment_data(self):
        """
        Return environment data in the format expected by the frontend
        """
        return {
            'wumpus': {'x': self.wumpus_x, 'y': self.wumpus_y},
            'gold': {'x': self.gold_x, 'y': self.gold_y},
            'pits': self.pits_data
        }

    def validate_positions(self):
        """
        Validate that all positions are within board bounds and don't conflict
        """
        agent_start = {'x': 0, 'y': 9}  # Bottom-left corner
        
        # Check bounds
        if not (0 <= self.wumpus_x < self.board_size and 0 <= self.wumpus_y < self.board_size):
            return False, "Wumpus position out of bounds"
        
        if not (0 <= self.gold_x < self.board_size and 0 <= self.gold_y < self.board_size):
            return False, "Gold position out of bounds"
        
        # Check agent start position conflicts
        if (self.wumpus_x == agent_start['x'] and self.wumpus_y == agent_start['y']):
            return False, "Wumpus cannot be at agent starting position"
        
        # Check pits
        for pit in self.pits_data:
            if not (0 <= pit['x'] < self.board_size and 0 <= pit['y'] < self.board_size):
                return False, f"Pit at ({pit['x']}, {pit['y']}) is out of bounds"
            
            if (pit['x'] == agent_start['x'] and pit['y'] == agent_start['y']):
                return False, "Pit cannot be at agent starting position"
        
        return True, "Valid"

class GameSession(models.Model):
    """
    Model to track individual game sessions and statistics
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    environment = models.ForeignKey(WumpusEnvironment, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    
    # Game state
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    final_score = models.IntegerField(default=0)
    moves_made = models.IntegerField(default=0)
    arrows_used = models.IntegerField(default=0)
    
    # Game outcome
    status = models.CharField(
        max_length=20,
        choices=[
            ('playing', 'Playing'),
            ('won', 'Won'),
            ('lost', 'Lost'),
            ('abandoned', 'Abandoned'),
        ],
        default='playing'
    )
    
    # Achievements
    gold_collected = models.BooleanField(default=False)
    wumpus_killed = models.BooleanField(default=False)
    perfect_game = models.BooleanField(default=False)  # Won without taking damage
    
    # Additional data
    game_data = models.JSONField(default=dict)  # Store detailed game state
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Game Session'
        verbose_name_plural = 'Game Sessions'

    def __str__(self):
        player_name = self.player.username if self.player else "Anonymous"
        return f"{player_name} - {self.environment.name} - {self.status}"

    def duration(self):
        """
        Calculate game duration in seconds
        """
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    def efficiency_score(self):
        """
        Calculate efficiency score based on moves and time
        """
        if self.moves_made == 0:
            return 0
        
        base_score = self.final_score
        move_penalty = self.moves_made * 2
        time_bonus = max(0, 300 - self.duration()) / 10  # Bonus for completing quickly
        
        return max(0, base_score - move_penalty + time_bonus)

class PlayerStatistics(models.Model):
    """
    Model to store aggregated player statistics
    """
    player = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Game counts
    total_games = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    
    # Scores
    best_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    
    # Achievements
    total_gold_collected = models.IntegerField(default=0)
    total_wumpus_killed = models.IntegerField(default=0)
    perfect_games = models.IntegerField(default=0)
    
    # Efficiency
    total_moves = models.IntegerField(default=0)
    total_arrows_used = models.IntegerField(default=0)
    fastest_win_time = models.FloatField(null=True, blank=True)  # In seconds
    
    # Streaks
    current_win_streak = models.IntegerField(default=0)
    best_win_streak = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Player Statistics'
        verbose_name_plural = 'Player Statistics'

    def __str__(self):
        return f"{self.player.username} - Stats"

    def win_rate(self):
        """
        Calculate win rate percentage
        """
        if self.total_games == 0:
            return 0
        return (self.games_won / self.total_games) * 100

    def average_score(self):
        """
        Calculate average score per game
        """
        if self.total_games == 0:
            return 0
        return self.total_score / self.total_games

    def average_moves_per_game(self):
        """
        Calculate average moves per game
        """
        if self.total_games == 0:
            return 0
        return self.total_moves / self.total_games

    def update_statistics(self, game_session):
        """
        Update statistics based on a completed game session
        """
        self.total_games += 1
        self.total_score += game_session.final_score
        self.total_moves += game_session.moves_made
        self.total_arrows_used += game_session.arrows_used
        
        if game_session.status == 'won':
            self.games_won += 1
            self.current_win_streak += 1
            self.best_win_streak = max(self.best_win_streak, self.current_win_streak)
            
            # Check fastest win
            duration = game_session.duration()
            if self.fastest_win_time is None or duration < self.fastest_win_time:
                self.fastest_win_time = duration
        else:
            self.games_lost += 1
            self.current_win_streak = 0
        
        if game_session.gold_collected:
            self.total_gold_collected += 1
        
        if game_session.wumpus_killed:
            self.total_wumpus_killed += 1
        
        if game_session.perfect_game:
            self.perfect_games += 1
        
        self.best_score = max(self.best_score, game_session.final_score)
        self.save()

class Leaderboard(models.Model):
    """
    Model for leaderboard entries
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    environment = models.ForeignKey(WumpusEnvironment, on_delete=models.CASCADE)
    game_session = models.OneToOneField(GameSession, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)
    
    # Leaderboard categories
    category = models.CharField(
        max_length=20,
        choices=[
            ('highest_score', 'Highest Score'),
            ('fastest_win', 'Fastest Win'),
            ('most_efficient', 'Most Efficient'),
            ('perfect_game', 'Perfect Game'),
        ],
        default='highest_score'
    )

    class Meta:
        ordering = ['-score', 'achieved_at']
        unique_together = ['player', 'environment', 'category']
        verbose_name = 'Leaderboard Entry'
        verbose_name_plural = 'Leaderboard Entries'

    def __str__(self):
        return f"{self.player.username} - {self.score} ({self.category})"