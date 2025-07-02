// Wumpus World Game Logic

class WumpusWorld {
    constructor() {
        this.boardSize = 10;
        this.board = [];
        this.agentPosition = { x: 0, y: 9 }; // Bottom-left corner
        this.agentDirection = 'right'; // right, up, left, down
        this.arrows = 1;
        this.score = 0;
        this.gameStatus = 'playing'; // playing, won, lost
        this.visitedCells = new Set();
        this.hasGold = false;
        this.wumpusAlive = true;
        
        this.initializeBoard();
        this.renderBoard();
        this.updateGameInfo();
    }

    initializeBoard() {
        // Initialize empty board
        this.board = Array(this.boardSize).fill().map(() => 
            Array(this.boardSize).fill().map(() => ({
                wumpus: false,
                pit: false,
                gold: false,
                agent: false,
                breeze: false,
                stench: false,
                glitter: false,
                visited: false
            }))
        );

        // Place agent at starting position
        this.board[this.agentPosition.y][this.agentPosition.x].agent = true;
        this.board[this.agentPosition.y][this.agentPosition.x].visited = true;
        this.visitedCells.add(`${this.agentPosition.x},${this.agentPosition.y}`);

        // For aesthetic purposes, we'll add a default safe layout
        // Later this will be replaced with environment input
        this.setupDefaultEnvironment();
    }

    setupDefaultEnvironment() {
        // Place Wumpus (example position)
        this.board[7][3].wumpus = true;
        
        // Place Gold (example position)
        this.board[2][8].gold = true;
        this.board[2][8].glitter = true;
        
        // Place some pits (example positions)
        const pitPositions = [
            {x: 2, y: 2}, {x: 3, y: 4}, {x: 6, y: 1}, 
            {x: 7, y: 7}, {x: 1, y: 5}, {x: 8, y: 3}
        ];
        
        pitPositions.forEach(pos => {
            if (pos.x !== this.agentPosition.x || pos.y !== this.agentPosition.y) {
                this.board[pos.y][pos.x].pit = true;
            }
        });

        // Generate breezes around pits
        this.generateBreezes();
        
        // Generate stenches around wumpus
        this.generateStenches();
    }

