from __future__ import annotations
from typing import List, Optional, Tuple
from enum import Enum


class PieceColor(Enum):
    WHITE = "white"
    BLACK = "black"

    def __str__(self):
        return self.value


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


class Piece:
    """
    Base class for all chess pieces.

    This class defines the common attributes and behaviors that all chess pieces share,
    including position tracking, color, and movement validation. It serves as an abstract
    base class that specific piece types (Pawn, Knight, Bishop, etc.) will inherit from
    and extend with their own movement rules.

    Attributes:
        color (PieceColor): Color of the piece (white or black)
        position (str): Position of the piece on the board as a tuple (column, row)
        symbol (str): Character representation of the piece
    """

    def __init__(self, color, position, symbol):
        self.color = color
        self.position = position
        self.symbol = symbol

    def is_valid_move(self, current_pos, next_pos, board):
        """Abstract method to check if a move is valid for the piece."""
        raise NotImplementedError("Subclasses should implement this method")

    def get_position(self) -> Tuple[int, int]:
        """Return the current position of the piece as a tuple (column, row)."""
        return self.position

    def get_algebraic_position(self) -> str:
        """Return the current position of the piece in algebraic notation (e.g., 'e4')."""
        return str(chr((self.position[0] + 1) + 96)) + str(self.position[1] + 1)

    def set_position(self, newPos: Tuple[int, int]):
        """Set the position of the piece to a new position."""
        self.position = newPos

    def get_color(self) -> PieceColor:
        """Return the color of the piece ('white' or 'black')."""
        return self.color

    def get_symbol(self) -> str:
        """Return the symbol of the piece (e.g., 'P' for Pawn, 'R' for Rook)."""
        return self.symbol


class Pawn(Piece):
    """
    Class representing a Pawn chess piece.

    Pawns move forward one square, with the option to move two squares on their first move.
    They capture diagonally forward one square. White pawns move up the board, while
    black pawns move down.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "P" if color == PieceColor.WHITE else "p")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        """Check if the pawn's move is valid based on its current position and the next position."""
        current_x, current_y = current_pos
        new_x, new_y = next_pos
        movement: int = new_y - current_y
        if current_x == new_x and not grid[new_x][new_y]:  # vertical movement with no piece in the new position
            if super().get_color() == PieceColor.WHITE:
                if current_y == 1:  # checks if it's the first move as the pawns can move two squares in first move
                    if movement > 0 and movement < 3:
                        return True
                elif movement == 1:  # regular forward movement (one square only)
                    return True
            else:
                if current_y == 6:  # checks if it's the first move as the pawns can move two squares in first move
                    if movement > -3 and movement < 0:
                        return True
                elif movement == -1:  # regular forward movement (one square only)
                    return True
        else:  # diagonal capture logic
            x_movement: int = new_x - current_x
            new_piece: Optional[Piece] = grid[new_x][new_y]
            if (x_movement == -1 or x_movement == 1) and new_piece is not None:  # Checks if there is a piece in diagonal
                if super().get_color() == PieceColor.WHITE:
                    if movement == 1 and new_piece.get_color() == PieceColor.BLACK:
                        return True
                elif super().get_color() == PieceColor.BLACK:
                    if movement == -1 and new_piece.get_color() == PieceColor.WHITE:
                        return True
        return False


class Rook(Piece):
    """
    Class representing a Rook chess piece.

    Rooks move horizontally or vertically any number of squares, but cannot
    jump over other pieces.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "R" if color == PieceColor.WHITE else "r")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        """Check if the rook's move is valid based on its current position and the next position."""
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        y_movement: int = next_y - current_y
        x_movement: int = next_x - current_x
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == super().get_color():
            return False  # cannot capture own piece

        if x_movement == 0 and y_movement != 0:  # Check vertical movement (same x, different y)
            start_y: int = min(current_y, next_y) + 1
            end_y: int = max(current_y, next_y)

            # Check for pieces in the path (excluding start and end positions)
            for i in range(start_y, end_y):
                if grid[current_x][i]:
                    return False
            return True

        elif x_movement != 0 and y_movement == 0:  # Check horizontal movement (different x, same y)
            start_x: int = min(current_x, next_x) + 1
            end_x: int = max(current_x, next_x)

            # Check for pieces in the path (excluding start and end positions)
            for i in range(start_x, end_x):
                if grid[i][current_y]:
                    return False
            return True

        return False  # Not a valid rook move (must be either horizontal or vertical)


