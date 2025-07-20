/**
 * @file Client-side JavaScript for a web-based chess game.
 * @description This script handles all user interactions, communicates with the
 * backend server via the Fetch API, and dynamically renders the game state. It manages
 * two primary pages: a starting page for game setup and the main game page. The script
s * is event-driven, responding to user actions like clicks and drag-and-drop to play
 * the game.
 */

/*
==========================================================================
    CHESS GAME CLIENT-SIDE SCRIPT
==========================================================================
    - Table of Contents -

    1.  Global State & Constants
    2.  Main Execution Flow & Initialization
    3.  State Management & Server Communication
    4.  Rendering Functions (UI Updates)
    5.  User Interaction (Event Handlers)
        - Setup
        - Click Handling
        - Drag & Drop Handling
    6.  UI Helper Functions
        - Board Interaction
        - Notifications & Modals
        - Starting Page Errors
    7.  Game Control Logic
==========================================================================
*/


/*
==========================================================================
    1. Global State & Constants
==========================================================================
*/

/**
 * Stores a reference to the DOM element of the currently selected square.
 * This is used for the click-to-move interaction model.
 * @type {HTMLElement | null}
 */
let selectedSquare = null;

/**
 * Stores a reference to the DOM element of the piece being dragged.
 * This is used for the drag-and-drop interaction model.
 * @type {HTMLElement | null}
 */
let draggedPiece = null;

/**
 * Stores the entire game state received from the server. This object is the
 * single source of truth for rendering the UI.
 * @type {object | null}
 * @property {string[][]} board - 8x8 grid of piece symbols.
 * @property {string} turn - The color of the current player ('white' or 'black').
 * @property {object} players - Names of the white and black players.
 * @property {string[][]} move_history - List of moves in algebraic notation.
 * @property {string} status - Current game status ('active', 'checkmate', etc.).
 * @property {string | null} winner - The winning color, if any.
 * @property {string | null} is_check - The color of the king in check, if any.
 * @property {string} game_mode - The mode of the game ('player_vs_player' or 'player_vs_ai').
 */
let gameState = null;

/**
 * Pre-loads the sound effect for a piece move to ensure it plays instantly on user action.
 * @const {Audio}
 */
const moveSound = new Audio('https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/move-self.mp3');
moveSound.volume = 1; // Volume can be adjusted from 0.0 to 1.0


/*
==========================================================================
    2. Main Execution Flow & Initialization
==========================================================================
*/

/**
 * Main entry point for the script. Runs after the DOM is fully loaded.
 * It identifies the current page and calls the appropriate setup function.
 */
document.addEventListener("DOMContentLoaded", function () {
    const pageId = document.body.id;

    if (pageId === "starting-page-body") {
        setupStartingPageListeners();
    } else if (pageId === "chess-body") {
        initializeBoard();
        const endButton = document.getElementById("end_button");
        if (endButton) {
            endButton.addEventListener("click", endGame);
        }
    }
});

/**
 * Initializes the game board on the main chess page. It fetches the initial game
 * state, sets up event listeners for all squares, and makes the board visible.
 * @async
 */
async function initializeBoard() {
    await updateGameState();      // Fetch initial state and render the UI.
    setupSquareEventListeners();  // Add click and drag-and-drop listeners.
    document.querySelector(".board").classList.add("ready"); // Show board to prevent Flash of Unstyled Content (FOUC).
}

/**
 * Sets up all necessary event listeners for the starting page, including the start
 * button, player name inputs, and game mode selection radios.
 */
function setupStartingPageListeners() {
    const startButton = document.getElementById("start_button");
    const whiteInput = document.getElementById("white_player");
    const blackInput = document.getElementById("black_player");
    const gameModeRadios = document.querySelectorAll('input[name="game_mode"]');

    if (startButton) {
        startButton.addEventListener("click", startGame);
    }
    // Allow pressing 'Enter' in input fields to trigger the start game action.
    whiteInput.addEventListener("keyup", (e) => { if (e.key === "Enter") startGame(); });
    blackInput.addEventListener("keyup", (e) => { if (e.key === "Enter") startGame(); });

    // Clear validation errors when the user starts typing.
    whiteInput.addEventListener('input', clearStartError);
    blackInput.addEventListener('input', clearStartError);

    gameModeRadios.forEach(radio => {
        radio.addEventListener('change', handleGameModeChange);
    });
}

