"""
app.py - Flask backend for Chess Game

This module provides the server-side logic for a web-based chess game.
It manages the game state, player actions, AI moves, leaderboard, and file I/O.

Key Features:
- RESTful API endpoints for game control, moves, state, leaderboard, save/load
- In-memory and file-based persistence for game state and leaderboard
- Handles both player-vs-player and player-vs-AI modes
- Uses models.py for chess logic and data structures
"""

import os
import json
import csv
from flask import Flask, request, jsonify, render_template, url_for, redirect
from models import Game, Difficulty, Piece, PieceColor, Pawn, Rook, Knight, Bishop, Queen, King

app = Flask(__name__)

# --- File Configuration ---
GAME_STATE_FILE = "data/games.json"  # Path to the file for saving/loading game state.
LEADERBOARD_FILE = "data/leaderboard.csv"  # Path to the CSV file for storing player leaderboard data.

# In-memory game object, which will be synced with the file system.
# This global object holds the state of the currently active game.
game = Game()

# --- Mapping for Deserialization ---
# Maps character symbols back to their corresponding Piece classes and colors.
# This is used when loading a game state from a file or another serialized format.
PIECE_MAP = {
    "p": (Pawn, PieceColor.BLACK),
    "r": (Rook, PieceColor.BLACK),
    "n": (Knight, PieceColor.BLACK),
    "b": (Bishop, PieceColor.BLACK),
    "q": (Queen, PieceColor.BLACK),
    "k": (King, PieceColor.BLACK),
    "P": (Pawn, PieceColor.WHITE),
    "R": (Rook, PieceColor.WHITE),
    "N": (Knight, PieceColor.WHITE),
    "B": (Bishop, PieceColor.WHITE),
    "Q": (Queen, PieceColor.WHITE),
    "K": (King, PieceColor.WHITE),
}

# --- Helper Functions for File I/O and Serialization ---


def get_current_state_json():
    """Gets the current game state and formats it for a JSON response.

    If no game has been started, it returns an error dictionary. Otherwise,
    it calls the `get_game_state` method on the global `game` object.

    Returns:
        dict: A dictionary representing the current game state or an error message.
    """
    if game.game_status == "not_started":
        return {"error": "Game not started. Please POST to /start first."}

    state = game.get_game_state()
    return state


