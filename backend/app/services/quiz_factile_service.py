"""
Factile (Jeopardy-style) Quiz Service.

Game flow:
1. Teacher creates session with categories (each has question_ids + point values)
2. Students join and get auto-assigned to 2 teams
3. Teacher starts game → board is broadcast
4. Teams take turns: teacher selects a cell → question appears
5. Team answers verbally → teacher judges correct/wrong
6. If wrong → other team can try (pass_to_other)
7. Teacher reveals answer → cell is closed, turn advances
8. Game ends when all cells are played (or teacher finishes early)
"""
import logging
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import QuizSession, QuizTeam, QuizSessionStatus
from app.models.test import Question, QuestionOption
from app.repositories.quiz_repo import QuizRepository
from app.repositories.quiz_team_repo import QuizTeamRepository

logger = logging.getLogger(__name__)


class QuizFactileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizRepository(db)
        self.team_repo = QuizTeamRepository(db)

    # ── Board initialization ──

    async def init_board(
        self,
        session_id: int,
        categories: list[dict],
        point_values: list[int],
    ) -> dict:
        """Initialize the Factile board state after session creation.

        Args:
            categories: [{"name": str, "question_ids": [int, ...]}]
            point_values: [100, 200, 300, 400, 500]

        Returns:
            board_state dict ready for storage in quiz_sessions.board_state
        """
        # Get teams for this session
        teams = await self.team_repo.get_teams(session_id)
        if len(teams) < 2:
            raise ValueError("Factile requires exactly 2 teams")

        total_cells = 0
        board_categories = []
        for cat in categories:
            cells = []
            for i, qid in enumerate(cat["question_ids"]):
                points = point_values[i] if i < len(point_values) else point_values[-1]
                cells.append({
                    "question_id": qid,
                    "points": points,
                    "status": "available",
                    "answered_by_team_id": None,
                    "is_correct": None,
                })
                total_cells += 1
            board_categories.append({
                "name": cat["name"],
                "cells": cells,
            })

        board_state = {
            "categories": board_categories,
            "team_ids": [teams[0].id, teams[1].id],
            "current_team_index": 0,
            "active_cell": None,
            "cells_remaining": total_cells,
            "pass_to_other": False,
        }

        # Save board_state
        await self.db.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(board_state=board_state)
        )

        return board_state

    # ── Cell selection ──

    async def select_cell(
        self, session_id: int, category_index: int, row_index: int,
    ) -> dict:
        """Teacher selects a cell on the board. Returns question data."""
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")

        board = session.board_state
        if not board:
            raise ValueError("Board not initialized")
        if board.get("active_cell"):
            raise ValueError("A cell is already active — judge it first")

        if category_index < 0 or category_index >= len(board["categories"]):
            raise ValueError("Invalid category index")

        cat = board["categories"][category_index]
        if row_index < 0 or row_index >= len(cat["cells"]):
            raise ValueError("Invalid row index")

        cell = cat["cells"][row_index]
        if cell["status"] != "available":
            raise ValueError("Cell already played")

        # Mark cell as active
        cell["status"] = "active"
        board["active_cell"] = {"category": category_index, "row": row_index}
        board["pass_to_other"] = False

        await self._save_board(session_id, board)
        await self.db.commit()

        # Load the question
        question_data = await self._load_question(cell["question_id"])

        # Get current team info
        teams = await self.team_repo.get_teams(session_id)
        current_team = teams[board["current_team_index"]] if board["current_team_index"] < len(teams) else teams[0]

        return {
            "category_index": category_index,
            "category_name": cat["name"],
            "row_index": row_index,
            "points": cell["points"],
            "question": question_data,
            "team_name": current_team.name,
            "team_id": current_team.id,
        }

    # ── Judge answer ──

    async def judge_correct(self, session_id: int) -> dict:
        """Teacher marks current answer as correct."""
        return await self._judge(session_id, is_correct=True)

    async def judge_wrong(self, session_id: int) -> dict:
        """Teacher marks current answer as wrong. Other team can try."""
        return await self._judge(session_id, is_correct=False)

    async def _judge(self, session_id: int, is_correct: bool) -> dict:
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")

        board = session.board_state
        if not board or not board.get("active_cell"):
            raise ValueError("No active cell to judge")

        ac = board["active_cell"]
        cell = board["categories"][ac["category"]]["cells"][ac["row"]]
        teams = await self.team_repo.get_teams(session_id)
        current_idx = board["current_team_index"]
        current_team = teams[current_idx]

        if is_correct:
            # Award points to the current team
            await self.team_repo.update_team_score(current_team.id, cell["points"], True)
            cell["status"] = "answered"
            cell["answered_by_team_id"] = current_team.id
            cell["is_correct"] = True
            board["active_cell"] = None
            board["cells_remaining"] -= 1
            board["pass_to_other"] = False
            # Turn passes to the OTHER team after correct answer
            board["current_team_index"] = 1 - current_idx

            await self._save_board(session_id, board)
            await self.db.commit()

            # Reload teams for updated scores
            teams = await self.team_repo.get_teams(session_id)
            team_scores = self._team_scores(teams)

            return {
                "is_correct": True,
                "points": cell["points"],
                "team_name": current_team.name,
                "team_id": current_team.id,
                "team_scores": team_scores,
                "next_team_name": teams[board["current_team_index"]].name,
                "pass_to_other": False,
                "cells_remaining": board["cells_remaining"],
            }
        else:
            # Wrong answer
            if board.get("pass_to_other"):
                # Second team also got it wrong — close the cell
                cell["status"] = "answered"
                cell["is_correct"] = False
                board["active_cell"] = None
                board["cells_remaining"] -= 1
                board["pass_to_other"] = False
                # Turn stays with the team that originally selected
                # (the other team already tried, turn goes to next)
                board["current_team_index"] = 1 - current_idx

                await self._save_board(session_id, board)
                await self.db.commit()

                team_scores = self._team_scores(teams)
                return {
                    "is_correct": False,
                    "points": 0,
                    "team_name": current_team.name,
                    "team_id": current_team.id,
                    "team_scores": team_scores,
                    "next_team_name": teams[board["current_team_index"]].name,
                    "pass_to_other": False,
                    "cells_remaining": board["cells_remaining"],
                }
            else:
                # First wrong — pass to other team
                board["pass_to_other"] = True
                board["current_team_index"] = 1 - current_idx

                await self._save_board(session_id, board)
                await self.db.commit()

                team_scores = self._team_scores(teams)
                other_team = teams[board["current_team_index"]]
                return {
                    "is_correct": False,
                    "points": 0,
                    "team_name": current_team.name,
                    "team_id": current_team.id,
                    "team_scores": team_scores,
                    "next_team_name": other_team.name,
                    "pass_to_other": True,
                    "cells_remaining": board["cells_remaining"],
                }

    # ── Reveal answer ──

    async def reveal_answer(self, session_id: int) -> dict:
        """Reveal the correct answer for the active cell."""
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        board = session.board_state
        if not board or not board.get("active_cell"):
            raise ValueError("No active cell")

        ac = board["active_cell"]
        cell = board["categories"][ac["category"]]["cells"][ac["row"]]

        # Load question to find correct answer
        question_data = await self._load_question(cell["question_id"])
        correct_option = None
        correct_text = ""
        for i, opt in enumerate(question_data.get("options", [])):
            if opt.get("is_correct"):
                correct_option = i
                correct_text = opt["text"]
                break

        return {
            "correct_option": correct_option,
            "correct_text": correct_text,
        }

    # ── Skip cell ──

    async def skip_cell(self, session_id: int) -> dict:
        """Skip the active cell without awarding points."""
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")

        board = session.board_state
        if not board or not board.get("active_cell"):
            raise ValueError("No active cell to skip")

        ac = board["active_cell"]
        cell = board["categories"][ac["category"]]["cells"][ac["row"]]
        cell["status"] = "skipped"
        board["active_cell"] = None
        board["cells_remaining"] -= 1
        board["pass_to_other"] = False
        # Turn advances to the other team
        board["current_team_index"] = 1 - board["current_team_index"]

        await self._save_board(session_id, board)
        await self.db.commit()

        teams = await self.team_repo.get_teams(session_id)
        return {
            "cells_remaining": board["cells_remaining"],
            "team_scores": self._team_scores(teams),
            "next_team_name": teams[board["current_team_index"]].name,
        }

    # ── Get board for broadcast ──

    async def get_board_message(self, session_id: int) -> dict:
        """Build the board state message for WS broadcast."""
        session = await self.repo.get_session(session_id)
        if not session or not session.board_state:
            raise ValueError("Board not initialized")

        board = session.board_state
        teams = await self.team_repo.get_teams(session_id)
        team_scores = self._team_scores(teams)
        current_team = teams[board["current_team_index"]] if board["current_team_index"] < len(teams) else teams[0]

        # Sanitize categories for clients (hide question_id)
        categories = []
        for cat in board["categories"]:
            cells = []
            for cell in cat["cells"]:
                cells.append({
                    "points": cell["points"],
                    "status": cell["status"],
                    "answered_by_team_id": cell.get("answered_by_team_id"),
                })
            categories.append({"name": cat["name"], "cells": cells})

        return {
            "categories": categories,
            "team_scores": team_scores,
            "current_team_index": board["current_team_index"],
            "current_team_name": current_team.name,
            "cells_remaining": board["cells_remaining"],
            "active_cell": board.get("active_cell"),
            "pass_to_other": board.get("pass_to_other", False),
        }

    # ── Finish ──

    async def get_winner(self, session_id: int) -> dict:
        """Determine winner based on team scores."""
        teams = await self.team_repo.get_teams(session_id)
        if not teams:
            return {}

        sorted_teams = sorted(teams, key=lambda t: t.total_score, reverse=True)
        winner = sorted_teams[0]
        team_scores = self._team_scores(sorted_teams)

        return {
            "team_scores": team_scores,
            "winner_team_name": winner.name,
            "winner_team_id": winner.id,
        }

    # ── Helpers ──

    async def _save_board(self, session_id: int, board: dict):
        """Persist board_state to DB."""
        await self.db.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(board_state=board)
        )

    async def _load_question(self, question_id: int) -> dict:
        """Load question with options from DB."""
        result = await self.db.execute(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.id == question_id, Question.is_deleted == False)
        )
        q = result.scalar_one_or_none()
        if not q:
            return {"text": "Question not found", "options": [], "question_type": "single_choice"}

        options = sorted(
            [o for o in q.options if not o.is_deleted],
            key=lambda o: o.sort_order,
        )

        return {
            "text": q.question_text,
            "question_type": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
            "options": [
                {"text": o.option_text, "is_correct": o.is_correct}
                for o in options
            ],
            "image_url": getattr(q, 'image_url', None),
        }

    def _team_scores(self, teams: list[QuizTeam]) -> list[dict]:
        return [
            {
                "id": t.id,
                "name": t.name,
                "color": t.color,
                "score": t.total_score,
                "correct_answers": t.correct_answers,
            }
            for t in teams
        ]
