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
 * @type {HTMLElement|null}
 * Stores a reference to the DOM element of the currently selected square.
 */
let selectedSquare = null;

/**
 * @type {HTMLElement|null}
 * Stores a reference to the DOM element of the piece being dragged.
 */
let draggedPiece = null;

/**
 * @type {object|null}
 * Stores the entire game state received from the server, including the board,
 * turn, players, move history, and game status.
 */
let gameState = null;

/**
 * @const {Audio}
 * Pre-loads the sound effect for a piece move to ensure it plays instantly.
 */
const moveSound = new Audio('https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/move-self.mp3');
moveSound.volume = 1; // Volume can be adjusted from 0.0 to 1.0


/*
==========================================================================
    2. Main Execution Flow & Initialization
==========================================================================
*/

/**
 * Entry point for the script. Runs after the DOM is fully loaded.
 * Acts as a router to set up event listeners based on which page is currently loaded.
 */
document.addEventListener("DOMContentLoaded", function () {
    const pageId = document.body.id;

    // --- Logic for the Starting Page ---
    if (pageId === "starting-page-body") {
        setupStartingPageListeners();
    }
    // --- Logic for the Main Chess Game Page ---
    else if (pageId === "chess-body") {
        initializeBoard(); // Fetches state and sets up the game
        const endButton = document.getElementById("end_button");
        if (endButton) {
            endButton.addEventListener("click", endGame);
        }
    }
});

/**
 * Initializes the game board by fetching the initial state, setting up
 * event listeners for the squares, and making the board visible.
 */
async function initializeBoard() {
    await updateGameState(); // Fetch initial state and render
    setupSquareEventListeners(); // Add interactivity to squares
    document.querySelector(".board").classList.add("ready"); // Show board to prevent FOUC
}


/**
 * Sets up all event listeners for the starting page.
 */
function setupStartingPageListeners() {
    const startButton = document.getElementById("start_button");
    const whiteInput = document.getElementById("white_player");
    const blackInput = document.getElementById("black_player");
    const gameModeRadios = document.querySelectorAll('input[name="game_mode"]');

    if (startButton) {
        startButton.addEventListener("click", startGame);
    }
    // Allow pressing 'Enter' in input fields to start the game
    whiteInput.addEventListener("keyup", (e) => { if (e.key === "Enter") startGame(); });
    blackInput.addEventListener("keyup", (e) => { if (e.key === "Enter") startGame(); });

    // Clear error messages when the user starts typing
    whiteInput.addEventListener('input', clearStartError);
    blackInput.addEventListener('input', clearStartError);

    // Add listeners for game mode change
    gameModeRadios.forEach(radio => {
        radio.addEventListener('change', handleGameModeChange);
    });
}

/**
 * Handles the change of the game mode radio buttons.
 * Shows/hides the black player name input or the AI difficulty dropdown.
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
    clearStartError(); // Clear errors when mode changes
}


/*
==========================================================================
    3. State Management & Server Communication
==========================================================================
*/

/**
 * Fetches the latest game state from the server's /state endpoint.
 * On success, it updates the global gameState and triggers rendering functions.
 * On failure, it logs and shows a toast with the error.
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
 * Attempts to make a move by sending the 'from' and 'to' squares to the server.
 * - On success: Plays a sound and updates the UI with the new state from the server.
 * - On failure: Shows a toast notification with the error and re-renders the last known
 *   good state to revert any visual changes.
 * @param {string} fromSqId - The ID of the source square (e.g., "e2").
 * @param {string} toSqId - The ID of the destination square (e.g., "e4").
 */
