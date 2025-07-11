import os
import json
import csv
from flask import Flask, request, jsonify, render_template, url_for, redirect
from models import Game, Difficulty, Piece, PieceColor, Pawn, Rook, Knight, Bishop, Queen, King

app = Flask(__name__)

# --- File Configuration ---
GAME_STATE_FILE = "data/games.json"
LEADERBOARD_FILE = "data/leaderboard.csv"

# In-memory game object, which will be synced with the file system.
game = Game()

# --- Mapping for Deserialization ---
# Maps character symbols back to their corresponding Piece classes and colors.
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
    """Gets the current game state and formats it for a JSON response."""
    if game.game_status == "not_started":
        return {"error": "Game not started. Please POST to /start first."}

    state = game.get_game_state()
    return state


def update_leaderboard(winner_name, loser_name):
    """Reads, updates, and writes the leaderboard CSV file."""
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
    """
    Converts algebraic chess notation (e.g., 'e4') to a tuple (row, column).
    Returns (row, col) with 1-based indexing: 'a1' -> (1, 1), 'h8' -> (8, 8)
    """
    if len(pos) != 2 or pos[0] not in "abcdefgh" or pos[1] not in "12345678":
        raise ValueError(f"Invalid chess position: {pos}")

    col = ord(pos[0]) - ord("a")  # 'a' → 0, 'h' → 7
    row = int(pos[1]) - 1  # '1' → 0, '8' → 7
    return (col, row)


# --- API Endpoints ---


@app.route("/")
def index():
    """Renders the main page."""
    if game.game_status != "active":
        return render_template("starting_page.html")
    else:
        return redirect(url_for("play"))


@app.route("/play")
def play():
    """Renders the game board page."""
    if game.game_status == "not_started":
        return redirect(url_for("index"))
    return render_template("chess.html")


@app.route("/start", methods=["POST"])
def start_game():
    """Starts a new game, requires player names."""
    global game
    data = request.get_json()
    if not data or "player_white" not in data or "player_black" not in data:
        return jsonify({"error": "Player names 'player_white' and 'player_black' must be provided."}), 400

    difficulty_str = data.get("difficulty", "medium")
    try:
        difficulty = Difficulty(difficulty_str.lower())
    except ValueError:
        return jsonify({"error": "Invalid difficulty. Choose from 'easy', 'medium', or 'hard'."}), 400

    game = Game()  # Create a fresh game instance
    game.start_game(difficulty, data["player_white"], data["player_black"])

    return jsonify(
        {
            "message": f"New game started for {game.player_white} (White) vs. {game.player_black} (Black).",
            "state": get_current_state_json(),
        }
    ), 200


@app.route("/end", methods=["GET"])
def end_game():
    """Ends the current game and resets the game object."""
    game.end_game()
    return jsonify({"message": "Game ended successfully. You can start a new game."}), 200


@app.route("/state", methods=["GET"])
def get_state():
    """Returns the current state of the game."""
    state_data = get_current_state_json()
    if "error" in state_data:
        return jsonify(state_data), 404
    return jsonify(state_data), 200


@app.route("/move", methods=["POST"])
def make_move():
    """Accepts a move, validates it, and updates the board."""
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


@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """Returns leaderboard data from leaderboard.csv."""
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
    """Saves the current game state to games.json."""
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
    """Loads a saved game state from games.json."""
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
    # Add a helper function to models.py for converting algebraic to tuple
    Game.Board.algebraic_to_tuple = lambda self, alg_pos: (ord(alg_pos[0].lower()) - ord("a") + 1, int(alg_pos[1]))
    app.run(debug=True, port=5001)

# --- END OF FILE app.py ---
