"""
models.py - Chess Game Logic and Data Structures

This module defines the core classes and logic for a chess game. It is responsible
for representing the board, pieces, and game state. It includes rules for
piece movement, move validation, check/checkmate detection, and a simple AI player.

The coordinate system used throughout this module is a 0-indexed tuple `(column, row)`,
where `(0, 0)` corresponds to the 'a1' square.

Classes:
    PieceColor: Enum for piece colors ('white', 'black').
    Difficulty: Enum for AI difficulty levels.
    GameMode: Enum for game modes.
    Board: Manages the 8x8 grid, piece placement, and move validation.
    Piece: Abstract base class for all chess pieces.
    Pawn, Rook, Knight, Bishop, Queen, King: Concrete piece classes with specific move logic.
    Game: High-level controller for the game state, turns, and player management.
    AIPlayer: A simple AI to play against, with different difficulty settings.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from enum import Enum
import random


class PieceColor(Enum):
    """Enumeration for the color of a chess piece or player."""

    WHITE = "white"
    BLACK = "black"

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class Difficulty(Enum):
    """Enumeration for the AI difficulty level."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameMode(Enum):
    """Enumeration for the game mode."""

    PLAYER_VS_PLAYER = "player_vs_player"
    PLAYER_VS_AI = "player_vs_ai"

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class Board:
    """
    Represents the chess board and its state.

    This class manages the piece positions on an 8x8 grid, validates moves,
    and detects check and checkmate conditions.

    Attributes:
        grid (List[List[Optional[Piece]]]): An 8x8 list of lists representing the
            board. Each cell contains either a `Piece` object or `None`.
        moveHistory (List[List[str]]): A list of moves made during the game,
            stored in algebraic notation (e.g., [['e2', 'e4']]).
    """

    def __init__(self):
        """Initializes the Board, creating an empty grid and setting up pieces."""
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.moveHistory = []
        self.setup_board()

    def setup_board(self):
        """Populates the grid with pieces in their standard starting positions."""
        # Pawns
        for i in range(8):
            self.grid[i][1] = Pawn(PieceColor.WHITE, (i, 1))
            self.grid[i][6] = Pawn(PieceColor.BLACK, (i, 6))
        # Rooks
        self.grid[0][0] = Rook(PieceColor.WHITE, (0, 0))
        self.grid[7][0] = Rook(PieceColor.WHITE, (7, 0))
        self.grid[0][7] = Rook(PieceColor.BLACK, (0, 7))
        self.grid[7][7] = Rook(PieceColor.BLACK, (7, 7))
        # Knights
        self.grid[1][0] = Knight(PieceColor.WHITE, (1, 0))
        self.grid[6][0] = Knight(PieceColor.WHITE, (6, 0))
        self.grid[1][7] = Knight(PieceColor.BLACK, (1, 7))
        self.grid[6][7] = Knight(PieceColor.BLACK, (6, 7))
        # Bishops
        self.grid[2][0] = Bishop(PieceColor.WHITE, (2, 0))
        self.grid[5][0] = Bishop(PieceColor.WHITE, (5, 0))
        self.grid[2][7] = Bishop(PieceColor.BLACK, (2, 7))
        self.grid[5][7] = Bishop(PieceColor.BLACK, (5, 7))
        # Queens
        self.grid[3][0] = Queen(PieceColor.WHITE, (3, 0))
        self.grid[3][7] = Queen(PieceColor.BLACK, (3, 7))
        # Kings
        self.grid[4][7] = King(PieceColor.BLACK, (4, 7))
        self.grid[4][0] = King(PieceColor.WHITE, (4, 0))

    def move_piece(self, current_pos: Tuple[int, int], new_pos: Tuple[int, int]) -> bool:
        """
        Moves a piece and validates that the move does not leave the king in check.

        Args:
            current_pos (Tuple[int, int]): The starting (col, row) of the piece.
            new_pos (Tuple[int, int]): The destination (col, row) for the piece.

        Returns:
            bool: True if the move is legal and completed, False otherwise.
        """
        piece: Optional[Piece] = self.grid[current_pos[0]][current_pos[1]]
        if not piece or not piece.is_valid_move(current_pos, new_pos, self.grid):
            return False

        # Temporarily make the move to check for self-check
        captured_piece = self.grid[new_pos[0]][new_pos[1]]
        self.grid[new_pos[0]][new_pos[1]] = piece
        self.grid[current_pos[0]][current_pos[1]] = None
        original_pos = piece.get_position()
        piece.set_position(new_pos)

        # A move is illegal if it places the mover's own king in check.
        if self.is_check() == piece.get_color():
            # Undo the move
            self.grid[current_pos[0]][current_pos[1]] = piece
            self.grid[new_pos[0]][new_pos[1]] = captured_piece
            piece.set_position(original_pos)
            return False

        # If the move is legal, finalize it and record it.
        self.moveHistory.append([piece.pos_to_algebraic(current_pos), piece.pos_to_algebraic(new_pos)])
        return True

    def is_check(self) -> Optional[PieceColor]:
        """
        Determines if a king is currently under attack ('in check').

        Returns:
            Optional[PieceColor]: The color of the king in check, or None if no king is in check.
        """
        white_king_pos, black_king_pos = None, None
        for col in range(8):
            for row in range(8):
                piece = self.grid[col][row]
                if isinstance(piece, King):
                    if piece.get_color() == PieceColor.WHITE:
                        white_king_pos = (col, row)
                    else:
                        black_king_pos = (col, row)
            if white_king_pos and black_king_pos:
                break

        # Check if any piece can attack the opposing king's position.
        for col in range(8):
            for row in range(8):
                piece = self.grid[col][row]
                if piece:
                    if piece.get_color() == PieceColor.WHITE and black_king_pos:
                        if piece.is_valid_move((col, row), black_king_pos, self.grid):
                            return PieceColor.BLACK  # Black king is in check.
                    elif piece.get_color() == PieceColor.BLACK and white_king_pos:
                        if piece.is_valid_move((col, row), white_king_pos, self.grid):
                            return PieceColor.WHITE  # White king is in check.
        return None

    def is_checkmate(self, checked_color: PieceColor) -> bool:
        """
        Determines if a player is in checkmate.

        A player is in checkmate if their king is in check and they have no
        legal moves to escape the check.

        Args:
            checked_color (PieceColor): The color of the player to check for checkmate.

        Returns:
            bool: True if the player is in checkmate, False otherwise.
        """
        # Iterate through every piece of the checked player.
        for col1 in range(8):
            for row1 in range(8):
                piece = self.grid[col1][row1]
                if piece and piece.get_color() == checked_color:
                    # Try every possible destination square for that piece.
                    for col2 in range(8):
                        for row2 in range(8):
                            if piece.is_valid_move((col1, row1), (col2, row2), self.grid):
                                # Simulate the move.
                                captured = self.grid[col2][row2]
                                self.grid[col2][row2] = piece
                                self.grid[col1][row1] = None
                                original_pos = piece.position
                                piece.set_position((col2, row2))

                                # If this move gets the king out of check, it's not checkmate.
                                still_in_check = self.is_check() == checked_color

                                # Undo the move to restore the board state.
                                self.grid[col1][row1] = piece
                                self.grid[col2][row2] = captured
                                piece.set_position(original_pos)

                                if not still_in_check:
                                    return False  # A legal move was found.

        # If no legal move was found after checking all pieces, it's checkmate.
        return True