    generateBreezes() {
        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                if (this.board[y][x].pit) {
                    // Add breeze to adjacent cells
                    this.addBreezeToAdjacent(x, y);
                }
            }
        }
    }

    generateStenches() {
        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                if (this.board[y][x].wumpus && this.wumpusAlive) {
                    // Add stench to adjacent cells
                    this.addStenchToAdjacent(x, y);
                }
            }
        }
    }

    addBreezeToAdjacent(x, y) {
        const directions = [
            {dx: 0, dy: 1}, {dx: 0, dy: -1},
            {dx: 1, dy: 0}, {dx: -1, dy: 0}
        ];

        directions.forEach(dir => {
            const newX = x + dir.dx;
            const newY = y + dir.dy;
            
            if (this.isValidPosition(newX, newY) && !this.board[newY][newX].pit) {
                this.board[newY][newX].breeze = true;
            }
        });
    }

    addStenchToAdjacent(x, y) {
        const directions = [
            {dx: 0, dy: 1}, {dx: 0, dy: -1},
            {dx: 1, dy: 0}, {dx: -1, dy: 0}
        ];

        directions.forEach(dir => {
            const newX = x + dir.dx;
            const newY = y + dir.dy;
            
            if (this.isValidPosition(newX, newY) && !this.board[newY][newX].wumpus) {
                this.board[newY][newX].stench = true;
            }
        });
    }

    isValidPosition(x, y) {
        return x >= 0 && x < this.boardSize && y >= 0 && y < this.boardSize;
    }

    renderBoard() {
        const boardElement = document.getElementById('wumpus-board');
        boardElement.innerHTML = '';

        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                
                const cellContent = document.createElement('div');
                cellContent.className = 'cell-content';
                
                const mainContent = document.createElement('div');
                mainContent.className = 'cell-main';
                
                const indicators = document.createElement('div');
                indicators.className = 'cell-indicators';

                const cellData = this.board[y][x];

                // Add main content (agent, wumpus, gold, pit)
                if (cellData.agent) {
                    mainContent.textContent = '🤖';
                    cell.classList.add('current');
                } else if (cellData.wumpus && this.wumpusAlive) {
                    mainContent.textContent = this.isCellVisible(x, y) ? '👹' : '';
                } else if (cellData.wumpus && !this.wumpusAlive) {
                    mainContent.textContent = this.isCellVisible(x, y) ? '💀' : '';
                } else if (cellData.gold && this.isCellVisible(x, y)) {
                    mainContent.textContent = '💰';
                } else if (cellData.pit && this.isCellVisible(x, y)) {
                    mainContent.textContent = '🕳️';
                    cell.classList.add('danger');
                }

                // Add indicators (breeze, stench, glitter)
                if (this.isCellVisible(x, y)) {
                    if (cellData.breeze) {
                        indicators.innerHTML += '💨';
                    }
                    if (cellData.stench && this.wumpusAlive) {
                        indicators.innerHTML += '💀';
                    }
                    if (cellData.glitter) {
                        indicators.innerHTML += '✨';
                    }
                }

                // Add cell state classes
                if (cellData.visited) {
                    cell.classList.add('visited');
                }
                
                if (this.isCellSafe(x, y) && cellData.visited) {
                    cell.classList.add('safe');
                }

                cellContent.appendChild(mainContent);
                cellContent.appendChild(indicators);
                cell.appendChild(cellContent);
                
                // Add click event for cell selection
                cell.addEventListener('click', () => this.handleCellClick(x, y));
                
                boardElement.appendChild(cell);
            }
        }
    }

    isCellVisible(x, y) {
        // Cell is visible if agent has visited it or if it's adjacent to visited cell
        if (this.visitedCells.has(`${x},${y}`)) {
            return true;
        }
        
        // Check if adjacent to any visited cell
        const directions = [
            {dx: 0, dy: 1}, {dx: 0, dy: -1},
            {dx: 1, dy: 0}, {dx: -1, dy: 0}
        ];

        for (let dir of directions) {
            const adjX = x + dir.dx;
            const adjY = y + dir.dy;
            if (this.visitedCells.has(`${adjX},${adjY}`)) {
                return true;
            }
        }
        
        return false;
    }

    isCellSafe(x, y) {
        const cellData = this.board[y][x];
        return !cellData.pit && !cellData.wumpus;
    }

    handleCellClick(x, y) {
        console.log(`Clicked cell (${x}, ${y})`);
        // This can be used for pathfinding or manual movement later
    }

    moveAgent(direction) {
        if (this.gameStatus !== 'playing') return;

        let newX = this.agentPosition.x;
        let newY = this.agentPosition.y;

        switch (direction) {
            case 'up':
                newY = Math.max(0, newY - 1);
                break;
            case 'down':
                newY = Math.min(this.boardSize - 1, newY + 1);
                break;
            case 'left':
                newX = Math.max(0, newX - 1);
                break;
            case 'right':
                newX = Math.min(this.boardSize - 1, newX + 1);
                break;
        }

        // Check if movement is valid
        if (newX === this.agentPosition.x && newY === this.agentPosition.y) {
            this.updateStatus('Cannot move outside the board!');
            return;
        }

        // Update agent position
        this.board[this.agentPosition.y][this.agentPosition.x].agent = false;
        this.agentPosition.x = newX;
        this.agentPosition.y = newY;
        this.agentDirection = direction;
        
        // Visit new cell
        this.board[newY][newX].agent = true;
        this.board[newY][newX].visited = true;
        this.visitedCells.add(`${newX},${newY}`);

        // Deduct movement score
        this.score -= 1;

        // Check for game events
        this.checkGameEvents();
        
        this.renderBoard();
        this.updateGameInfo();
    }

    checkGameEvents() {
        const currentCell = this.board[this.agentPosition.y][this.agentPosition.x];

        // Check for pit
        if (currentCell.pit) {
            this.gameStatus = 'lost';
            this.score -= 1000;
            this.updateStatus('Game Over! You fell into a pit!');
            return;
        }

        // Check for wumpus
        if (currentCell.wumpus && this.wumpusAlive) {
            this.gameStatus = 'lost';
            this.score -= 1000;
            this.updateStatus('Game Over! You were eaten by the Wumpus!');
            return;
        }

        // Check for gold
        if (currentCell.gold && !this.hasGold) {
            this.updateStatus('You see glittering gold!');
        }

        // Update status with perceptions
        this.updatePerceptions();
    }

    updatePerceptions() {
        const currentCell = this.board[this.agentPosition.y][this.agentPosition.x];
        let perceptions = [];

        if (currentCell.breeze) perceptions.push('breeze');
        if (currentCell.stench && this.wumpusAlive) perceptions.push('stench');
        if (currentCell.glitter) perceptions.push('glitter');

        if (perceptions.length > 0) {
            this.updateStatus(`You perceive: ${perceptions.join(', ')}`);
        } else {
            this.updateStatus('All clear!');
        }
    }

    shootArrow() {
        if (this.gameStatus !== 'playing') return;
        
        if (this.arrows <= 0) {
            this.updateStatus('No arrows remaining!');
            return;
        }

        this.arrows--;
        this.score -= 10;

        // Calculate arrow path based on direction
        let targetX = this.agentPosition.x;
        let targetY = this.agentPosition.y;

        switch (this.agentDirection) {
            case 'up':
                targetY = 0;
                break;
            case 'down':
                targetY = this.boardSize - 1;
                break;
            case 'left':
                targetX = 0;
                break;
            case 'right':
                targetX = this.boardSize - 1;
                break;
        }

        // Check if wumpus is in the line of fire
        let wumpusHit = false;
        
        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                if (this.board[y][x].wumpus && this.isInLineOfFire(x, y)) {
                    wumpusHit = true;
                    this.wumpusAlive = false;
                    this.score += 500;
                    this.updateStatus('You hear a loud scream! The Wumpus is dead!');
                    
                    // Remove stenches
                    this.removeStenches();
                    break;
                }
            }
        }

        if (!wumpusHit) {
            this.updateStatus('Your arrow misses...');
        }

        this.renderBoard();
        this.updateGameInfo();
    }

    isInLineOfFire(x, y) {
        switch (this.agentDirection) {
            case 'up':
                return x === this.agentPosition.x && y < this.agentPosition.y;
            case 'down':
                return x === this.agentPosition.x && y > this.agentPosition.y;
            case 'left':
                return y === this.agentPosition.y && x < this.agentPosition.x;
            case 'right':
                return y === this.agentPosition.y && x > this.agentPosition.x;
            default:
                return false;
        }
    }

    removeStenches() {
        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                this.board[y][x].stench = false;
            }
        }
    }

    grabGold() {
        if (this.gameStatus !== 'playing') return;

        const currentCell = this.board[this.agentPosition.y][this.agentPosition.x];
        
        if (currentCell.gold && !this.hasGold) {
            this.hasGold = true;
            currentCell.gold = false;
            currentCell.glitter = false;
            this.score += 1000;
            this.updateStatus('You grabbed the gold!');
        } else if (this.hasGold) {
            this.updateStatus('You already have the gold!');
        } else {
            this.updateStatus('No gold here to grab!');
        }

        this.renderBoard();
        this.updateGameInfo();
    }

    climbOut() {
        if (this.gameStatus !== 'playing') return;

        // Can only climb out from starting position (0, 9)
        if (this.agentPosition.x === 0 && this.agentPosition.y === 9) {
            if (this.hasGold) {
                this.gameStatus = 'won';
                this.score += 1000;
                this.updateStatus('Congratulations! You won the game!');
            } else {
                this.gameStatus = 'won';
                this.updateStatus('You climbed out safely, but without the gold...');
            }
        } else {
            this.updateStatus('You can only climb out from the starting position (bottom-left)!');
        }

        this.updateGameInfo();
    }

    updateGameInfo() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('arrows').textContent = this.arrows;
        
        let status = '';
        switch (this.gameStatus) {
            case 'playing':
                status = 'Exploring';
                break;
            case 'won':
                status = 'Victory!';
                break;
            case 'lost':
                status = 'Game Over';
                break;
        }
        document.getElementById('status').textContent = status;
    }

    updateStatus(message) {
        console.log(message);
        // You can add a status display element to show messages to the user
        // For now, we'll just log to console
    }

    // Method to reset the game
    resetGame() {
        this.agentPosition = { x: 0, y: 9 };
        this.agentDirection = 'right';
        this.arrows = 1;
        this.score = 0;
        this.gameStatus = 'playing';
        this.visitedCells = new Set();
        this.hasGold = false;
        this.wumpusAlive = true;
        
        this.initializeBoard();
        this.renderBoard();
        this.updateGameInfo();
    }

    // Method to load custom environment (for future use)
    loadEnvironment(environmentData) {
        // This method will be used when taking environment as input
        // environmentData should contain positions of wumpus, pits, and gold
        console.log('Loading custom environment:', environmentData);
        
        // Reset board
        this.board = Array(this.boardSize).fill().map(() => 
            Array(this.boardSize).fill().map(() => ({
                wumpus: false,
                pit: false,
                gold: false,
                agent: false,
                breeze: false,
                stench: false,
                glitter: false,
                visited: false
            }))
        );

        // Place agent
        this.board[this.agentPosition.y][this.agentPosition.x].agent = true;
        this.board[this.agentPosition.y][this.agentPosition.x].visited = true;
        this.visitedCells.add(`${this.agentPosition.x},${this.agentPosition.y}`);

        // Apply environment data
        if (environmentData.wumpus) {
            this.board[environmentData.wumpus.y][environmentData.wumpus.x].wumpus = true;
        }

        if (environmentData.gold) {
            this.board[environmentData.gold.y][environmentData.gold.x].gold = true;
            this.board[environmentData.gold.y][environmentData.gold.x].glitter = true;
        }

        if (environmentData.pits) {
            environmentData.pits.forEach(pit => {
                if (pit.x !== this.agentPosition.x || pit.y !== this.agentPosition.y) {
                    this.board[pit.y][pit.x].pit = true;
                }
            });
        }

        // Generate perceptions
        this.generateBreezes();
        this.generateStenches();
        
        this.renderBoard();
        this.updateGameInfo();
    }
}

