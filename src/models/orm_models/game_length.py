from sqlalchemy import Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from .base import Base


class GameLength(Base):
    """
    Represents a single entry for a game's lengths.

    References games table (one to many relationship).
    """

    __tablename__ = "game_lengths"

    game_lengths_id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE")
    )
    playstyle: Mapped[Optional[str]] = mapped_column(String(255))
    avg_hours: Mapped[Optional[float]] = mapped_column(Numeric(precision=6, scale=2))
    leisure_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=6, scale=2)
    )
    median_hours: Mapped[Optional[float]] = mapped_column(Numeric(precision=6, scale=2))
    rushed_hours: Mapped[Optional[float]] = mapped_column(Numeric(precision=6, scale=2))
    num_players_polled: Mapped[Optional[int]] = mapped_column(Integer)
