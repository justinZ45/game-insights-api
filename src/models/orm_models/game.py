from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from .base import Base
from .game_length import GameLength
from .game_genre import GameGenre
from .game_publisher import GamePublisher


class Game(Base):
    """Represents a single video game entry"""

    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True)
    lengths: Mapped[list["GameLength"]] = relationship(
        "GameLength", backref="game", cascade="all, delete-orphan"
    )
    genres: Mapped[list["GameGenre"]] = relationship(
        "GameGenre", backref="game", cascade="all, delete-orphan"
    )
    publishers: Mapped[list["GamePublisher"]] = relationship(
        "GamePublisher", backref="game", cascade="all, delete-orphan"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_handheld: Mapped[Optional[bool]]
    max_players: Mapped[Optional[int]]
    is_multiplatform: Mapped[Optional[bool]]
    is_online: Mapped[Optional[bool]]
    is_licensed: Mapped[Optional[bool]]
    is_sequel: Mapped[Optional[bool]]
    review_score: Mapped[Optional[int]]
    sales_millions_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    used_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    console: Mapped[Optional[str]] = mapped_column(String(255))
    esrb_rating: Mapped[Optional[str]] = mapped_column(String(5))
    is_re_release: Mapped[Optional[bool]]
    release_year: Mapped[Optional[int]]
