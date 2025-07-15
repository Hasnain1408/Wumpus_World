class WumpusWorldUI {
    constructor() {
        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        this.gameState = null;
        this.boardSize = 10;
        this.gameMode = 'manual'; // 'manual' or 'ai'
        this.aiPlaying = false;
        this.aiInterval = null;
        this.moveDelay = 1500; // Delay between AI moves in milliseconds
        this.csrfToken = null;
        this.showEnvironment = false; // Show environment elements by default
        
        this.initializeUI();
        this.initializeCSRF();
    }

    async initializeCSRF() {
        // Try to get CSRF token from multiple sources
        await this.ensureCSRFToken();
        // Load game state after CSRF token is available
        this.loadGameState();
    }

    async ensureCSRFToken() {
        // Try to get CSRF token from window (if set in template)
        if (window.csrfToken) {
            this.csrfToken = window.csrfToken;
            return;
        }

        // Try to get from cookie
        const cookieToken = this.getCSRFTokenFromCookie();
        if (cookieToken) {
            this.csrfToken = cookieToken;
            return;
        }

        // Try to get from meta tag
        const metaToken = this.getCSRFTokenFromMeta();
        if (metaToken) {
            this.csrfToken = metaToken;
            return;
        }

        // Last resort: make a GET request to get CSRF token
        try {
            const response = await fetch('/api/csrf-token/', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.csrfToken = data.csrfToken;
            }
        } catch (error) {
            console.error('Failed to get CSRF token:', error);
        }
    }

    getCSRFTokenFromCookie() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : null;
    }

    getCSRFTokenFromMeta() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : null;
    }

    initializeUI() {
        // Initialize the game board UI
        this.renderBoard();
        this.setupEventListeners();
        this.createNotificationContainer();
        
        // Generate initial random environment (delayed to ensure CSRF token is ready)
        setTimeout(() => {
            this.generateRandomEnvironment();
        }, 1000);
    }

    createNotificationContainer() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
    }

    showMessage(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
            transform: translateX(100%);
            transition: all 0.3s ease;
            pointer-events: auto;
            cursor: pointer;
        `;

        // Add colored border based on type
        const borderColors = {
            'success': '#38a169',
            'error': '#e53e3e',
            'info': '#3182ce',
            'warning': '#d69e2e'
        };
        
        notification.style.borderLeft = `4px solid ${borderColors[type] || borderColors.info}`;
        
        const container = document.getElementById('notification-container');
        container.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (container.contains(notification)) {
                    container.removeChild(notification);
                }
            }, 300);
        }, 3000);
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (container.contains(notification)) {
                    container.removeChild(notification);
                }
            }, 300);
        });
    }

    updateGameInfo() {
        if (!this.gameState) return;
        
        const scoreElement = document.getElementById('score');
        const arrowsElement = document.getElementById('arrows');
        const statusElement = document.getElementById('status');
        
        if (scoreElement) scoreElement.textContent = this.gameState.score || 0;
        if (arrowsElement) arrowsElement.textContent = this.gameState.agent?.arrows || 0;
        
        // Update game status
        if (statusElement) {
            if (this.gameState.game_over) {
                if (this.gameState.game_won) {
                    statusElement.textContent = 'Victory!';
                    statusElement.style.color = '#38a169';
                } else {
                    statusElement.textContent = 'Game Over';
                    statusElement.style.color = '#e53e3e';
                }
            } else {
                statusElement.textContent = 'Playing';
                statusElement.style.color = '#ffd700';
            }
        }
    }

    setupEventListeners() {
        // Add event listeners for UI controls
        document.addEventListener('keydown', (e) => this.handleKeyboardInput(e));
    }

    setGameMode(mode) {
        this.gameMode = mode;
        
        // Update UI elements if they exist
        const manualModeElement = document.getElementById('manual-mode');
        const aiModeElement = document.getElementById('ai-mode');
        const currentModeElement = document.getElementById('current-mode');
        const manualControlsElement = document.getElementById('manual-controls');
        const aiControlsElement = document.getElementById('ai-controls');
        
        if (manualModeElement) manualModeElement.classList.toggle('active', mode === 'manual');
        if (aiModeElement) aiModeElement.classList.toggle('active', mode === 'ai');
        if (currentModeElement) currentModeElement.textContent = mode === 'manual' ? 'Manual' : 'AI';
        
        // Show/hide appropriate controls
        if (manualControlsElement) manualControlsElement.style.display = mode === 'manual' ? 'block' : 'none';
        if (aiControlsElement) aiControlsElement.style.display = mode === 'ai' ? 'block' : 'none';
        
        // Stop AI if switching to manual
        if (mode === 'manual' && this.aiPlaying) {
            this.pauseAI();
        }
        
        this.showMessage(`Switched to ${mode === 'manual' ? 'Manual' : 'AI'} mode`);
    }

    async generateRandomEnvironment() {
        try {
            const response = await fetch('/api/random-environment/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.success) {
                await this.loadCustomEnvironment(data.environment);
                this.showMessage('Random environment generated!', 'success');
            } else {
                this.showMessage('Failed to generate random environment', 'error');
            }
        } catch (error) {
            console.error('Error generating random environment:', error);
            this.showMessage('Error generating random environment', 'error');
        }
    }

    async loadGameState() {
        // Ensure we have a CSRF token before making the request
        if (!this.csrfToken) {
            await this.ensureCSRFToken();
        }

        try {
            // Try POST request first
            let response = await fetch('/api/game-state/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            // If POST fails due to CSRF issues, try GET request as fallback
            if (!response.ok && response.status === 403) {
                console.log('POST request failed, trying GET request...');
                response = await fetch(`/api/game-state/?session_id=${encodeURIComponent(this.sessionId)}`, {
                    method: 'GET',
                    credentials: 'include'
                });
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.renderBoard();
                this.updateGameInfo();
            } else {
                this.showMessage(data.message || 'Failed to load game state', 'error');
            }
        } catch (error) {
            console.error('Error loading game state:', error);
            
            // Final fallback: try GET request without CSRF
            try {
                console.log('Trying GET request as final fallback...');
                const fallbackResponse = await fetch(`/api/game-state/?session_id=${encodeURIComponent(this.sessionId)}`, {
                    method: 'GET',
                    credentials: 'include'
                });
                
                const fallbackData = await fallbackResponse.json();
                
                if (fallbackData.success) {
                    this.gameState = fallbackData.game_state;
                    this.renderBoard();
                    this.updateGameInfo();
                    this.showMessage('Game state loaded successfully', 'success');
                } else {
                    this.showMessage('Failed to load game state', 'error');
                }
            } catch (fallbackError) {
                console.error('Fallback GET request also failed:', fallbackError);
                this.showMessage('Error loading game state', 'error');
            }
        }
    }

    renderBoard() {
        const boardElement = document.getElementById('wumpus-board');
        if (!boardElement) return;
        
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

                // Populate cell content based on game state
                this.populateCellContent(x, y, mainContent, indicators, cell);

                cellContent.appendChild(mainContent);
                cellContent.appendChild(indicators);
                cell.appendChild(cellContent);
                
                // Add click event for cell selection
                cell.addEventListener('click', () => this.handleCellClick(x, y));
                
                boardElement.appendChild(cell);
            }
        }
    }

    populateCellContent(x, y, mainContent, indicators, cell) {
        if (!this.gameState) return;

        const cellData = this.gameState.board[y][x];
        mainContent.textContent = '';
        indicators.innerHTML = '';
        cell.className = 'cell';

        const agentX = this.gameState.agent?.x || 0;
        const agentY = this.gameState.agent?.y || 0;
        const isCurrent = (agentX === x && agentY === y);
        const isVisited = this.isCellVisible(x, y);

        // Show agent
        if (isCurrent) {
            mainContent.textContent = '🤖';
            cell.classList.add('current');
            const direction = this.gameState.agent?.direction || 'right';
            const directionSymbols = {
                'right': '→',
                'left': '←',
                'up': '↑',
                'down': '↓'
            };
            indicators.innerHTML += `<span title="Facing ${direction}">${directionSymbols[direction]}</span>`;
            if (cellData.gold) {
                indicators.innerHTML += '<span title="Glitter - Gold here">✨</span>';
            }
        } else if (this.showEnvironment || isVisited) {
            // Show environment elements if revealed or visited
            if (cellData.wumpus && this.gameState.wumpus_alive) {
                mainContent.textContent = '👹';
                cell.classList.add('danger');
            } else if (cellData.wumpus && !this.gameState.wumpus_alive) {
                mainContent.textContent = '💀';
            } else if (cellData.gold) {
                mainContent.textContent = '💰';
            } else if (cellData.pit) {
                mainContent.textContent = '🕳️';
                cell.classList.add('danger');
            }
        }

        // Show percepts if revealed or visited (but not on agent's current cell)
        if ((this.showEnvironment || isVisited) && !isCurrent) {
            if (cellData.breeze) {
                indicators.innerHTML += '<span title="Breeze - Pit nearby">💨</span>';
            }
            if (cellData.stench && this.gameState.wumpus_alive) {
                indicators.innerHTML += '<span title="Stench - Wumpus nearby">💀</span>';
            }
            if (cellData.glitter) {
                indicators.innerHTML += '<span title="Glitter - Gold here">✨</span>';
            }
        }

        // Only add visited/safe classes for truly visited cells
        if (isVisited) {
            cell.classList.add('visited');
        }
        if (this.isCellSafe(x, y) && isVisited) {
            cell.classList.add('safe');
        }
        cell.title = `(${x}, ${y})`;
    }

    isCellVisible(x, y) {
        if (!this.gameState) return false;
        return this.gameState.visited_cells.includes(`${x},${y}`);
    }

    isCellSafe(x, y) {
        if (!this.gameState) return false;
        
        const cellData = this.gameState.board[y][x];
        return !cellData.pit && !cellData.wumpus;
    }

    handleCellClick(x, y) {
        console.log(`Clicked cell (${x}, ${y})`);
        // This can be used for pathfinding or manual movement later
    }

    async makeMove(action) {
        // In AI mode, don't allow manual moves
        if (this.gameMode === 'ai' && this.aiPlaying) {
            return;
        }

        try {
            const response = await fetch('/api/make-move/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action: action
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                console.log('Game state updated:', this.gameState.agent); // Debug log
                this.renderBoard();
                this.updateGameInfo();
                this.showMessage(data.message);
                
                // Check if game ended
                if (this.gameState.game_over) {
                    this.pauseAI(); // Stop AI if game ended
                }
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Error making move:', error);
            this.showMessage('Error making move', 'error');
        }
    }

    getCSRFToken() {
        // Return the stored CSRF token or try to get it fresh
        if (this.csrfToken) {
            return this.csrfToken;
        }

        // Try to get from cookie as fallback
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    async makeAIMove() {
        if (this.gameMode !== 'ai' || !this.gameState || this.gameState.game_over) {
            return;
        }

        try {
            // First get AI hint
            const hintResponse = await fetch('/api/ai-hint/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const hintData = await hintResponse.json();
            
            if (hintData.success && hintData.suggestion) {
                // Make the suggested move
                const moveResponse = await fetch('/api/make-move/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        action: hintData.suggestion
                    })
                });
                
                const moveData = await moveResponse.json();
                
                if (moveData.success) {
                    this.gameState = moveData.game_state;
                    console.log('AI move - Game state updated:', this.gameState.agent); // Debug log
                    this.renderBoard();
                    this.updateGameInfo();
                    this.showMessage(`AI made move: ${hintData.suggestion}`, 'info');
                    
                    // Update AI info display
                    const aiSuggestionElement = document.getElementById('ai-suggestion');
                    if (aiSuggestionElement) {
                        aiSuggestionElement.textContent = `AI made move: ${hintData.suggestion}`;
                    }
                } else {
                    this.showMessage(`AI move failed: ${moveData.message}`, 'error');
                }
            } else {
                this.showMessage('AI could not determine a safe move', 'warning');
                const aiSuggestionElement = document.getElementById('ai-suggestion');
                if (aiSuggestionElement) {
                    aiSuggestionElement.textContent = 'AI could not determine a safe move';
                }
            }
        } catch (error) {
            console.error('Error making AI move:', error);
            this.showMessage('Error making AI move', 'error');
        }
    }

    async autoPlay() {
        if (this.gameMode !== 'ai' || this.aiPlaying) {
            return;
        }

        this.aiPlaying = true;
        this.showMessage('AI Auto-play started', 'info');
        
        // Update button states
        const autoPlayBtn = document.querySelector('button[onclick="autoPlay()"]');
        const pauseBtn = document.querySelector('button[onclick="pauseAI()"]');
        
        if (autoPlayBtn) autoPlayBtn.disabled = true;
        if (pauseBtn) pauseBtn.disabled = false;

        this.aiInterval = setInterval(async () => {
            if (!this.aiPlaying || !this.gameState || this.gameState.game_over) {
                this.pauseAI();
                return;
            }

            await this.makeAIMove();
            
        }, this.moveDelay);
    }

    pauseAI() {
        this.aiPlaying = false;
        
        if (this.aiInterval) {
            clearInterval(this.aiInterval);
            this.aiInterval = null;
        }
        
        // Update button states
        const autoPlayBtn = document.querySelector('button[onclick="autoPlay()"]');
        const pauseBtn = document.querySelector('button[onclick="pauseAI()"]');
        
        if (autoPlayBtn) autoPlayBtn.disabled = false;
        if (pauseBtn) pauseBtn.disabled = true;
        
        this.showMessage('AI Auto-play paused', 'info');
    }

    async resetGame() {
        // Stop AI if running
        if (this.aiPlaying) {
            this.pauseAI();
        }
        
        try {
            const response = await fetch('/api/reset-game/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.renderBoard();
                this.updateGameInfo();
                this.showMessage('Game reset successfully', 'success');
                
                // Generate new random environment
                setTimeout(() => {
                    this.generateRandomEnvironment();
                }, 500);
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Error resetting game:', error);
            this.showMessage('Error resetting game', 'error');
        }
    }

    async loadCustomEnvironment(environmentData) {
        try {
            const response = await fetch('/api/load-environment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    environment: environmentData
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.renderBoard();
                this.updateGameInfo();
                this.showMessage('Environment loaded successfully', 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading environment:', error);
            this.showMessage('Error loading environment', 'error');
        }
    }

    async loadEnvironmentFromFile(filePath = null) {
        try {
            const response = await fetch('/api/load-environment-from-file/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    file_path: filePath
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.renderBoard();
                this.updateGameInfo();
                this.showMessage('Environment loaded from file successfully', 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading environment from file:', error);
            this.showMessage('Error loading environment from file', 'error');
        }
    }

    async loadDefaultEnvironment() {
        try {
            const response = await fetch('/api/load-default-environment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.renderBoard();
                this.updateGameInfo();
                this.showMessage('Environment loaded from wumpus.txt', 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading default environment:', error);
            this.showMessage('Error loading wumpus.txt', 'error');
        }
    }

    async getAIHint() {
        try {
            const response = await fetch('/api/ai-hint/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(`AI suggests: ${data.suggestion}`, 'info');
                const aiSuggestionElement = document.getElementById('ai-suggestion');
                if (aiSuggestionElement) {
                    aiSuggestionElement.textContent = `AI suggests: ${data.suggestion}`;
                }
            } else {
                this.showMessage('No AI suggestion available', 'warning');
            }
        } catch (error) {
            console.error('Error getting AI hint:', error);
            this.showMessage('Error getting AI hint', 'error');
        }
    }

    handleKeyboardInput(event) {
        // Only allow keyboard input in manual mode
        if (this.gameMode !== 'manual' || !this.gameState || this.gameState.game_over) {
            return;
        }

        switch (event.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                event.preventDefault();
                this.makeMove('move_up');
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                event.preventDefault();
                this.makeMove('move_down');
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                event.preventDefault();
                this.makeMove('move_left');
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                event.preventDefault();
                this.makeMove('move_right');
                break;
            case ' ':
                event.preventDefault();
                this.makeMove('shoot');
                break;
            case 'g':
            case 'G':
                event.preventDefault();
                this.makeMove('grab');
                break;
            case 'c':
            case 'C':
                event.preventDefault();
                this.makeMove('climb');
                break;
            case 'r':
            case 'R':
                event.preventDefault();
                this.resetGame();
                break;
        }
    }

    toggleEnvironment() {
        this.showEnvironment = !this.showEnvironment;
        const toggleBtn = document.getElementById('toggle-environment');
        if (toggleBtn) {
            toggleBtn.innerHTML = this.showEnvironment ? '🙈 Hide Environment' : '👁️ Show Environment';
        }
        this.renderBoard();
        this.showMessage(
            this.showEnvironment ? 'Environment elements are now visible' : 'Environment elements are hidden',
            'info'
        );
    }
}

// Global UI instance
let gameUI;

// Initialize UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    gameUI = new WumpusWorldUI();
});

// Button event handlers (called by HTML buttons)
function moveAgent(direction) {
    if (gameUI) {
        gameUI.makeMove(`move_${direction}`);
    }
}

function shootArrow() {
    if (gameUI) {
        gameUI.makeMove('shoot');
    }
}

function grabGold() {
    if (gameUI) {
        gameUI.makeMove('grab');
    }
}

function climbOut() {
    if (gameUI) {
        gameUI.makeMove('climb');
    }
}

function resetGame() {
    if (gameUI) {
        gameUI.resetGame();
    }
}

function getAIHint() {
    if (gameUI) {
        gameUI.getAIHint();
    }
}

function loadCustomEnvironment(environmentData) {
    if (gameUI) {
        gameUI.loadCustomEnvironment(environmentData);
    }
}

// New global functions for game mode control and AI functionality
function setGameMode(mode) {
    if (gameUI) {
        gameUI.setGameMode(mode);
    }
}

function generateRandomEnvironment() {
    if (gameUI) {
        gameUI.generateRandomEnvironment();
    }
}

function makeAIMove() {
    if (gameUI) {
        gameUI.makeAIMove();
    }
}

function autoPlay() {
    if (gameUI) {
        gameUI.autoPlay();
    }
}

function pauseAI() {
    if (gameUI) {
        gameUI.pauseAI();
    }
}

function toggleEnvironment() {
    if (gameUI) {
        gameUI.toggleEnvironment();
    }
}

function loadEnvironmentFromFile(filePath = null) {
    if (gameUI) {
        gameUI.loadDefaultEnvironment();
    }
}

function loadDefaultEnvironment() {
    if (gameUI) {
        gameUI.loadDefaultEnvironment();
    }
}

// Example of how to use custom environment
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