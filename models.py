from __future__ import annotations
from typing import List, Optional, Tuple
from enum import Enum
from pieces import Piece, PieceColor, Pawn, Rook, Knight, Bishop, Queen, King


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Board:
    """
    Class representing a chess board.

    This class manages the chess board state, including piece placement,
    movement validation, check detection, and checkmate detection.

    Attributes:
        grid (list): 8x8 grid representing the chess board with pieces
        moveHistory (list): List of moves made during the game
    """

    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.moveHistory = []
        self.setup_board()

    def setup_board(self):
        """Initializes the chess board with pieces in their starting positions."""
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

    def move_piece(self, current_pos: Tuple[int, int], new_pos: Tuple[int, int]) -> bool:
        """Move a piece from current position to new position."""
        piece: Optional[Piece] = self.grid[current_pos[0]][current_pos[1]]
        # Check if piece exists and if the move is valid
        if not piece or not piece.is_valid_move(current_pos, new_pos, self.grid):
            return False
        in_check_color: Optional[PieceColor] = self.is_check()  # check if any king is in check
        if in_check_color and piece.get_color() == in_check_color:  # if piece's king is in check
            # Try the move
            captured_piece: Optional[Piece] = self.grid[new_pos[0]][new_pos[1]]  # store potentially captured piece

            # Make the move temporarily
            self.grid[new_pos[0]][new_pos[1]] = piece  # place piece in new position
            self.grid[current_pos[0]][current_pos[1]] = None  # remove piece from current position
            piece.set_position(new_pos)  # update piece's internal position

            still_in_check: bool = self.is_check() == in_check_color  # Check if still in check after the move

            # Undo the move
            self.grid[current_pos[0]][current_pos[1]] = piece  # restore piece to original position
            self.grid[new_pos[0]][new_pos[1]] = captured_piece  # restore captured piece if any
            piece.set_position(current_pos)  # reset piece's internal position

            if still_in_check:
                return False  # Move doesn't resolve check
        self.grid[new_pos[0]][new_pos[1]] = piece  # place piece in new position
        self.grid[current_pos[0]][current_pos[1]] = None  # remove piece from current position
        self.moveHistory.append(
            [piece.get_algebraic_position(), str(chr((new_pos[0] + 1) + 96)) + str(new_pos[1] + 1)]
        )  # add move to history in algebraic notation
        piece.set_position(new_pos)  # update piece's internal position
        return True

    def is_check(self) -> Optional[PieceColor]:
        """Check if either king is in check and return the color of the king in check."""
        white_king_pos: Optional[Piece] = None
        black_king_pos: Optional[Piece] = None
        # Find the positions of both kings
        for column in range(8):
            for row in range(8):
                piece: Optional[Piece] = self.grid[column][row]
                if isinstance(piece, King):  # if piece is a king
                    if piece.get_color() == PieceColor.WHITE:
                        white_king_pos = (column, row)  # store white king position
                    elif piece.get_color() == PieceColor.BLACK:
                        black_king_pos = (column, row)  # store black king position
            if white_king_pos and black_king_pos:
                break

        # Check if any piece can attack the opposing king
        for column in range(8):
            for row in range(8):
                piece: Optional[Piece] = self.grid[column][row]
                if piece:
                    if piece.get_color() == PieceColor.WHITE and black_king_pos:  # if white piece and black king exists
                        if piece.is_valid_move((column, row), black_king_pos, self.grid):  # check if piece can attack black king
                            return PieceColor.BLACK  # black king is in check
                    elif piece.get_color() == PieceColor.BLACK and white_king_pos:  # if black piece and white king exists
                        if piece.is_valid_move((column, row), white_king_pos, self.grid):  # check if piece can attack white king
                            return PieceColor.WHITE  # white king is in check

        return None

    def is_checkmate(self, checked_color) -> bool:
        """Check if the player whose king is in check has no valid moves to escape check."""

        # Try every possible move for the checked player
        for col1 in range(8):
            for row1 in range(8):
                piece: Optional[Piece] = self.grid[col1][row1]
                if piece and piece.get_color() == checked_color:
                    for col2 in range(8):
                        for row2 in range(8):
                            if piece.is_valid_move((col1, row1), (col2, row2), self.grid):
                                # Save original state
                                captured = self.grid[col2][row2]
                                self.grid[col2][row2] = piece
                                self.grid[col1][row1] = None
                                original_pos = piece.position
                                piece.set_position((col2, row2))

                                still_in_check = self.is_check() == checked_color

                                # Undo
                                self.grid[col1][row1] = piece
                                self.grid[col2][row2] = captured
                                piece.set_position(original_pos)

                                if not still_in_check:
                                    return False
        return True


