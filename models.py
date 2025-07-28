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
        self.position_history = {}
        self.setup_board()

    def setup_board(self):
        """Populates the grid with pieces in their standard starting positions."""
        for i in range(8):
            self.grid[i][1] = Pawn(PieceColor.WHITE, (i, 1))
            self.grid[i][6] = Pawn(PieceColor.BLACK, (i, 6))
        self.grid[0][0] = Rook(PieceColor.WHITE, (0, 0))
        self.grid[7][0] = Rook(PieceColor.WHITE, (7, 0))
        self.grid[0][7] = Rook(PieceColor.BLACK, (0, 7))
        self.grid[7][7] = Rook(PieceColor.BLACK, (7, 7))
        self.grid[1][0] = Knight(PieceColor.WHITE, (1, 0))
        self.grid[6][0] = Knight(PieceColor.WHITE, (6, 0))
        self.grid[1][7] = Knight(PieceColor.BLACK, (1, 7))
        self.grid[6][7] = Knight(PieceColor.BLACK, (6, 7))
        self.grid[2][0] = Bishop(PieceColor.WHITE, (2, 0))
        self.grid[5][0] = Bishop(PieceColor.WHITE, (5, 0))
        self.grid[2][7] = Bishop(PieceColor.BLACK, (2, 7))
        self.grid[5][7] = Bishop(PieceColor.BLACK, (5, 7))
        self.grid[3][0] = Queen(PieceColor.WHITE, (3, 0))
        self.grid[3][7] = Queen(PieceColor.BLACK, (3, 7))
        self.grid[4][7] = King(PieceColor.BLACK, (4, 7))
        self.grid[4][0] = King(PieceColor.WHITE, (4, 0))
        self.record_position(PieceColor.WHITE)

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
        if not piece or new_pos not in piece.get_moves(self.grid):
            return False
        # Temporarily make the move to check for self-check
        captured_piece = self.grid[new_pos[0]][new_pos[1]]
        self.grid[new_pos[0]][new_pos[1]] = piece
        self.grid[current_pos[0]][current_pos[1]] = None
        original_pos = piece.get_position()
        piece.set_position(new_pos)
        # A move is illegal if it places the mover's own king in check.
        if self.is_color_in_check(piece.get_color()):
            # Undo the move
            self.grid[current_pos[0]][current_pos[1]] = piece
            self.grid[new_pos[0]][new_pos[1]] = captured_piece
            piece.set_position(original_pos)
            return False
        # If the move is legal, finalize it and record it.
        self.moveHistory.append([piece.pos_to_algebraic(current_pos), piece.pos_to_algebraic(new_pos)])
        return True

    def is_square_attacked_by(self, pos: Tuple[int, int], attacking_color: PieceColor) -> bool:
        """
        Checks if a given square 'pos' is being attacked by any piece of the
        'attacking_color'.
        """
        target_x, target_y = pos
        grid = self.grid
        # 1. Check for Pawn attacks
        pawn_direction = -1 if attacking_color == PieceColor.WHITE else 1
        for dx in [-1, 1]:
            px, py = target_x + dx, target_y + pawn_direction
            if 0 <= px <= 7 and 0 <= py <= 7:
                piece = grid[px][py]
                if isinstance(piece, Pawn) and piece.color == attacking_color:
                    return True
        # 2. Check for Knight attacks
        for dx, dy in [(1, 2), (-1, 2), (1, -2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1)]:
            nx, ny = target_x + dx, target_y + dy
            if 0 <= nx <= 7 and 0 <= ny <= 7:
                piece = grid[nx][ny]
                if isinstance(piece, Knight) and piece.color == attacking_color:
                    return True
        # 3. Check for sliding attacks (Rook, Bishop, Queen) and King attacks
        # 8 directions: 4 diagonal, 4 orthogonal
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1), (0, 1), (0, -1), (1, 0), (-1, 0)]:
            for i in range(1, 8):
                sx, sy = target_x + i * dx, target_y + i * dy
                if not (0 <= sx <= 7 and 0 <= sy <= 7):
                    break  # Off the board
                piece = grid[sx][sy]
                if piece:
                    # Is it an attacking piece of the correct color?
                    if piece.color == attacking_color:
                        # Diagonal check for Bishop/Queen
                        if (dx, dy) in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                            if isinstance(piece, (Bishop, Queen)):
                                return True
                            if i == 1 and isinstance(piece, King):
                                return True
                        # Orthogonal check for Rook/Queen
                        else:
                            if isinstance(piece, (Rook, Queen)):
                                return True
                            if i == 1 and isinstance(piece, King):
                                return True
                    # If any piece is blocking the path, we can stop searching in this direction.
                    break
        return False

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
        if white_king_pos and self.is_square_attacked_by(white_king_pos, PieceColor.BLACK):
            return PieceColor.WHITE
        if black_king_pos and self.is_square_attacked_by(black_king_pos, PieceColor.WHITE):
            return PieceColor.BLACK
        return None

    def is_color_in_check(self, color: PieceColor) -> bool:
        """
        Checks if a specific color's king is in check.

        Args:
            color (PieceColor): The color of the player to check.

        Returns:
            bool: True if the king of the specified color is in check, False otherwise.
        """
        king_pos = None
        for col in range(8):
            for row in range(8):
                piece = self.grid[col][row]
                if isinstance(piece, King):
                    if piece.get_color() == color:
                        king_pos = (col, row)
                        if self.is_square_attacked_by(
                            king_pos, PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
                        ):
                            return True
        return False

    def is_checkmate(self, checked_color: PieceColor) -> bool:
        """
        Determines if a player is in checkmate.
        A player is in checkmate if their king is in check and they have no
        legal moves to escape the check. This is determined by checking if the
        player is currently in check and has no legal moves.
        Args:
            checked_color (PieceColor): The color of the player to check for checkmate.
        Returns:
            bool: True if the player is in checkmate, False otherwise.
        """
        # A player can't be in checkmate if they are not in check.
        # And if they have any legal move, they are not in checkmate.
        return self.is_color_in_check(checked_color) and not self.has_legal_move(checked_color)

    def has_legal_move(self, color: PieceColor) -> bool:
        """
        Checks if a player has at least one legal move.
        This method is more efficient than generating all legal moves, as it
        returns True as soon as the first legal move is found.
        Args:
            color (PieceColor): The color of the player to check.
        Returns:
            bool: True if at least one legal move exists, False otherwise.
        """
        for col in range(8):
            for row in range(8):
                piece = self.grid[col][row]
                if piece and piece.color == color:
                    start_pos = (col, row)
                    for end_pos in piece.get_moves(self.grid):
                        # Simulate the move
                        captured_piece = self.grid[end_pos[0]][end_pos[1]]
                        self.grid[end_pos[0]][end_pos[1]] = piece
                        self.grid[start_pos[0]][start_pos[1]] = None
                        original_pos = piece.position
                        piece.set_position(end_pos)
                        # Check if the king is STILL in check after this move
                        still_in_check = self.is_color_in_check(color)
                        # Undo the move to restore board state
                        self.grid[start_pos[0]][start_pos[1]] = piece
                        self.grid[end_pos[0]][end_pos[1]] = captured_piece
                        piece.set_position(original_pos)
                        if not still_in_check:
                            # Found a legal move, no need to search further.
                            return True
        # Looped through all possible moves and found none that are legal.
        return False

    def get_all_legal_moves(self, color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generates a list of all legal moves for a given color.
        A move is legal if it follows piece movement rules and does not leave the
        player's own king in check.

        Args:
            color (PieceColor): The color of the player to generate moves for.

        Returns:
            List[Tuple[Tuple[int, int], Tuple[int, int]]]: A list of legal moves,
                where each move is ((start_col, start_row), (end_col, end_row)).
        """
        legal_moves = []
        for col in range(8):
            for row in range(8):
                piece = self.grid[col][row]
                if piece and piece.color == color:
                    start_pos = (col, row)
                    for end_pos in piece.get_moves(self.grid):
                        # Simulate the move to check for self-check
                        captured = self.grid[end_pos[0]][end_pos[1]]
                        original_pos = piece.position
                        self.grid[end_pos[0]][end_pos[1]] = piece
                        self.grid[start_pos[0]][start_pos[1]] = None
                        piece.set_position(end_pos)
                        if not self.is_color_in_check(color):
                            legal_moves.append((start_pos, end_pos))
                        # Undo the move
                        self.grid[start_pos[0]][start_pos[1]] = piece
                        self.grid[end_pos[0]][end_pos[1]] = captured
                        piece.set_position(original_pos)
        return legal_moves

    def get_position_hash(self, turn: PieceColor) -> str:
        """
        Generates a unique string representation (hash) of the current board state,
        including piece positions and the current turn. Uses a simplified FEN notation.
        """
        parts = []
        for row in reversed(range(8)):
            empty_count = 0
            row_str = ""
            for col in range(8):
                piece = self.grid[col][row]
                if piece:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += piece.get_symbol()
                else:
                    empty_count += 1
            if empty_count > 0:
                row_str += str(empty_count)
            parts.append(row_str)
        # Add the current turn to make the hash unique to the player to move.
        return "/".join(parts) + " " + turn.value[0]

    def record_position(self, turn: PieceColor):
        """Records the current board state in the position history."""
        pos_hash = self.get_position_hash(turn)
        self.position_history[pos_hash] = self.position_history.get(pos_hash, 0) + 1


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

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        """
        Generates a list of pseudo-legal moves for this piece.

        "Pseudo-legal" means they follow the piece's move rules but do not
        account for whether the move would leave the king in check.

        Args:
            grid (List[List[Optional[Piece]]]): The current board grid.

        Returns:
            List[Tuple[int, int]]: A list of possible destination coordinates.
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

    def get_moves(self, grid: List[List[Optional[Piece]]]) -> List[Tuple[int, int]]:
        moves = []
        x, y = self.position
        direction = 1 if self.color == PieceColor.WHITE else -1
        start_row = 1 if self.color == PieceColor.WHITE else 6
        if 0 <= y + direction <= 7 and not grid[x][y + direction]:
            moves.append((x, y + direction))
            # 2-square forward (only if 1-square is also possible)
            if y == start_row and not grid[x][y + 2 * direction]:
                moves.append((x, y + 2 * direction))
        # Captures
        for dx in [-1, 1]:
            if 0 <= x + dx <= 7 and 0 <= y + direction <= 7:
                target = grid[x + dx][y + direction]
                if target and target.get_color() != self.color:
                    moves.append((x + dx, y + direction))
        return moves


class Rook(Piece):
    """Represents a Rook, which moves horizontally or vertically."""
    def __init__(self, color, position):
        super().__init__(color, position, "R" if color == PieceColor.WHITE else "r")

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        moves = []
        x, y = self.position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            for i in range(1, 8):
                nx, ny = x + i * dx, y + i * dy
                if not (0 <= nx <= 7 and 0 <= ny <= 7):
                    break
                target = grid[nx][ny]
                if target:
                    if target.get_color() != self.color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
        return moves


class Knight(Piece):
    """Represents a Knight, which moves in an 'L' shape and can jump over pieces."""
    def __init__(self, color, position):
        super().__init__(color, position, "N" if color == PieceColor.WHITE else "n")

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        moves = []
        x, y = self.position
        potential_moves = [
            (x + 1, y + 2), (x - 1, y + 2), (x + 1, y - 2), (x - 1, y - 2),
            (x + 2, y + 1), (x - 2, y + 1), (x + 2, y - 1), (x - 2, y - 1),
        ]
        for nx, ny in potential_moves:
            if 0 <= nx <= 7 and 0 <= ny <= 7:
                target = grid[nx][ny]
                if not target or target.get_color() != self.color:
                    moves.append((nx, ny))
        return moves


class Bishop(Piece):
    """Represents a Bishop, which moves diagonally."""
    def __init__(self, color, position):
        super().__init__(color, position, "B" if color == PieceColor.WHITE else "b")

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        moves = []
        x, y = self.position
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            for i in range(1, 8):
                nx, ny = x + i * dx, y + i * dy
                if not (0 <= nx <= 7 and 0 <= ny <= 7):
                    break
                target = grid[nx][ny]
                if target:
                    if target.get_color() != self.color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
        return moves


class Queen(Piece):
    """Represents a Queen, which combines the moves of a Rook and a Bishop."""
    def __init__(self, color, position):
        super().__init__(color, position, "Q" if color == PieceColor.WHITE else "q")

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        # A Queen's moves are the combination of a Rook's and a Bishop's moves.
        return Rook.get_moves(self, grid) + Bishop.get_moves(self, grid)


class King(Piece):
    """Represents a King, which moves one square in any direction."""
    def __init__(self, color, position):
        super().__init__(color, position, "K" if color == PieceColor.WHITE else "k")

    def get_moves(self, grid: List[List[Optional["Piece"]]]) -> List[Tuple[int, int]]:
        moves = []
        x, y = self.position
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx <= 7 and 0 <= ny <= 7:
                    target = grid[nx][ny]
                    if not target or target.get_color() != self.color:
                        moves.append((nx, ny))
        return moves


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

    def start_game(
        self,
        difficulty: Optional[Difficulty],
        white_player: str,
        black_player: str,
        game_mode: GameMode,
    ):
        """Sets up and starts a new game."""
        self.board = Board()
        self.turn = PieceColor.WHITE
        self.game_status = "active"
        self.winner = None
        self.difficulty = difficulty
        self.player_white = white_player
        self.player_black = black_player
        self.game_mode = game_mode
        if game_mode == GameMode.PLAYER_VS_AI:
            self.ai_player = AIPlayer(difficulty, PieceColor.BLACK)

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
            if self.board.is_color_in_check(self.turn):
                return False, "Invalid move: your king would be in check."
            return False, "Invalid move for this piece."
        # After a successful move, check for game-ending conditions.
        self.check_game_end_conditions()
        # If the game is still active, switch turns.
        if self.game_status == "active":
            self.turn = PieceColor.BLACK if self.turn == PieceColor.WHITE else PieceColor.WHITE
            self.board.record_position(self.turn)
        return True, "Move successful."

    def make_ai_move(self, color: PieceColor = None) -> Tuple[bool, str]:
        """
        Generates and applies a move for the AI player of the specified color.
        If no color is specified, uses the current turn.

        Args:
            color (PieceColor, optional): The color of the AI to move.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean for success and a
                              message describing the result of the AI's move.
        """
        if self.game_status != "active":
            return False, f"Game is not active. Status: {self.game_status}"
        if color is None:
            color = self.turn
        if color != self.turn:
            return False, f"It is not {color.value}'s turn."
        if not self.ai_player:
            return False, f"No AI player configured for {color.value}."
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
            return True, f"AI ({color.value}) moved from {start_alg} to {end_alg}."
        else:
            # This case should be rare if get_best_move is correct.
            return False, "AI failed to make a valid move."

    def check_game_end_conditions(self) -> Optional[Tuple[str, PieceColor]]:
        """Check if the game has ended (checkmate, stalemate)"""
        checked_color: Optional[str] = self.board.is_check()
        if checked_color:
            if self.board.is_checkmate(checked_color):
                self.game_status = "checkmate"
                self.winner = PieceColor.WHITE if checked_color == PieceColor.BLACK else PieceColor.BLACK
                return self.game_status, self.winner
        self.game_status = "active"

    def get_move_history(self) -> List[List[str]]:
        """Returns the history of moves made in the game."""
        return self.board.moveHistory

    def get_possible_moves(self, pos: Tuple[int, int]) -> List[str]:
        """
        Gets all legally possible moves for a piece at a given position,
        returning them in algebraic notation for the frontend.
        """
        if not self.board or self.game_status != "active":
            return []
        piece = self.board.grid[pos[0]][pos[1]]
        if not piece or piece.get_color() != self.turn:
            return []
        legal_moves = []
        pseudo_legal_moves = piece.get_moves(self.board.grid)
        # We must check each pseudo-legal move to see if it's truly legal (doesn't cause self-check)
        for end_pos in pseudo_legal_moves:
            # Simulate move
            captured = self.board.grid[end_pos[0]][end_pos[1]]
            original_pos = piece.position
            self.board.grid[end_pos[0]][end_pos[1]] = piece
            self.board.grid[pos[0]][pos[1]] = None
            piece.set_position(end_pos)
            if not self.board.is_color_in_check(self.turn):
                legal_moves.append(Piece.pos_to_algebraic(end_pos))
            # Undo move
            self.board.grid[pos[0]][pos[1]] = piece
            self.board.grid[end_pos[0]][end_pos[1]] = captured
            piece.set_position(original_pos)
        return legal_moves


class AIPlayer:
    """
    Represents an AI player that can make moves based on a difficulty level.
    This class uses a simple evaluation function and a minimax algorithm with alpha-beta pruning
    to determine the best move for the AI.
    Attributes:
        difficulty (Difficulty): The difficulty level of the AI.
        color (PieceColor): The color of the AI player.
        PIECE_VALUES (Dict[str, int]): A dictionary mapping piece symbols to their values.
        POSITION_TABLES (Dict[str, List[List[int]]]): A dictionary mapping piece symbols to their
            position evaluation tables, which provide a score based on the piece's position on the board.
    """
    PAWN_TABLE = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    KNIGHT_TABLE = [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ]
    BISHOP_TABLE = [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ]
    ROOK_TABLE = [
        [0, 0, 0, 5, 5, 0, 0, 0],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    QUEEN_TABLE = [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ]

    def __init__(self, difficulty: Difficulty, color: PieceColor):
        """Initializes the AIPlayer with a difficulty level and color."""
        self.difficulty = difficulty
        self.color = color
        self.PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}
        self.POSITION_TABLES = {
            "P": self.PAWN_TABLE, "N": self.KNIGHT_TABLE, "B": self.BISHOP_TABLE,
            "R": self.ROOK_TABLE, "Q": self.QUEEN_TABLE,
        }

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
        legal_moves = self.get_legal_moves(board, self.color)
        if not legal_moves:
            return None
        if self.difficulty == Difficulty.EASY:
            return self.get_easy_move(board)
        elif self.difficulty == Difficulty.MEDIUM:
            return self.get_medium_move(board)
        elif self.difficulty == Difficulty.HARD:
            return self.get_hard_move(board)
        return None

    def get_legal_moves(self, board: Board, color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generates a list of all possible legal moves for the AI's color by calling
        the board's move generation method.

        Args:
            board (Board): The current game board.
            color (PieceColor): The color of the AI player.

        Returns:
            List[Tuple[Tuple[int, int], Tuple[int, int]]]: A list of valid moves.
        """
        return board.get_all_legal_moves(color)

    def evaluate_board(self, board: Board, turn: PieceColor) -> float:
        """
        Calculates a score for the current board state from the AI's perspective.
        The evaluation function considers:
        - Material value: Each piece has a point value.
        - Positional value: Pieces are worth more on certain squares.
        - Repetition penalty: Discourages repeating moves that lead to a draw.
        The final score is relative to the AI player's color (`self.color`). A positive
        score is good for the AI, while a negative score is good for the opponent.

        Args:
            board (Board): The board state to evaluate.
            turn (PieceColor): The player whose turn it is in this position.

        Returns:
            float: The calculated score for the board position.
        """
        total_value = 0
        for col in range(8):
            for row in range(8):
                piece = board.grid[col][row]
                if piece:
                    piece_type = piece.get_symbol().upper()
                    material_value = self.PIECE_VALUES[piece_type]
                    pos_table = self.POSITION_TABLES.get(piece_type)
                    positional_value = 0
                    if pos_table:
                        if piece.get_color() == PieceColor.WHITE:
                            positional_value = pos_table[row][col]
                        else:
                            positional_value = pos_table[7 - row][col]
                    score = material_value + positional_value
                    if piece.get_color() == self.color:
                        total_value += score
                    else:
                        total_value -= score
        # Repetition Penalty: Discourage moving to a state that has already occurred.
        position_hash = board.get_position_hash(turn)
        repetitions = board.position_history.get(position_hash, 0)
        repetition_penalty = 0
        if repetitions > 0:
            # Penalize the first repetition slightly, and subsequent ones more harshly.
            repetition_penalty = 150 * repetitions
        # The evaluation is always from the perspective of self.color.
        # Subtracting the penalty makes this repeated move less attractive.
        return total_value - repetition_penalty

    def minmax(
        self, board: Board, depth: int, alpha: float, beta: float, maximizing_player: bool
    ) -> Tuple[float, Optional[Tuple]]:
        """
        Implements the minimax algorithm with alpha-beta pruning to find the best move.

        This is a recursive function that explores future game states to a certain
        `depth`, evaluating the outcome of each move. Alpha-beta pruning is used
        to cut off branches of the search tree that are guaranteed to be worse
        than a previously found move, significantly speeding up the search.

        Args:
            board (Board): The current board state.
            depth (int): The remaining depth to search.
            alpha (float): The best score found so far for the maximizing player.
            beta (float): The best score found so far for the minimizing player.
            maximizing_player (bool): True if the current player is the AI (maximizer),
                                      False if it's the opponent (minimizer).

        Returns:
            Tuple[float, Optional[Tuple]]: A tuple containing the best evaluation score
                                           and the corresponding move.
        """
        current_player_color = (
            self.color if maximizing_player else (PieceColor.BLACK if self.color == PieceColor.WHITE else PieceColor.WHITE)
        )
        if depth == 0:
            return self.evaluate_board(board, current_player_color), None
        legal_moves = self.get_legal_moves(board, current_player_color)
        if not legal_moves:
            # If there are no legal moves, the game is over (checkmate or stalemate).
            if board.is_color_in_check(current_player_color):
                # Checkmate: worst possible score for the current player.
                score = float("-inf") if maximizing_player else float("inf")
                return score, None
            else:
                # Stalemate: a neutral score of 0.
                return 0, None
        # Score moves to prioritize captures. This makes alpha-beta pruning much more effective.
        def score_move(move):
            start_pos, end_pos = move
            score = 0
            captured_piece = board.grid[end_pos[0]][end_pos[1]]
            if captured_piece:
                # Prioritize capturing a high-value piece with a low-value one
                attacking_piece = board.grid[start_pos[0]][start_pos[1]]
                score = 10 * self.PIECE_VALUES[captured_piece.symbol.upper()] - self.PIECE_VALUES[attacking_piece.symbol.upper()]
            return score
        sorted_moves = sorted(legal_moves, key=score_move, reverse=True)
        best_move = sorted_moves[0]  # Default to the best-scored move
        if maximizing_player:
            max_eval = float("-inf")
            for move in sorted_moves:
                start_pos, end_pos = move
                original_piece = board.grid[start_pos[0]][start_pos[1]]
                captured_piece = board.grid[end_pos[0]][end_pos[1]]
                board.grid[end_pos[0]][end_pos[1]] = original_piece
                board.grid[start_pos[0]][start_pos[1]] = None
                original_piece.set_position(end_pos)
                eval_score, _ = self.minmax(board, depth - 1, alpha, beta, False)
                board.grid[start_pos[0]][start_pos[1]] = original_piece
                board.grid[end_pos[0]][end_pos[1]] = captured_piece
                original_piece.set_position(start_pos)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:  # Minimizing Player
            min_eval = float("inf")
            for move in sorted_moves:
                start_pos, end_pos = move
                original_piece = board.grid[start_pos[0]][start_pos[1]]
                captured_piece = board.grid[end_pos[0]][end_pos[1]]
                board.grid[end_pos[0]][end_pos[1]] = original_piece
                board.grid[start_pos[0]][start_pos[1]] = None
                original_piece.set_position(end_pos)
                eval_score, _ = self.minmax(board, depth - 1, alpha, beta, True)
                board.grid[start_pos[0]][start_pos[1]] = original_piece
                board.grid[end_pos[0]][end_pos[1]] = captured_piece
                original_piece.set_position(start_pos)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_easy_move(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Selects a move for the 'Easy' difficulty level.

        The strategy is to find the highest-value capture available. If no
        captures are possible, it makes a random legal move.

        Args:
            board (Board): The current game board.

        Returns:
            A legal move, or None if no moves are available.
        """
        legal_moves = self.get_legal_moves(board, self.color)
        if not legal_moves:
            return None
        best_capture_score = -1
        best_move = None
        for move in legal_moves:
            end_pos = move[1]
            captured_piece = board.grid[end_pos[0]][end_pos[1]]
            if captured_piece:
                score = self.PIECE_VALUES[captured_piece.get_symbol().upper()]
                if score > best_capture_score:
                    best_capture_score = score
                    best_move = move
        if best_move:
            return best_move
        return random.choice(legal_moves)

    def get_medium_move(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Selects a move for the 'Medium' difficulty level.

        This method uses the minimax algorithm with a search depth of 2 to find
        the best move according to the evaluation function.

        Args:
            board (Board): The current game board.

        Returns:
            The best move found by the minimax search, or None.
        """
        score, best_move = self.minmax(board, 2, float("-inf"), float("inf"), True)
        return best_move

    def get_hard_move(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Selects a move for the 'Hard' difficulty level.

        This method uses the minimax algorithm with a search depth of 3, allowing
        it to look further ahead and make more strategic decisions than the
        medium difficulty.

        Args:
            board (Board): The current game board.

        Returns:
            The best move found by the minimax search, or None.
        """
        score, best_move = self.minmax(board, 3, float("-inf"), float("inf"), True)
        return best_move