async function attemptMove(fromSqId, toSqId) {
    clearSelection(); // Clear visual selection immediately
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

        // --- Play sound and update UI on a successful move ---
        moveSound.play().catch(e => console.error("Error playing sound:", e));
        gameState = data.state;
        renderBoard(gameState);
        renderGameInfo(gameState);

        // Check for game over conditions
        if (gameState.status === 'checkmate' || gameState.status === 'stalemate') {
            showGameOverModal(gameState.status, gameState.winner);
        }

    } catch (error) {
        showToast(error.message);
        // If move failed, re-render the last known good state to reset piece positions.
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
 * Renders the chessboard based on the provided state object.
 * It clears the board, places pieces, and highlights the king if in check.
 * @param {object} state - The gameState object from the server.
 */
function renderBoard(state) {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const PIECE_UNICODE = {
        'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', // Black pieces
        'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'  // White pieces
    };

    // Clear previous highlights and pieces before redrawing.
    document.querySelectorAll('.square.in-check').forEach(sq => sq.classList.remove('in-check'));
    document.querySelectorAll('.piece').forEach(p => p.remove());

    // Place pieces on the board based on the 2D array from the server state.
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

                // A piece is only draggable if it is that player's turn.
                if (pieceColor === state.turn) {
                    pieceEl.draggable = true;
                }
                square.appendChild(pieceEl);
            }
        }
    }

    // After drawing all pieces, find and highlight the checked king.
    if (state.is_check) {
        const kingSymbol = (state.is_check === 'white') ? 'K' : 'k';
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                if (state.board[r][c] === kingSymbol) {
                    const kingSquareId = files[c] + (r + 1);
                    document.getElementById(kingSquareId).classList.add('in-check');
                    return; // King found and highlighted, exit.
                }
            }
        }
    }
}

/**
 * Renders all game information outside the board, such as player names,
 * turn indicators, and the move history table.
 * @param {object} state - The gameState object from the server.
 */
function renderGameInfo(state) {
    // Update player names
    document.getElementById('white-player-name').textContent = state.players.white || 'White Player';
    document.getElementById('black-player-name').textContent = state.players.black || 'Black Player';

    // Update turn indicators
    document.getElementById('white-turn-indicator').classList.toggle('active-turn', state.turn === 'white');
    document.getElementById('black-turn-indicator').classList.toggle('active-turn', state.turn === 'black');

    // Re-render move history table
    const historyBody = document.getElementById('move-history-body');
    historyBody.innerHTML = ''; // Clear old history

    for (let i = 0; i < state.move_history.length; i += 2) {
        const moveNumber = i / 2 + 1;
        const whiteMove = `${state.move_history[i][0]} → ${state.move_history[i][1]}`;
        const blackMove = state.move_history[i + 1] ? `${state.move_history[i + 1][0]} → ${state.move_history[i + 1][1]}` : '';

        const row = document.createElement('tr');
        row.innerHTML = `<td>${moveNumber}</td><td>${whiteMove}</td><td>${blackMove}</td>`;
        historyBody.appendChild(row);
    }

    // Auto-scroll the move history to show the latest move
    const historyContainer = document.querySelector('.move-history-container');
    historyContainer.scrollTop = historyContainer.scrollHeight;
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
 * Handles a click event on a square.
 * - If no square is selected, it selects the clicked square if it contains a valid piece.
 * - If a square is already selected, it attempts to move the piece to the clicked square.
 * @param {Event} event - The click event.
 */
function handleClick(event) {
    const clickedSquare = event.currentTarget;
    const piece = clickedSquare.querySelector('.piece');

    if (selectedSquare) { // This is the second click (destination)
        if (clickedSquare.id === selectedSquare.id) {
            clearSelection(); // Clicked the same square, so deselect it.
            return;
        }
        attemptMove(selectedSquare.id, clickedSquare.id);
    } else if (piece) { // This is the first click (source)
        const pieceColor = piece.classList.contains('white') ? 'white' : 'black';
        if (pieceColor === gameState.turn) {
            selectSquare(clickedSquare);
        }
    }
}

// --- Drag & Drop Handling ---

/**
 * Handles the start of a drag operation on a piece.
 * @param {DragEvent} event
 */
function handleDragStart(event) {
    const piece = event.target;
    if (piece.classList.contains('piece')) {
        draggedPiece = piece;
        event.dataTransfer.setData('text/plain', piece.parentElement.id);
        event.dataTransfer.effectAllowed = 'move';
        setTimeout(() => piece.classList.add('dragging'), 0); // Add class for styling
    } else {
        event.preventDefault(); // Don't allow dragging the square itself
    }
}

/**
 * Allows a square to be a valid drop target.
 * @param {DragEvent} event
 */
function handleDragOver(event) {
    event.preventDefault(); // Necessary to allow a drop
    event.dataTransfer.dropEffect = 'move';
}

/**
 * Handles the drop event on a square, attempting a move.
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
 * Cleans up after a drag operation is finished (either dropped or cancelled).
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
 * Visually selects a square by adding the 'selected' class.
 * @param {HTMLElement} square - The square element to select.
 */
function selectSquare(square) {
    clearSelection();
    selectedSquare = square;
    square.classList.add('selected');
}

/**
 * Clears any existing square selection and resets the global variable.
 */
function clearSelection() {
    const selected = document.querySelector('.square.selected');
    if (selected) {
        selected.classList.remove('selected');
    }
    selectedSquare = null;
}

// --- Notifications & Modals ---

/**
 * Displays a short-lived toast notification at the bottom-right of the screen.
 * @param {string} message - The message to display in the toast.
 * @param {string} [type='error'] - The type of toast (e.g., 'error'), used for styling.
 */
function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Toast removes itself after CSS animation completes (4s total duration).
    setTimeout(() => toast.remove(), 4000);
}

