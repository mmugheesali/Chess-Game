"""
models.py - Chess Game Logic and Data Structures

This module defines the core classes and logic for a chess game. It is responsible
for representing the board, pieces, and game state. It includes rules for
piece movement, move validation, check/checkmate detection, and a simple AI player.

The coordinate system used throughout this module is a 0-indexed tuple `(column, row)`,
where `(0, 0)` corresponds to the 'a1' square.

Classes:
    Board: Manages the 8x8 grid, piece placement, and move validation.
    Game: High-level controller for the game state, turns, and player management.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from enums import Difficulty, GameMode, PieceColor
from pieces import Piece, Pawn, Rook, Knight, Bishop, Queen, King
from ai import AIPlayer


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
                if isinstance(piece, King) and piece.get_color() == color:
                    king_pos = (col, row)
                    break
                if king_pos:
                    break
        if not king_pos:
            return False

        opponent_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
        return self.is_square_attacked_by(king_pos, opponent_color)

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