/**
 * Handles the UI changes when the game mode (Player vs Player or Player vs AI) is switched.
 * It shows or hides the black player name input and the AI difficulty dropdown accordingly.
 */
function handleGameModeChange() {
    const selectedMode = document.querySelector('input[name="game_mode"]:checked').value;
    const blackPlayerInput = document.getElementById('black_player_input_container');
    const aiDifficultySelect = document.getElementById('ai_difficulty_container');

    if (selectedMode === 'single_player') {
        blackPlayerInput.classList.add('hidden');
        aiDifficultySelect.classList.remove('hidden');
    } else { // two_player
        blackPlayerInput.classList.remove('hidden');
        aiDifficultySelect.classList.add('hidden');
    }
    clearStartError(); // Clear any validation errors when the mode changes.
}


/*
==========================================================================
    3. State Management & Server Communication
==========================================================================
*/

/**
 * Fetches the latest game state from the server's `/state` endpoint.
 * On success, it updates the global `gameState` and triggers rendering functions.
 * On failure, it logs the error and displays a user-friendly toast notification.
 * @async
 */
async function updateGameState() {
    try {
        const response = await fetch("/state");
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to fetch game state.");
        }
        gameState = await response.json();
        renderBoard(gameState);
        renderGameInfo(gameState);
    } catch (error) {
        console.error("Error updating board state:", error);
        showToast(error.message);
    }
}

/**
 * Attempts to make a move by sending the 'from' and 'to' squares to the server's `/move` endpoint.
 * - On success: Plays a sound, updates the UI with the new state, and checks for game over.
 *               If in an AI game, it may trigger the AI's turn.
 * - On failure: Shows a toast notification with the error and re-renders the last known
 *               valid state to revert any optimistic UI changes.
 * @async
 * @param {string} fromSqId - The ID of the source square (e.g., "e2").
 * @param {string} toSqId - The ID of the destination square (e.g., "e4").
 */
async function attemptMove(fromSqId, toSqId) {
    clearSelection(); // Clear visual selection immediately for responsiveness.
    try {
        const response = await fetch('/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 'from': fromSqId, 'to': toSqId })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Invalid move');
        }

        // --- Handle successful move ---
        moveSound.play().catch(e => console.error("Error playing sound:", e));
        gameState = data.state;
        renderBoard(gameState);
        renderGameInfo(gameState);

        if (gameState.status === 'checkmate' || gameState.status === 'stalemate') {
            showGameOverModal(gameState.status, gameState.winner);
        }

    } catch (error) {
        showToast(error.message);
        // If the move failed on the server, revert the board to the last valid state.
        if (gameState) {
            renderBoard(gameState);
            renderGameInfo(gameState);
        }
    }
}

/*
==========================================================================
    4. Rendering Functions (UI Updates)
==========================================================================
*/

/**
 * Renders the entire chessboard based on the provided state object. It clears
 * the board, places pieces with their correct unicode symbols and colors,
 * and highlights the king if it is in check.
 * @param {object} state - The `gameState` object from the server.
 */