/**
 * Displays the game over modal with a specific message.
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
 * Displays an error message on the starting page and highlights empty input fields.
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
    if (selectedMode == 'two_player' && !blackInput.value.trim()) {
        blackInput.classList.add('input-error')
    };
}

/**
 * Clears any visible error messages and input highlighting on the starting page.
 */
function clearStartError() {
    const errorEl = document.getElementById('start_error_message');
    errorEl.textContent = ''; // Clear the message text
    errorEl.classList.remove('visible'); // Hide the element by removing the class
    document.getElementById('white_player').classList.remove('input-error');
    document.getElementById('black_player').classList.remove('input-error');
}

/*
==========================================================================
    7. Game Control Logic
==========================================================================
*/

/**
 * Handles the logic for starting a new game from the starting page.
 * It validates input, sends player names to the server, and redirects to the game.
 */
function startGame() {
    const whitePlayer = document.getElementById("white_player").value.trim();
    const startButton = document.getElementById("start_button");
    const selectedMode = document.querySelector("input[name='game_mode']:checked").value

    clearStartError();

    let payload = {};

    if (selectedMode === 'two_player') {
        const blackPlayer = document.getElementById("black_player").value.trim();
        if (!whitePlayer || !blackPlayer) {
            showStartError("Please enter names for both players.");
            return;
        }
        payload = { player_white: whitePlayer, player_black: blackPlayer };
    } else { //single_player
        const aiDifficulty = document.getElementById("ai_difficulty").value;
        if (!whitePlayer) {
            showStartError("Please enter a name for the white player.");
            return;
        }
        payload = { player_white: whitePlayer, player_black: `AI (${aiDifficulty})`, ai_difficulty: aiDifficulty };
    }

    // Disable button to prevent multiple clicks
    startButton.disabled = true;
    startButton.textContent = "Starting...";

    fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(async (response) => {
            const data = await response.json();
            if (response.ok) {
                window.location.href = "/play"; // Redirect to game page on success
            } else {
                throw new Error(data.error || "Unknown error");
            }
        })
        .catch(error => {
            showStartError("Error: " + error.message);
            // Re-enable button on failure
            startButton.disabled = false;
            startButton.textContent = "Start Game";
        });
}

/**
 * Handles the logic for ending a game and returning to the starting page.
 * It calls the /end endpoint on the server and redirects on success.
 */
async function endGame() {
    const endButton = document.getElementById("end_button");
    endButton.disabled = true;
    endButton.textContent = "Ending...";

    try {
        const response = await fetch("/end");
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to end game.");
        }
        window.location.href = "/"; // Redirect to home/starting page
    } catch (error) {
        showToast("Error: " + error.message);
        endButton.disabled = false;
        endButton.textContent = "New Game"; // Reset button text on failure
    }
}