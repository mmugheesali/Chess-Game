"""
pieces.py - Chess Piece Definitions

This module defines the abstract base class for a chess piece and all the
concrete piece implementations (Pawn, Rook, Knight, Bishop, Queen, King).
It includes their specific movement logic and attributes.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from enums import PieceColor


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
            (x + 1, y + 2),
            (x - 1, y + 2),
            (x + 1, y - 2),
            (x - 1, y - 2),
            (x + 2, y + 1),
            (x - 2, y + 1),
            (x + 2, y - 1),
            (x - 2, y - 1),
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