class Piece:
    """
    Abstract base class for all chess pieces.

    Attributes:
        color (PieceColor): The color of the piece.
        position (Tuple[int, int]): The (column, row) coordinates of the piece.
        symbol (str): A single character representing the piece type and color
                      (e.g., 'P' for white pawn, 'p' for black pawn).
    """

    def __init__(self, color: PieceColor, position: Tuple[int, int], symbol: str):
        """Initializes a Piece with a color, position, and symbol."""
        self.color = color
        self.position = position
        self.symbol = symbol

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], board: List[List[Optional[Piece]]]) -> bool:
        """
        Abstract method to determine if a move is valid for this piece type.

        This method should be implemented by all subclasses. It checks the move
        rules for the specific piece (e.g., pawn forward, bishop diagonal) but
        does not account for check conditions.

        Args:
            current_pos (Tuple[int, int]): The starting (col, row) of the piece.
            next_pos (Tuple[int, int]): The destination (col, row) of the piece.
            board (List[List[Optional[Piece]]]): The current board grid.

        Returns:
            bool: True if the move follows the piece's rules, False otherwise.
        """
        raise NotImplementedError("Subclasses should implement this method")

    @staticmethod
    def pos_to_algebraic(pos: Tuple[int, int]) -> str:
        """Converts a 0-indexed (col, row) tuple to an algebraic notation string."""
        col, row = pos
        return f"{chr(col + ord('a'))}{row + 1}"

    def get_position(self) -> Tuple[int, int]:
        """Returns the current (col, row) position of the piece."""
        return self.position

    def get_algebraic_position(self) -> str:
        """Returns the current position in algebraic notation (e.g., 'e4')."""
        return self.pos_to_algebraic(self.position)

    def set_position(self, newPos: Tuple[int, int]):
        """Updates the piece's position."""
        self.position = newPos

    def get_color(self) -> PieceColor:
        """Returns the color of the piece."""
        return self.color

    def get_symbol(self) -> str:
        """Returns the character symbol of the piece."""
        return self.symbol


