"""
enums.py - Game Enumerations

This module defines the enumerations used throughout the chess game application.
These enums provide type safety and clear, readable constants for game states,
piece colors, difficulty levels, and game modes.
"""

from enum import Enum


class PieceColor(Enum):
    """
    Enumeration for chess piece colors.

    Values:
        WHITE: Represents white pieces (moves first)
        BLACK: Represents black pieces (moves second)
    """

    WHITE = "white"
    BLACK = "black"

    def opposite(self) -> "PieceColor":
        """Returns the opposite color."""
        return PieceColor.BLACK if self == PieceColor.WHITE else PieceColor.WHITE

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class Difficulty(Enum):
    """
    Enumeration for AI difficulty levels.

    Values:
        EASY: Simple capture-focused AI with random moves
        MEDIUM: Minimax with depth 2 search
        HARD: Minimax with depth 3+ search
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class GameMode(Enum):
    """
    Enumeration for different game modes.

    Values:
        PLAYER_VS_PLAYER: Two human players
        PLAYER_VS_AI: One human player against AI
    """

    PLAYER_VS_PLAYER = "player_vs_player"
    PLAYER_VS_AI = "player_vs_ai"

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class GameStatus(Enum):
    """
    Enumeration for game status states.

    Values:
        NOT_STARTED: Game has not been initialized
        ACTIVE: Game is in progress
        CHECKMATE: Game ended by checkmate
        STALEMATE: Game ended by stalemate
        DRAW: Game ended in a draw (by repetition, etc.)
    """

    NOT_STARTED = "not_started"
    ACTIVE = "active"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW = "draw"

    def __str__(self):
        """Return the string value of the enum member."""
        return self.value