// Global game instance
let game;

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', function() {
    game = new WumpusWorld();
});

// Movement functions (called by buttons)
function moveAgent(direction) {
    if (game) {
        game.moveAgent(direction);
    }
}

function shootArrow() {
    if (game) {
        game.shootArrow();
    }
}

function grabGold() {
    if (game) {
        game.grabGold();
    }
}

function climbOut() {
    if (game) {
        game.climbOut();
    }
}

// Additional utility functions
function resetGame() {
    if (game) {
        game.resetGame();
    }
}

function loadCustomEnvironment(environmentData) {
    if (game) {
        game.loadEnvironment(environmentData);
    }
}

// Keyboard controls
document.addEventListener('keydown', function(event) {
    if (!game || game.gameStatus !== 'playing') return;

    switch (event.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
            event.preventDefault();
            moveAgent('up');
            break;
        case 'ArrowDown':
        case 's':
        case 'S':
            event.preventDefault();
            moveAgent('down');
            break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
            event.preventDefault();
            moveAgent('left');
            break;
        case 'ArrowRight':
        case 'd':
        case 'D':
            event.preventDefault();
            moveAgent('right');
            break;
        case ' ':
            event.preventDefault();
            shootArrow();
            break;
        case 'g':
        case 'G':
            event.preventDefault();
            grabGold();
            break;
        case 'c':
        case 'C':
            event.preventDefault();
            climbOut();
            break;
        case 'r':
        case 'R':
            event.preventDefault();
            resetGame();
            break;
    }
});

// Example of how to use custom environment (for testing)
function loadExampleEnvironment() {
    const exampleEnv = {
        wumpus: { x: 5, y: 3 },
        gold: { x: 7, y: 2 },
        pits: [
            { x: 2, y: 3 },
            { x: 4, y: 6 },
            { x: 7, y: 7 },
            { x: 1, y: 1 }
        ]
    };
    
    loadCustomEnvironment(exampleEnv);
}