function renderBoard(state) {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const PIECE_UNICODE = {
        'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', // Black
        'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'  // White
    };

    // Clear previous highlights and pieces before redrawing.
    document.querySelectorAll('.square.in-check').forEach(sq => sq.classList.remove('in-check'));
    document.querySelectorAll('.piece').forEach(p => p.remove());

    // Place pieces based on the 2D array from the server state.
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const pieceSymbol = state.board[row][col];
            if (pieceSymbol) {
                const squareId = files[col] + (row + 1);
                const square = document.getElementById(squareId);
                if (!square) continue;

                const pieceEl = document.createElement('span');
                const pieceColor = (pieceSymbol === pieceSymbol.toUpperCase()) ? 'white' : 'black';

                pieceEl.className = `piece ${pieceColor}`;
                pieceEl.textContent = PIECE_UNICODE[pieceSymbol];
                pieceEl.draggable = (pieceColor === state.turn); // A piece is only draggable if it is its turn.
                square.appendChild(pieceEl);
            }
        }
    }

    // Highlight the king if in check.
    if (state.is_check) {
        const kingSymbol = (state.is_check === 'white') ? 'K' : 'k';
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                if (state.board[r][c] === kingSymbol) {
                    const kingSquareId = files[c] + (r + 1);
                    document.getElementById(kingSquareId)?.classList.add('in-check');
                    return; // King found, exit loop.
                }
            }
        }
    }
}

/**
 * Renders all game information displayed outside the board, such as player names,
 * turn indicators, and the move history table.
 * @param {object} state - The `gameState` object from the server.
 */
function renderGameInfo(state) {
    document.getElementById('white-player-name').textContent = state.players.white || 'White Player';
    document.getElementById('black-player-name').textContent = state.players.black || 'Black Player';

    document.getElementById('white-turn-indicator').classList.toggle('active-turn', state.turn === 'white');
    document.getElementById('black-turn-indicator').classList.toggle('active-turn', state.turn === 'black');

    // Re-render move history.
    const historyBody = document.getElementById('move-history-body');
    historyBody.innerHTML = ''; // Clear old history.

    for (let i = 0; i < state.move_history.length; i += 2) {
        const moveNumber = i / 2 + 1;
        const whiteMove = `${state.move_history[i][0]} → ${state.move_history[i][1]}`;
        const blackMove = state.move_history[i + 1] ? `${state.move_history[i + 1][0]} → ${state.move_history[i + 1][1]}` : '';

        const row = document.createElement('tr');
        row.innerHTML = `<td>${moveNumber}</td><td>${whiteMove}</td><td>${blackMove}</td>`;
        historyBody.appendChild(row);
    }

    // Auto-scroll move history to show the latest move.
    const historyContainer = document.querySelector('.move-history-container');
    historyContainer.scrollTop = historyContainer.scrollHeight;

    // --- Trigger AI move if applicable ---
    if (gameState.game_mode === 'player_vs_ai' && gameState.turn === 'black') {
        disableBoardInteraction();
        setTimeout(triggerAIMove, 700); // Small delay for better UX.
    }
}


/*
==========================================================================
    5. User Interaction (Event Handlers)
==========================================================================
*/

// --- Setup ---

/**
 * Adds all necessary click and drag-and-drop event listeners to every square on the board.
 */
function setupSquareEventListeners() {
    const squares = document.querySelectorAll('.square');
    squares.forEach(square => {
        square.addEventListener('click', handleClick);
        square.addEventListener('dragstart', handleDragStart);
        square.addEventListener('dragover', handleDragOver);
        square.addEventListener('drop', handleDrop);
        square.addEventListener('dragend', handleDragEnd);
    });
}

// --- Click Handling ---

/**
 * Handles a click event on a square for the click-to-move mechanic.
 * - If no piece is selected, it selects the clicked square if it contains a valid piece.
 * - If a piece is already selected, it attempts to move that piece to the clicked square.
 * @param {Event} event - The click event object.
 */
function handleClick(event) {
    const clickedSquare = event.currentTarget;
    const piece = clickedSquare.querySelector('.piece');

    if (selectedSquare) { // A piece is already selected, this is the destination click.
        if (clickedSquare.id === selectedSquare.id) {
            clearSelection(); // Deselect if the same square is clicked again.
            return;
        }
        attemptMove(selectedSquare.id, clickedSquare.id);
    } else if (piece) { // No piece is selected, this is the source click.
        const pieceColor = piece.classList.contains('white') ? 'white' : 'black';
        if (pieceColor === gameState.turn) {
            selectSquare(clickedSquare); // Select the square if it's the current player's piece.
        }
    }
}

