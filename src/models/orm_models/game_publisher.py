from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class GamePublisher(Base):
    """Junction table - (map game id to publisher id for lookup)"""

    __tablename__ = "game_publishers"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True
    )
    publisher_id: Mapped[int] = mapped_column(
        ForeignKey("publishers.publisher_id", ondelete="CASCADE"), primary_key=True
    )