class Pawn(Piece):
    """Represents a Pawn, which moves forward and captures diagonally."""

    def __init__(self, color, position):
        super().__init__(color, position, "P" if color == PieceColor.WHITE else "p")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        new_x, new_y = next_pos
        direction = 1 if self.color == PieceColor.WHITE else -1
        start_row = 1 if self.color == PieceColor.WHITE else 6

        # Standard 1-square forward move to an empty square.
        if current_x == new_x and new_y == current_y + direction and not grid[new_x][new_y]:
            return True
        # Initial 2-square forward move from the starting row.
        if (
            current_x == new_x
            and current_y == start_row
            and new_y == current_y + 2 * direction
            and not grid[new_x][new_y]
            and not grid[current_x][current_y + direction]
        ):
            return True
        # Diagonal capture move.
        if (
            abs(current_x - new_x) == 1
            and new_y == current_y + direction
            and grid[new_x][new_y]
            and grid[new_x][new_y].get_color() != self.color
        ):
            return True

        return False


class Rook(Piece):
    """Represents a Rook, which moves horizontally or vertically."""

    def __init__(self, color, position):
        super().__init__(color, position, "R" if color == PieceColor.WHITE else "r")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == self.color:
            return False  # Cannot capture own piece.

        # Vertical move
        if current_x == next_x:
            step = 1 if next_y > current_y else -1
            for y in range(current_y + step, next_y, step):
                if grid[current_x][y]:
                    return False  # Path is blocked.
            return True
        # Horizontal move
        if current_y == next_y:
            step = 1 if next_x > current_x else -1
            for x in range(current_x + step, next_x, step):
                if grid[x][current_y]:
                    return False  # Path is blocked.
            return True

        return False


class Knight(Piece):
    """Represents a Knight, which moves in an 'L' shape and can jump over pieces."""

    def __init__(self, color, position):
        super().__init__(color, position, "N" if color == PieceColor.WHITE else "n")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == self.color:
            return False  # Cannot capture own piece.

        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)
        return (dx == 2 and dy == 1) or (dx == 1 and dy == 2)


class Bishop(Piece):
    """Represents a Bishop, which moves diagonally."""

    def __init__(self, color, position):
        super().__init__(color, position, "B" if color == PieceColor.WHITE else "b")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == self.color:
            return False  # Cannot capture own piece.

        if abs(current_x - next_x) != abs(current_y - next_y):
            return False  # Must be a diagonal move.

        dx = 1 if next_x > current_x else -1
        dy = 1 if next_y > current_y else -1
        x, y = current_x + dx, current_y + dy
        while x != next_x:
            if grid[x][y]:
                return False  # Path is blocked.
            x += dx
            y += dy
        return True


class Queen(Piece):
    """Represents a Queen, which combines the moves of a Rook and a Bishop."""

    def __init__(self, color, position):
        super().__init__(color, position, "Q" if color == PieceColor.WHITE else "q")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        # A Queen's move is valid if it's a valid Rook OR Bishop move.
        is_rook_move = Rook.is_valid_move(self, current_pos, next_pos, grid)
        is_bishop_move = Bishop.is_valid_move(self, current_pos, next_pos, grid)
        return is_rook_move or is_bishop_move


class King(Piece):
    """Represents a King, which moves one square in any direction."""

    def __init__(self, color, position):
        super().__init__(color, position, "K" if color == PieceColor.WHITE else "k")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == self.color:
            return False  # Cannot capture own piece.

        # Move must be exactly one square away in any direction.
        return abs(current_x - next_x) <= 1 and abs(current_y - next_y) <= 1


