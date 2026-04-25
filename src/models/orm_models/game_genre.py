from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class GameGenre(Base):
    """Junction table - (map game id to genre id for lookup)"""

    __tablename__ = "game_genres"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.genre_id", ondelete="CASCADE"), primary_key=True
    )