class Knight(Piece):
    """
    Class representing a Knight chess piece.

    Knights move in an L-shape: two squares horizontally then one square vertically,
    or two squares vertically then one square horizontally. Knights can jump over
    other pieces.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "N" if color == PieceColor.WHITE else "n")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        """Check if the knight's move is valid based on its current position and the next position."""
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        x_movement: int = next_x - current_x
        y_movement: int = next_y - current_y
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == super().get_color():
            return False  # cannot capture own piece
        if x_movement != 0 and y_movement != 0:  # non-orthogonal movement
            if y_movement > -3 and y_movement < 3 and x_movement > -3 and x_movement < 3:  # check if within L-shape range
                if (y_movement == 2 or y_movement == -2) and (
                    x_movement == 1 or x_movement == -1
                ):  # L-shape: 2 vertical, 1 horizontal
                    return True
                if (y_movement == 1 or y_movement == -1) and (
                    x_movement == 2 or x_movement == -2
                ):  # L-shape: 1 vertical, 2 horizontal
                    return True
        return False


class Bishop(Piece):
    """
    Class representing a Bishop chess piece.

    Bishops move diagonally any number of squares, but cannot jump over other pieces.
    They always remain on squares of the same color.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "B" if color == PieceColor.WHITE else "b")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        x_movement: int = next_x - current_x
        y_movement: int = next_y - current_y
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == super().get_color():
            return False  # cannot capture own piece
        if abs(x_movement) == abs(y_movement) and x_movement != 0:  # diagonal movement (like a bishop)
            dx = 1 if x_movement > 0 else -1
            dy = 1 if y_movement > 0 else -1
            x, y = current_x + dx, current_y + dy
            while x != next_x:
                if grid[x][y]:
                    return False
                x += dx
                y += dy
            return True


class Queen(Piece):
    """
    Class representing a Queen chess piece.

    Queens combine the movement powers of a Rook and Bishop. They can move any number
    of squares horizontally, vertically, or diagonally, but cannot jump over other pieces.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "Q" if color == PieceColor.WHITE else "q")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        x_movement: int = next_x - current_x
        y_movement: int = next_y - current_y
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == super().get_color():
            return False  # cannot capture own piece
        if x_movement == 0 and y_movement != 0:  # vertical movement (like a rook)
            start_y: int = min(current_y, next_y) + 1
            end_y: int = max(current_y, next_y)
            for i in range(start_y, end_y):  # check path for obstacles
                if grid[current_x][i]:
                    return False
            return True
        elif x_movement != 0 and y_movement == 0:  # horizontal movement (like a rook)
            start_x: int = min(current_x, next_x) + 1
            end_x: int = max(current_x, next_x)
            for i in range(start_x, end_x):  # check path for obstacles
                if grid[i][current_y]:
                    return False
            return True
        elif abs(x_movement) == abs(y_movement) and x_movement != 0:  # diagonal movement (like a bishop)
            dx = 1 if x_movement > 0 else -1
            dy = 1 if y_movement > 0 else -1
            x, y = current_x + dx, current_y + dy
            while x != next_x and y != next_y:
                if grid[x][y]:
                    return False
                x += dx
                y += dy
            return True
        return False


class King(Piece):
    """
    Class representing a King chess piece.

    Kings can move one square in any direction (horizontally, vertically, or diagonally).
    The king is the most important piece that must be protected from checkmate.

    Attributes:
        Inherits all attributes from Piece class
    """

    def __init__(self, color, position):
        super().__init__(color, position, "K" if color == PieceColor.WHITE else "k")

    def is_valid_move(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int], grid: List[List[Optional[Piece]]]) -> bool:
        """Check if the king's move is valid based on its current position and the next position."""
        current_x, current_y = current_pos
        next_x, next_y = next_pos
        x_movement: int = next_x - current_x
        y_movement: int = next_y - current_y
        if grid[next_x][next_y] and grid[next_x][next_y].get_color() == super().get_color():
            return False  # cannot capture own piece
        if x_movement != 0 or y_movement != 0:  # ensure some movement is happening
            if (
                x_movement > -2 and x_movement < 2 and y_movement > -2 and y_movement < 2
            ):  # check movement is at most one square in any direction
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