class Game:
    """
    Manages the overall state and flow of a single chess game.

    This class acts as the main controller, holding the board, tracking the current
    turn, game status, players, and AI settings.

    Attributes:
        board (Optional[Board]): The game's `Board` object. `None` if game not started.
        turn (PieceColor): The color of the player whose turn it is.
        game_status (str): The current status ('not_started', 'active', 'checkmate', etc.).
        winner (Optional[PieceColor]): The color of the winning player, if any.
        difficulty (Optional[Difficulty]): The AI difficulty. `None` for PvP games.
        player_white (str): Name of the player controlling white pieces.
        player_black (str): Name of the player controlling black pieces.
        ai_player (Optional[AIPlayer]): The `AIPlayer` instance for PvAI games.
        game_mode (Optional[GameMode]): The current game mode.
    """

    def __init__(self):
        """Initializes a Game object in a 'not_started' state."""
        self.board = None
        self.turn = PieceColor.WHITE
        self.game_status = "not_started"
        self.winner = None
        self.difficulty = None
        self.player_white = ""
        self.player_black = ""
        self.ai_player = None
        self.game_mode = None

    def start_game(self, difficulty: Optional[Difficulty], white_player: str, black_player: str, game_mode: GameMode):
        """Sets up and starts a new game."""
        self.board = Board()
        self.turn = PieceColor.WHITE
        self.game_status = "active"
        self.winner = None
        self.difficulty = difficulty
        self.player_white = white_player
        self.player_black = black_player
        self.game_mode = game_mode
        if game_mode == str(GameMode.PLAYER_VS_AI):
            self.ai_player = AIPlayer(difficulty)

    def end_game(self):
        """Ends the current game and resets all attributes to their initial state."""
        self.board = None
        self.turn = PieceColor.WHITE
        self.game_status = "not_started"
        self.winner = None
        self.difficulty = None
        self.player_white = ""
        self.player_black = ""
        self.ai_player = None
        self.game_mode = None

    def serialize_board_to_symbols(self, board_grid: List[List[Optional[Piece]]]) -> Optional[List[List[Optional[str]]]]:
        """Converts the object grid into a simple 2D list of piece symbols for serialization."""
        if not board_grid:
            return None

        serialized_grid = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                piece = board_grid[c][r]
                if piece:
                    serialized_grid[r][c] = piece.get_symbol()
        return serialized_grid

    def get_game_state(self) -> dict:
        """
        Returns a dictionary representing the complete current state of the game.

        Returns:
            dict: A dictionary containing all relevant game state information.
        """
        check_status = self.board.is_check()
        return {
            "board": self.serialize_board_to_symbols(self.board.grid),
            "turn": self.turn.value,
            "status": self.game_status,
            "winner": self.winner.value if self.winner else None,
            "is_check": check_status.value if check_status else None,
            "move_history": self.get_move_history(),
            "players": {"white": self.player_white, "black": self.player_black},
            "game_mode": str(self.game_mode),
        }

    def make_move(self, current_pos: Tuple[int, int], new_pos: Tuple[int, int]) -> Tuple[bool, str]:
        """
        Processes a player's move, validates it, and updates the game state.

        Args:
            current_pos (Tuple[int, int]): The starting (col, row) of the move.
            new_pos (Tuple[int, int]): The destination (col, row) of the move.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean for success and a
                              message describing the result.
        """
        if self.game_status != "active":
            return False, f"Game is not active. Status: {self.game_status}"

        piece = self.board.grid[current_pos[0]][current_pos[1]]
        if not piece:
            return False, "No piece at the starting position."

        if piece.get_color() != self.turn:
            return False, f"It's {self.turn.value}'s turn, not {piece.get_color().value}'s."

        move_successful = self.board.move_piece(current_pos, new_pos)
        if not move_successful:
            # Provide more specific feedback if the move was invalid.
            if self.board.is_check() == self.turn:
                return False, "Invalid move: your king would be in check."
            return False, "Invalid move for this piece."

        # After a successful move, check for game-ending conditions.
        self.check_game_end_conditions()

        # If the game is still active, switch turns.
        if self.game_status == "active":
            self.turn = PieceColor.BLACK if self.turn == PieceColor.WHITE else PieceColor.WHITE

        return True, "Move successful."

    def make_ai_move(self) -> Tuple[bool, str]:
        """
        Generates and applies a move for the AI player.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean for success and a
                              message describing the result of the AI's move.
        """
        if self.game_status != "active":
            return False, f"Game is not active. Status: {self.game_status}"
        if not self.ai_player or self.turn != self.ai_player.color:
            return False, "It is not the AI's turn."

        move = self.ai_player.get_best_move(self.board)
        if not move:
            # This implies the AI has no legal moves, which should be handled by end conditions.
            self.check_game_end_conditions()
            return False, f"AI has no legal moves. Game status: {self.game_status}"

        start_pos, end_pos = move
        start_alg = Piece.pos_to_algebraic(start_pos)
        end_alg = Piece.pos_to_algebraic(end_pos)

        success, _ = self.make_move(start_pos, end_pos)
        if success:
            return True, f"AI moved from {start_alg} to {end_alg}."
        else:
            # This case should be rare if get_best_move is correct.
            return False, "AI failed to make a valid move."

    def check_game_end_conditions(self) -> Optional[Tuple[str, PieceColor]]:
        """Check if the game has ended (checkmate, stalemate)"""
        # Check for checkmate
        checked_color: Optional[str] = self.board.is_check()
        if checked_color:
            if self.board.is_checkmate(checked_color):
                self.game_status = "checkmate"
                self.winner = PieceColor.WHITE if checked_color == PieceColor.BLACK else PieceColor.BLACK
                return self.game_status, self.winner
        # Game continues
        self.game_status = "active"

    def get_move_history(self) -> List[List[str]]:
        """Returns the history of moves made in the game."""
        return self.board.moveHistory