// --- Drag & Drop Handling ---

/**
 * Handles the `dragstart` event when a user begins dragging a piece.
 * @param {DragEvent} event
 */
function handleDragStart(event) {
    const piece = event.target;
    if (piece.classList.contains('piece')) {
        draggedPiece = piece;
        event.dataTransfer.setData('text/plain', piece.parentElement.id);
        event.dataTransfer.effectAllowed = 'move';
        setTimeout(() => piece.classList.add('dragging'), 0); // Style the piece being dragged.
    } else {
        event.preventDefault(); // Prevent dragging the square itself.
    }
}

/**
 * Handles the `dragover` event, allowing a square to be a valid drop target.
 * @param {DragEvent} event
 */
function handleDragOver(event) {
    event.preventDefault(); // This is necessary to allow a 'drop' event.
    event.dataTransfer.dropEffect = 'move';
}

/**
 * Handles the `drop` event on a target square, triggering a move attempt.
 * @param {DragEvent} event
 */
function handleDrop(event) {
    event.preventDefault();
    const toSquare = event.currentTarget;
    const fromSqId = event.dataTransfer.getData('text/plain');

    if (draggedPiece) draggedPiece.classList.remove('dragging');
    if (fromSqId && toSquare.id !== fromSqId) {
        attemptMove(fromSqId, toSquare.id);
    }
}

/**
 * Handles the `dragend` event, cleaning up styles and state after a drag operation finishes.
 */
function handleDragEnd() {
    if (draggedPiece) {
        draggedPiece.classList.remove('dragging');
        draggedPiece = null;
    }
}

/*
==========================================================================
    6. UI Helper Functions
==========================================================================
*/

// --- Board Interaction ---

/**
 * Visually selects a square by adding the 'selected' CSS class.
 * @param {HTMLElement} square - The DOM element of the square to select.
 */
function selectSquare(square) {
    clearSelection();
    selectedSquare = square;
    square.classList.add('selected');
}

/**
 * Clears any existing visual selection from a square and resets the global variable.
 */
function clearSelection() {
    if (selectedSquare) {
        selectedSquare.classList.remove('selected');
    }
    selectedSquare = null;
}

/**
 * Disables user interaction with the board by adding a 'disabled' class.
 * This is used to prevent input while the AI is "thinking".
 */
function disableBoardInteraction() {
    document.querySelector('.board-container').classList.add('disabled');
}

/**
 * Re-enables user interaction with the board by removing the 'disabled' class.
 */
function enableBoardInteraction() {
    document.querySelector('.board-container').classList.remove('disabled');
}

// --- Notifications & Modals ---

/**
 * Displays a short-lived "toast" notification at the bottom-right of the screen.
 * @param {string} message - The message to display in the toast.
 * @param {string} [type='error'] - The type of toast ('error', 'success', 'info'), used for styling.
 */
function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Toast removes itself after the CSS animation completes (4s total duration).
    setTimeout(() => toast.remove(), 4000);
}

/**
 * Displays the game-over modal with a message indicating the result.
 * @param {string} status - The game status ('checkmate' or 'stalemate').
 * @param {string|null} winner - The winning color ('white' or 'black'), if any.
 */
function showGameOverModal(status, winner) {
    const modal = document.getElementById('game-over-modal');
    const overlay = document.getElementById('modal-overlay');
    const messageEl = document.getElementById('game-over-message');

    let message = '';
    if (status === 'checkmate') {
        const winnerName = (winner === 'white') ? gameState.players.white : gameState.players.black;
        message = `Checkmate! ${winnerName} (${winner}) wins.`;
    } else if (status === 'stalemate') {
        message = 'Stalemate! The game is a draw.';
    }

    messageEl.textContent = message;
    modal.classList.remove('hidden');
    overlay.classList.remove('hidden');
}


