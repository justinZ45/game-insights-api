from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .game_genre import GameGenre


class Genre(Base):
    """Lookup table - represents a single unique entry per game Genre"""

    __tablename__ = "genres"

    game_links: Mapped[list["GameGenre"]] = relationship(
        "GameGenre", backref="genre", cascade="all, delete-orphan"
    )

    genre_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
