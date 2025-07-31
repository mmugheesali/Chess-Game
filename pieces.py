"""
pieces.py - Chess Piece Definitions

This module defines the abstract base class for a chess piece and all the
concrete piece implementations (Pawn, Rook, Knight, Bishop, Queen, King).
It includes their specific movement logic and attributes.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from enum import Enum


class PieceColor(Enum):
    WHITE = "white"
    BLACK = "black"

    def __str__(self):
        return self.value


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