// --- Starting Page Errors ---

/**
 * Displays a validation error message on the starting page and highlights empty input fields.
 * @param {string} message - The error message to show.
 */
function showStartError(message) {
    const errorEl = document.getElementById('start_error_message');
    const whiteInput = document.getElementById('white_player');
    const blackInput = document.getElementById('black_player');
    const selectedMode = document.querySelector('input[name="game_mode"]:checked').value;

    errorEl.textContent = message;
    errorEl.classList.add('visible');

    if (!whiteInput.value.trim()) whiteInput.classList.add('input-error');
    if (selectedMode === 'two_player' && !blackInput.value.trim()) {
        blackInput.classList.add('input-error');
    }
}

/**
 * Clears any visible validation error messages and input highlighting on the starting page.
 */
function clearStartError() {
    const errorEl = document.getElementById('start_error_message');
    errorEl.textContent = '';
    errorEl.classList.remove('visible');
    document.getElementById('white_player').classList.remove('input-error');
    document.getElementById('black_player').classList.remove('input-error');
}

/*
==========================================================================
    7. Game Control Logic
==========================================================================
*/

/**
 * Handles the logic for starting a new game from the setup page. It validates
 * inputs, constructs a payload, sends it to the server's `/start` endpoint,
 * and redirects to the game page on success.
 */
function startGame() {
    const whitePlayer = document.getElementById("white_player").value.trim();
    const startButton = document.getElementById("start_button");
    const selectedMode = document.querySelector("input[name='game_mode']:checked").value;

    clearStartError();

    let payload = {};
    if (selectedMode === 'two_player') {
        const blackPlayer = document.getElementById("black_player").value.trim();
        if (!whitePlayer || !blackPlayer) {
            showStartError("Please enter names for both players.");
            return;
        }
        payload = { player_white: whitePlayer, player_black: blackPlayer, game_mode: 'player_vs_player' };
    } else { // 'single_player'
        const aiDifficulty = document.getElementById("ai_difficulty").value;
        if (!whitePlayer) {
            showStartError("Please enter your name.");
            return;
        }
        payload = { player_white: whitePlayer, player_black: `AI (${aiDifficulty})`, difficulty: aiDifficulty, game_mode: 'player_vs_ai' };
    }

    startButton.disabled = true;
    startButton.textContent = "Starting...";

    fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(response => {
            if (response.ok) {
                window.location.href = "/play"; // Redirect to game page on success.
            } else {
                return response.json().then(data => { throw new Error(data.error || "Unknown server error"); });
            }
        })
        .catch(error => {
            showStartError(error.message);
            startButton.disabled = false;
            startButton.textContent = "Start Game";
        });
}

/**
 * Triggers the AI move by calling the `/ai-move` endpoint, then updates the UI
 * with the new game state returned by the server.
 * @async
 */
async function triggerAIMove() {
    try {
        const response = await fetch('/ai-move');
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'AI failed to make a move.');
        }

        moveSound.play().catch(e => console.error("Error playing sound:", e));
        gameState = data.state;
        renderBoard(gameState);
        renderGameInfo(gameState);

        if (gameState.status === 'checkmate' || gameState.status === 'stalemate') {
            showGameOverModal(gameState.status, gameState.winner);
        }

    } catch (error) {
        showToast(error.message);
    } finally {
        // Always re-enable the board after the AI move is complete or an error occurs.
        enableBoardInteraction();
    }
}

/**
 * Handles ending the current game. It calls the `/end` endpoint on the server
 * and redirects the user back to the starting page on success.
 * @async
 */
async function endGame() {
    const endButton = document.getElementById("end_button");
    endButton.disabled = true;
    endButton.textContent = "Ending...";

    try {
        const response = await fetch("/end");
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to end the game.");
        }
        window.location.href = "/"; // Redirect to home/starting page.
    } catch (error) {
        showToast("Error: " + error.message);
        endButton.disabled = false;
        endButton.textContent = "New Game"; // Reset button text on failure.
    }
}