def update_leaderboard(winner_name, loser_name):
    """Reads, updates, and writes the leaderboard CSV file.

    This function is called when a game ends in a checkmate. It updates the win/loss
    records for the specified players. If a player is not already in the
    leaderboard, they are added.

    Args:
        winner_name (str): The name of the winning player.
        loser_name (str): The name of the losing player.
    """
    records = []
    player_found = {"winner": False, "loser": False}

    # Read existing data
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["player_name"] == winner_name:
                    row["wins"] = int(row["wins"]) + 1
                    player_found["winner"] = True
                elif row["player_name"] == loser_name:
                    row["losses"] = int(row["losses"]) + 1
                    player_found["loser"] = True
                records.append(row)

    # Add new players if they weren't in the file
    if not player_found["winner"]:
        records.append({"player_name": winner_name, "wins": 1, "losses": 0, "draws": 0})
    if not player_found["loser"]:
        records.append({"player_name": loser_name, "wins": 0, "losses": 1, "draws": 0})

    # Write all data back to the file
    with open(LEADERBOARD_FILE, mode="w", newline="") as f:
        fieldnames = ["player_name", "wins", "losses", "draws"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def algebraic_to_tuple(pos: str) -> tuple[int, int]:
    """Converts algebraic chess notation (e.g., 'e4') to a 0-indexed tuple.

    Args:
        pos (str): The algebraic notation string (e.g., 'a1', 'h8').

    Returns:
        tuple[int, int]: A 0-indexed (column, row) tuple. For example,
                         'a1' becomes (0, 0) and 'h8' becomes (7, 7).

    Raises:
        ValueError: If the input string is not valid algebraic notation.
    """
    if len(pos) != 2 or pos[0] not in "abcdefgh" or pos[1] not in "12345678":
        raise ValueError(f"Invalid chess position: {pos}")

    col = ord(pos[0]) - ord("a")  # 'a' -> 0, 'h' -> 7
    row = int(pos[1]) - 1  # '1' -> 0, '8' -> 7
    return (col, row)


# --- API Endpoints ---


@app.route("/")
def index():
    """Renders the main page.

    If a game is not active, it displays the starting page where users can
    set up a new game. If a game is already active, it redirects the user to the
    `/play` route to continue their game.
    """
    if game.game_status != "active":
        return render_template("starting_page.html")
    else:
        return redirect(url_for("play"))


@app.route("/play")
def play():
    """Renders the game board page.

    If a game is active, it displays the main `chess.html` template.
    If no game has been started, it redirects back to the index page.
    """
    if game.game_status == "not_started":
        return redirect(url_for("index"))
    return render_template("chess.html")


@app.route("/start", methods=["POST"])
def start_game():
    """Starts a new game.

    Initializes a new global `game` object based on the provided settings.
    This endpoint expects a JSON payload with player names and game mode.

    JSON Payload:
        {
            "player_white": "Player1",
            "player_black": "Player2",
            "game_mode": "player_vs_player" | "player_vs_ai",
            "difficulty": "easy" | "medium" | "hard" (optional, required for AI mode)
        }

    Returns:
        JSON: A success message and the initial game state, or an error message.
              (200 OK, 400 Bad Request)
    """
    global game
    data = request.get_json()
    difficulty = None
    if not data or "player_white" not in data or "player_black" not in data or "game_mode" not in data:
        return jsonify(
            {"error": "Player names 'player_white' and 'player_black' must be provided.Along with the game mode."}
        ), 400

    if data["game_mode"] == "player_vs_ai":
        difficulty_str = data.get("difficulty")
        try:
            difficulty = Difficulty(difficulty_str.lower())
        except ValueError:
            return jsonify({"error": "Invalid difficulty. Choose from 'easy', 'medium', or 'hard'."}), 400

    game = Game()  # Create a fresh game instance
    game.start_game(difficulty, data["player_white"], data["player_black"], data["game_mode"])

    return jsonify(
        {
            "message": f"New game started for {game.player_white} (White) vs. {game.player_black} (Black).",
            "state": get_current_state_json(),
        }
    ), 200


@app.route("/end", methods=["GET"])
def end_game():
    """Ends the current game and resets the global game object.

    This allows users to return to the starting screen to begin a new game
    without restarting the server.

    Returns:
        JSON: A confirmation message. (200 OK)
    """
    game.end_game()
    return jsonify({"message": "Game ended successfully. You can start a new game."}), 200


@app.route("/state", methods=["GET"])
def get_state():
    """Returns the current state of the game.

    This is a public API endpoint for fetching the complete game state, including
    the board layout, current turn, game status, and player information.

    Returns:
        JSON: The current game state object, or an error if the game is not
              started. (200 OK, 404 Not Found)
    """
    state_data = get_current_state_json()
    if "error" in state_data:
        return jsonify(state_data), 404
    return jsonify(state_data), 200


@app.route("/move", methods=["POST"])
def make_move():
    """Accepts a move, validates it, and updates the board.

    This endpoint processes a player's move. It validates the move's legality
    through the `game.make_move` method. If the move results in a checkmate,
    it updates the leaderboard.

    JSON Payload:
        {
            "from": "e2",
            "to": "e4"
        }

    Returns:
        JSON: A success message and the updated game state, or an error message
              explaining why the move was invalid. (200 OK, 400 Bad Request)
    """
    if game.game_status != "active":
        return jsonify({"error": f"Game not active (status: {game.game_status}). Please start a new game."}), 400

    data = request.get_json()
    if not data or "from" not in data or "to" not in data:
        return jsonify({"error": "Move requires 'from' and 'to' positions in algebraic notation (e.g., 'e2')."}), 400

    try:
        start_pos = algebraic_to_tuple(data["from"])
        end_pos = algebraic_to_tuple(data["to"])
    except ValueError:
        return jsonify({"error": "Invalid algebraic notation. Use format like 'a2'."}), 400

    success, message = game.make_move(start_pos, end_pos)

    if success:
        # Check if the game ended to update the leaderboard
        if game.game_status == "checkmate":
            winner = game.player_white if game.winner == PieceColor.WHITE else game.player_black
            loser = game.player_black if game.winner == PieceColor.WHITE else game.player_white
            update_leaderboard(winner, loser)
            message = f"Checkmate! {winner} wins."

        response = {"message": message, "state": get_current_state_json()}
        return jsonify(response), 200
    else:
        return jsonify({"error": message}), 400


@app.route("/ai-move", methods=["GET"])
def ai_move():
    """Generates and applies a move for the AI player.

    This should be called when it is the AI's turn in a 'player_vs_ai' game.
    It triggers the `game.make_ai_move` method to calculate and perform a move.

    Returns:
        JSON: A message describing the AI's move and the updated game state,
              or an error if an AI move cannot be made. (200 OK, 400 Bad Request)
    """

    if game.game_status != "active" or not game.ai_player:
        return jsonify({"error": "AI move not available. Ensure the game is active and against AI."}), 400

    success, message = game.make_ai_move()
    if success:
        return jsonify({"message": message, "state": get_current_state_json()}), 200
    else:
        return jsonify({"error": message}), 400


@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """Returns leaderboard data from the CSV file.

    Reads the `leaderboard.csv` file, converts its contents to a list of
    JSON objects, sorts them by wins in descending order, and returns the list.

    Returns:
        JSON: A list of player objects, each with 'player_name', 'wins',
              'losses', and 'draws'. The list is sorted by wins. (200 OK)
    """
    if not os.path.exists(LEADERBOARD_FILE):
        return jsonify([]), 200  # Return empty list if file doesn't exist

    leaderboard = []
    with open(LEADERBOARD_FILE, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numbers to int for proper JSON typing
            row["wins"] = int(row["wins"])
            row["losses"] = int(row["losses"])
            row["draws"] = int(row["draws"])
            leaderboard.append(row)

    # Sort by wins, descending
    leaderboard.sort(key=lambda x: x["wins"], reverse=True)
    return jsonify(leaderboard), 200


@app.route("/save", methods=["POST"])
def save_game_to_file():
    """Saves the current game state to `games.json`.

    Serializes the current in-memory `game` object and writes it to the
    `GAME_STATE_FILE`.

    Returns:
        JSON: A success message, or an error if there is no active game
              to save. (200 OK, 400 Bad Request)
    """
    if game.game_status == "not_started":
        return jsonify({"error": "No active game to save."}), 400

    # Create a dictionary matching the required file format
    state_to_save = {
        "game_id": 1,  # Using a static ID as per the example
        "game": get_current_state_json(),
    }

    with open(GAME_STATE_FILE, "w") as f:
        json.dump(state_to_save, f, indent=4)

    return jsonify({"message": f"Game state saved to {GAME_STATE_FILE}."}), 200


@app.route("/load", methods=["GET"])
def load_game_from_file():
    """Loads a saved game state from `games.json`.

    Reads the `GAME_STATE_FILE`, reconstructs the `Game` object from the
    JSON data, and replaces the global `game` instance with the loaded game.
    This allows play to resume from a previously saved state.

    Returns:
        JSON: A success message and the loaded game state, or an error if
              the file doesn't exist. (200 OK, 404 Not Found)
    """
    global game
    if not os.path.exists(GAME_STATE_FILE):
        return jsonify({"error": f"No saved game file found at {GAME_STATE_FILE}."}), 404

    with open(GAME_STATE_FILE, "r") as f:
        data = json.load(f)

    # Reconstruct the game object from the loaded data
    loaded_game = Game()
    loaded_game.board = Game.Board()  # Use the nested Board class for clarity
    loaded_game.board.grid = [[None for _ in range(9)] for _ in range(9)]

    # Re-create Piece objects on the board
    board_data = data["board"]
    for r_idx, row in enumerate(board_data):
        for c_idx, symbol in enumerate(row):
            if symbol:
                piece_class, color = PIECE_MAP[symbol]
                # Convert 0-indexed from file to 1-indexed for model
                pos_tuple = (c_idx + 1, r_idx + 1)
                loaded_game.board.grid[c_idx + 1][r_idx + 1] = piece_class(color, pos_tuple)

    loaded_game.turn = PieceColor(data["turn"])
    loaded_game.board.moveHistory = data["history"]
    loaded_game.game_status = data["status"]
    loaded_game.winner = PieceColor(data["winner"]) if data.get("winner") else None
    loaded_game.player_white = data["players"]["white"]
    loaded_game.player_black = data["players"]["black"]

    game = loaded_game  # Replace the global game object with the loaded one

    return jsonify({"message": "Game state loaded successfully.", "state": get_current_state_json()}), 200


if __name__ == "__main__":
    app.run(debug=True)

# --- END OF FILE app.py ---
