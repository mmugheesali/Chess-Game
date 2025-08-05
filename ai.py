"""
ai.py - AI Player Logic for Chess
This module defines the AIPlayer class, which is responsible for determining the
best move for an AI opponent. It uses the minimax algorithm with alpha-beta pruning
and a custom board evaluation function to make decisions. The AI's strength
can be adjusted via different difficulty levels.
"""

from __future__ import annotations
from typing import Optional, List, Tuple, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from models import Board
from enums import Difficulty, PieceColor


class AIPlayer:
    """
    Represents an AI player that can make moves based on a difficulty level.
    This class uses a material and positional evaluation function and a minimax algorithm with alpha-beta pruning
    to determine the best move for the AI.
    Attributes:
        difficulty (Difficulty): The difficulty level of the AI.
        color (PieceColor): The color of the AI player.
        PIECE_VALUES (Dict[str, int]): A dictionary mapping piece symbols to their values.
        POSITION_TABLES (Dict[str, List[List[int]]]): A dictionary mapping piece symbols to their
            position evaluation tables, which provide a score based on the piece's position on the board.
    """

    # Piece-Square Tables for positional evaluation.
    # These tables are for WHITE. For BLACK, the row index is flipped (7 - row).
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
            "P": self.PAWN_TABLE,
            "N": self.KNIGHT_TABLE,
            "B": self.BISHOP_TABLE,
            "R": self.ROOK_TABLE,
            "Q": self.QUEEN_TABLE,
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
            score, best_move = self.minmax(board, 2, float("-inf"), float("inf"), True)
            return best_move
        elif self.difficulty == Difficulty.HARD:
            score, best_move = self.minmax(board, 3, float("-inf"), float("inf"), True)
            return best_move
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