class AIPlayer:
    """
    Represents an AI player capable of choosing moves.

    Attributes:
        difficulty (Difficulty): The configured difficulty level of the AI.
        color (PieceColor): The color the AI is playing as (always BLACK).
        PIECE_VALUES (dict): A mapping of piece symbols to their point values,
                             used for evaluating captures.
    """

    def __init__(self, difficulty: Difficulty):
        """Initializes the AI player with a difficulty level."""
        self.difficulty = difficulty
        self.color = PieceColor.BLACK
        self.PIECE_VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}

    def get_best_move(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Determines the best move for the AI based on its difficulty setting.

        Args:
            board (Board): The current game board.

        Returns:
            Optional[Tuple[Tuple[int, int], Tuple[int, int]]]: The chosen move as
                a ((start_col, start_row), (end_col, end_row)) tuple, or None
                if no legal moves are available.
        """
        # For now, all difficulties use the "easy" logic. This can be expanded.
        if self.difficulty in [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]:
            return self.get_easy_move(board)
        return None

    def get_legal_moves(self, board: Board) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generates a list of all possible legal moves for the AI's color.

        A move is legal if it follows piece movement rules and does not result
        in the AI's own king being in check.

        Args:
            board (Board): The current game board.

        Returns:
            List[Tuple[...]: A list of all legal moves.
        """
        legal_moves = []
        for col1 in range(8):
            for row1 in range(8):
                piece = board.grid[col1][row1]
                if piece and piece.get_color() == self.color:
                    start_pos = (col1, row1)
                    for col2 in range(8):
                        for row2 in range(8):
                            end_pos = (col2, row2)
                            if piece.is_valid_move(start_pos, end_pos, board.grid):
                                # Simulate move to check for self-check
                                captured = board.grid[col2][row2]
                                original_pos = piece.position
                                board.grid[col2][row2] = piece
                                board.grid[col1][row1] = None
                                piece.set_position(end_pos)

                                if board.is_check() != self.color:
                                    legal_moves.append((start_pos, end_pos))

                                # Undo the move
                                board.grid[col1][row1] = piece
                                board.grid[col2][row2] = captured
                                piece.set_position(original_pos)
        return legal_moves

    def get_easy_move(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Selects a move based on a simple strategy:
        1. Find all legal moves.
        2. Prioritize moves that capture the highest-value piece.
        3. If no captures are available, choose a random legal move.

        Args:
            board (Board): The current game board.

        Returns:
            Optional[Tuple[...]]: The selected move, or None if no moves exist.
        """
        legal_moves = self.get_legal_moves(board)
        if not legal_moves:
            return None

        best_capture_score = -1
        best_move = None

        # Find the best possible capture.
        for move in legal_moves:
            end_pos = move[1]
            captured_piece = board.grid[end_pos[0]][end_pos[1]]
            if captured_piece:
                score = self.PIECE_VALUES[captured_piece.get_symbol().upper()]
                if score > best_capture_score:
                    best_capture_score = score
                    best_move = move

        # If a capture was found, make that move.
        if best_move:
            return best_move

        # Otherwise, make a random move.
        return random.choice(legal_moves)