class Game:
    """
    Class representing a chess game.
    This class manages the game state, including the chess board, current turn,
    game status, and player turns. It provides methods to start the game, make moves,
    check game status, and retrieve the current game state.
    Attributes:
        board (Board): The chess board for the game.
        turn (str): The color of the player whose turn it is ('white' or 'black').
        game_status (str): The current status of the game ('active', 'checkmate', 'stalemate', 'draw').
        winner (Optional[str]): The color of the winning player, if any.
        difficulty (Difficulty): The difficulty level of the game.
    """

    def __init__(self):
        self.board = None
        self.turn = PieceColor.WHITE  # Default starting player
        self.game_status = "not_started"  # Can be "active", "checkmate", "stalemate", "draw"
        self.winner = None
        self.difficulty = Difficulty.MEDIUM  # Default difficulty level
        self.player_white = ""
        self.player_black = ""

    def start_game(self, difficulty: Difficulty, white_player: str, black_player: str):
        """Initialize a new game with the specified difficulty level"""
        self.board = Board()
        self.turn = PieceColor.WHITE
        self.game_status = "active"
        self.winner = None
        self.difficulty: Difficulty = difficulty
        self.player_white = white_player
        self.player_black = black_player

    def end_game(self):
        """End the game and reset the board"""
        self.board = None
        self.turn = PieceColor.WHITE
        self.game_status = "not_started"
        self.winner = None
        self.difficulty = Difficulty.MEDIUM
        self.player_white = ""
        self.player_black = ""

    def serialize_board_to_symbols(self, board_grid):
        """Converts the Board object's grid into a simple 2D list of piece symbols."""
        if not board_grid:
            return None

        serialized_grid = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                piece = board_grid[c][r]
                if piece:
                    serialized_grid[r][c] = piece.get_symbol()
        return serialized_grid

    def get_game_state(self):
        """Return the current state of the game"""
        check: Optional[PieceColor] = self.board.is_check()
        return {
            "board": self.serialize_board_to_symbols(self.board.grid),
            "turn": self.turn.value,
            "status": self.game_status,
            "winner": str(self.winner.value) if self.winner else None,
            "is_check": check.value if check else None,
            "move_history": self.get_move_history(),
            "players": {"white": self.player_white, "black": self.player_black},
        }

    def make_move(self, current_pos: Tuple[list, list], new_pos: Tuple[list, list]) -> (bool, str):
        """Process a move and update game state accordingly"""
        # Check if game is already over
        if self.game_status != "active":
            return False, f"Game already ended: {self.game_status}"

        # Check if it's the correct player's turn
        piece = self.board.grid[current_pos[0]][current_pos[1]]
        if not piece:
            return False, "No piece at the starting position"

        # Validate piece color
        if piece.get_color() != self.turn:
            return False, f"It's {self.turn}'s turn to move"

        # Attempt to make the move
        move_successful = self.board.move_piece(current_pos, new_pos)
        if not move_successful:
            if self.board.is_check():
                return False, "Invalid move: King is in check"
            return False, "Invalid move for the piece"

        # Check for checkmate and stalemate after move
        self.check_game_end_conditions()

        # Change turn if game is still active
        if self.game_status == "active":
            self.turn = PieceColor.BLACK if self.turn == PieceColor.WHITE else PieceColor.WHITE

        return True, "Move successful"

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

    def get_move_history(self):
        """Return the history of moves in the game"""
        return self.board.moveHistory


class AIPlayer:
    """
    Class representing an AI player in the chess game.
    This class is responsible for making moves based on the difficulty level.
    Attributes:
        difficulty (Difficulty): The difficulty level of the AI player.
    """

    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty

    def get_best_move(self):
        pass
